"""Tests for the ranking module."""
from datetime import datetime, timezone, timedelta
from app.ranking import recency_score, title_key, cluster_boost, rank_items


def test_recency_score_recent_is_higher():
    now = datetime.now(timezone.utc)
    old = now - timedelta(hours=48)
    assert recency_score(now) > recency_score(old)


def test_recency_score_none():
    assert recency_score(None) < 0.01


def test_title_key_strips_stopwords():
    k = title_key("The Quick Brown Fox and the Lazy Dog")
    assert "the" not in k.split()
    assert "quick" in k.split()


def test_cluster_boost_groups_similar():
    items = [
        {"id": "1", "title": "AI is great"},
        {"id": "2", "title": "AI is great"},
        {"id": "3", "title": "Something else"},
    ]
    boosts = cluster_boost(items)
    assert boosts["1"] > boosts["3"]


def test_rank_items_produces_scores():
    now = datetime.now(timezone.utc)
    items = [
        {"id": "1", "title": "A", "source_id": "s1", "published_at": now},
        {"id": "2", "title": "B", "source_id": "s1", "published_at": now - timedelta(hours=24)},
    ]
    ranked = rank_items(items, {"s1": 1.0}, w_recency=1.0, w_source=1.0, w_cluster=0.5)
    assert ranked[0]["score"] >= ranked[1]["score"]
    assert all("score" in it for it in ranked)
