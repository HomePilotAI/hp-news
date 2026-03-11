.PHONY: install test smoke lint clean run-http run-mcp

VENV       := .venv
PYTHON     := $(VENV)/bin/python
PIP        := $(VENV)/bin/pip
PYTEST     := $(VENV)/bin/pytest
DB_PATH    := /tmp/hp-news-test.sqlite3

# Detect uv for faster installs
UV := $(shell command -v uv 2>/dev/null)

# ── Install ──────────────────────────────────────────────
install: $(VENV)/bin/activate
ifdef UV
	$(UV) pip install --python $(PYTHON) .
	$(UV) pip install --python $(PYTHON) pytest httpx pytest-asyncio
else
	$(PIP) install --upgrade pip
	$(PIP) install .
	$(PIP) install pytest httpx pytest-asyncio
endif
	@echo "\n✓ install complete – run 'make test' to verify"

$(VENV)/bin/activate:
ifdef UV
	$(UV) venv $(VENV) --python python3.11
else
	python3 -m venv $(VENV)
endif

# ── Test ─────────────────────────────────────────────────
test: install
	NEWS_DB_PATH=$(DB_PATH) $(PYTEST) tests/ -v --tb=short
	@echo "\n✓ all tests passed"

# ── Smoke (live integration test) ────────────────────────
smoke: install
	$(PYTHON) smoke_test.py

# ── Lint (optional) ─────────────────────────────────────
lint: install
ifdef UV
	$(UV) pip install --python $(PYTHON) ruff 2>/dev/null; $(VENV)/bin/ruff check app/
else
	$(PIP) install ruff 2>/dev/null; $(VENV)/bin/ruff check app/
endif

# ── Run ──────────────────────────────────────────────────
run-http: install
	NEWS_DB_PATH=$(DB_PATH) $(PYTHON) -m app.main --http

run-mcp: install
	NEWS_DB_PATH=$(DB_PATH) $(PYTHON) -m app.main --mcp

# ── Clean ────────────────────────────────────────────────
clean:
	rm -rf $(VENV) __pycache__ .pytest_cache tests/__pycache__
	rm -f $(DB_PATH)
