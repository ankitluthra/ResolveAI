import json
from datetime import UTC, datetime

import httpx
import pytest
from apps.api.app.core.config import Settings
from apps.api.app.models.domain import KnowledgeDocument
from apps.api.app.providers.coveo import (
    CoveoSearchProvider,
    RetryPolicy,
    document_body,
    parse_retry_after,
    parse_tags,
)

SETTINGS = Settings(
    _env_file=None, coveo_org_id="org", coveo_source_id="src", coveo_api_key="push-key"
)
NO_JITTER = RetryPolicy(max_attempts=4, start_delay=5, multiplier=2, max_delay=None, jitter=False)


class FakeSleep:
    def __init__(self):
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def make_doc(**overrides) -> KnowledgeDocument:
    values = {
        "id": "doc-001",
        "title": "Rotate OAuth secrets",
        "content": "Steps to rotate a client secret.",
        "source_type": "documentation",
        "tags": ["oauth", "security"],
    }
    return KnowledgeDocument(**{**values, **overrides})


def provider_for(handler, sleep, retry=NO_JITTER, settings=SETTINGS) -> CoveoSearchProvider:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return CoveoSearchProvider(settings, client, retry=retry, sleep=sleep)


@pytest.mark.asyncio
async def test_upload_retries_after_429_then_succeeds():
    calls = []

    def handler(request: httpx.Request):
        calls.append(request.method)
        if len(calls) <= 2:
            return httpx.Response(429)
        return httpx.Response(202)

    sleep = FakeSleep()
    provider = provider_for(handler, sleep)
    assert await provider.upload([make_doc()]) == (1, 0)
    assert calls == ["PUT", "PUT", "PUT"]
    # Same schedule as push-api-client.js: start delay, then doubled.
    assert sleep.delays == [5, 10]
    assert provider.failed_ids == []


@pytest.mark.asyncio
async def test_retry_honors_retry_after_header_and_retries_5xx():
    responses = iter(
        [httpx.Response(429, headers={"Retry-After": "7"}), httpx.Response(503), httpx.Response(200)]
    )
    sleep = FakeSleep()
    provider = provider_for(lambda request: next(responses), sleep)
    assert await provider.delete(["doc-001"]) == (1, 0)
    assert sleep.delays == [7.0, 10]


@pytest.mark.asyncio
async def test_upload_gives_up_after_max_attempts():
    calls = []

    def handler(request: httpx.Request):
        calls.append(request)
        return httpx.Response(429)

    sleep = FakeSleep()
    provider = provider_for(handler, sleep)
    assert await provider.upload([make_doc()]) == (0, 1)
    assert len(calls) == NO_JITTER.max_attempts
    assert sleep.delays == [5, 10, 20]
    assert provider.failed_ids == ["doc-001"]


@pytest.mark.asyncio
async def test_client_errors_are_not_retried():
    calls = []

    def handler(request: httpx.Request):
        calls.append(request)
        return httpx.Response(400)

    sleep = FakeSleep()
    provider = provider_for(handler, sleep)
    assert await provider.upload([make_doc()]) == (0, 1)
    assert len(calls) == 1 and sleep.delays == []


def test_retry_policy_defaults_match_official_client_and_jitter_stays_in_range():
    policy = RetryPolicy.from_settings(Settings(_env_file=None))
    assert (policy.max_attempts, policy.start_delay, policy.multiplier) == (10, 5.0, 2.0)
    for retry_number in range(1, 10):
        assert 0 <= policy.delay(retry_number) <= min(5.0 * 2 ** (retry_number - 1), 60.0)
    assert parse_retry_after("3") == 3.0
    assert parse_retry_after("Thu, 01 Jan 1970 00:00:00 GMT") == 0.0
    assert parse_retry_after("soon") is None


@pytest.mark.asyncio
async def test_upload_body_sends_tags_list_and_clickable_uri():
    bodies = []

    def handler(request: httpx.Request):
        bodies.append(json.loads(request.read()))
        assert request.headers["Authorization"] == "Bearer push-key"
        return httpx.Response(202)

    provider = provider_for(handler, FakeSleep())
    updated = datetime(2026, 3, 1, 12, tzinfo=UTC)
    await provider.upload([make_doc(updated_at=updated, url="https://example.com/a")])
    body = bodies[0]
    assert body["ra_tags"] == ["oauth", "security"]
    assert body["clickableUri"] == "https://example.com/a"
    assert "clickableuri" not in body
    assert body["date"] == body["ra_updated_at"] == updated.isoformat()


def test_document_body_omits_empty_values():
    body = document_body(make_doc(updated_at=None, tags=[], case_id=None, product=""))
    for key in ("date", "ra_updated_at", "ra_tags", "ra_case_id", "ra_product", "ra_category"):
        assert key not in body
    assert "" not in body.values()
    assert body["clickableUri"].endswith("/doc-001")


@pytest.mark.asyncio
async def test_search_reads_tags_from_list_or_string():
    def handler(request: httpx.Request):
        return httpx.Response(
            200,
            json={
                "results": [
                    {"title": "A", "raw": {"ra_id": "a", "ra_tags": ["oauth", "sso"]}},
                    {"title": "B", "raw": {"ra_id": "b", "ra_tags": "oauth;sso"}},
                    {"title": "C", "raw": {"ra_id": "c", "ra_tags": "oauth,sso"}},
                ]
            },
        )

    provider = provider_for(handler, FakeSleep())
    response = await provider.search("oauth")
    assert [result.tags for result in response.results] == [["oauth", "sso"]] * 3
    assert parse_tags(None) == []
