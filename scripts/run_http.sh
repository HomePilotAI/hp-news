#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1
python -m app.main --http
