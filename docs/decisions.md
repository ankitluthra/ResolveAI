# Architecture decisions

## ADR-001 — Shared provider interface

**Decision:** One asynchronous `SearchProvider` contract returns canonical `SearchResponse` objects. **Reason:** A single UI, answer service, and evaluator can run against either platform. **Tradeoff:** Advanced provider capabilities require explicit extensions.

## ADR-002 — Normalize before indexing

**Decision:** Transform every source to `KnowledgeDocument`. **Reason:** Prevent provider mappings from changing business meaning. **Tradeoff:** Some source-specific fields remain in `metadata`.

## ADR-003 — Synthetic AcmeCloud corpus

**Decision:** Generate 250 fictional records with stable IDs and related topics across sources. **Reason:** Safe, reproducible demonstration without customer data. **Tradeoff:** Templated synthetic prose does not represent real enterprise relevance difficulty.

## ADR-004 — Server-side retrieval and LLM calls

**Decision:** Keep keys and HTTP integrations in FastAPI. **Reason:** Browser bundles must not contain credentials. **Tradeoff:** Adds a server hop.

## ADR-005 — Retrieval before generation

**Decision:** OpenAI receives at most five retrieved excerpts, not the corpus. Citations must match returned IDs. **Reason:** Grounding and traceability. **Tradeoff:** Search failures and missing passages limit answer quality.

## ADR-006 — Fixed relevance set

**Decision:** Check in 20 questions and expected IDs before tuning. **Reason:** Relevance changes can be measured. **Tradeoff:** The set is small and contains narrow topics; customer review is required.

## ADR-007 — Honest missing metrics

**Decision:** The evaluation dashboard displays blanks until the live runner writes results. **Reason:** Mocked benchmark numbers would misrepresent platform quality. **Tradeoff:** A fresh clone needs provider setup to show comparison scores.
