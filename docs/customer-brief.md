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

The prototype normalizes five source types into one schema, indexes them in two retrieval platforms, exposes search and filters in one workspace, permits provider switching, logs diagnostics, and evaluates 20 fixed questions. The answer layer is grounded in returned documents and rejects unsupported citations. This demonstration uses synthetic records and descriptive visibility metadata; a production deployment needs identity and enforceable permissions.
