"""Check local data and, optionally, the configured live search indexes."""

import argparse
import asyncio
import json
from pathlib import Path

import httpx

from apps.api.app.core.config import get_settings
from apps.api.app.models.domain import KnowledgeDocument, SearchFilters
from apps.api.app.providers.azure_search import AzureSearchProvider
from apps.api.app.providers.coveo import CoveoSearchProvider
from apps.api.app.services.cases import load_cases

ROOT = Path(__file__).resolve().parents[1]


def check_local_data() -> tuple[list[KnowledgeDocument], list[dict]]:
    documents = [
        KnowledgeDocument.model_validate(item)
        for item in json.loads((ROOT / "data/normalized/documents.json").read_text())
    ]
    cases = json.loads((ROOT / "evals/dataset.json").read_text())
    ids = {item.id for item in documents}
    if len(documents) < 150 or len(ids) != len(documents):
        raise ValueError("Corpus must contain at least 150 documents with unique IDs")
    if len(cases) < 20 or len({item["id"] for item in cases}) != len(cases):
        raise ValueError("Evaluation set must contain at least 20 unique questions")
    for case in cases:
        expected = set(case["expected_document_ids"])
        if not expected or not expected.issubset(ids):
            raise ValueError(f"Invalid expected document IDs in {case['id']}")
    linked_cases = load_cases()
    case_questions = json.loads((ROOT / "evals/case_dataset.json").read_text())
    linked_by_id = {item.id: item for item in linked_cases}
    for question in case_questions:
        linked = linked_by_id.get(question["case_id"])
        if not linked or not set(question["expected_document_ids"]).issubset(
            linked.document_ids
        ):
            raise ValueError(f"Invalid case question {question['id']}")
    print(
        f"Local data: {len(documents)} documents, {len(cases)} retrieval questions, "
        f"{len(linked_cases)} linked cases, {len(case_questions)} case questions — ready"
    )
    return documents, cases


async def check_provider(name: str, expected_count: int) -> None:
    settings = get_settings()
    provider = (
        AzureSearchProvider(settings)
        if name == "azure"
        else CoveoSearchProvider(settings)
    )
    try:
        all_query = "*" if name == "azure" else ""
        all_results = await provider.search(all_query, limit=1)
        if all_results.total_results != expected_count:
            raise ValueError(
                f"{name}: expected {expected_count} searchable items, found "
                f"{all_results.total_results}. Check indexing status and source configuration."
            )
        filtered = await provider.search(
            all_query, SearchFilters(source_type="documentation"), limit=5
        )
        if not filtered.results or any(
            result.source_type != "documentation" for result in filtered.results
        ):
            raise ValueError(f"{name}: source type filter did not return documentation")
        example = await provider.search("OAuth client secret rotation", limit=10)
        if not example.results:
            raise ValueError(f"{name}: representative OAuth query returned no results")
        linked = next(item for item in load_cases() if item.id == "case-oauth-rotation")
        related = await provider.search("", SearchFilters(case_id=linked.id), limit=50)
        if {item.id for item in related.results} != set(linked.document_ids):
            raise ValueError(
                f"{name}: case ID filter did not retrieve all linked evidence"
            )
        print(
            f"{name}: {all_results.total_results} searchable items; source/case filters and "
            "representative query — ready"
        )
    finally:
        await provider.client.aclose()


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true", help="Query configured live providers"
    )
    parser.add_argument(
        "--provider", choices=("azure", "coveo", "both"), default="both"
    )
    args = parser.parse_args()
    documents, _ = check_local_data()
    if not args.live:
        print("Live providers: skipped (pass --live after configuring .env)")
        return
    names = ("azure", "coveo") if args.provider == "both" else (args.provider,)
    for name in names:
        try:
            await check_provider(name, len(documents))
        except (ValueError, httpx.HTTPError) as exc:
            raise SystemExit(f"Readiness failed: {exc}") from exc


if __name__ == "__main__":
    asyncio.run(main())
