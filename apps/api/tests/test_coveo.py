import json
from datetime import UTC, datetime

import httpx
import pytest
from apps.api.app.core.config import Settings
from apps.api.app.models.domain import KnowledgeDocument
from apps.api.app.providers.coveo import CoveoSearchProvider, document_body, parse_tags

SETTINGS = Settings(
    _env_file=None, coveo_org_id="org", coveo_source_id="src", coveo_api_key="push-key"
)


def make_doc(**overrides) -> KnowledgeDocument:
    values = {
        "id": "doc-001",
        "title": "Rotate OAuth secrets",
        "content": "Steps to rotate a client secret.",
        "source_type": "documentation",
        "tags": ["oauth", "security"],
    }
    return KnowledgeDocument(**{**values, **overrides})


def provider_for(handler, settings=SETTINGS) -> CoveoSearchProvider:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return CoveoSearchProvider(settings, client)


@pytest.mark.asyncio
async def test_upload_body_sends_tags_list_and_clickable_uri():
    bodies = []

    def handler(request: httpx.Request):
        bodies.append(json.loads(request.read()))
        assert request.headers["Authorization"] == "Bearer push-key"
        return httpx.Response(202)

    provider = provider_for(handler)
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

    provider = provider_for(handler)
    response = await provider.search("oauth")
    assert [result.tags for result in response.results] == [["oauth", "sso"]] * 3
    assert parse_tags(None) == []
