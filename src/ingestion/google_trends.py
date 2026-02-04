from storage.database import save_raw_data
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

    def rank_and_score(self, trends):
            """
            Rank and score the trends based on SearchCount
            Rank: This is assigned based on the SearchCount in ascending order
            Score: This is calculated as the ratio of SearchCount to the maximum SearchCount in the list, 
                    rounded to 3 decimal places
            """
            sorted_trends = sorted(trends, key=lambda x: x["SearchCount"], reverse=True)

            for i, item in enumerate(sorted_trends, start=1):
                item["Rank"] = i

                max_count = max(t["SearchCount"] for t in trends)

                item["Score"] = round(item["SearchCount"] / max_count, 3)

            # save_raw_data(sorted_trends, "google_trends_sorted.json")
            logger.info("Saved sorted Google Trends data with ranks and scores.")
            return sorted_trends


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
                "SearchTerm": keyword.keyword, # convert object to string
                "SearchCount": keyword.volume, 
                # "TrendScore": keyword.trend_score,
                "Topic": keyword.topics[0],
                "Source": "google_trends",
                "Geo": self.geo,
                "FetchedAt": timestamp
            })

        logger.success(f"Fetched {len(trends)} Google Trends records")
        ranked_and_sorted = self.rank_and_score(trends)

        return ranked_and_sorted
    
    