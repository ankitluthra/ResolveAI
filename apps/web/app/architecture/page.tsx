import {
  ArrowDown,
  Database,
  FileStack,
  GitBranch,
  Search,
  Sparkles,
  UserRound,
} from "lucide-react";
const sources = [
  "Product docs",
  "GitHub issues",
  "Support tickets",
  "FAQs",
  "Release notes",
];
export default function ArchitecturePage() {
  return (
    <div className="workspace">
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            SUPPORT WORKSPACE <span className="eyebrow-line" /> 03 /
            ARCHITECTURE
          </div>
          <h1>One corpus. Two retrieval paths.</h1>
          <p>
            The customer’s source systems are normalized once, then indexed
            independently.
          </p>
        </div>
      </div>
      <div className="architecture-flow">
        <section className="flow-stage">
          <div className="flow-label">
            <FileStack size={18} /> 01 / CONTENT
          </div>
          <h2>Fragmented knowledge</h2>
          <div className="flow-chips">
            {sources.map((x) => (
              <span key={x}>{x}</span>
            ))}
          </div>
        </section>
        <ArrowDown className="flow-arrow" />
        <section className="flow-stage">
          <div className="flow-label">
            <Database size={18} /> 02 / NORMALIZE
          </div>
          <h2>Canonical document schema</h2>
          <p>
            Stable IDs, source type, product, category, timestamps, tags and
            visibility travel with every item.
          </p>
        </section>
        <ArrowDown className="flow-arrow" />
        <div className="flow-split">
          <section className="flow-stage">
            <div className="flow-label">
              <Search size={18} /> 03A / INDEX
            </div>
            <h2>Azure AI Search</h2>
            <p>Search index, upload, keyword retrieval and metadata filters.</p>
          </section>
          <section className="flow-stage">
            <div className="flow-label">
              <Search size={18} /> 03B / INDEX
            </div>
            <h2>Coveo</h2>
            <p>Push source, Search API retrieval and mapped custom metadata.</p>
          </section>
        </div>
        <ArrowDown className="flow-arrow" />
        <section className="flow-stage accent">
          <div className="flow-label">
            <GitBranch size={18} /> 04 / CONTRACT
          </div>
          <h2>SearchProvider interface</h2>
          <p>
            Both services return the same result shape. The UI, answer layer and
            evaluator can compare them without vendor-specific branching.
          </p>
        </section>
        <ArrowDown className="flow-arrow" />
        <div className="flow-split">
          <section className="flow-stage">
            <div className="flow-label">
              <Sparkles size={18} /> 05A / ANSWER
            </div>
            <h2>Grounded response</h2>
            <p>
              Retrieved context only, validated source IDs and an
              insufficient-evidence fallback.
            </p>
          </section>
          <section className="flow-stage">
            <div className="flow-label">
              <UserRound size={18} /> 05B / WORKSPACE
            </div>
            <h2>Support engineer</h2>
            <p>
              Search, inspect sources, switch providers and examine measured
              relevance.
            </p>
          </section>
        </div>
      </div>
      <div className="architecture-note">
        <strong>Prototype boundary</strong>
        <p>
          Visibility is descriptive metadata in this demo. Production access
          requires authenticated users and provider-level document permissions
          before indexing confidential customer content.
        </p>
      </div>
    </div>
  );
}
