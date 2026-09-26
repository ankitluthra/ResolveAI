import json
from pathlib import Path

from apps.api.app.models.domain import KnowledgeDocument
from ingestion.normalizer import normalize

SOURCE_FILES = {
    "documentation": "documentation.json",
    "faq": "faq.json",
    "github_issue": "github_issues.json",
    "support_ticket": "support_tickets.json",
    "release_note": "release_notes.json",
}


def fetch_local(root: Path) -> list[KnowledgeDocument]:
    documents: list[KnowledgeDocument] = []
    for source_type, filename in SOURCE_FILES.items():
        for item in json.loads((root / filename).read_text()):
            documents.append(normalize(item, source_type))
    ids = [document.id for document in documents]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate document IDs in source data")
    return documents
