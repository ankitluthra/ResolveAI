import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

from apps.api.app.models.domain import KnowledgeDocument, ProviderName
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[4]
CASES = ROOT / "data" / "synthetic" / "cases.json"
DOCUMENTS = ROOT / "data" / "normalized" / "documents.json"


class EvidenceEdge(BaseModel):
    from_id: str
    to_id: str
    relation: Literal["investigated_as", "fixed_by", "guided_by", "summarized_by"]
    label: str
    evidence_document_id: str
    evidence_excerpt: str


class CaseSignal(BaseModel):
    kind: Literal["version_mismatch", "content_gap", "missing_evidence"]
    label: str
    detail: str
    source_ids: list[str]


class CaseDefinition(BaseModel):
    id: str
    customer: str
    title: str
    product: str
    affected_version: str | None = None
    status: str
    summary: str
    search_query: str
    finding: str
    finding_source_ids: list[str]
    next_step: str
    next_step_source_ids: list[str]
    document_ids: list[str]
    edges: list[EvidenceEdge]
    signals: list[CaseSignal] = Field(default_factory=list)


class CaseSummary(BaseModel):
    id: str
    customer: str
    title: str
    product: str
    status: str
    summary: str
    document_count: int


class CaseRetrieval(BaseModel):
    provider: ProviderName
    search_query: str
    entry_result_ids: list[str]
    indexed_document_ids: list[str]
    total_indexed_results: int
    entry_latency_ms: float
    related_latency_ms: float


class CaseDetail(CaseDefinition):
    documents: list[KnowledgeDocument]
    retrieval: CaseRetrieval | None = None


@lru_cache(maxsize=1)
def load_cases() -> tuple[CaseDefinition, ...]:
    cases = tuple(CaseDefinition.model_validate(item) for item in json.loads(CASES.read_text()))
    documents = {
        item["id"]: KnowledgeDocument.model_validate(item)
        for item in json.loads(DOCUMENTS.read_text())
    }
    if len({case.id for case in cases}) != len(cases):
        raise ValueError("Duplicate case IDs")
    for case in cases:
        ids = case.document_ids
        if len(ids) != len(set(ids)) or not ids or not set(ids).issubset(documents):
            raise ValueError(f"Invalid document IDs in {case.id}")
        if any(documents[document_id].case_id != case.id for document_id in ids):
            raise ValueError(f"Case ID mismatch in {case.id}")
        for edge in case.edges:
            if not {edge.from_id, edge.to_id, edge.evidence_document_id}.issubset(ids):
                raise ValueError(f"Invalid edge in {case.id}")
            if edge.evidence_excerpt not in documents[edge.evidence_document_id].content:
                raise ValueError(f"Unverified edge excerpt in {case.id}")
        cited = [*case.finding_source_ids, *case.next_step_source_ids]
        cited.extend(source_id for signal in case.signals for source_id in signal.source_ids)
        if not set(cited).issubset(ids):
            raise ValueError(f"Invalid source citation in {case.id}")
    return cases


def case_summaries() -> list[CaseSummary]:
    return [
        CaseSummary(**case.model_dump(), document_count=len(case.document_ids))
        for case in load_cases()
    ]


def case_detail(case_id: str) -> CaseDetail | None:
    case = next((item for item in load_cases() if item.id == case_id), None)
    if case is None:
        return None
    documents = {
        item["id"]: KnowledgeDocument.model_validate(item)
        for item in json.loads(DOCUMENTS.read_text())
    }
    return CaseDetail(
        **case.model_dump(), documents=[documents[item] for item in case.document_ids]
    )
