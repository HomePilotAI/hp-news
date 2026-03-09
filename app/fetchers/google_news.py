from __future__ import annotations
from urllib.parse import quote_plus

def google_news_rss_url(query: str, hl: str="en", gl: str="US", ceid: str="US:en") -> str:
    q = quote_plus(query)
    return f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"
