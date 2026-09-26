from datetime import UTC, datetime
from time import perf_counter

import httpx
from apps.api.app.core.config import Settings
from apps.api.app.models.domain import (
    KnowledgeDocument,
    SearchFilters,
    SearchResponse,
    SearchResult,
)


def _escape(value: str) -> str:
    return value.replace("'", "''")


def azure_filter(filters: SearchFilters | None) -> str | None:
    if not filters:
        return None
    clauses = []
    for field in ("source_type", "product", "category", "visibility"):
        value = getattr(filters, field)
        if value:
            clauses.append(f"{field} eq '{_escape(value)}'")
    if filters.updated_after:
        clauses.append(f"updated_at ge {filters.updated_after.isoformat()}")
    if filters.updated_before:
        clauses.append(f"updated_at le {filters.updated_before.isoformat()}")
    return " and ".join(clauses) or None


INDEX_FIELDS = [
    {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
    {"name": "title", "type": "Edm.String", "searchable": True},
    {"name": "content", "type": "Edm.String", "searchable": True},
    *[
        {"name": field, "type": "Edm.String", "filterable": True, "facetable": True}
        for field in ("source_type", "product", "category", "visibility")
    ],
    {"name": "url", "type": "Edm.String"},
    {"name": "created_at", "type": "Edm.DateTimeOffset", "filterable": True, "sortable": True},
    {"name": "updated_at", "type": "Edm.DateTimeOffset", "filterable": True, "sortable": True},
    {"name": "tags", "type": "Collection(Edm.String)", "filterable": True, "facetable": True},
    {"name": "metadata_json", "type": "Edm.String"},
]


class AzureSearchProvider:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        if not settings.azure_search_endpoint or not settings.azure_search_api_key:
            raise ValueError("Azure AI Search is not configured")
        self.settings = settings
        self.client = client or httpx.AsyncClient(timeout=20)
        self.base = (
            f"{settings.azure_search_endpoint.rstrip('/')}/indexes('{settings.azure_search_index}')"
        )
        self.params = {"api-version": settings.azure_search_api_version}
        self.headers = {"api-key": settings.azure_search_api_key}
        self.failed_ids: list[str] = []

    async def search(
        self, query: str, filters: SearchFilters | None = None, limit: int = 10
    ) -> SearchResponse:
        start = perf_counter()
        response = await self.client.post(
            f"{self.base}/docs/search.post.search",
            params=self.params,
            headers=self.headers,
            json={
                "search": query,
                "filter": azure_filter(filters),
                "top": limit,
                "count": True,
                "searchFields": "title,content",
            },
        )
        response.raise_for_status()
        payload = response.json()
        results = [
            SearchResult(
                id=item["id"],
                title=item["title"],
                content_preview=item.get("content", "")[:520],
                source_type=item["source_type"],
                product=item.get("product"),
                category=item.get("category"),
                url=item.get("url"),
                score=item.get("@search.score"),
                tags=item.get("tags") or [],
                visibility=item.get("visibility", "public"),
                updated_at=item.get("updated_at"),
            )
            for item in payload.get("value", [])
        ]
        return SearchResponse(
            query=query,
            provider="azure",
            latency_ms=round((perf_counter() - start) * 1000, 1),
            total_results=payload.get("@odata.count", len(results)),
            results=results,
            timestamp=datetime.now(UTC),
        )

    async def create_index(self) -> None:
        response = await self.client.put(
            self.base,
            params=self.params,
            headers=self.headers,
            json={"name": self.settings.azure_search_index, "fields": INDEX_FIELDS},
        )
        response.raise_for_status()

    async def upload(self, documents: list[KnowledgeDocument]) -> tuple[int, int]:
        import json

        succeeded = failed = 0
        self.failed_ids = []
        for start in range(0, len(documents), 100):
            batch = []
            for doc in documents[start : start + 100]:
                item = doc.model_dump(mode="json", exclude={"metadata"})
                item["metadata_json"] = json.dumps(doc.metadata)
                item["@search.action"] = "upload"
                batch.append(item)
            response = await self.client.post(
                f"{self.base}/docs/index",
                params=self.params,
                headers=self.headers,
                json={"value": batch},
            )
            response.raise_for_status()
            results = response.json().get("value", [])
            by_key = {result.get("key"): result for result in results}
            for item in batch:
                result = by_key.get(item["id"])
                if result and result.get("status") is True:
                    succeeded += 1
                else:
                    failed += 1
                    self.failed_ids.append(item["id"])
        return succeeded, failed
