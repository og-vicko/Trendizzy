from ingestion.google_trends import GoogleTrendsIngestor
from storage.database import *
from processing.loader import load_trends_from_json
from processing.filter import filter_trends
from processing.enrichment import enrich_trends
from loguru import logger

USE_OFFLINE_JSON = True # Set to True to load from local JSON file instead of fetching live data    
RAW_JSON = "google_trends_raw.json"



def main():
    
    logger.info("Starting Google Trends ingestion...")
    init_db()

    # Load trends from JSON file or fetch live data
    if USE_OFFLINE_JSON:
        logger.info("Using offline JSON data")
        loaded_trends = load_trends_from_json(RAW_JSON)
    else:
        gt = GoogleTrendsIngestor(geo="GB")
        trends = gt.fetch_daily_trends()
        save_raw_data(trends, RAW_JSON) # save raw data to json file for offline use
        loaded_trends = load_trends_from_json(RAW_JSON)

    # Save to DB regardless of whether we fetched live or loaded from JSON
    save_google_trends_from_json(loaded_trends)

    top_trends = get_top_trends(limit=5, min_score=0.1)

    # Filter out junk before doing anything with the trends
    actionable_trends = filter_trends(top_trends)

    # Enrich only trends that haven't been enriched before (enrichment is None in DB)
    # Then save any newly enriched ones back to the DB so future runs skip the API call
    enriched_trends = enrich_trends(actionable_trends)
    for t in enriched_trends:
        if t.get("enrichment"):
            save_enrichment(t["topic_id"], t["enrichment"])

    logger.success("Actionable Trends:")
    for t in enriched_trends:
        e = t.get("enrichment") or {}
        logger.success(
            f"{t['rank']} | {t['keyword']} | score={t['score']} | {e.get('category', 'not enriched')} | {e.get('time_sensitivity', '')}"
        )

    logger.success("Google Trends ingestion completed")

if __name__ == "__main__":
    main()

