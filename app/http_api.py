from __future__ import annotations
import sqlite3
from fastapi import FastAPI, Query
from app.models import TopResponse, SourcesResponse, HealthResponse, NewsItem
from app import db, service

def create_app(conn: sqlite3.Connection, settings) -> FastAPI:
    app = FastAPI(title="HomePilot News MCP", version="0.1.0")

    @app.get("/health", response_model=HealthResponse)
    def health():
        return HealthResponse(
            ok=True,
            db_path=settings.db_path,
            last_refresh_at=service.get_last_refresh_at(conn),
            sources_enabled={"google_news_rss": settings.enable_google_news_rss, "gdelt": settings.enable_gdelt},
        )

    @app.get("/v1/news/sources", response_model=SourcesResponse)
    def sources():
        return SourcesResponse(sources=db.list_sources(conn, enabled_only=False))

    @app.get("/v1/news/top", response_model=TopResponse)
    def top(topic: str = Query("world"), limit: int = Query(10, ge=1, le=50), hours: int = Query(24, ge=1, le=168)):
        items = service.top(
            conn,
            topic=topic,
            limit=limit,
            hours=hours,
            w_recency=settings.weight_recency,
            w_source=settings.weight_source,
            w_cluster=settings.weight_cluster,
        )
        return TopResponse(items=[NewsItem(**it) for it in items])

    @app.get("/v1/news/search", response_model=TopResponse)
    def search(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50), hours: int = Query(72, ge=1, le=720)):
        items = service.search(conn, q=q, limit=limit, hours=hours)
        return TopResponse(items=[NewsItem(**it) for it in items])

    return app
