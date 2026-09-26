"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, FileText } from "lucide-react";
import { apiGet } from "@/lib/api";
import type { SearchResult } from "@/types/api";
type Document = SearchResult & {
  content: string;
  created_at: string | null;
  metadata: Record<string, unknown>;
};
export default function DocumentPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const record = useQuery({
    queryKey: ["document", id],
    queryFn: () => apiGet<Document>(`/api/documents/${encodeURIComponent(id)}`),
  });
  return (
    <div className="workspace document-page">
      <Link href="/" className="back-link">
        <ArrowLeft size={15} /> Back to search
      </Link>
      {record.isLoading ? (
        <div className="state-message">Loading source…</div>
      ) : null}
      {record.isError ? (
        <div className="state-message error">{record.error.message}</div>
      ) : null}
      {record.data ? (
        <article className="document-panel">
          <div className="panel-kicker">
            <FileText size={14} /> SOURCE RECORD / {record.data.id}
          </div>
          <h1>{record.data.title}</h1>
          <div className="document-fields">
            <span>{record.data.source_type.replace("_", " ")}</span>
            <span>{record.data.product}</span>
            <span>{record.data.visibility} visibility</span>
            <span>
              {record.data.updated_at
                ? `Updated ${new Date(record.data.updated_at).toLocaleDateString()}`
                : ""}
            </span>
          </div>
          <p>{record.data.content}</p>
          <div className="document-provenance">
            <strong>Provenance</strong>
            <p>
              This is a synthetic AcmeCloud record in the checked-in canonical
              corpus. Its stable ID is used by both search providers and the
              evaluation set.
            </p>
          </div>
        </article>
      ) : null}
    </div>
  );
}
