export type Provider = "azure" | "coveo";
export type SourceType =
  "documentation" | "faq" | "github_issue" | "support_ticket" | "release_note";
export type Visibility = "public" | "support" | "engineering";
export interface SearchResult {
  id: string;
  title: string;
  content_preview: string;
  source_type: SourceType;
  product: string | null;
  category: string | null;
  url: string | null;
  score: number | null;
  tags: string[];
  visibility: Visibility;
  updated_at: string | null;
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
