.PHONY: install test smoke lint clean run-http run-mcp

VENV       := .venv
PYTHON     := $(VENV)/bin/python
PIP        := $(VENV)/bin/pip
PYTEST     := $(VENV)/bin/pytest
DB_PATH    := /tmp/hp-news-test.sqlite3

# ── Install ──────────────────────────────────────────────
install: $(VENV)/bin/activate
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install pytest httpx pytest-asyncio
	@echo "\n✓ install complete – run 'make test' to verify"

$(VENV)/bin/activate:
	python3 -m venv $(VENV)

# ── Test ─────────────────────────────────────────────────
test: install
	NEWS_DB_PATH=$(DB_PATH) $(PYTEST) tests/ -v --tb=short
	@echo "\n✓ all tests passed"

# ── Smoke (live integration test) ────────────────────────
smoke: install
	$(PYTHON) smoke_test.py

# ── Lint (optional) ─────────────────────────────────────
lint: install
	$(PIP) install ruff 2>/dev/null; $(VENV)/bin/ruff check app/

# ── Run ──────────────────────────────────────────────────
run-http: install
	NEWS_DB_PATH=$(DB_PATH) $(PYTHON) -m app.main --http

run-mcp: install
	NEWS_DB_PATH=$(DB_PATH) $(PYTHON) -m app.main --mcp

# ── Clean ────────────────────────────────────────────────
clean:
	rm -rf $(VENV) __pycache__ .pytest_cache tests/__pycache__
	rm -f $(DB_PATH)
