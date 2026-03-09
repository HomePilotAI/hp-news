from __future__ import annotations
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional
from dateutil import parser as dtparser

from app import db
from app.ranking import rank_items

def _parse_dt(value: str|None) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = dtparser.parse(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def get_last_refresh_at(conn: sqlite3.Connection) -> Optional[datetime]:
    v = db.get_meta(conn, "last_refresh_at")
    return _parse_dt(v)

def _cutoff(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

def top(conn: sqlite3.Connection, *, topic: str="general", limit: int=10, hours: int=24,
        w_recency: float=1.0, w_source: float=1.0, w_cluster: float=0.5) -> list[dict]:
    cutoff = _cutoff(hours)
    rows = conn.execute(
        """SELECT id,title,url,source_id,source_name,topic,summary,published_at,language,region
             FROM news_items
             WHERE topic=? AND (published_at IS NULL OR published_at >= ?)
             ORDER BY fetched_at DESC
             LIMIT 400
        """,
        (topic, cutoff)
    ).fetchall()

    items: list[dict] = []
    for r in rows:
        items.append({
            "id": r["id"],
            "title": r["title"],
            "url": r["url"],
            "source_id": r["source_id"],
            "source": r["source_name"],
            "topic": r["topic"],
            "summary": r["summary"],
            "published_at": _parse_dt(r["published_at"]),
            "language": r["language"],
            "region": r["region"],
        })

    src_w = {s["id"]: float(s.get("weight",1.0)) for s in db.list_sources(conn, enabled_only=False)}
    ranked = rank_items(items, src_w, w_recency, w_source, w_cluster)
    return ranked[:limit]

def search(conn: sqlite3.Connection, *, q: str, limit: int=10, hours: int=72) -> list[dict]:
    qn = f"%{q.lower()}%"
    cutoff = _cutoff(hours)
    rows = conn.execute(
        """SELECT id,title,url,source_name,topic,summary,published_at,language,region
             FROM news_items
             WHERE (lower(title) LIKE ? OR lower(summary) LIKE ?)
               AND (published_at IS NULL OR published_at >= ?)
             ORDER BY fetched_at DESC
             LIMIT ?
        """,
        (qn, qn, cutoff, max(limit*5, 50))
    ).fetchall()

    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "title": r["title"],
            "url": r["url"],
            "source": r["source_name"],
            "topic": r["topic"],
            "summary": r["summary"],
            "published_at": _parse_dt(r["published_at"]),
            "language": r["language"],
            "region": r["region"],
            "score": 0.0,
        })
    return out[:limit]
