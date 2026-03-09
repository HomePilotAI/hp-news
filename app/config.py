from __future__ import annotations
from dataclasses import dataclass
import os

def _bool(v: str | None, default: bool=False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("1","true","yes","y","on")

@dataclass(frozen=True)
class Settings:
    http_host: str
    http_port: int
    db_path: str
    refresh_interval_minutes: int
    enable_google_news_rss: bool
    enable_gdelt: bool
    weight_recency: float
    weight_source: float
    weight_cluster: float
    log_level: str

def load_settings() -> Settings:
    return Settings(
        http_host=os.getenv("NEWS_MCP_HTTP_HOST","0.0.0.0"),
        http_port=int(os.getenv("NEWS_MCP_HTTP_PORT","8787")),
        db_path=os.getenv("NEWS_DB_PATH","/data/news.sqlite3"),
        refresh_interval_minutes=int(os.getenv("NEWS_REFRESH_INTERVAL_MINUTES","15")),
        enable_google_news_rss=_bool(os.getenv("NEWS_ENABLE_GOOGLE_NEWS_RSS"), True),
        enable_gdelt=_bool(os.getenv("NEWS_ENABLE_GDELT"), True),
        weight_recency=float(os.getenv("NEWS_WEIGHT_RECENCY","1.0")),
        weight_source=float(os.getenv("NEWS_WEIGHT_SOURCE","1.0")),
        weight_cluster=float(os.getenv("NEWS_WEIGHT_CLUSTER","0.5")),
        log_level=os.getenv("LOG_LEVEL","INFO").upper(),
    )
