from ingestion.google_trends import GoogleTrendsIngestor
from storage.database import save_raw_data
from loguru import logger


def main():
    logger.info("Starting Google Trends ingestion...")

    gt = GoogleTrendsIngestor(geo="GB")
    trends = gt.fetch_daily_trends()
    save_raw_data(trends, "google_trends_raw.json")

    logger.success("Google Trends ingestion completed")


if __name__ == "__main__":
    main()
