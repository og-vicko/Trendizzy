import json
import sqlite3
import uuid
from pathlib import Path
from loguru import logger
from pathlib import Path



def save_raw_data(data, filename, base_path="data/raw"):
    Path(base_path).mkdir(parents=True, exist_ok=True) # Ensure the directory exists
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
            keyword TEXT NOT NULL UNIQUE,  -- prevents the same keyword being inserted twice
            category TEXT,
            geo TEXT,
            status TEXT DEFAULT 'raw',
            created_at TEXT,
            enrichment TEXT              -- JSON blob from Claude, NULL until enriched
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
    """Save trends into the database, avoiding duplicate keywords.

    For each trend:
    - If the keyword already exists in `trends`, reuse its topic_id
    - If it's new, create a fresh UUID and insert it
    - Always insert a new row into `trend_signals` (each run is a new signal)
    """

    conn = get_connection()
    cursor = conn.cursor()

    new_count = 0
    existing_count = 0

    for trend in trends:
        keyword = trend["SearchTerm"]

        # Check if this keyword already exists in the trends table
        cursor.execute("SELECT topic_id FROM trends WHERE keyword = ?", (keyword,))
        row = cursor.fetchone()

        if row:
            # Keyword exists — reuse the existing topic_id
            topic_id = row[0]
            existing_count += 1
        else:
            # New keyword — generate a fresh UUID and insert it
            topic_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO trends (topic_id, keyword, category, geo, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                topic_id,
                keyword,
                trend.get("Topic"),
                trend["Geo"],
                "raw",
                trend["FetchedAt"]
            ))
            new_count += 1

        # Always insert a new signal row — each run is a fresh data point
        cursor.execute("""
            INSERT INTO trend_signals (topic_id, source, rank, score, raw_payload, fetched_at)
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

    logger.info(f"Trends saved — {new_count} new, {existing_count} already existed.")


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
            t.topic_id,
            t.keyword,
            t.geo,
            t.enrichment,
            s.rank,
            s.score,
            s.fetched_at
        FROM trends t
        -- Only join the latest signal row for each trend (highest id = most recent insert)
        JOIN trend_signals s ON s.id = (
            SELECT MAX(id) FROM trend_signals
            WHERE topic_id = t.topic_id AND source = ?
        )
        WHERE t.geo = ?
          AND s.score >= ?
        ORDER BY s.rank ASC
        LIMIT ?
    """, (source, geo, min_score, limit))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "topic_id":   r[0],
            "keyword":    r[1],
            "geo":        r[2],
            "enrichment": json.loads(r[3]) if r[3] else None,  # parse JSON back to dict, or None if not yet enriched
            "rank":       r[4],
            "score":      r[5],
            "fetched_at": r[6],
        }
        for r in rows
    ]


def save_enrichment(topic_id, enrichment):
    """Save Claude's enrichment result for a trend back into the trends table.

    enrichment is a dict — we serialise it to JSON before storing.
    This is called once per trend, after Claude has analysed it.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE trends SET enrichment = ? WHERE topic_id = ?
    """, (json.dumps(enrichment), topic_id))

    conn.commit()
    conn.close()


