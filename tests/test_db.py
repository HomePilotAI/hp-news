"""Tests for the database layer."""
from app import db


def test_connect_creates_tables(conn):
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "meta" in tables
    assert "sources" in tables
    assert "news_items" in tables


def test_meta_roundtrip(conn):
    db.set_meta(conn, "foo", "bar")
    assert db.get_meta(conn, "foo") == "bar"
    db.set_meta(conn, "foo", "baz")
    assert db.get_meta(conn, "foo") == "baz"


def test_meta_missing(conn):
    assert db.get_meta(conn, "nonexistent") is None


def test_seed_sources(seeded_conn):
    sources = db.list_sources(seeded_conn, enabled_only=False)
    assert len(sources) >= 7  # DEFAULT_SOURCES has 7 entries


def test_upsert_deduplicates(conn):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    kwargs = dict(
        title="Headline", url="https://a.com/1", canonical_url="https://a.com/1",
        source_id="s1", source_name="S1", topic="tech", summary="sum",
        published_at=now, fetched_at=now, language="en", region="us",
    )
    id1 = db.upsert_news_item(conn, **kwargs)
    id2 = db.upsert_news_item(conn, **{**kwargs, "title": "Updated"})
    conn.commit()
    assert id1 == id2
    row = conn.execute("SELECT title FROM news_items WHERE id=?", (id1,)).fetchone()
    assert row["title"] == "Updated"


def test_sha1_id_deterministic():
    assert db.sha1_id("hello") == db.sha1_id("hello")
    assert db.sha1_id("a") != db.sha1_id("b")
