"""Plan or apply document updates and deletes using a local sync manifest."""

import argparse
import asyncio
import json
from hashlib import sha256
from pathlib import Path

from apps.api.app.core.config import get_settings
from apps.api.app.models.domain import KnowledgeDocument
from apps.api.app.providers.azure_search import AzureSearchProvider
from apps.api.app.providers.coveo import CoveoSearchProvider

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"


def corpus() -> list[KnowledgeDocument]:
    return [
        KnowledgeDocument.model_validate(item)
        for item in json.loads((ROOT / "data/normalized/documents.json").read_text())
    ]


def fingerprint(document: KnowledgeDocument) -> str:
    payload = json.dumps(document.model_dump(mode="json"), sort_keys=True).encode()
    return sha256(payload).hexdigest()


def plan_sync(
    documents: list[KnowledgeDocument], previous: dict[str, str]
) -> tuple[list[KnowledgeDocument], list[str], dict[str, str]]:
    current = {document.id: fingerprint(document) for document in documents}
    if len(current) != len(documents):
        raise ValueError("Duplicate document IDs in normalized corpus")
    changed = [document for document in documents if previous.get(document.id) != current[document.id]]
    removed = sorted(previous.keys() - current.keys())
    return changed, removed, current


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, choices=("azure", "coveo"))
    parser.add_argument("--apply", action="store_true", help="Send planned changes to the provider")
    args = parser.parse_args()
    path = LOCAL / f"{args.provider}-sync-state.json"
    previous = json.loads(path.read_text()) if path.exists() else {}
    changed, removed, current = plan_sync(corpus(), previous)
    print(f"{args.provider}: {len(changed)} to add/update, {len(removed)} to delete")
    if removed:
        print(f"Delete IDs: {', '.join(removed)}")
    if not args.apply:
        print("Dry run only. Pass --apply to send changes.")
        return

    settings = get_settings()
    provider = (
        AzureSearchProvider(settings)
        if args.provider == "azure"
        else CoveoSearchProvider(settings)
    )
    next_state = previous.copy()
    try:
        if changed:
            accepted, failed = await provider.upload(changed)
            failed_ids = set(provider.failed_ids)
            for document in changed:
                if document.id not in failed_ids:
                    next_state[document.id] = current[document.id]
            print(f"Add/update accepted: {accepted}; failed: {failed}")
            if failed_ids:
                print(f"Failed IDs: {', '.join(sorted(failed_ids))}")
        if removed:
            accepted, failed = await provider.delete(removed)
            failed_ids = set(provider.failed_ids)
            for document_id in removed:
                if document_id not in failed_ids:
                    next_state.pop(document_id, None)
            print(f"Delete accepted: {accepted}; failed: {failed}")
            if failed_ids:
                print(f"Failed IDs: {', '.join(sorted(failed_ids))}")
    finally:
        await provider.client.aclose()

    LOCAL.mkdir(exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(next_state, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)
    print(f"Local state saved to {path.relative_to(ROOT)}")
    print("Wait for indexing and verify search before evaluating.")


if __name__ == "__main__":
    asyncio.run(main())
