from datetime import UTC, datetime

import httpx
import pytest
from apps.api.app.core.config import Settings
from apps.api.app.models.domain import AnswerRequest, SearchResponse, SearchResult
from apps.api.app.services.answers import FALLBACK, generate_answer


def response(results: list[SearchResult]) -> SearchResponse:
    return SearchResponse(
        query="OAuth rotation",
        provider="azure",
        latency_ms=12,
        total_results=len(results),
        results=results,
        timestamp=datetime.now(UTC),
    )


def source() -> SearchResult:
    return SearchResult(
        id="doc-001",
        title="OAuth rotation",
        content_preview="Deploy the new secret before revoking the old secret.",
        source_type="documentation",
        score=2,
    )


@pytest.mark.asyncio
async def test_no_evidence_returns_fallback_without_model_call():
    answer = await generate_answer(
        AnswerRequest(query="OAuth rotation", provider="azure"), response([]), Settings()
    )
    assert answer.insufficient_evidence and answer.answer == FALLBACK


@pytest.mark.asyncio
async def test_unknown_citation_is_rejected():
    def handler(_: httpx.Request):
        return httpx.Response(
            200,
            json={
                "output": [
                    {"content": [{"type": "output_text", "text": "Use the new secret [invented]."}]}
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        answer = await generate_answer(
            AnswerRequest(query="OAuth rotation", provider="azure"),
            response([source()]),
            Settings(openai_api_key="test"),
            client,
        )
    assert answer.insufficient_evidence and answer.sources == [] and answer.answer == FALLBACK


@pytest.mark.asyncio
async def test_valid_citation_maps_to_retrieved_source():
    def handler(_: httpx.Request):
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "text": "Deploy the replacement secret first [doc-001].",
                            }
                        ]
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        answer = await generate_answer(
            AnswerRequest(query="OAuth rotation", provider="azure"),
            response([source()]),
            Settings(openai_api_key="test"),
            client,
        )
    assert not answer.insufficient_evidence and [item.id for item in answer.sources] == ["doc-001"]
