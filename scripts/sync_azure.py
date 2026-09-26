import asyncio
import json
from pathlib import Path
from time import perf_counter

from apps.api.app.core.config import get_settings
from apps.api.app.models.domain import KnowledgeDocument
from apps.api.app.providers.azure_search import AzureSearchProvider

ROOT = Path(__file__).resolve().parents[1]


async def main():
    documents = [
        KnowledgeDocument.model_validate(item)
        for item in json.loads((ROOT / "data/normalized/documents.json").read_text())
    ]
    provider = AzureSearchProvider(get_settings())
    start = perf_counter()
    try:
        await provider.create_index()
        indexed, failed = await provider.upload(documents)
    finally:
        await provider.client.aclose()
    print(
        f"ResolveAI Sync — Azure AI Search\nDocuments read: {len(documents)}\nIndexed: {indexed}\nFailed: {failed}\nDuration: {perf_counter() - start:.1f}s"
    )
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
