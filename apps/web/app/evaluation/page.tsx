"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Activity, ChevronDown } from "lucide-react";
import { evaluations } from "@/lib/api";
import type { EvalCase, EvalRun } from "@/types/api";
const names = { azure: "Azure AI Search", coveo: "Coveo" };
function Metric({
  label,
  azure,
  coveo,
  format,
}: {
  label: string;
  azure: number | undefined;
  coveo: number | undefined;
  format: (v: number) => string;
}) {
  return (
    <div className="metric-row">
      <span>{label}</span>
      <strong>{azure === undefined ? "—" : format(azure)}</strong>
      <strong>{coveo === undefined ? "—" : format(coveo)}</strong>
    </div>
  );
}
function QueryDetail({
  item,
  runs,
}: {
  item: EvalCase;
  runs: { azure: EvalRun | null; coveo: EvalRun | null };
}) {
  return (
    <div className="query-detail">
      <div>
        <span>EXPECTED RELEVANT DOCUMENTS</span>
        <p>{item.expected_document_ids.join(" · ")}</p>
      </div>
      <div className="query-comparison">
        {(["azure", "coveo"] as const).map((name) => {
          const row = runs[name]?.queries.find((r) => r.id === item.id);
          return (
            <section key={name}>
              <strong>{names[name]}</strong>
              {row ? (
                row.returned_document_ids.slice(0, 5).map((id, i) => (
                  <p
                    key={`${id}-${i}`}
                    className={
                      item.expected_document_ids.includes(id) ? "relevant" : ""
                    }
                  >
                    <span>{i + 1}.</span>
                    {id}
                    {item.expected_document_ids.includes(id) ? " ✓" : ""}
                  </p>
                ))
              ) : (
                <p>No run recorded</p>
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
}
export default function EvaluationPage() {
  const data = useQuery({ queryKey: ["evaluations"], queryFn: evaluations });
  const [open, setOpen] = useState<string | null>(null);
  const runs = data.data?.runs;
  return (
    <div className="workspace">
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            SUPPORT WORKSPACE <span className="eyebrow-line" /> 02 / EVALUATION
          </div>
          <h1>Measure what retrieval finds.</h1>
          <p>
            Twenty customer questions with expected documents, fixed before
            provider tuning.
          </p>
        </div>
        <div className="heading-note">
          <Activity size={18} /> RELEVANCE / LATENCY
          <br />
          <strong>Results from recorded runs only.</strong>
        </div>
      </div>
      <section className="eval-summary">
        <div className="summary-title">
          <div>
            <span className="panel-kicker">PROVIDER COMPARISON</span>
            <h2>Evaluation results</h2>
          </div>
          <span>Run with the API after indexing</span>
        </div>
        <div className="metric-table">
          <div className="metric-row metric-head">
            <span>METRIC</span>
            <span>AZURE AI SEARCH</span>
            <span>COVEO</span>
          </div>
          <Metric
            label="Queries"
            azure={runs?.azure?.query_count}
            coveo={runs?.coveo?.query_count}
            format={String}
          />
          <Metric
            label="Hit@1"
            azure={runs?.azure?.summary.hit_at_1}
            coveo={runs?.coveo?.summary.hit_at_1}
            format={(v) => `${Math.round(v * 100)}%`}
          />
          <Metric
            label="Hit@3"
            azure={runs?.azure?.summary.hit_at_3}
            coveo={runs?.coveo?.summary.hit_at_3}
            format={(v) => `${Math.round(v * 100)}%`}
          />
          <Metric
            label="MRR"
            azure={runs?.azure?.summary.mrr}
            coveo={runs?.coveo?.summary.mrr}
            format={(v) => v.toFixed(2)}
          />
          <Metric
            label="Avg latency"
            azure={runs?.azure?.summary.average_latency_ms}
            coveo={runs?.coveo?.summary.average_latency_ms}
            format={(v) => `${v} ms`}
          />
        </div>
        {!runs?.azure && !runs?.coveo ? (
          <div className="eval-empty">
            No evaluation runs yet. Configure a provider, index the corpus, then
            run <code>POST /api/evaluations/run?provider=azure</code> or{" "}
            <code>provider=coveo</code>.
          </div>
        ) : null}
      </section>
      <section className="eval-queries">
        <div className="list-heading">
          QUERY SET <span>{data.data?.dataset.length || 0} questions</span>
        </div>
        {data.isLoading ? (
          <div className="state-message">Loading evaluation set…</div>
        ) : null}
        {data.isError ? (
          <div className="state-message error">{data.error.message}</div>
        ) : null}
        {data.data?.dataset.map((item, i) => (
          <div key={item.id} className="query-item">
            <button
              onClick={() => setOpen(open === item.id ? null : item.id)}
              aria-expanded={open === item.id}
            >
              <span className="query-no">{String(i + 1).padStart(2, "0")}</span>
              <span className="query-title">{item.query}</span>
              <span className="query-category">{item.category}</span>
              <ChevronDown size={16} />
            </button>
            {open === item.id ? (
              <QueryDetail item={item} runs={data.data.runs} />
            ) : null}
          </div>
        ))}
      </section>
      <div className="eval-footnote">
        Scores are calculated from live search results. Missing runs are
        deliberately shown as blank.
      </div>
    </div>
  );
}
