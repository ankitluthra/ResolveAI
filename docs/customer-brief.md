# Customer brief — AcmeCloud

## Initial request

> “We want an AI assistant that can answer technical support questions using all of our company knowledge.”

AcmeCloud is a fictional B2B developer platform. A support engineer currently searches product docs, API guides, FAQs, issue discussions, tickets, and release notes separately. An OAuth rotation question can require evidence from several of those systems.

## Discovery questions

1. Where does knowledge live, and which source is authoritative when records disagree?
2. Which users may see support tickets and internal engineering records?
3. How quickly must changed content become searchable?
4. What should happen when evidence is missing or conflicting?
5. What search and answer latency can support engineers tolerate?
6. What corpus size and query volume should the first rollout support?
7. Which sources contain PII or contractual restrictions?
8. Which cases represent success, and who judges relevance?
9. How should citations lead engineers back to the original records?

## Resulting requirements

The prototype normalizes five source types into one schema, prepares them for indexing in two retrieval platforms, exposes search and filters in one workspace, permits provider switching, logs diagnostics, and evaluates 25 fixed questions. Live provider indexing and comparison remain pending credentials. The answer layer uses retrieved documents and rejects unsupported citation IDs. This demonstration uses synthetic records and descriptive visibility metadata; a production deployment needs identity and enforceable permissions.

The support outcome is a faster, traceable case investigation: find the relevant records, identify the current fix or procedure, and show the evidence behind that conclusion. The planned Case Evidence Trail will connect tickets, issues, affected versions, releases, and procedures with explicit, sourced links. A graph view is useful only if it helps the engineer verify a resolution or identify conflicting evidence.
