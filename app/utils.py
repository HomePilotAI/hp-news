from __future__ import annotations
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import re

_TRACKING_PARAMS = {
    "utm_source","utm_medium","utm_campaign","utm_term","utm_content",
    "gclid","fbclid","mc_cid","mc_eid","igshid","ref","spm"
}

def canonicalize_url(url: str) -> str:
    try:
        p = urlparse(url)
        q = [(k,v) for (k,v) in parse_qsl(p.query, keep_blank_values=True) if k not in _TRACKING_PARAMS]
        query = urlencode(q, doseq=True)
        return urlunparse((p.scheme, p.netloc, p.path, p.params, query, ""))
    except Exception:
        return url

def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def safe_text(s: str, max_len: int=500) -> str:
    s = normalize_whitespace(s)
    return s[:max_len]
