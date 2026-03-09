from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional
import feedparser
import requests
from dateutil import parser as dtparser
from app.utils import canonicalize_url, safe_text

log = logging.getLogger("news.rss")

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

def fetch_rss(url: str, timeout_s: int=20) -> list[dict]:
    headers = {"User-Agent": "HomePilotNewsMCP/0.1"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout_s)
        r.raise_for_status()
        parsed = feedparser.parse(r.text)
    except Exception as e:
        log.warning("RSS fetch failed url=%s err=%s", url, e)
        return []

    out: list[dict] = []
    for e in parsed.entries[:60]:
        link = getattr(e, "link", None) or ""
        title = safe_text(getattr(e, "title", "") or "", 300)
        summary = safe_text(getattr(e, "summary", "") or "", 600)
        published = _parse_dt(getattr(e, "published", None) or getattr(e, "updated", None))
        if not link or not title:
            continue
        out.append({
            "title": title,
            "url": link,
            "canonical_url": canonicalize_url(link),
            "summary": summary if summary else None,
            "published_at": published,
            "language": getattr(parsed.feed, "language", None),
        })
    return out
