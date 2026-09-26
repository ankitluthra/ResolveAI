"use client";
import { FormEvent, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ArrowRight,
  ChevronDown,
  Clock3,
  FileText,
  Filter,
  Search,
  Sparkles,
  ExternalLink,
  AlertCircle,
} from "lucide-react";
import { answer, search } from "@/lib/api";
import type {
  AnswerResponse,
  Provider,
  SearchResult,
  SourceType,
  Visibility,
} from "@/types/api";
const sources: { id: SourceType; label: string }[] = [
  { id: "documentation", label: "Documentation" },
  { id: "github_issue", label: "GitHub issues" },
  { id: "support_ticket", label: "Support tickets" },
  { id: "faq", label: "FAQs" },
  { id: "release_note", label: "Release notes" },
];
const products = [
  "Authentication",
  "API",
  "Billing",
  "Webhooks",
  "SDK",
  "SSO",
  "Integrations",
];
const visibility: Visibility[] = ["public", "support", "engineering"];
const examples = [
  "Why does OAuth fail after rotating the client secret?",
  "How do I configure SSO with Okta?",
  "Why are webhook signatures failing?",
];
const labelSource = (value: SourceType) =>
  sources.find((x) => x.id === value)?.label || value;
function ResultCard({ item, index }: { item: SearchResult; index: number }) {
  return (
    <article className="result-card">
      <div className="result-index">{String(index + 1).padStart(2, "0")}</div>
      <div className="result-content">
        <div className="result-meta">
          <span className={`source-badge source-${item.source_type}`}>
            {labelSource(item.source_type)}
          </span>
          <span>{item.product || "General"}</span>
          <span>·</span>
          <span>{item.visibility}</span>
        </div>
        <h3>
          {
            <a href={`/documents/${item.id}`}>
              {item.title}
              <ExternalLink size={14} />
            </a>
          }
        </h3>
        <p>{item.content_preview || "No preview available for this result."}</p>
        <div className="result-bottom">
          <div className="tags">
            {item.tags.slice(0, 3).map((tag) => (
              <span key={tag}>{tag}</span>
            ))}
          </div>
          <span>
            {item.updated_at
              ? `Updated ${new Date(item.updated_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`
              : ""}
          </span>
        </div>
      </div>
    </article>
  );
}
function CategoryFilter({
  value,
  onApply,
}: {
  value: string;
  onApply: (value: string) => void;
}) {
  const [draft, setDraft] = useState(value);
  return (
    <form
      className="category-filter"
      onSubmit={(event) => {
        event.preventDefault();
        if (draft.trim() !== value) onApply(draft.trim());
      }}
    >
      <input
        className="filter-text"
        aria-label="Category"
        placeholder="e.g. OAuth"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
      />
      <button type="submit">Apply</button>
    </form>
  );
}
export default function SearchPage() {
  const router = useRouter();
  const params = useSearchParams();
  const [draft, setDraft] = useState(params.get("q") || "");
  const [answerData, setAnswerData] = useState<AnswerResponse | null>(null);
  const [answerLoading, setAnswerLoading] = useState(false);
  const [answerError, setAnswerError] = useState("");
  const query = params.get("q") || "";
  const provider: Provider =
    params.get("provider") === "coveo" ? "coveo" : "azure";
  const source = params.get("source_type") || "";
  const product = params.get("product") || "";
  const role = params.get("visibility") || "";
  const category = params.get("category") || "";
  const updatedAfter = params.get("updated_after") || "";
  const updatedBefore = params.get("updated_before") || "";
  const request = useMemo(() => {
    const next = new URLSearchParams({ q: query, provider });
    if (source) next.set("source_type", source);
    if (product) next.set("product", product);
    if (role) next.set("visibility", role);
    if (category) next.set("category", category);
    if (updatedAfter)
      next.set("updated_after", new Date(updatedAfter).toISOString());
    if (updatedBefore)
      next.set("updated_before", new Date(updatedBefore).toISOString());
    return next;
  }, [
    query,
    provider,
    source,
    product,
    role,
    category,
    updatedAfter,
    updatedBefore,
  ]);
  const searchState = useQuery({
    queryKey: ["search", request.toString()],
    queryFn: () => search(request),
    enabled: query.length >= 2,
  });
  function update(key: string, value: string) {
    const next = new URLSearchParams(params.toString());
    if (value) next.set(key, value);
    else next.delete(key);
    router.push(`/?${next}`);
    setAnswerData(null);
  }
  function submit(event: FormEvent) {
    event.preventDefault();
    update("q", draft.trim());
  }
  async function askAnswer() {
    setAnswerError("");
    setAnswerLoading(true);
    try {
      setAnswerData(
        await answer(query, provider, {
          ...(source ? { source_type: source } : {}),
          ...(product ? { product } : {}),
          ...(category ? { category } : {}),
          ...(role ? { visibility: role } : {}),
          ...(updatedAfter
            ? { updated_after: new Date(updatedAfter).toISOString() }
            : {}),
          ...(updatedBefore
            ? { updated_before: new Date(updatedBefore).toISOString() }
            : {}),
        }),
      );
    } catch (error) {
      setAnswerError(error instanceof Error ? error.message : "Answer failed");
    } finally {
      setAnswerLoading(false);
    }
  }
  return (
    <div className="workspace">
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            SUPPORT WORKSPACE <span className="eyebrow-line" /> 01 / SEARCH
          </div>
          <h1>Find the answer in the evidence.</h1>
          <p>
            Search AcmeCloud knowledge across documentation, engineering issues,
            tickets, FAQs and releases.
          </p>
        </div>
        <div className="heading-note">
          <span className="pulse-dot" /> RETRIEVAL COMPARISON
          <br />
          <strong>One question. Two search platforms.</strong>
        </div>
      </div>
      <form className="search-form" onSubmit={submit}>
        <Search size={21} />
        <input
          aria-label="Ask a support question"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask a support question…"
        />
        <button type="submit">
          Search <ArrowRight size={17} />
        </button>
      </form>
      <div className="provider-strip">
        <span className="strip-label">SEARCH PROVIDER</span>
        <div className="segmented" role="group" aria-label="Search provider">
          <button
            className={provider === "azure" ? "selected" : ""}
            onClick={() => update("provider", "azure")}
          >
            Azure AI Search
          </button>
          <button
            className={provider === "coveo" ? "selected" : ""}
            onClick={() => update("provider", "coveo")}
          >
            Coveo
          </button>
        </div>
        <span className="strip-info">Switching reruns the same question</span>
      </div>
      {!query ? (
        <div className="welcome-grid">
          <section className="welcome-panel">
            <div className="panel-kicker">START WITH A QUESTION</div>
            <h2>Search across the places support actually works.</h2>
            <p>
              Find the product guidance, related case history and release
              context behind a customer issue.
            </p>
            <div className="example-list">
              {examples.map((example, i) => (
                <button
                  key={example}
                  onClick={() => {
                    setDraft(example);
                    update("q", example);
                  }}
                >
                  <span>0{i + 1}</span>
                  {example}
                  <ArrowRight size={16} />
                </button>
              ))}
            </div>
          </section>
          <aside className="signal-panel">
            <span className="panel-kicker">KNOWLEDGE SIGNAL</span>
            <div className="signal-number">
              05<span> sources</span>
            </div>
            <p>
              A shared document schema gives both retrieval platforms the same
              content and metadata.
            </p>
            <div className="source-stack">
              {sources.map((x) => (
                <span key={x.id}>{x.label}</span>
              ))}
            </div>
          </aside>
        </div>
      ) : (
        <div className="results-layout">
          <aside className="filters">
            <div className="filter-header">
              <Filter size={16} /> Filters{" "}
              <button
                onClick={() => {
                  const next = new URLSearchParams(params.toString());
                  [
                    "source_type",
                    "product",
                    "visibility",
                    "category",
                    "updated_after",
                    "updated_before",
                  ].forEach((x) => next.delete(x));
                  router.push(`/?${next}`);
                }}
              >
                Clear
              </button>
            </div>
            <div className="filter-group">
              <h3>Source</h3>
              {sources.map((x) => (
                <label key={x.id}>
                  <input
                    type="checkbox"
                    checked={source === x.id}
                    onChange={() =>
                      update("source_type", source === x.id ? "" : x.id)
                    }
                  />
                  {x.label}
                </label>
              ))}
            </div>
            <div className="filter-group">
              <h3>Product</h3>
              {products.map((x) => (
                <label key={x}>
                  <input
                    type="checkbox"
                    checked={product === x}
                    onChange={() => update("product", product === x ? "" : x)}
                  />
                  {x}
                </label>
              ))}
            </div>
            <div className="filter-group">
              <h3>Visibility</h3>
              {visibility.map((x) => (
                <label key={x}>
                  <input
                    type="checkbox"
                    checked={role === x}
                    onChange={() => update("visibility", role === x ? "" : x)}
                  />
                  {x[0].toUpperCase() + x.slice(1)}
                </label>
              ))}
            </div>
            <div className="filter-group">
              <h3>Category</h3>
              <CategoryFilter
                key={category}
                value={category}
                onApply={(value) => update("category", value)}
              />
            </div>
            <div className="filter-group">
              <h3>Updated from</h3>
              <input
                className="filter-date"
                aria-label="Updated from"
                type="date"
                value={updatedAfter}
                onChange={(e) => update("updated_after", e.target.value)}
              />
              <h3>Updated before</h3>
              <input
                className="filter-date"
                aria-label="Updated before"
                type="date"
                value={updatedBefore}
                onChange={(e) => update("updated_before", e.target.value)}
              />
            </div>
          </aside>
          <div className="results-main">
            <div className="results-toolbar">
              <div>
                <span className="panel-kicker">SEARCH RESULTS</span>
                <h2>
                  {searchState.isLoading
                    ? "Searching…"
                    : searchState.data
                      ? `${searchState.data.total_results} results for “${query}”`
                      : `Results for “${query}”`}
                </h2>
              </div>
              <div className="latency">
                <Clock3 size={15} />
                {searchState.data ? `${searchState.data.latency_ms} ms` : "—"}
              </div>
            </div>
            {searchState.isError ? (
              <div className="state-message error">
                <AlertCircle size={22} />
                <strong>Search unavailable</strong>
                <p>{searchState.error.message}</p>
                <span>
                  Check the provider configuration in the API environment.
                </span>
              </div>
            ) : null}
            {searchState.isLoading ? (
              <div className="loading-list" aria-live="polite">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="loading-card" />
                ))}
              </div>
            ) : null}
            {searchState.data ? (
              <>
                <div className="answer-banner">
                  <div>
                    <span className="answer-icon">
                      <Sparkles size={18} />
                    </span>
                    <div>
                      <strong>Grounded AI answer</strong>
                      <p>Generate a response from the retrieved sources.</p>
                    </div>
                  </div>
                  <button onClick={askAnswer} disabled={answerLoading}>
                    {answerLoading ? "Generating…" : "Generate answer"}{" "}
                    <ArrowRight size={15} />
                  </button>
                </div>
                {answerError ? (
                  <div className="inline-error">{answerError}</div>
                ) : null}
                {answerData ? (
                  <section className="answer-panel">
                    <span className="panel-kicker">
                      AI ANSWER ·{" "}
                      {answerData.insufficient_evidence
                        ? "INSUFFICIENT EVIDENCE"
                        : "GROUNDED IN SOURCES"}
                    </span>
                    <p>{answerData.answer}</p>
                    {answerData.sources.length > 0 ? (
                      <div className="answer-sources">
                        <strong>Sources</strong>
                        {answerData.sources.map((s) => (
                          <a key={s.id} href={`/documents/${s.id}`}>
                            {s.title} <ExternalLink size={13} />
                          </a>
                        ))}
                      </div>
                    ) : null}
                  </section>
                ) : null}
                <div className="list-heading">
                  <FileText size={16} /> Retrieved documents{" "}
                  <span>{searchState.data.results.length} shown</span>
                </div>
                {searchState.data.results.length ? (
                  searchState.data.results.map((item, i) => (
                    <ResultCard key={item.id} item={item} index={i} />
                  ))
                ) : (
                  <div className="state-message">
                    <strong>No matching documents</strong>
                    <p>Try a broader question or clear the filters.</p>
                  </div>
                )}
                <details className="inspect">
                  <summary>
                    Inspect retrieval <ChevronDown size={16} />
                  </summary>
                  <dl>
                    <div>
                      <dt>Query</dt>
                      <dd>{query}</dd>
                    </div>
                    <div>
                      <dt>Provider</dt>
                      <dd>
                        {provider === "azure" ? "Azure AI Search" : "Coveo"}
                      </dd>
                    </div>
                    <div>
                      <dt>Latency</dt>
                      <dd>{searchState.data.latency_ms} ms</dd>
                    </div>
                    <div>
                      <dt>Results</dt>
                      <dd>{searchState.data.total_results}</dd>
                    </div>
                    <div>
                      <dt>Documents used for answer</dt>
                      <dd>{answerData?.sources.length || 0}</dd>
                    </div>
                  </dl>
                  <div className="inspect-top">
                    Top sources
                    {searchState.data.results.slice(0, 5).map((r, i) => (
                      <div key={r.id}>
                        <span>{i + 1}</span>
                        {r.title}
                        <code>{r.id}</code>
                      </div>
                    ))}
                  </div>
                </details>
              </>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
