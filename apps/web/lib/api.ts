import type {
  AnswerResponse,
  Evaluations,
  Provider,
  SearchResponse,
} from "@/types/api";
const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed (${response.status})`);
  }
  return response.json();
}
export async function search(params: URLSearchParams): Promise<SearchResponse> {
  return apiGet(`/api/search?${params}`);
}
export async function evaluations(): Promise<Evaluations> {
  return apiGet("/api/evaluations");
}
export async function answer(
  query: string,
  provider: Provider,
  filters: Record<string, string>,
): Promise<AnswerResponse> {
  const response = await fetch(`${BASE}/api/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, provider, filters }),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed (${response.status})`);
  }
  return response.json();
}
