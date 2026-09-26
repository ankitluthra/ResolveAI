from datetime import datetime, timezone
from typing import Any

from apps.api.app.models.domain import KnowledgeDocument


def normalize(raw: dict[str, Any], source_type: str) -> KnowledgeDocument:
    """Validate source records and give every connector the same output contract."""
    record = {**raw, "source_type": source_type}
    for field in ("created_at", "updated_at"):
        if isinstance(record.get(field), str):
            record[field] = datetime.fromisoformat(record[field].replace("Z", "+00:00"))
    if not record.get("updated_at"):
        record["updated_at"] = record.get("created_at") or datetime.now(timezone.utc)
    return KnowledgeDocument.model_validate(record)
