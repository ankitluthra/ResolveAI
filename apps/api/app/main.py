import json
import logging
from datetime import datetime
from pathlib import Path

import httpx
from apps.api.app.core.config import get_settings
from apps.api.app.models.domain import (
    AnswerRequest,
    AnswerResponse,
    KnowledgeDocument,
    ProviderName,
    SearchFilters,
    SearchResponse,
    SourceType,
    Visibility,
)
from apps.api.app.providers.azure_search import AzureSearchProvider
from apps.api.app.providers.coveo import CoveoSearchProvider
from apps.api.app.services.answers import generate_answer
from evals.evaluator import read_evaluations, run_evaluation
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("resolveai")
app = FastAPI(title="ResolveAI API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().cors_origin, "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def get_provider(name: ProviderName):
    settings = get_settings()
    try:
        return AzureSearchProvider(settings) if name == "azure" else CoveoSearchProvider(settings)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


async def execute_search(
    query: str, provider: ProviderName, filters: SearchFilters, limit: int
) -> SearchResponse:
    adapter = get_provider(provider)
    try:
        response = await adapter.search(query, filters, limit)
    except httpx.HTTPError as exc:
        logger.error(
            json.dumps(
                {"event": "search_error", "provider": provider, "error_type": type(exc).__name__}
            )
        )
        raise HTTPException(status_code=502, detail=f"{provider} search request failed") from exc
    finally:
        await adapter.client.aclose()
    logger.info(
        json.dumps(
            {
                "event": "search",
                "provider": provider,
                "query": query,
                "result_count": response.total_results,
                "latency_ms": response.latency_ms,
                "top_documents": [item.id for item in response.results[:5]],
                "timestamp": response.timestamp.isoformat(),
            }
        )
    )
    return response


@app.get("/health")
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "providers": {
            "azure": bool(settings.azure_search_endpoint and settings.azure_search_api_key),
            "coveo": bool(
                settings.coveo_org_id and settings.coveo_api_key and settings.coveo_source_id
            ),
        },
        "answer_enabled": bool(settings.openai_api_key),
    }


@app.get("/api/search", response_model=SearchResponse)
async def search(
    q: str = Query(min_length=2, max_length=500),
    provider: ProviderName = "azure",
    source_type: SourceType | None = None,
    product: str | None = None,
    category: str | None = None,
    visibility: Visibility | None = None,
    updated_after: datetime | None = None,
    updated_before: datetime | None = None,
    limit: int = Query(default=10, ge=1, le=50),
):
    filters = SearchFilters(
        source_type=source_type,
        product=product,
        category=category,
        visibility=visibility,
        updated_after=updated_after,
        updated_before=updated_before,
    )
    return await execute_search(q, provider, filters, limit)


@app.post("/api/answer", response_model=AnswerResponse)
async def answer(request: AnswerRequest):
    search_response = await execute_search(
        request.query, request.provider, request.filters or SearchFilters(), 5
    )
    try:
        return await generate_answer(request, search_response, get_settings())
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Answer generation failed") from exc


@app.get("/api/evaluations")
def evaluations():
    return {
        "dataset": json.loads(
            (Path(__file__).resolve().parents[3] / "evals" / "dataset.json").read_text()
        ),
        "runs": read_evaluations(),
    }


@app.post("/api/evaluations/run")
async def evaluation_run(provider: ProviderName):
    adapter = get_provider(provider)
    try:
        return await run_evaluation(provider, adapter)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"{provider} evaluation failed") from exc
    finally:
        await adapter.client.aclose()


@app.get("/api/evaluations/{query_id}")
def evaluation_query(query_id: str):
    dataset = json.loads(
        (Path(__file__).resolve().parents[3] / "evals" / "dataset.json").read_text()
    )
    case = next((case for case in dataset if case["id"] == query_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Evaluation query not found")
    runs = read_evaluations()
    return {
        "case": case,
        "runs": {
            name: next((row for row in run["queries"] if row["id"] == query_id), None)
            if run
            else None
            for name, run in runs.items()
        },
    }


@app.get("/api/documents/{document_id}", response_model=KnowledgeDocument)
def get_document(document_id: str):
    path = Path(__file__).resolve().parents[3] / "data" / "normalized" / "documents.json"
    records = json.loads(path.read_text())
    record = next((item for item in records if item["id"] == document_id), None)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    return KnowledgeDocument.model_validate(record)
