from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
import hashlib

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT
);

CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  name TEXT NOT NULL,
  topic TEXT NOT NULL,
  url TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 1.0,
  enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS news_items (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  canonical_url TEXT NOT NULL,
  source_id TEXT NOT NULL,
  source_name TEXT NOT NULL,
  topic TEXT NOT NULL,
  summary TEXT,
  published_at TEXT,
  fetched_at TEXT NOT NULL,
  language TEXT,
  region TEXT
);

CREATE INDEX IF NOT EXISTS idx_news_topic_time ON news_items(topic, published_at);
CREATE INDEX IF NOT EXISTS idx_news_fetched ON news_items(fetched_at);
"""

def connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
    conn.commit()

def get_meta(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None

def sha1_id(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def upsert_news_item(conn: sqlite3.Connection, *, title: str, url: str, canonical_url: str,
                     source_id: str, source_name: str, topic: str, summary: str|None,
                     published_at, fetched_at, language: str|None, region: str|None) -> str:
    nid = sha1_id(canonical_url)
    conn.execute(
        """INSERT INTO news_items(id,title,url,canonical_url,source_id,source_name,topic,summary,published_at,fetched_at,language,region)
             VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
             ON CONFLICT(id) DO UPDATE SET
               title=excluded.title,
               url=excluded.url,
               summary=COALESCE(excluded.summary, news_items.summary),
               published_at=COALESCE(excluded.published_at, news_items.published_at),
               fetched_at=excluded.fetched_at,
               language=COALESCE(excluded.language, news_items.language),
               region=COALESCE(excluded.region, news_items.region)
        """,
        (
            nid, title, url, canonical_url, source_id, source_name, topic, summary,
            published_at.isoformat() if published_at else None,
            fetched_at.isoformat(),
            language, region
        )
    )
    return nid

def list_sources(conn: sqlite3.Connection, enabled_only: bool=True) -> list[dict]:
    q = "SELECT * FROM sources" + (" WHERE enabled=1" if enabled_only else "")
    rows = conn.execute(q).fetchall()
    return [dict(r) for r in rows]

def seed_sources(conn: sqlite3.Connection, sources: list[dict]) -> None:
    for s in sources:
        conn.execute(
            """INSERT INTO sources(id,kind,name,topic,url,weight,enabled)
                 VALUES(?,?,?,?,?,?,?)
                 ON CONFLICT(id) DO UPDATE SET
                   kind=excluded.kind,
                   name=excluded.name,
                   topic=excluded.topic,
                   url=excluded.url,
                   weight=excluded.weight,
                   enabled=excluded.enabled
            """,
            (s["id"], s["kind"], s["name"], s["topic"], s["url"], float(s.get("weight",1.0)), int(s.get("enabled",1)))
        )
    conn.commit()
