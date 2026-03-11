from __future__ import annotations
import sqlite3
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from app.models import TopResponse, SourcesResponse, HealthResponse, NewsItem
from app import db, service
from app.mcp_stdio import TOOLS


def create_app(conn: sqlite3.Connection, settings) -> FastAPI:
    app = FastAPI(title="HomePilot News MCP", version="0.1.0")

    @app.get("/health")
    def health():
        return {"ok": True, "name": "mcp-news", "ts": __import__("time").time()}

    # ── JSON-RPC /rpc endpoint (MCP-compatible) ─────────────────────────
    # Required by HomePilot's tool discovery and invocation pipeline.
    @app.post("/rpc")
    async def rpc(request: Request) -> JSONResponse:
        body = await request.json()
        req_id = body.get("id")
        method = body.get("method")
        params = body.get("params") or {}

        def _err(code: int, message: str) -> JSONResponse:
            return JSONResponse({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})

        if method in ("initialize", "mcp/initialize"):
            return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": "2025-03-26",
                "serverInfo": {"name": "mcp-news", "version": "0.1.0"},
                "capabilities": {"tools": True, "resources": False, "prompts": False},
            }})

        if method in ("tools/list", "mcp/tools/list"):
            return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}})

        if method in ("tools/call", "mcp/tools/call"):
            name = params.get("name")
            args = params.get("arguments") or {}
            if not name:
                return _err(-32602, "Missing params.name")

            try:
                if name == "news.top":
                    items = service.top(
                        conn,
                        topic=str(args.get("topic", "world")),
                        limit=int(args.get("limit", 10)),
                        hours=int(args.get("hours", 24)),
                        w_recency=settings.weight_recency,
                        w_source=settings.weight_source,
                        w_cluster=settings.weight_cluster,
                    )
                    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {"content": items}})

                if name == "news.search":
                    items = service.search(
                        conn,
                        q=str(args.get("q", "")),
                        limit=int(args.get("limit", 10)),
                        hours=int(args.get("hours", 72)),
                    )
                    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {"content": items}})

                if name == "news.sources":
                    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {
                        "content": db.list_sources(conn, enabled_only=False),
                    }})

                if name == "news.health":
                    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {"content": {
                        "ok": True,
                        "db_path": settings.db_path,
                        "last_refresh_at": service.get_last_refresh_at(conn),
                        "sources_enabled": {
                            "google_news_rss": settings.enable_google_news_rss,
                            "gdelt": settings.enable_gdelt,
                        },
                    }}})

                return _err(-32601, f"Unknown tool: {name}")
            except Exception as exc:
                return _err(-32000, f"Tool execution failed: {exc}")

        return _err(-32601, f"Method not found: {method}")

    # ── REST convenience endpoints ──────────────────────────────────────
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
