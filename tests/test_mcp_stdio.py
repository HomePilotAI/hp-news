"""Tests for MCP stdio protocol handling."""
import json
from app.mcp_stdio import TOOLS


def test_tools_list_has_expected_names():
    names = {t["name"] for t in TOOLS}
    assert names == {"news.top", "news.search", "news.sources", "news.health"}


def test_tools_have_input_schemas():
    for t in TOOLS:
        assert "inputSchema" in t
        assert t["inputSchema"]["type"] == "object"


def test_tools_list_is_not_empty():
    assert len(TOOLS) == 4
