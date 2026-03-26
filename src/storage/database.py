import json
import sqlite3
import uuid
from pathlib import Path
from loguru import logger
from pathlib import Path



def save_raw_data(data, filename, base_path="data/raw"):
    Path(base_path).mkdir(parents=True, exist_ok=True)
    file_path = Path(base_path) / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.success(f"Saved raw data to {file_path}")


# def load_json_file(filename, base_path="data/raw"):
#     """Load a JSON file and return the parsed object.

#     Returns the parsed JSON (dict/list) on success. If the file is missing, returns None.
#     Raises json.JSONDecodeError if the file contains invalid JSON, or other exceptions for I/O errors.
#     """
#     file_path = Path(base_path) / filename

#     if not file_path.exists():
#         logger.warning(f"JSON file not found: {file_path}")
#         return None

#     try:
#         with open(file_path, "r", encoding="utf-8") as f:
#             return json.load(f)
#     except json.JSONDecodeError as e:
#         logger.error(f"Failed to decode JSON from {file_path}: {e}")
#         raise
#     except Exception as e:
#         logger.error(f"Error reading JSON file {file_path}: {e}")
#         raise


#################### DATABASE FUNCTIONS #######################
DB_PATH = Path("data/trendizzy.db")

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize the SQLite database and create necessary tables."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trends (
            topic_id TEXT PRIMARY KEY,
            keyword TEXT NOT NULL,
            category TEXT,
            geo TEXT,
            status TEXT DEFAULT 'raw',
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trend_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id TEXT NOT NULL,
            source TEXT NOT NULL,
            rank INTEGER,
            score REAL,
            raw_payload TEXT,
            fetched_at TEXT,
            FOREIGN KEY (topic_id) REFERENCES trends (topic_id)
        )
    """)

    conn.commit()
    conn.close()

def save_google_trends_from_json(trends):
    """Save Trends data from a list of trend dictionaries into the database."""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for trend in trends:
        topic_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT OR IGNORE INTO trends
            (topic_id, keyword, category, geo, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            topic_id,
            trend["SearchTerm"],
            trend.get("Topic"),
            trend["Geo"],
            "raw",
            trend["FetchedAt"]
        ))

        cursor.execute("""
            INSERT INTO trend_signals
            (topic_id, source, rank, score, raw_payload, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            topic_id,
            trend["Source"],
            trend["Rank"],
            trend["Score"],
            json.dumps(trend),
            trend["FetchedAt"]
        ))

    conn.commit()
    conn.close()


def get_top_trends(
    source="google_trends",
    geo="GB",
    limit=5,
    min_score=0.0
):
    """Fetch top trends from the database"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            t.keyword,
            t.geo,
            s.rank,
            s.score,
            s.fetched_at
        FROM trends t
        JOIN trend_signals s ON t.topic_id = s.topic_id
        WHERE s.source = ?
          AND t.geo = ?
          AND s.score >= ?
        ORDER BY s.rank ASC
        LIMIT ?
    """, (source, geo, min_score, limit))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "keyword": r[0],
            "geo": r[1],
            "rank": r[2],
            "score": r[3],
            "fetched_at": r[4],
        }
        for r in rows
    ]


