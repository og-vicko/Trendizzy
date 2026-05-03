from ingestion.google_trends import GoogleTrendsIngestor
from ingestion.reddit import RedditIngestor
from storage.database import *
from processing.loader import load_trends_from_json
from processing.filter import filter_trends
from processing.enrichment import enrich_trends
from processing.selection import select_actionable_trends
from loguru import logger

USE_OFFLINE_GOOGLE = True  # Set to False to fetch live from Google Trends
USE_OFFLINE_REDDIT = False  # Reddit has no rate limit issues — always fetch live by default

GOOGLE_RAW_JSON = "google_trends_raw.json"
REDDIT_RAW_JSON = "reddit_raw.json"


def main():
    init_db()

    # --- Google Trends ingestion ---
    logger.info("Starting Google Trends ingestion...")
    if USE_OFFLINE_GOOGLE:
        logger.info("Using offline Google Trends JSON")
        google_trends = load_trends_from_json(GOOGLE_RAW_JSON)
    else:
        gt = GoogleTrendsIngestor(geo="GB")
        google_trends = gt.fetch_daily_trends()
        save_raw_data(google_trends, GOOGLE_RAW_JSON)

    save_trends(google_trends)

    # --- Reddit ingestion ---
    logger.info("Starting Reddit ingestion...")
    if USE_OFFLINE_REDDIT:
        logger.info("Using offline Reddit JSON")
        reddit_trends = load_trends_from_json(REDDIT_RAW_JSON)
    else:
        reddit = RedditIngestor(geo="GB")
        reddit_trends = reddit.fetch_hot(limit=25)
        save_raw_data(reddit_trends, REDDIT_RAW_JSON)

    save_trends(reddit_trends)

    # --- Pipeline (runs across all sources combined) ---
    top_trends = get_top_trends(limit=20, min_score=0.1)
    logger.info(f"Pulled {len(top_trends)} trends from DB across all sources")

    actionable_trends = filter_trends(top_trends)

    enriched_trends = enrich_trends(actionable_trends)
    for t in enriched_trends:
        if t.get("enrichment"):
            save_enrichment(t["topic_id"], t["enrichment"])

    selected_trends = select_actionable_trends(enriched_trends)
    save_selected_trends([t["topic_id"] for t in selected_trends])

    logger.success("Selected Actionable Trends:")
    for t in selected_trends:
        e = t.get("enrichment") or {}
        logger.success(
            f"[{t['actionability_score']:.2f}] {t['keyword']} | "
            f"{t.get('source', '?')} | {e.get('category', 'unknown')} | "
            f"{e.get('time_sensitivity', '')} | score={t['score']}"
        )

    logger.success("Pipeline completed")


if __name__ == "__main__":
    main()
