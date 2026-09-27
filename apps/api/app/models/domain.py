from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

SourceType = Literal["documentation", "faq", "github_issue", "support_ticket", "release_note"]
Visibility = Literal["public", "support", "engineering"]
ProviderName = Literal["azure", "coveo"]


class KnowledgeDocument(BaseModel):
    id: str
    title: str
    content: str
    source_type: SourceType
    case_id: str | None = None
    product: str | None = None
    category: str | None = None
    url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    visibility: Visibility = "public"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchFilters(BaseModel):
    case_id: str | None = None
    source_type: SourceType | None = None
    product: str | None = None
    category: str | None = None
    visibility: Visibility | None = None
    updated_after: datetime | None = None
    updated_before: datetime | None = None


class SearchResult(BaseModel):
    id: str
    title: str
    content_preview: str
    source_type: SourceType
    case_id: str | None = None
    product: str | None = None
    category: str | None = None
    url: str | None = None
    score: float | None = None
    tags: list[str] = Field(default_factory=list)
    visibility: Visibility = "public"
    updated_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    provider: ProviderName
    latency_ms: float
    total_results: int
    results: list[SearchResult]
    timestamp: datetime


class AnswerRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    provider: ProviderName
    filters: SearchFilters | None = None


class AnswerSource(BaseModel):
    id: str
    title: str
    url: str | None = None


class AnswerResponse(BaseModel):
    answer: str
    provider: ProviderName
    search_latency_ms: float
    generation_latency_ms: float
    sources: list[AnswerSource]
    insufficient_evidence: bool
