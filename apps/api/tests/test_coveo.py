import json

import httpx
import pytest
from apps.api.app.core.config import Settings
from apps.api.app.models.domain import KnowledgeDocument
from apps.api.app.providers.coveo import CoveoSearchProvider, parse_tags

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
async def test_upload_body_sends_tags_as_list():
    bodies = []

    def handler(request: httpx.Request):
        bodies.append(json.loads(request.read()))
        return httpx.Response(202)

    await provider_for(handler).upload([make_doc()])
    assert bodies[0]["ra_tags"] == ["oauth", "security"]


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
