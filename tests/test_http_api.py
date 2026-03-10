"""Tests for the HTTP API endpoints using FastAPI TestClient."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.http_api import create_app
from app.config import load_settings


@pytest.fixture()
def client(populated_conn):
    settings = load_settings()
    app = create_app(populated_conn, settings)
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert "db_path" in body
    assert "sources_enabled" in body


@pytest.mark.asyncio
async def test_sources_endpoint(client):
    resp = await client.get("/v1/news/sources")
    assert resp.status_code == 200
    body = resp.json()
    assert "sources" in body


@pytest.mark.asyncio
async def test_top_endpoint(client):
    resp = await client.get("/v1/news/top", params={"topic": "tech", "limit": 5, "hours": 48})
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body


@pytest.mark.asyncio
async def test_search_endpoint(client):
    resp = await client.get("/v1/news/search", params={"q": "AI", "limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert len(body["items"]) >= 1


@pytest.mark.asyncio
async def test_search_requires_query(client):
    resp = await client.get("/v1/news/search")
    assert resp.status_code == 422  # missing required param
