import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import httpx
import pytest
from apps.api.app.main import app
from apps.api.app.models.domain import SearchFilters, SearchResponse
from apps.api.app.providers.azure_search import AzureSearchProvider, azure_filter
from apps.api.app.providers.coveo import CoveoSearchProvider, coveo_context
from evals import evaluator
from evals.evaluator import metric_for_query
from fastapi.testclient import TestClient
from ingestion.connectors.local import fetch_local
from ingestion.normalizer import normalize
from pydantic import ValidationError
from scripts.sync_incremental import fingerprint, plan_sync

ROOT = Path(__file__).resolve().parents[3]


def test_normalized_corpus_and_stable_ids():
    docs = fetch_local(ROOT / "data/synthetic")
    assert len(docs) == 250
    assert len({item.id for item in docs}) == 250
    assert {item.source_type for item in docs} == {
        "documentation",
        "faq",
        "github_issue",
        "support_ticket",
        "release_note",
    }
    assert all(item.metadata["synthetic"] for item in docs)
    with pytest.raises(ValidationError):
        normalize({"id": "bad", "title": "x", "content": "x"}, "unknown")


def test_evaluation_set_references_real_documents():
    docs = {item.id for item in fetch_local(ROOT / "data/synthetic")}
    cases = json.loads((ROOT / "evals/dataset.json").read_text())
    assert len(cases) >= 20
    assert all(set(case["expected_document_ids"]).issubset(docs) for case in cases)
    assert metric_for_query(["a"], ["b", "a"]) == {"hit_at_1": 0.0, "hit_at_3": 1.0, "mrr": 0.5}
    assert metric_for_query(["a"], ["b"]) == {"hit_at_1": 0.0, "hit_at_3": 0.0, "mrr": 0.0}


def test_filters_escape_input():
    filters = SearchFilters(product="Bob's API", visibility="public")
    assert "Bob''s API" in azure_filter(filters)
    assert '@ra_visibility=="public"' in coveo_context(filters)


def test_api_validation_and_missing_configuration():
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/api/search", params={"q": "a"}).status_code == 422
    assert (
        client.get("/api/search", params={"q": "oauth", "provider": "invalid"}).status_code == 422
    )
    assert client.get("/api/search", params={"q": "oauth", "provider": "azure"}).status_code == 503
    assert client.get("/api/documents/doc-001").json()["id"] == "doc-001"
    assert client.get("/api/documents/missing").status_code == 404
    assert len(client.get("/api/evaluations").json()["dataset"]) >= 20


@pytest.mark.asyncio
async def test_azure_search_adapter_maps_response():
    from apps.api.app.core.config import Settings

    def handler(request: httpx.Request):
        assert request.headers["api-key"] == "test-key"
        assert request.url.path.endswith("/docs/search.post.search")
        assert request.read() is not None
        return httpx.Response(
            200,
            json={
                "@odata.count": 1,
                "value": [
                    {
                        "id": "doc-001",
                        "title": "OAuth",
                        "content": "Rotate secret",
                        "source_type": "documentation",
                        "@search.score": 2.5,
                    }
                ],
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = AzureSearchProvider(
            Settings(
                azure_search_endpoint="https://test.search.windows.net",
                azure_search_api_key="test-key",
            ),
            client,
        )
        response = await provider.search("oauth")
    assert response.provider == "azure" and response.results[0].id == "doc-001"


@pytest.mark.asyncio
async def test_coveo_search_adapter_maps_response():
    from apps.api.app.core.config import Settings

    def handler(request: httpx.Request):
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "totalCount": 1,
                "results": [
                    {
                        "title": "OAuth",
                        "excerpt": "Rotate secret",
                        "score": 20,
                        "raw": {"ra_id": "doc-001", "ra_source_type": "documentation"},
                    }
                ],
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = CoveoSearchProvider(
            Settings(coveo_org_id="test", coveo_source_id="src", coveo_api_key="test-key"), client
        )
        response = await provider.search("oauth")
    assert response.provider == "coveo" and response.results[0].id == "doc-001"


@pytest.mark.asyncio
async def test_azure_upload_reports_missing_item_status_as_failure():
    from apps.api.app.core.config import Settings

    documents = fetch_local(ROOT / "data/synthetic")[:2]

    def handler(request: httpx.Request):
        assert request.url.path.endswith("/docs/index")
        return httpx.Response(200, json={"value": [{"key": documents[0].id, "status": True}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = AzureSearchProvider(
            Settings(
                azure_search_endpoint="https://test.search.windows.net",
                azure_search_api_key="test-key",
            ),
            client,
        )
        succeeded, failed = await provider.upload(documents)
    assert (succeeded, failed) == (1, 1)
    assert provider.failed_ids == [documents[1].id]


@pytest.mark.asyncio
async def test_coveo_upload_reports_failed_document_and_configured_source():
    from apps.api.app.core.config import Settings

    documents = fetch_local(ROOT / "data/synthetic")[:1]

    def handler(request: httpx.Request):
        if request.method == "POST":
            assert json.loads(request.read())["cq"] == '@source=="My Source"'
            return httpx.Response(200, json={"results": []})
        return httpx.Response(429, json={"message": "rate limited"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = CoveoSearchProvider(
            Settings(
                coveo_org_id="test",
                coveo_source_id="src",
                coveo_source_name="My Source",
                coveo_api_key="test-key",
            ),
            client,
        )
        await provider.search("oauth")
        succeeded, failed = await provider.upload(documents)
    assert (succeeded, failed) == (0, 1)
    assert provider.failed_ids == [documents[0].id]


@pytest.mark.asyncio
async def test_evaluation_records_input_fingerprints(tmp_path, monkeypatch):
    monkeypatch.setattr(evaluator, "RESULTS", tmp_path)

    class EmptyProvider:
        async def search(self, query, filters=None, limit=10):
            return SearchResponse(
                query=query,
                provider="azure",
                latency_ms=1,
                total_results=0,
                results=[],
                timestamp=datetime.now(UTC),
            )

    result = await evaluator.run_evaluation("azure", EmptyProvider())
    assert result["query_count"] == 20
    assert result["dataset_sha256"] == sha256(evaluator.DATASET.read_bytes()).hexdigest()
    assert result["corpus_sha256"] == sha256(evaluator.CORPUS.read_bytes()).hexdigest()
    assert (tmp_path / "azure.json").exists()


def test_incremental_sync_identifies_update_and_delete():
    documents = fetch_local(ROOT / "data/synthetic")[:2]
    previous = {documents[0].id: fingerprint(documents[0]), "removed-001": "old"}
    changed, removed, current = plan_sync(documents, previous)
    assert [item.id for item in changed] == [documents[1].id]
    assert removed == ["removed-001"]
    assert set(current) == {item.id for item in documents}


@pytest.mark.asyncio
async def test_provider_delete_calls_use_stable_ids():
    from apps.api.app.core.config import Settings

    seen = []

    def azure_handler(request: httpx.Request):
        body = json.loads(request.read())
        seen.append(body["value"][0])
        return httpx.Response(200, json={"value": [{"key": "doc-001", "status": True}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(azure_handler)) as client:
        provider = AzureSearchProvider(
            Settings(
                azure_search_endpoint="https://test.search.windows.net",
                azure_search_api_key="test-key",
            ),
            client,
        )
        assert await provider.delete(["doc-001"]) == (1, 0)
    assert seen == [{"@search.action": "delete", "id": "doc-001"}]

    def coveo_handler(request: httpx.Request):
        assert request.method == "DELETE"
        assert request.url.params["documentId"].endswith("/doc-001")
        return httpx.Response(202)

    async with httpx.AsyncClient(transport=httpx.MockTransport(coveo_handler)) as client:
        provider = CoveoSearchProvider(
            Settings(coveo_org_id="test", coveo_source_id="src", coveo_api_key="test-key"),
            client,
        )
        assert await provider.delete(["doc-001"]) == (1, 0)
