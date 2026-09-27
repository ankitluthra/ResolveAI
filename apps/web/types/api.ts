export type Provider = "azure" | "coveo";
export type SourceType =
  "documentation" | "faq" | "github_issue" | "support_ticket" | "release_note";
export type Visibility = "public" | "support" | "engineering";
export interface SearchResult {
  id: string;
  title: string;
  content_preview: string;
  source_type: SourceType;
  case_id: string | null;
  product: string | null;
  category: string | null;
  url: string | null;
  score: number | null;
  tags: string[];
  visibility: Visibility;
  updated_at: string | null;
}
export interface CaseSummary {
  id: string;
  customer: string;
  title: string;
  product: string;
  status: string;
  summary: string;
  document_count: number;
}
export interface CaseDocument {
  id: string;
  title: string;
  content: string;
  source_type: SourceType;
  case_id: string | null;
  product: string | null;
  updated_at: string | null;
  visibility: Visibility;
}
export interface EvidenceEdge {
  from_id: string;
  to_id: string;
  relation: "investigated_as" | "fixed_by" | "guided_by" | "summarized_by";
  label: string;
  evidence_document_id: string;
  evidence_excerpt: string;
}
export interface CaseSignal {
  kind: "version_mismatch" | "content_gap" | "missing_evidence";
  label: string;
  detail: string;
  source_ids: string[];
}
export interface CaseRetrieval {
  provider: Provider;
  search_query: string;
  entry_result_ids: string[];
  indexed_document_ids: string[];
  total_indexed_results: number;
  entry_latency_ms: number;
  related_latency_ms: number;
}
export interface CaseDetail extends Omit<CaseSummary, "document_count"> {
  affected_version: string | null;
  search_query: string;
  finding: string;
  finding_source_ids: string[];
  next_step: string;
  next_step_source_ids: string[];
  document_ids: string[];
  edges: EvidenceEdge[];
  signals: CaseSignal[];
  documents: CaseDocument[];
  retrieval: CaseRetrieval | null;
}
export interface SearchResponse {
  query: string;
  provider: Provider;
  latency_ms: number;
  total_results: number;
  results: SearchResult[];
  timestamp: string;
}
export interface AnswerResponse {
  answer: string;
  provider: Provider;
  search_latency_ms: number;
  generation_latency_ms: number;
  sources: { id: string; title: string; url: string | null }[];
  insufficient_evidence: boolean;
}
export interface EvalCase {
  id: string;
  query: string;
  expected_document_ids: string[];
  category: string;
}
export interface EvalRow extends EvalCase {
  returned_document_ids: string[];
  latency_ms: number;
  metrics: { hit_at_1: number; hit_at_3: number; mrr: number };
}
export interface EvalRun {
  provider: Provider;
  timestamp: string;
  query_count: number;
  summary: {
    hit_at_1: number;
    hit_at_3: number;
    mrr: number;
    average_latency_ms: number;
  };
  queries: EvalRow[];
}
export interface Evaluations {
  dataset: EvalCase[];
  runs: { azure: EvalRun | null; coveo: EvalRun | null };
}
