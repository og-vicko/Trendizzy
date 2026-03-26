from ingestion.google_trends import GoogleTrendsIngestor
from storage.database import *
from processing.loader import load_trends_from_json
from loguru import logger

USE_OFFLINE_JSON = True
RAW_JSON_PATH = "data/raw/google_trends_raw.json"


from storage.database import (
    init_db,
    save_google_trends_from_json,
    get_top_trends,
)

def main():

    logger.info("Starting Google Trends ingestion...")
    init_db()

    if USE_OFFLINE_JSON:
        logger.info("Using offline JSON data")
        loaded_trends = load_trends_from_json(RAW_JSON_PATH)
    else:
        gt = GoogleTrendsIngestor(geo="GB")
        trends = gt.fetch_daily_trends()
        save_raw_data(trends, RAW_JSON_PATH)
        loaded_trends = load_trends_from_json(RAW_JSON_PATH)

    save_google_trends_from_json(loaded_trends)

    top_trends = get_top_trends(limit=5, min_score=0.1)

    logger.success("Top Trends:")
    for t in top_trends:
        logger.success(
            f"{t['rank']} | {t['keyword']} | score={t['score']}"
        )

    logger.success("Google Trends ingestion completed")

if __name__ == "__main__":
    main()

