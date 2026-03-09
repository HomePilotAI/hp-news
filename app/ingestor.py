from __future__ import annotations
import logging
from datetime import datetime, timezone
import sqlite3

from app import db
from app.sources import DEFAULT_SOURCES, GOOGLE_NEWS_RSS_QUERIES
from app.fetchers.rss_fetcher import fetch_rss
from app.fetchers.google_news import google_news_rss_url
from app.fetchers.gdelt import fetch_gdelt_latest

log = logging.getLogger("news.ingest")

def ensure_seeded(conn: sqlite3.Connection) -> None:
    db.seed_sources(conn, DEFAULT_SOURCES)
    db.set_meta(conn, "seeded_at", datetime.now(timezone.utc).isoformat())

def refresh(conn: sqlite3.Connection, *, enable_google: bool, enable_gdelt: bool) -> dict:
    sources = db.list_sources(conn, enabled_only=True)
    fetched_at = datetime.now(timezone.utc)

    inserted = 0
    failures = 0

    for s in sources:
        try:
            entries = fetch_rss(s["url"])
            for e in entries:
                db.upsert_news_item(
                    conn,
                    title=e["title"],
                    url=e["url"],
                    canonical_url=e["canonical_url"],
                    source_id=s["id"],
                    source_name=s["name"],
                    topic=s["topic"],
                    summary=e.get("summary"),
                    published_at=e.get("published_at"),
                    fetched_at=fetched_at,
                    language=e.get("language"),
                    region=e.get("region"),
                )
                inserted += 1
            conn.commit()
        except Exception as ex:
            failures += 1
            log.warning("source failed id=%s err=%s", s["id"], ex)

    if enable_google:
        for q in GOOGLE_NEWS_RSS_QUERIES:
            try:
                url = google_news_rss_url(q["q"])
                entries = fetch_rss(url)
                source_id = f"google_{q['id']}"
                source_name = f"Google News: {q['q']}"
                for e in entries:
                    db.upsert_news_item(
                        conn,
                        title=e["title"],
                        url=e["url"],
                        canonical_url=e["canonical_url"],
                        source_id=source_id,
                        source_name=source_name,
                        topic=q["topic"],
                        summary=e.get("summary"),
                        published_at=e.get("published_at"),
                        fetched_at=fetched_at,
                        language=e.get("language"),
                        region=e.get("region"),
                    )
                    inserted += 1
                conn.commit()
            except Exception as ex:
                failures += 1
                log.warning("google rss failed q=%s err=%s", q["q"], ex)

    if enable_gdelt:
        for topic in ("world","business","tech","science","sports","entertainment"):
            try:
                entries = fetch_gdelt_latest(topic=topic, hours=24, max_records=50)
                source_id = f"gdelt_{topic}"
                source_name = f"GDELT: {topic}"
                for e in entries:
                    db.upsert_news_item(
                        conn,
                        title=e["title"],
                        url=e["url"],
                        canonical_url=e["canonical_url"],
                        source_id=source_id,
                        source_name=source_name,
                        topic=topic,
                        summary=e.get("summary"),
                        published_at=e.get("published_at"),
                        fetched_at=fetched_at,
                        language=e.get("language"),
                        region=e.get("region"),
                    )
                    inserted += 1
                conn.commit()
            except Exception as ex:
                failures += 1
                log.warning("gdelt failed topic=%s err=%s", topic, ex)

    db.set_meta(conn, "last_refresh_at", fetched_at.isoformat())
    return {"inserted": inserted, "failures": failures, "last_refresh_at": fetched_at.isoformat()}
