from ingestion.google_trends import GoogleTrendsIngestor
from storage.database import *
from processing.loader import load_trends_from_json
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

    logger.success("Top Trends:")
    for t in top_trends:
        logger.success(
            f"{t['rank']} | {t['keyword']} | score={t['score']}"
        )

    logger.success("Google Trends ingestion completed")

if __name__ == "__main__":
    main()

