from __future__ import annotations
import argparse
from dotenv import load_dotenv
import uvicorn

from app.config import load_settings
from app.logging_setup import configure_logging
from app import db
from app.ingestor import ensure_seeded
from app.scheduler import Refresher
from app.http_api import create_app
from app.mcp_stdio import serve as serve_mcp

def main():
    load_dotenv()
    settings = load_settings()
    configure_logging(settings.log_level)

    conn = db.connect(settings.db_path)
    ensure_seeded(conn)

    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="Run HTTP API server")
    parser.add_argument("--mcp", action="store_true", help="Run MCP stdio server")
    args = parser.parse_args()

    refresher = Refresher(
        conn,
        interval_minutes=settings.refresh_interval_minutes,
        enable_google=settings.enable_google_news_rss,
        enable_gdelt=settings.enable_gdelt,
    )
    refresher.start()

    if args.mcp and not args.http:
        serve_mcp(conn, settings)
        return

    app = create_app(conn, settings)
    uvicorn.run(app, host=settings.http_host, port=settings.http_port)

if __name__ == "__main__":
    main()
