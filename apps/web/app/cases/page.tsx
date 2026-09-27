"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Network, AlertCircle } from "lucide-react";
import { cases } from "@/lib/api";

export default function CasesPage() {
  const caseList = useQuery({ queryKey: ["cases"], queryFn: cases });
  return (
    <div className="workspace">
      <div className="page-heading">
        <div>
          <div className="eyebrow">SUPPORT WORKSPACE / CONNECTED CASES</div>
          <h1>Follow the evidence to a resolution.</h1>
          <p>
            Open a customer case to inspect the ticket, engineering finding,
            release, and maintained procedure as one traceable path.
          </p>
        </div>
      </div>
      <div className="case-intro">
        <Network size={20} aria-hidden="true" />
        <p>
          These cases use explicit links in the synthetic AcmeCloud corpus. Open
          a case to inspect each source and verify indexed evidence in a search
          provider.
        </p>
      </div>
      {caseList.isLoading ? (
        <div className="state-message">Loading cases…</div>
      ) : null}
      {caseList.isError ? (
        <div className="state-message error">
          <AlertCircle size={20} /> {caseList.error.message}
        </div>
      ) : null}
      <div className="case-grid">
        {caseList.data?.map((item) => (
          <Link className="case-card" href={`/cases/${item.id}`} key={item.id}>
            <div className="case-card-top">
              <span className="panel-kicker">{item.customer}</span>
              <span className="case-status">{item.status}</span>
            </div>
            <h2>{item.title}</h2>
            <p>{item.summary}</p>
            <div className="case-card-bottom">
              <span>
                {item.product} · {item.document_count} connected sources
              </span>
              <ArrowRight size={18} aria-hidden="true" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
