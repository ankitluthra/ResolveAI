"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Clock3,
  ExternalLink,
  GitBranch,
  Search,
} from "lucide-react";
import { caseDetail } from "@/lib/api";
import type { CaseDocument, Provider } from "@/types/api";

const sourceLabel: Record<string, string> = {
  support_ticket: "Support ticket",
  github_issue: "Engineering issue",
  release_note: "Release note",
  documentation: "Documentation",
  faq: "FAQ",
};

function SourceLinks({ ids }: { ids: string[] }) {
  return (
    <span className="case-citations">
      {ids.map((id) => (
        <Link key={id} href={`/documents/${id}`}>
          {id} <ExternalLink size={12} aria-hidden="true" />
        </Link>
      ))}
    </span>
  );
}

function EvidenceNode({
  document,
  indexed,
  rank,
  checking,
}: {
  document: CaseDocument;
  indexed: boolean;
  rank: number;
  checking: boolean;
}) {
  return (
    <article className="evidence-node">
      <div className="evidence-node-header">
        <span className={`source-badge source-${document.source_type}`}>
          {sourceLabel[document.source_type]}
        </span>
        <span className="evidence-date">
          <Clock3 size={13} aria-hidden="true" />
          {document.updated_at
            ? new Date(document.updated_at).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              })
            : "Date unavailable"}
        </span>
      </div>
      <h3>
        <Link href={`/documents/${document.id}`}>
          {document.title} <ExternalLink size={14} aria-hidden="true" />
        </Link>
      </h3>
      <p>{document.content}</p>
      <div className="evidence-node-footer">
        <code>{document.id}</code>
        {checking ? (
          <span className={indexed ? "indexed-ok" : "indexed-missing"}>
            {indexed ? "In provider results" : "Missing from provider results"}
            {rank > 0 ? ` · entry rank ${rank}` : ""}
          </span>
        ) : (
          <span>Curated source record</span>
        )}
      </div>
    </article>
  );
}

export default function CasePage() {
  const { id } = useParams<{ id: string }>();
  const [provider, setProvider] = useState<Provider | null>(null);
  const record = useQuery({
    queryKey: ["case", id],
    queryFn: () => caseDetail(id),
  });
  const live = useQuery({
    queryKey: ["case", id, provider],
    queryFn: () => caseDetail(id, provider ?? undefined),
    enabled: provider !== null && Boolean(record.data),
    retry: false,
  });
  const item = record.data;
  const retrieval = provider ? live.data?.retrieval : null;
  const indexed = new Set(
    item?.document_ids.filter((documentId) =>
      retrieval?.indexed_document_ids.includes(documentId),
    ) ?? [],
  );

  return (
    <div className="workspace case-page">
      <Link href="/cases" className="back-link">
        <ArrowLeft size={15} /> All cases
      </Link>
      {record.isLoading ? (
        <div className="state-message">Loading case…</div>
      ) : null}
      {record.isError ? (
        <div className="state-message error">{record.error.message}</div>
      ) : null}
      {item ? (
        <>
          <div className="case-hero">
            <div>
              <div className="eyebrow">
                CASE EVIDENCE TRAIL / {item.customer}
              </div>
              <h1>{item.title}</h1>
              <p>{item.summary}</p>
              <div className="case-hero-tags">
                <span>{item.product}</span>
                {item.affected_version ? (
                  <span>{item.affected_version}</span>
                ) : null}
                <span>{item.status}</span>
              </div>
            </div>
            <div className="case-hero-count">
              <strong>{item.documents.length}</strong>
              <span>source records</span>
            </div>
          </div>

          <div className="case-body">
            <div className="case-main">
              <section className="case-section">
                <div className="case-section-heading">
                  <GitBranch size={18} aria-hidden="true" />
                  <div>
                    <span className="panel-kicker">CONNECTED EVIDENCE</span>
                    <h2>How the records connect</h2>
                  </div>
                </div>
                <p className="case-section-description">
                  Every connection is backed by an excerpt from a source record.
                  Open any record to inspect its full text.
                </p>
                <div className="evidence-chain">
                  {item.documents.map((document, index) => {
                    const edge = item.edges.find(
                      (candidate) =>
                        candidate.from_id === document.id &&
                        candidate.to_id === item.documents[index + 1]?.id,
                    );
                    return (
                      <div key={document.id}>
                        <EvidenceNode
                          document={document}
                          indexed={indexed.has(document.id)}
                          rank={
                            (retrieval?.entry_result_ids.indexOf(document.id) ??
                              -1) + 1
                          }
                          checking={Boolean(retrieval)}
                        />
                        {edge ? (
                          <div className="evidence-link">
                            <div className="evidence-link-line" />
                            <div>
                              <strong>{edge.label}</strong>
                              <p>“{edge.evidence_excerpt}”</p>
                              <Link
                                href={`/documents/${edge.evidence_document_id}`}
                              >
                                Evidence: {edge.evidence_document_id}{" "}
                                <ArrowRight size={12} aria-hidden="true" />
                              </Link>
                            </div>
                          </div>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              </section>
            </div>

            <aside className="case-rail">
              <section className="case-insight">
                <span className="panel-kicker">CURRENT FINDING</span>
                <h2>{item.finding}</h2>
                <SourceLinks ids={item.finding_source_ids} />
                <div className="case-next-step">
                  <strong>Suggested next step</strong>
                  <p>{item.next_step}</p>
                  <SourceLinks ids={item.next_step_source_ids} />
                </div>
              </section>
              <section className="case-signals">
                <span className="panel-kicker">EVIDENCE SIGNALS</span>
                {item.signals.map((signal) => (
                  <div className="case-signal" key={signal.kind}>
                    <AlertCircle size={17} aria-hidden="true" />
                    <div>
                      <strong>{signal.label}</strong>
                      <p>{signal.detail}</p>
                      <SourceLinks ids={signal.source_ids} />
                    </div>
                  </div>
                ))}
              </section>
              <section className="case-verification">
                <span className="panel-kicker">SEARCH PROVIDER CHECK</span>
                <h2>Verify indexed evidence</h2>
                <p>
                  Run the case query and retrieve records indexed under this
                  case ID. The evidence path above is curated from the source
                  corpus.
                </p>
                <div
                  className="case-provider-buttons"
                  role="group"
                  aria-label="Evidence provider"
                >
                  <button
                    className={provider === null ? "selected" : ""}
                    onClick={() => setProvider(null)}
                  >
                    Local
                  </button>
                  <button
                    className={provider === "coveo" ? "selected" : ""}
                    onClick={() => setProvider("coveo")}
                  >
                    Coveo
                  </button>
                  <button
                    className={provider === "azure" ? "selected" : ""}
                    onClick={() => setProvider("azure")}
                  >
                    Azure
                  </button>
                </div>
                {live.isLoading && provider ? (
                  <p role="status">Checking {provider}…</p>
                ) : null}
                {live.isError && provider ? (
                  <div className="case-provider-error" role="alert">
                    <AlertCircle size={16} aria-hidden="true" />
                    <span>{live.error.message}</span>
                  </div>
                ) : null}
                {retrieval ? (
                  <div className="case-provider-result">
                    <div className="case-provider-count">
                      <CheckCircle2 size={17} aria-hidden="true" />
                      <strong>
                        {indexed.size}/{item.document_ids.length}
                      </strong>{" "}
                      linked records retrieved
                    </div>
                    <p>
                      <Search size={13} aria-hidden="true" /> “
                      {retrieval.search_query}”
                    </p>
                    <small>
                      Entry search {retrieval.entry_latency_ms} ms · Case filter{" "}
                      {retrieval.related_latency_ms} ms · Filter returned{" "}
                      {retrieval.total_indexed_results} items
                    </small>
                  </div>
                ) : null}
              </section>
            </aside>
          </div>
        </>
      ) : null}
    </div>
  );
}
