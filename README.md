# HomePilot News MCP Server (free, no paid APIs)

A lightweight sidecar service that keeps a **local cache of real news headlines** using **free sources**
(RSS/Atom feeds, Google News RSS queries, and optional GDELT). It exposes:
- a **simple MCP-over-stdio** tool interface (for agents),
- and an **HTTP API** (for debugging/ops).

Designed for low resources:
- stores only metadata (title/source/url/published time/summary),
- uses RSS where possible (no heavy scraping),
- background refresh on a schedule,
- deduplicates by canonical URL.

## Tools (MCP)
Minimal MCP-style protocol over stdio:
- `tools/list`
- `tools/call`

Tools:
- `news.top` — top headlines
- `news.search` — keyword search
- `news.sources` — configured sources
- `news.health` — readiness/status

### Example (stdio)
```json
{"id":"1","method":"tools/list","params":{}}
```

Call:
```json
{"id":"2","method":"tools/call","params":{"name":"news.top","arguments":{"topic":"world","limit":10,"hours":24}}}
```

## HTTP API
- `GET /health`
- `GET /v1/news/top?topic=world&limit=10&hours=24`
- `GET /v1/news/search?q=ai&limit=10&hours=72`
- `GET /v1/news/sources`

## Quick start

```bash
# Using make (auto-detects uv for faster installs)
make install
cp .env.example .env
make run-http
```

Or manually:

```bash
# With uv (fast)
uv venv .venv --python python3.11
uv pip install --python .venv/bin/python .
cp .env.example .env
.venv/bin/python -m app.main --http

# With pip
python3 -m venv .venv
source .venv/bin/activate
pip install .
cp .env.example .env
python -m app.main --http
```

**Requires Python 3.11+**

## Run as MCP (stdio)
```bash
make run-mcp
# or: .venv/bin/python -m app.main --mcp
```

## Testing
```bash
make test
```

## Docker
```bash
docker build -t homepilot-news-mcp .
docker run --rm -p 8787:8787 --env-file .env homepilot-news-mcp
```
