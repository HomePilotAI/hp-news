"""Shared fixtures for hp-news tests."""
from __future__ import annotations
import os, pytest, sqlite3
from datetime import datetime, timezone, timedelta

# Force a temp DB path so tests never touch production data
os.environ.setdefault("NEWS_DB_PATH", "/tmp/hp-news-test.sqlite3")

from app import db
from app.config import load_settings
from app.ingestor import ensure_seeded


@pytest.fixture()
def conn(tmp_path):
    """Return a fresh in-memory-style SQLite connection with schema applied."""
    db_file = str(tmp_path / "test.sqlite3")
    c = db.connect(db_file)
    yield c
    c.close()


@pytest.fixture()
def seeded_conn(conn):
    """Connection with default sources already seeded."""
    ensure_seeded(conn)
    return conn


@pytest.fixture()
def settings():
    return load_settings()


@pytest.fixture()
def populated_conn(seeded_conn):
    """Connection with a few fake news items for query tests."""
    now = datetime.now(timezone.utc)
    items = [
        ("Breaking: AI advances rapidly", "https://example.com/ai", "tech", "AI is advancing fast"),
        ("Stock market hits new high", "https://example.com/stocks", "business", "Markets rally today"),
        ("World leaders meet at summit", "https://example.com/summit", "world", "G20 summit held"),
        ("New species discovered in Amazon", "https://example.com/species", "science", "Scientists find new frog"),
        ("Champions League final recap", "https://example.com/football", "sports", "Exciting match last night"),
    ]
    for i, (title, url, topic, summary) in enumerate(items):
        db.upsert_news_item(
            seeded_conn,
            title=title,
            url=url,
            canonical_url=url,
            source_id=f"test_src_{topic}",
            source_name=f"Test {topic}",
            topic=topic,
            summary=summary,
            published_at=now - timedelta(hours=i),
            fetched_at=now,
            language="en",
            region="us",
        )
    seeded_conn.commit()
    return seeded_conn
