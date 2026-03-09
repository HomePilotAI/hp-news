from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
import requests
from app.utils import canonicalize_url, safe_text

log = logging.getLogger("news.gdelt")

def fetch_gdelt_latest(topic: str="world", hours: int=24, max_records: int=50, timeout_s: int=20) -> list[dict]:
    qmap = {
        "world":"world",
        "business":"economy OR business",
        "tech":"technology OR AI OR software",
        "science":"science OR research",
        "sports":"sports",
        "entertainment":"entertainment OR film OR music",
        "general":"news"
    }
    q = qmap.get(topic, topic or "news")
    base = "https://api.gdeltproject.org/api/v2/doc/doc"
    start_dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    params = {
        "query": q,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(max_records),
        "startdatetime": start_dt.strftime("%Y%m%d%H%M%S"),
        "sort": "HybridRel"
    }
    try:
        r = requests.get(base, params=params, timeout=timeout_s, headers={"User-Agent":"HomePilotNewsMCP/0.1"})
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.warning("GDELT fetch failed topic=%s err=%s", topic, e)
        return []

    out: list[dict] = []
    for a in (data.get("articles") or [])[:max_records]:
        url = a.get("url") or ""
        title = safe_text(a.get("title") or "", 300)
        if not url or not title:
            continue
        published = None
        p = a.get("seendate")
        if p:
            try:
                published = datetime.strptime(p, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            except Exception:
                published = None
        out.append({
            "title": title,
            "url": url,
            "canonical_url": canonicalize_url(url),
            "summary": safe_text(a.get("snippet") or "", 600) or None,
            "published_at": published,
            "language": a.get("language"),
            "region": a.get("sourceCountry"),
        })
    return out
