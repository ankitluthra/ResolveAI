from datetime import UTC, datetime

import pytest
from apps.api.app import main
from apps.api.app.models.domain import SearchFilters, SearchResponse, SearchResult
from apps.api.app.providers.azure_search import azure_filter
from apps.api.app.providers.coveo import coveo_context
from apps.api.app.services.cases import case_detail, load_cases
from evals import case_evaluator
from fastapi.testclient import TestClient


def test_curated_case_links_have_source_evidence():
    cases = load_cases()
    assert {case.id for case in cases} == {
        "case-oauth-rotation",
        "case-webhook-signature",
        "case-sso-roles",
    }
    for case in cases:
        detail = case_detail(case.id)
        assert detail is not None
        documents = {document.id: document for document in detail.documents}
        assert len(documents) == len(case.document_ids)
        for edge in case.edges:
            assert edge.evidence_excerpt in documents[edge.evidence_document_id].content
        assert set(case.finding_source_ids).issubset(documents)
    assert "not confirmed" in case_detail("case-sso-roles").finding


def test_case_routes_and_provider_retrieval(monkeypatch):
    calls = []

    async def fake_search(query, provider, filters, limit):
        calls.append((query, provider, filters.case_id, limit))
        ids = ["ticket-001"] if query else ["ticket-001", "issue-001", "release-001"]
        return SearchResponse(
            query=query,
            provider="coveo",
            latency_ms=12,
            total_results=len(ids),
            results=[
                SearchResult(
                    id=document_id,
                    title=document_id,
                    content_preview="Evidence",
                    source_type="support_ticket",
                )
                for document_id in ids
            ],
            timestamp=datetime.now(UTC),
        )

    monkeypatch.setattr(main, "execute_search", fake_search)
    client = TestClient(main.app)
    summaries = client.get("/api/cases").json()
    assert len(summaries) == 3
    assert client.get("/api/cases/missing").status_code == 404
    local = client.get("/api/cases/case-oauth-rotation").json()
    assert local["retrieval"] is None
    assert len(local["edges"]) == 4
    live = client.get("/api/cases/case-oauth-rotation?provider=coveo").json()
    assert live["retrieval"]["entry_result_ids"] == ["ticket-001"]
    assert live["retrieval"]["indexed_document_ids"] == [
        "ticket-001",
        "issue-001",
        "release-001",
    ]
    assert calls == [
        (local["search_query"], "coveo", None, 10),
        ("", "coveo", "case-oauth-rotation", 50),
    ]


@pytest.mark.parametrize(
    "value",
    ["case-oauth-rotation", "case-webhook-signature"],
)
def test_case_id_is_filterable_in_both_providers(value):
    filters = SearchFilters(case_id=value)
    assert f"case_id eq '{value}'" in azure_filter(filters)
    assert f'@ra_case_id=="{value}"' in coveo_context(filters)


@pytest.mark.asyncio
async def test_case_evaluation_separates_entry_search_from_connected_retrieval(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(case_evaluator, "RESULTS", tmp_path)
    cases = {case.id: case for case in load_cases()}

    class Provider:
        async def search(self, query, filters=None, limit=10):
            case_id = filters.case_id if filters else "case-oauth-rotation"
            ids = cases[case_id].document_ids if filters else ["ticket-001"]
            return SearchResponse(
                query=query,
                provider="coveo",
                latency_ms=9,
                total_results=len(ids),
                results=[
                    SearchResult(
                        id=document_id,
                        title=document_id,
                        content_preview="Evidence",
                        source_type="support_ticket",
                    )
                    for document_id in ids
                ],
                timestamp=datetime.now(UTC),
            )

    result = await case_evaluator.run_case_evaluation("coveo", Provider())
    assert result["query_count"] == 6
    assert result["summary"]["related_evidence_recall"] == 1
    assert result["summary"]["path_coverage"] == 1
    assert result["summary"]["entry_evidence_recall"] < 1
    assert (tmp_path / "coveo-cases.json").exists()
