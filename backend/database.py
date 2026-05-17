"""
backend/database.py
-------------------
SQLite schema creation and async CRUD helpers for detection events.
"""
import aiosqlite
from backend.config import DB_PATH


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS detections (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL,           -- ISO-8601
    label       TEXT    NOT NULL,           -- e.g. "person"
    confidence  REAL    NOT NULL,           -- 0.0 – 1.0
    bbox_x1     INTEGER NOT NULL,
    bbox_y1     INTEGER NOT NULL,
    bbox_x2     INTEGER NOT NULL,
    bbox_y2     INTEGER NOT NULL,
    frame_id    INTEGER NOT NULL DEFAULT 0  -- sequential frame counter
);

CREATE TABLE IF NOT EXISTS screenshots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL,
    filename    TEXT    NOT NULL,
    object_count INTEGER NOT NULL DEFAULT 0
);
"""


async def init_db() -> None:
    """Create tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()


async def insert_detections(events: list[dict]) -> None:
    """Bulk-insert a list of detection dicts from a single frame."""
    if not events:
        return
    sql = """
        INSERT INTO detections
            (timestamp, label, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2, frame_id)
        VALUES
            (:timestamp, :label, :confidence, :bbox_x1, :bbox_y1, :bbox_x2, :bbox_y2, :frame_id)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(sql, events)
        await db.commit()


async def insert_screenshot(timestamp: str, filename: str, object_count: int) -> int:
    """Insert a screenshot record; returns the new row id."""
    sql = """
        INSERT INTO screenshots (timestamp, filename, object_count)
        VALUES (?, ?, ?)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(sql, (timestamp, filename, object_count))
        await db.commit()
        return cursor.lastrowid


async def fetch_recent_detections(limit: int = 200) -> list[dict]:
    """Return the N most-recent detection rows as dicts."""
    sql = """
        SELECT id, timestamp, label, confidence,
               bbox_x1, bbox_y1, bbox_x2, bbox_y2, frame_id
        FROM   detections
        ORDER  BY id DESC
        LIMIT  ?
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, (limit,)) as cursor:
            rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def fetch_object_counts() -> list[dict]:
    """Return aggregate counts per label."""
    sql = """
        SELECT label, COUNT(*) AS count
        FROM   detections
        GROUP  BY label
        ORDER  BY count DESC
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql) as cursor:
            rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def fetch_screenshots(limit: int = 50) -> list[dict]:
    """Return the N most-recent screenshot records."""
    sql = """
        SELECT id, timestamp, filename, object_count
        FROM   screenshots
        ORDER  BY id DESC
        LIMIT  ?
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, (limit,)) as cursor:
            rows = await cursor.fetchall()
    return [dict(r) for r in rows]
