import asyncio
import json
from pathlib import Path
from time import perf_counter

from apps.api.app.core.config import get_settings
from apps.api.app.models.domain import KnowledgeDocument
from apps.api.app.providers.coveo import CoveoSearchProvider

ROOT = Path(__file__).resolve().parents[1]


async def main():
    documents = [
        KnowledgeDocument.model_validate(item)
        for item in json.loads((ROOT / "data/normalized/documents.json").read_text())
    ]
    provider = CoveoSearchProvider(get_settings())
    start = perf_counter()
    try:
        indexed, failed = await provider.upload(documents)
    finally:
        await provider.client.aclose()
    print(
        f"ResolveAI Sync — Coveo\nDocuments read: {len(documents)}\nAccepted for processing: {indexed}\nRequest failures: {failed}\nDuration: {perf_counter() - start:.1f}s"
    )
    if provider.failed_ids:
        print(f"Failed document IDs: {', '.join(provider.failed_ids)}")
    print("Check the Coveo source status and searchable item count before evaluation.")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
