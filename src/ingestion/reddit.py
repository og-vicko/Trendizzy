import requests
from datetime import datetime, timezone
from loguru import logger


class RedditIngestor:

    BASE_URL = "https://www.reddit.com"
    HEADERS = {"User-Agent": "trendizzy/0.1"}

    def __init__(self, geo="GB"):
        self.geo = geo

    def rank_and_score(self, posts):
        """Assign rank and normalised score (0-1) based on Reddit upvote score.

        Same logic as Google Trends ingestor — highest score gets rank 1,
        and each post's score is divided by the max to normalise to 0-1.
        """
        sorted_posts = sorted(posts, key=lambda x: x["RawScore"], reverse=True)
        max_score = sorted_posts[0]["RawScore"] if sorted_posts else 1

        for i, post in enumerate(sorted_posts, start=1):
            post["Rank"] = i
            post["Score"] = round(post["RawScore"] / max_score, 3)

        return sorted_posts

    def fetch_hot(self, limit=25):
        """Fetch hot posts from r/all — the broadest real-time signal Reddit has.

        We use r/all/hot rather than a specific subreddit because the goal is
        detecting what's broadly trending across the internet, not within a niche.
        """
        logger.info(f"Fetching Reddit r/all/hot (limit={limit})...")

        url = f"{self.BASE_URL}/r/all/hot.json?limit={limit}"

        try:
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Reddit fetch failed: {e}")
            raise

        posts = response.json()["data"]["children"]
        timestamp = datetime.now(timezone.utc).isoformat()

        normalised = []
        for post in posts:
            d = post["data"]
            normalised.append({
                "SearchTerm":    d["title"],
                "RawScore":      d["score"],
                "UpvoteRatio":   d["upvote_ratio"],
                "Subreddit":     d["subreddit"],
                "PostUrl":       f"{self.BASE_URL}{d['permalink']}",
                "Source":        "reddit",
                "Geo":           self.geo,
                "FetchedAt":     timestamp,
            })

        logger.success(f"Fetched {len(normalised)} Reddit posts")
        ranked = self.rank_and_score(normalised)
        return ranked


# if __name__ == "__main__":
#     ingestor = RedditIngestor()
#     posts = ingestor.fetch_hot(limit=10)
#     for post in posts:
#         print(f"{post['Rank']} | {post['Score']} | {post['Subreddit']} | {post['SearchTerm'][:60]}")
