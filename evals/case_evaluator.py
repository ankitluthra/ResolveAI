import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from apps.api.app.models.domain import ProviderName, SearchFilters
from apps.api.app.providers.base import SearchProvider
from apps.api.app.services.cases import CASES, load_cases

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "evals" / "case_dataset.json"
CORPUS = ROOT / "data" / "normalized" / "documents.json"
RESULTS = ROOT / "evals" / "results"


def evidence_recall(expected: list[str], returned: list[str]) -> float:
    return len(set(expected) & set(returned)) / len(set(expected))


def path_coverage(edges: list, returned: list[str]) -> float:
    found = set(returned)
    return sum(
        {edge.from_id, edge.to_id, edge.evidence_document_id}.issubset(found)
        for edge in edges
    ) / len(edges)


async def run_case_evaluation(
    provider_name: ProviderName, provider: SearchProvider
) -> dict:
    dataset_bytes = DATASET.read_bytes()
    dataset = json.loads(dataset_bytes)
    cases = {case.id: case for case in load_cases()}
    rows = []
    for item in dataset:
        case = cases[item["case_id"]]
        expected = item["expected_document_ids"]
        if not set(expected).issubset(case.document_ids):
            raise ValueError(f"Invalid expected documents in {item['id']}")
        entry = await provider.search(item["query"], limit=10)
        related = await provider.search("", SearchFilters(case_id=case.id), limit=50)
        entry_ids = [result.id for result in entry.results]
        related_ids = [result.id for result in related.results]
        rows.append(
            {
                **item,
                "entry_result_ids": entry_ids,
                "related_result_ids": related_ids,
                "entry_latency_ms": entry.latency_ms,
                "related_latency_ms": related.latency_ms,
                "entry_evidence_recall": evidence_recall(expected, entry_ids),
                "related_evidence_recall": evidence_recall(expected, related_ids),
                "path_coverage": path_coverage(case.edges, related_ids),
            }
        )
    count = len(rows)
    result = {
        "provider": provider_name,
        "timestamp": datetime.now(UTC).isoformat(),
        "query_count": count,
        "dataset_sha256": sha256(dataset_bytes).hexdigest(),
        "case_definitions_sha256": sha256(CASES.read_bytes()).hexdigest(),
        "corpus_sha256": sha256(CORPUS.read_bytes()).hexdigest(),
        "summary": {
            metric: round(sum(row[metric] for row in rows) / count, 4)
            for metric in (
                "entry_evidence_recall",
                "related_evidence_recall",
                "path_coverage",
            )
        },
        "queries": rows,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{provider_name}-cases.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    return result
