"""Tests for the service layer (top, search, health)."""
from app import service


def test_top_returns_results(populated_conn, settings):
    items = service.top(populated_conn, topic="tech", limit=5, hours=48,
                        w_recency=settings.weight_recency,
                        w_source=settings.weight_source,
                        w_cluster=settings.weight_cluster)
    assert len(items) >= 1
    assert items[0]["topic"] == "tech"


def test_top_respects_limit(populated_conn, settings):
    items = service.top(populated_conn, topic="tech", limit=1, hours=48,
                        w_recency=1.0, w_source=1.0, w_cluster=0.5)
    assert len(items) == 1


def test_search_finds_keyword(populated_conn):
    items = service.search(populated_conn, q="AI", limit=10, hours=168)
    assert len(items) >= 1
    assert any("AI" in it["title"] for it in items)


def test_search_no_match(populated_conn):
    items = service.search(populated_conn, q="zzzyyyxxx_nomatch", limit=10, hours=168)
    assert len(items) == 0


def test_get_last_refresh_at_none(conn):
    assert service.get_last_refresh_at(conn) is None


def test_get_last_refresh_at_set(conn):
    from app import db
    db.set_meta(conn, "last_refresh_at", "2025-01-01T00:00:00+00:00")
    dt = service.get_last_refresh_at(conn)
    assert dt is not None
    assert dt.year == 2025
