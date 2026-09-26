"""Live answer and abstention checks; factual correctness still needs human review."""

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from apps.api.app.core.config import Settings
from apps.api.app.models.domain import AnswerRequest, AnswerResponse, ProviderName
from apps.api.app.providers.base import SearchProvider
from apps.api.app.services.answers import generate_answer

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "evals" / "answer_dataset.json"
CORPUS = ROOT / "data" / "normalized" / "documents.json"
RESULTS = ROOT / "evals" / "results"


def score_answer(case: dict, answer: AnswerResponse) -> dict[str, bool | None]:
    abstention_correct = answer.insufficient_evidence == case["expected_abstain"]
    citation_hit = None
    if not case["expected_abstain"]:
        citation_hit = bool(
            {source.id for source in answer.sources} & set(case["expected_document_ids"])
        )
    return {"abstention_correct": abstention_correct, "expected_citation_hit": citation_hit}


async def run_answer_evaluation(
    provider_name: ProviderName, provider: SearchProvider, settings: Settings
) -> dict:
    if not settings.openai_api_key:
        raise ValueError("OpenAI is not configured")
    dataset_bytes = DATASET.read_bytes()
    cases = json.loads(dataset_bytes)
    rows = []
    for case in cases:
        search = await provider.search(case["query"], limit=5)
        answer = await generate_answer(
            AnswerRequest(query=case["query"], provider=provider_name), search, settings
        )
        rows.append(
            {
                **case,
                "answer": answer.answer,
                "cited_document_ids": [source.id for source in answer.sources],
                "insufficient_evidence": answer.insufficient_evidence,
                "search_latency_ms": answer.search_latency_ms,
                "generation_latency_ms": answer.generation_latency_ms,
                "checks": score_answer(case, answer),
                "factual_review": "pending",
            }
        )
    supported = [row for row in rows if not row["expected_abstain"]]
    result = {
        "provider": provider_name,
        "timestamp": datetime.now(UTC).isoformat(),
        "dataset_sha256": sha256(dataset_bytes).hexdigest(),
        "corpus_sha256": sha256(CORPUS.read_bytes()).hexdigest(),
        "query_count": len(rows),
        "summary": {
            "abstention_accuracy": sum(row["checks"]["abstention_correct"] for row in rows)
            / len(rows),
            "expected_citation_hit": sum(
                row["checks"]["expected_citation_hit"] for row in supported
            )
            / len(supported),
            "factual_review": "pending",
        },
        "queries": rows,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{provider_name}-answers.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
