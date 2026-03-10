#!/usr/bin/env python3
"""
smoke_test.py  –  End-to-end live verification of hp-news MCP server.

Run:  make smoke          (or directly: .venv/bin/python smoke_test.py)

What it does:
  1. Creates a fresh SQLite DB in /tmp
  2. Seeds default sources
  3. Runs a REAL ingestion cycle (RSS + Google News RSS + GDELT)
  4. Queries news.top for every topic
  5. Queries news.search with a broad keyword
  6. Hits every HTTP endpoint via TestClient
  7. Validates MCP stdio tool definitions
  8. Prints a pass/fail report

Requires network access – this is NOT a unit test; it proves the server
delivers real-time news from live sources.
"""
from __future__ import annotations

import sys
import os
import json
import tempfile
import textwrap
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── ensure the project root is on sys.path ───────────────
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

os.environ["NEWS_DB_PATH"] = "/tmp/hp-news-smoke.sqlite3"

from app import db
from app.config import load_settings
from app.ingestor import ensure_seeded, refresh
from app import service
from app.mcp_stdio import TOOLS
from app.http_api import create_app

# ── colours for terminal output ──────────────────────────
GREEN = "\033[92m"
RED   = "\033[91m"
BOLD  = "\033[1m"
RESET = "\033[0m"
CYAN  = "\033[96m"

results: list[tuple[str, bool, str]] = []   # (name, passed, detail)


def check(name: str, passed: bool, detail: str = ""):
    results.append((name, passed, detail))
    mark = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
    print(f"  [{mark}] {name}" + (f"  — {detail}" if detail else ""))


def main():
    print(f"\n{BOLD}{CYAN}═══  hp-news  smoke test  ═══{RESET}\n")

    # ── 1. Database & seed ────────────────────────────────
    db_path = "/tmp/hp-news-smoke.sqlite3"
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = db.connect(db_path)
    ensure_seeded(conn)
    sources = db.list_sources(conn, enabled_only=True)
    check("DB created & seeded", len(sources) >= 7, f"{len(sources)} sources")

    # ── 2. Live ingestion ─────────────────────────────────
    print(f"\n{CYAN}Ingesting from live sources (RSS, Google News, GDELT) …{RESET}")
    settings = load_settings()
    stats = refresh(conn, enable_google=True, enable_gdelt=True)
    inserted = stats["inserted"]
    failures = stats["failures"]
    check(
        "Live ingestion completed",
        inserted > 0,
        f"{inserted} articles ingested, {failures} source failures",
    )

    total_rows = conn.execute("SELECT COUNT(*) FROM news_items").fetchone()[0]
    check("Articles in DB", total_rows > 0, f"{total_rows} total rows")

    # ── 3. news.top per topic ─────────────────────────────
    print(f"\n{CYAN}Querying news.top for each topic …{RESET}")
    topics_with_results = 0
    for topic in ("world", "business", "tech", "science", "sports", "entertainment"):
        items = service.top(
            conn, topic=topic, limit=5, hours=48,
            w_recency=1.0, w_source=1.0, w_cluster=0.5,
        )
        if items:
            topics_with_results += 1
            sample = items[0]["title"][:70]
            check(f"  top({topic})", True, f"{len(items)} items — e.g. \"{sample}\"")
        else:
            check(f"  top({topic})", False, "0 items")

    check("At least 3 topics have headlines", topics_with_results >= 3,
          f"{topics_with_results}/6 topics returned results")

    # ── 4. Recency check ─────────────────────────────────
    print(f"\n{CYAN}Checking recency …{RESET}")
    now = datetime.now(timezone.utc)
    cutoff_48h = (now - timedelta(hours=48)).isoformat()
    recent = conn.execute(
        "SELECT COUNT(*) FROM news_items WHERE published_at >= ?", (cutoff_48h,)
    ).fetchone()[0]
    check("Recent articles (< 48 h old)", recent > 0, f"{recent} articles within 48 hours")

    # ── 5. news.search ────────────────────────────────────
    print(f"\n{CYAN}Testing news.search …{RESET}")
    # pick a word from the most recent headline to guarantee a hit
    any_title = conn.execute("SELECT title FROM news_items ORDER BY fetched_at DESC LIMIT 1").fetchone()
    if any_title:
        word = any_title[0].split()[0]
        search_hits = service.search(conn, q=word, limit=10, hours=168)
        check(f"search(q=\"{word}\")", len(search_hits) >= 1,
              f"{len(search_hits)} results")
    else:
        check("search", False, "no articles to search")

    # ── 6. HTTP API via TestClient ────────────────────────
    print(f"\n{CYAN}Testing HTTP endpoints …{RESET}")
    try:
        import httpx
        from httpx import ASGITransport

        app = create_app(conn, settings)
        transport = ASGITransport(app=app)

        import asyncio

        async def _http_checks():
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
                # /health
                r = await c.get("/health")
                check("GET /health", r.status_code == 200 and r.json()["ok"] is True)

                # /v1/news/sources
                r = await c.get("/v1/news/sources")
                check("GET /v1/news/sources", r.status_code == 200 and len(r.json()["sources"]) >= 7)

                # /v1/news/top
                r = await c.get("/v1/news/top", params={"topic": "world", "limit": 5, "hours": 48})
                body = r.json()
                check("GET /v1/news/top", r.status_code == 200,
                      f"{len(body.get('items',[]))} items")

                # /v1/news/search
                r = await c.get("/v1/news/search", params={"q": "news", "limit": 5})
                body = r.json()
                check("GET /v1/news/search", r.status_code == 200,
                      f"{len(body.get('items',[]))} results")

        asyncio.run(_http_checks())

    except Exception as e:
        check("HTTP endpoints", False, str(e))

    # ── 7. MCP stdio tool definitions ─────────────────────
    print(f"\n{CYAN}Verifying MCP tool definitions …{RESET}")
    tool_names = {t["name"] for t in TOOLS}
    check("MCP tools registered",
          tool_names == {"news.top", "news.search", "news.sources", "news.health"},
          ", ".join(sorted(tool_names)))

    # ── 8. last_refresh_at meta ───────────────────────────
    last_ref = service.get_last_refresh_at(conn)
    check("last_refresh_at set", last_ref is not None,
          last_ref.isoformat() if last_ref else "None")

    conn.close()

    # ── Report ────────────────────────────────────────────
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    total  = len(results)

    print(f"\n{BOLD}{'═'*50}")
    if failed == 0:
        print(f"{GREEN}  ALL {total} CHECKS PASSED{RESET}")
    else:
        print(f"{RED}  {failed}/{total} CHECKS FAILED{RESET}")
    print(f"{'═'*50}{RESET}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
