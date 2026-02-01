from trendspy import Trends
from datetime import datetime
from loguru import logger


class GoogleTrendsIngestor:
    """
    Ingests Google Trends data using trends.py
    """

    def __init__(self, geo="GB"):
        self.geo = geo
        self.trends = Trends()

    def fetch_daily_trends(self):
        """
        Fetch daily trending searches.
        """
        logger.info("Fetching Google Trends daily searches...")

        try:
            daily_trends = self.trends.trending_now(geo=self.geo)
        except Exception as e:
            logger.error(f"Google Trends fetch failed: {e}")
            raise

        timestamp = datetime.utcnow().isoformat()
        trends = []

        for keyword in daily_trends:
            trends.append({
                "keyword": keyword.keyword, # convert object to string 
                "source": "google_trends",
                "geo": self.geo,
                "fetched_at": timestamp
            })

        logger.success(f"Fetched {len(trends)} Google Trends records")
        return trends
