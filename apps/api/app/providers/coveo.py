import asyncio
import random
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from time import perf_counter
from typing import Any
from urllib.parse import quote

import httpx
from apps.api.app.core.config import Settings
from apps.api.app.models.domain import (
    KnowledgeDocument,
    SearchFilters,
    SearchResponse,
    SearchResult,
)

Sleep = Callable[[float], Awaitable[None]]

# 429 is Coveo's throttling status. The 5xx codes are transient gateway or server errors.
# Push PUT/DELETE calls are idempotent, so repeating them is safe.
RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


@dataclass(frozen=True)
class RetryPolicy:
    """Exponential backoff with full jitter, matching Coveo's push-api-client.js defaults.

    The official client makes up to 10 attempts, waiting about 5 s, 10 s, 20 s, ... between
    them. ``max_delay`` caps one wait; the official client has no cap.
    """

    max_attempts: int = 10
    start_delay: float = 5.0
    multiplier: float = 2.0
    max_delay: float | None = 60.0
    jitter: bool = True

    @classmethod
    def from_settings(cls, settings: Settings) -> "RetryPolicy":
        return cls(
            max_attempts=max(1, settings.coveo_max_attempts),
            start_delay=settings.coveo_retry_start_delay_ms / 1000,
            multiplier=settings.coveo_retry_multiplier,
            max_delay=(settings.coveo_retry_max_delay_ms / 1000)
            if settings.coveo_retry_max_delay_ms > 0
            else None,
        )

    def delay(self, retry_number: int, retry_after: float | None = None) -> float:
        """Seconds to wait before retry ``retry_number`` (1 for the first retry)."""
        if retry_after is not None:
            return retry_after
        delay = self.start_delay * self.multiplier ** (retry_number - 1)
        if self.max_delay is not None:
            delay = min(delay, self.max_delay)
        return random.uniform(0, delay) if self.jitter else delay


def parse_retry_after(value: str | None) -> float | None:
    """Read a Retry-After header given in seconds or as an HTTP date."""
    if not value:
        return None
    value = value.strip()
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return max(0.0, (when - datetime.now(UTC)).total_seconds())


async def send_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    policy: RetryPolicy,
    sleep: Sleep = asyncio.sleep,
    **kwargs: Any,
) -> httpx.Response:
    """Send a request, retrying throttled (429), transient 5xx and connection failures.

    Returns the final response, which may still be an error; callers decide whether to raise.
    """
    for attempt in range(1, policy.max_attempts + 1):
        last_attempt = attempt == policy.max_attempts
        try:
            response = await client.request(method, url, **kwargs)
        except httpx.TransportError:
            if last_attempt:
                raise
            await sleep(policy.delay(attempt))
            continue
        if response.status_code not in RETRYABLE_STATUS or last_attempt:
            return response
        await sleep(policy.delay(attempt, parse_retry_after(response.headers.get("Retry-After"))))
    raise AssertionError("unreachable")


def coveo_context(filters: SearchFilters | None) -> str:
    clauses = []
    if filters:
        for field in ("case_id", "source_type", "product", "category", "visibility"):
            value = getattr(filters, field)
            if value:
                safe = re.sub(r"[^\w .:/-]", "", value)
                clauses.append(f'@ra_{field}=="{safe}"')
        if filters.updated_after:
            clauses.append(f"@ra_updated_at>={filters.updated_after:%Y/%m/%d}")
        if filters.updated_before:
            clauses.append(f"@ra_updated_at<={filters.updated_before:%Y/%m/%d}")
    return " AND ".join(clauses)


def document_uri(document_id: str) -> str:
    return f"https://docs.acmecloud.example/knowledge/{quote(document_id)}"


def parse_tags(value: Any) -> list[str]:
    """Read ra_tags from a result, whether Coveo returns a list or a delimited string."""
    if not value:
        return []
    if isinstance(value, str):
        value = re.split(r"[;,]", value)
    return [str(tag).strip() for tag in value if str(tag).strip()]


def document_body(doc: KnowledgeDocument) -> dict[str, Any]:
    """Build a Push API document body. Empty optional values are left out, not sent as ""."""
    body: dict[str, Any] = {
        "title": doc.title,
        "data": doc.content,
        "fileExtension": ".txt",
        "clickableUri": doc.url or document_uri(doc.id),
        "ra_id": doc.id,
        "ra_source_type": doc.source_type,
        "ra_visibility": doc.visibility,
    }
    if doc.updated_at:
        body["date"] = doc.updated_at.isoformat()
        body["ra_updated_at"] = doc.updated_at.isoformat()
    optional = {
        "ra_case_id": doc.case_id,
        "ra_product": doc.product,
        "ra_category": doc.category,
    }
    body.update({key: value for key, value in optional.items() if value})
    tags = [tag for tag in doc.tags if tag]
    if tags:
        body["ra_tags"] = tags
    return body


class CoveoSearchProvider:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        *,
        pipeline: str = "",
        retry: RetryPolicy | None = None,
        sleep: Sleep = asyncio.sleep,
    ):
        if not settings.coveo_org_id or not settings.coveo_api_key or not settings.coveo_source_id:
            raise ValueError("Coveo is not configured")
        self.settings = settings
        self.client = client or httpx.AsyncClient(timeout=20)
        self.headers = {"Authorization": f"Bearer {settings.coveo_api_key}"}
        self.retry = retry or RetryPolicy.from_settings(settings)
        self.sleep = sleep
        self.failed_ids: list[str] = []
        self.pipeline = pipeline
        self.search_url = (
            settings.coveo_search_endpoint
            or f"https://{settings.coveo_org_id}.org.coveo.com/rest/search/v2"
        )
        self.push_url = (
            f"{settings.coveo_push_base_url.rstrip('/')}/push/v1/organizations/"
            f"{settings.coveo_org_id}/sources/{settings.coveo_source_id}/documents"
        )

    async def _push(self, method: str, **kwargs: Any) -> httpx.Response:
        response = await send_with_retry(
            self.client,
            method,
            self.push_url,
            policy=self.retry,
            sleep=self.sleep,
            headers=self.headers,
            **kwargs,
        )
        response.raise_for_status()
        return response

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
            params={"pipeline": self.pipeline} if self.pipeline else None,
            headers=self.headers,
            json={
                "q": query,
                "cq": context,
                "numberOfResults": limit,
                "fieldsToInclude": [
                    "ra_id",
                    "ra_case_id",
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
                    case_id=raw.get("ra_case_id") or None,
                    product=raw.get("ra_product"),
                    category=raw.get("ra_category"),
                    url=item.get("clickUri"),
                    score=item.get("score"),
                    tags=parse_tags(raw.get("ra_tags")),
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
            try:
                await self._push(
                    "PUT", params={"documentId": document_uri(doc.id)}, json=document_body(doc)
                )
                succeeded += 1
            except httpx.HTTPError:
                failed += 1
                self.failed_ids.append(doc.id)
        return succeeded, failed

    async def delete(self, document_ids: list[str]) -> tuple[int, int]:
        succeeded = failed = 0
        self.failed_ids = []
        for document_id in document_ids:
            try:
                await self._push("DELETE", params={"documentId": document_uri(document_id)})
                succeeded += 1
            except httpx.HTTPError:
                failed += 1
                self.failed_ids.append(document_id)
        return succeeded, failed
