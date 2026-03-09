from __future__ import annotations
from datetime import datetime, timezone
import math
from collections import defaultdict

def _hours_ago(dt):
    if not dt:
        return 1e6
    now = datetime.now(timezone.utc)
    return max((now - dt).total_seconds() / 3600.0, 0.0)

def recency_score(published_at):
    h = _hours_ago(published_at)
    return 1.0 / (1.0 + (h/12.0))

def title_key(title: str) -> str:
    t = (title or "").lower()
    for ch in ",.:;!?()[]{}'\"":
        t = t.replace(ch, " ")
    t = " ".join(t.split())
    stop = {"the","a","an","and","or","to","of","in","on","for","with","at","from","by","as","is","are","was","were"}
    words = [w for w in t.split() if w not in stop]
    return " ".join(words[:12])

def cluster_boost(items: list[dict]) -> dict[str, float]:
    clusters = defaultdict(list)
    for it in items:
        clusters[title_key(it.get("title",""))].append(it)
    boost = {}
    for k, group in clusters.items():
        b = math.log(1 + len(group), 2)
        for it in group:
            boost[it["id"]] = b
    return boost

def rank_items(items: list[dict], source_weights: dict[str,float], w_recency: float, w_source: float, w_cluster: float) -> list[dict]:
    boosts = cluster_boost(items)
    for it in items:
        s_w = float(source_weights.get(it.get("source_id",""), 1.0))
        r = recency_score(it.get("published_at"))
        c = float(boosts.get(it["id"], 0.0))
        it["score"] = (w_recency * r) + (w_source * s_w) + (w_cluster * c)
    return sorted(items, key=lambda x: x["score"], reverse=True)
