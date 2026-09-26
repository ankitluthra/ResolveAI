import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from apps.api.app.models.domain import ProviderName
from apps.api.app.providers.base import SearchProvider

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "evals" / "dataset.json"
CORPUS = ROOT / "data" / "normalized" / "documents.json"
RESULTS = ROOT / "evals" / "results"


def metric_for_query(expected: list[str], returned: list[str]) -> dict[str, float]:
    first = next(
        (rank for rank, item in enumerate(returned, 1) if item in expected), None
    )
    return {
        "hit_at_1": float(first == 1),
        "hit_at_3": float(first is not None and first <= 3),
        "mrr": 1 / first if first else 0.0,
    }


async def run_evaluation(
    provider_name: ProviderName, provider: SearchProvider, variant: str = "baseline"
) -> dict:
    dataset_bytes = DATASET.read_bytes()
    dataset = json.loads(dataset_bytes)
    rows = []
    for case in dataset:
        response = await provider.search(case["query"], limit=10)
        returned = [item.id for item in response.results]
        rows.append(
            {
                **case,
                "returned_document_ids": returned,
                "latency_ms": response.latency_ms,
                "metrics": metric_for_query(case["expected_document_ids"], returned),
            }
        )
    count = len(rows)
    summary = {
        metric: round(sum(row["metrics"][metric] for row in rows) / count, 4)
        for metric in ("hit_at_1", "hit_at_3", "mrr")
    }
    summary["average_latency_ms"] = round(
        sum(row["latency_ms"] for row in rows) / count, 1
    )
    result = {
        "provider": provider_name,
        "variant": variant,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query_count": count,
        "dataset_sha256": sha256(dataset_bytes).hexdigest(),
        "corpus_sha256": sha256(CORPUS.read_bytes()).hexdigest(),
        "summary": summary,
        "queries": rows,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    filename = f"{provider_name}.json" if variant == "baseline" else f"{provider_name}-{variant}.json"
    (RESULTS / filename).write_text(json.dumps(result, indent=2) + "\n")
    return result


def read_evaluations() -> dict:
    return {
        provider: json.loads(path.read_text()) if path.exists() else None
        for provider in ("azure", "coveo")
        for path in [RESULTS / f"{provider}.json"]
    }
