from typing import Protocol

from apps.api.app.models.domain import SearchFilters, SearchResponse


class SearchProvider(Protocol):
    async def search(
        self, query: str, filters: SearchFilters | None = None, limit: int = 10
    ) -> SearchResponse: ...
