from __future__ import annotations
import sys, json, logging, sqlite3
from app import db, service

log = logging.getLogger("news.mcp")

TOOLS = [
    {"name":"news.top","description":"Get top headlines for a topic from the local cache.",
     "inputSchema":{"type":"object","properties":{"topic":{"type":"string","default":"world"},"limit":{"type":"integer","minimum":1,"maximum":50,"default":10},"hours":{"type":"integer","minimum":1,"maximum":168,"default":24}}}},
    {"name":"news.search","description":"Search cached headlines by keyword.",
     "inputSchema":{"type":"object","properties":{"q":{"type":"string"},"limit":{"type":"integer","minimum":1,"maximum":50,"default":10},"hours":{"type":"integer","minimum":1,"maximum":720,"default":72}},"required":["q"]}},
    {"name":"news.sources","description":"List configured sources and their enabled state.","inputSchema":{"type":"object","properties":{}}},
    {"name":"news.health","description":"Check readiness and last refresh timestamp.","inputSchema":{"type":"object","properties":{}}},
]

def _respond(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, default=str) + "\n")
    sys.stdout.flush()

def serve(conn: sqlite3.Connection, settings) -> None:
    log.info("MCP stdio server started")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            rid = req.get("id")
            method = req.get("method")
            params = req.get("params") or {}
        except Exception as e:
            _respond({"id": None, "error": {"message": f"Invalid JSON: {e}"}})
            continue

        try:
            if method == "tools/list":
                _respond({"id": rid, "result": {"tools": TOOLS}})
                continue

            if method == "tools/call":
                name = params.get("name")
                args = params.get("arguments") or {}

                if name == "news.top":
                    items = service.top(
                        conn,
                        topic=str(args.get("topic","world")),
                        limit=int(args.get("limit",10)),
                        hours=int(args.get("hours",24)),
                        w_recency=settings.weight_recency,
                        w_source=settings.weight_source,
                        w_cluster=settings.weight_cluster,
                    )
                    _respond({"id": rid, "result": {"content": items}})
                    continue

                if name == "news.search":
                    items = service.search(
                        conn,
                        q=str(args.get("q","")),
                        limit=int(args.get("limit",10)),
                        hours=int(args.get("hours",72)),
                    )
                    _respond({"id": rid, "result": {"content": items}})
                    continue

                if name == "news.sources":
                    _respond({"id": rid, "result": {"content": db.list_sources(conn, enabled_only=False)}})
                    continue

                if name == "news.health":
                    _respond({"id": rid, "result": {"content": {
                        "ok": True,
                        "db_path": settings.db_path,
                        "last_refresh_at": service.get_last_refresh_at(conn),
                        "sources_enabled": {"google_news_rss": settings.enable_google_news_rss, "gdelt": settings.enable_gdelt},
                    }}})
                    continue

                _respond({"id": rid, "error": {"message": f"Unknown tool: {name}"}})
                continue

            _respond({"id": rid, "error": {"message": f"Unknown method: {method}"}})
        except Exception as e:
            log.exception("Request failed")
            _respond({"id": rid, "error": {"message": str(e)}})
