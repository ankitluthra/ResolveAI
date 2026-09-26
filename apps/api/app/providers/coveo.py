import re
from datetime import UTC, datetime
from time import perf_counter
from urllib.parse import quote

import httpx
from apps.api.app.core.config import Settings
from apps.api.app.models.domain import (
    KnowledgeDocument,
    SearchFilters,
    SearchResponse,
    SearchResult,
)


def coveo_context(filters: SearchFilters | None) -> str:
    clauses = []
    if filters:
        for field in ("source_type", "product", "category", "visibility"):
            value = getattr(filters, field)
            if value:
                safe = re.sub(r"[^\w .:/-]", "", value)
                clauses.append(f'@ra_{field}=="{safe}"')
        if filters.updated_after:
            clauses.append(f"@ra_updated_at>={filters.updated_after:%Y/%m/%d}")
        if filters.updated_before:
            clauses.append(f"@ra_updated_at<={filters.updated_before:%Y/%m/%d}")
    return " AND ".join(clauses)


class CoveoSearchProvider:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        if not settings.coveo_org_id or not settings.coveo_api_key or not settings.coveo_source_id:
            raise ValueError("Coveo is not configured")
        self.settings = settings
        self.client = client or httpx.AsyncClient(timeout=20)
        self.headers = {"Authorization": f"Bearer {settings.coveo_api_key}"}
        self.failed_ids: list[str] = []
        self.search_url = (
            settings.coveo_search_endpoint
            or f"https://{settings.coveo_org_id}.org.coveo.com/rest/search/v2"
        )
        self.push_url = (
            f"{settings.coveo_push_base_url.rstrip('/')}/push/v1/organizations/"
            f"{settings.coveo_org_id}/sources/{settings.coveo_source_id}/documents"
        )

    async def search(
        self, query: str, filters: SearchFilters | None = None, limit: int = 10
    ) -> SearchResponse:
        start = perf_counter()
        source_name = re.sub(r'[^\w .:/-]', '', self.settings.coveo_source_name)
        context = f'@source=="{source_name}"'
        extra = coveo_context(filters)
        if extra:
            context += f" AND {extra}"
        response = await self.client.post(
            self.search_url,
            headers=self.headers,
            json={
                "q": query,
                "cq": context,
                "numberOfResults": limit,
                "fieldsToInclude": [
                    "ra_id",
                    "ra_source_type",
                    "ra_product",
                    "ra_category",
                    "ra_visibility",
                    "ra_tags",
                    "ra_updated_at",
                ],
            },
        )
        response.raise_for_status()
        payload = response.json()
        results = []
        for item in payload.get("results", []):
            raw = item.get("raw", {})
            document_id = raw.get("ra_id")
            if not document_id:
                continue
            results.append(
                SearchResult(
                    id=document_id,
                    title=item.get("title") or raw.get("title") or document_id,
                    content_preview=item.get("excerpt") or item.get("firstSentences") or "",
                    source_type=raw.get("ra_source_type", "documentation"),
                    product=raw.get("ra_product"),
                    category=raw.get("ra_category"),
                    url=item.get("clickUri"),
                    score=item.get("score"),
                    tags=(raw.get("ra_tags") or "").split(",")
                    if isinstance(raw.get("ra_tags"), str)
                    else raw.get("ra_tags", []),
                    visibility=raw.get("ra_visibility", "public"),
                    updated_at=raw.get("ra_updated_at"),
                )
            )
        return SearchResponse(
            query=query,
            provider="coveo",
            latency_ms=round((perf_counter() - start) * 1000, 1),
            total_results=payload.get("totalCount", len(results)),
            results=results,
            timestamp=datetime.now(UTC),
        )

    async def upload(self, documents: list[KnowledgeDocument]) -> tuple[int, int]:
        succeeded = failed = 0
        self.failed_ids = []
        for doc in documents:
            uri = f"https://docs.acmecloud.example/knowledge/{quote(doc.id)}"
            body = {
                "title": doc.title,
                "data": doc.content,
                "fileExtension": ".txt",
                "clickableuri": doc.url or uri,
                "date": doc.updated_at.isoformat() if doc.updated_at else "",
                "ra_id": doc.id,
                "ra_source_type": doc.source_type,
                "ra_product": doc.product or "",
                "ra_category": doc.category or "",
                "ra_visibility": doc.visibility,
                "ra_tags": ",".join(doc.tags),
                "ra_updated_at": doc.updated_at.isoformat() if doc.updated_at else "",
            }
            try:
                response = await self.client.put(
                    self.push_url, params={"documentId": uri}, headers=self.headers, json=body
                )
                response.raise_for_status()
                succeeded += 1
            except httpx.HTTPError:
                failed += 1
                self.failed_ids.append(doc.id)
        return succeeded, failed
