from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class NewsItem(BaseModel):
    id: str
    title: str
    url: str
    source: str
    topic: str = "general"
    published_at: Optional[datetime] = None
    summary: Optional[str] = None
    language: Optional[str] = None
    region: Optional[str] = None
    score: float = 0.0

class TopResponse(BaseModel):
    items: List[NewsItem] = Field(default_factory=list)

class SourcesResponse(BaseModel):
    sources: list[dict] = Field(default_factory=list)

class HealthResponse(BaseModel):
    ok: bool
    db_path: str
    last_refresh_at: Optional[datetime] = None
    sources_enabled: dict
