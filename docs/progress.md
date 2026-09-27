# ResolveAI progress

Last reviewed: 2026-09-27

This is the living record for ResolveAI. Add newly discovered work to the relevant section, check off items only after verification, and update the review date. For completed milestones, add a dated note under **Progress log** with a commit or other evidence. Keep pending work visible rather than deleting it. The full original project brief is stored locally in `.local/project-idea.md` and is excluded from Git.

## Done

- [x] Set up the Next.js, TypeScript, FastAPI, lint, test, and CI foundations.
- [x] Generate and normalize 250 synthetic AcmeCloud records across five source types.
- [x] Define one canonical document schema and stable IDs for both search providers.
- [x] Define 25 retrieval questions and expected relevant documents before provider tuning.
- [x] Implement Azure AI Search index creation, upload, keyword search, and filters.
- [x] Implement Coveo Push upload, search, and filters behind the shared provider interface.
- [x] Build the search workspace, provider switch, document view, retrieval diagnostics, and evaluation UI.
- [x] Implement evaluation metrics and an optional answer service with source citations.
- [x] Document the customer brief, architecture, decisions, experiments, and production considerations.
- [x] Create the public GitHub repository with focused commits and passing CI.
- [x] Add a repeatable local/live readiness command and detailed provider setup runbook.
- [x] Add a command line evaluation runner that fingerprints the corpus and question set.
- [x] Add optional Azure semantic and Coveo named-pipeline evaluation paths that save separate variant results.
- [x] Implement a dry-run-first incremental update/delete workflow with an ignored local manifest and mocked provider tests.
- [x] Make the category filter apply on submit, avoiding a search on every keystroke.
- [x] Revise repeated synthetic records into related scenarios, expand retrieval labels, and add five harder source-specific questions.
- [x] Add eight supported/unsupported answer cases and a live runner for abstention and citation checks.

## Next: prove the MVP with live services

- [ ] Configure an Azure AI Search service locally; create the index and upload all 250 records.
- [ ] Verify the Azure document count, representative queries, every filter, and error handling; record the service tier and date.
- [ ] Run the 25-question Azure baseline and save actual query-level results and metrics.
- [ ] Configure a Coveo organization and `ResolveAI Knowledge` Push source with the required custom fields.
- [ ] Upload the identical 250 records to Coveo; verify searchable count, metadata mapping, representative queries, and filters.
- [ ] Run the same 25-question Coveo baseline and save actual query-level results and metrics.
- [ ] Inspect pushed items and mapped field values in Coveo Content Browser; keep a reproducible record of the source configuration and observed search results.
- [ ] Verify incremental updates and deletes against both live providers after the baseline.
- [ ] Fix any issues found by the live runs, then update `docs/experiments.md` and the README with measured results and setup details.

**MVP completion check:** Both providers search the same indexed corpus, and the evaluation page shows real Hit@1, Hit@3, MRR, and latency results for both. No benchmark number should be published before a successful live run.

## After the live baselines

- [ ] Run and document the Azure keyword-versus-semantic experiment if the selected service supports it.
- [ ] Run and document a Coveo query configuration experiment supported by the organization.
- [ ] Use Coveo-native facets for support-relevant fields where the organization supports them, and verify the counts against the indexed corpus.
- [ ] Record real search and result-selection interactions in Coveo Analytics where supported; inspect the events and use them to identify a content or relevance gap. Keep synthetic evaluation runs separate from user interaction analytics.
- [ ] Review query-level failures with support-style relevance judgments; document any label changes and rerun both providers on identical fingerprints.
- [ ] Exercise live grounded answers, citations, conflicting evidence, and insufficient-evidence fallback; improve the guard where results do not support an answer.
- [ ] Run the eight-case answer check on both providers and manually review factual support and citation quality.
- [ ] Capture actual search and evaluation screenshots and a five-minute demo flow.
- [ ] Check that each resume claim is supported by the running app, recorded results, and repository evidence.

## Case Evidence Trail

The product goal is to help an engineer locate and verify a resolution to a customer case. The relationship model is part of ResolveAI; Coveo and Azure index and retrieve evidence. The local experience is implemented; measured provider behavior follows live indexing.

- [x] Define typed, explicit relationships between stable document IDs; validate that each edge's cited excerpt exists in its source record.
- [x] Add three coherent synthetic customer cases spanning all five source types, including version context, a confirmed fix, a procedure-only resolution, and an unresolved investigation.
- [x] Add a searchable `case_id` field to both provider adapters and a case API that separately runs an entry query and a case-filtered query. Live field mapping and query behavior remain unverified.
- [x] Build an interactive case view with the ordered evidence path, dates, reasons for each connection, source links, evidence signals, and live-provider retrieval status.
- [x] Add six fixed multi-document case questions and a runner for entry-search evidence recall, case-filtered evidence recall, and complete-path coverage. Results are written only after a live run.
- [ ] Live index the revised 250-document corpus in both providers and verify every case ID filter and linked record count.
- [ ] Run the case evaluation against both providers and review query-level failures, link support, and the wording of each finding and suggested next step.
- [ ] Add a support-focused Coveo query pipeline experiment where available, and compare it with the untuned baseline. Do not assume machine-learning ranking gains from the small synthetic corpus.
- [ ] Run a small manual usability check with a support-style task to assess whether the connected view shortens the time to locate a defensible resolution. Do not claim a time saving before measuring it.

**Completion check:** A user can start from a support query, inspect a ticket-to-fix evidence path, verify every link from source records, and see an evaluation showing whether the connected view improves the investigation. Synthetic visibility remains descriptive metadata; live confidential content requires enforceable document permissions before use.

**Product evidence rule:** Describe Coveo Push indexing, Search API retrieval, mapped fields, and any query-pipeline tuning as working product capabilities only after they are configured and observed in a live organization. Keep the support workflow as the public narrative; use the Azure comparison to diagnose retrieval behavior and validate choices.

## Later, if needed

- [ ] Replace synthetic connectors with real content sources and enforce document permissions.
- [ ] Add production controls such as retry queues, reconciliation, monitoring, PII handling, and cost limits.

## Current dependency

Live provider verification needs Azure and Coveo accounts and credentials in the local, ignored `.env` file. OpenAI credentials are only needed for the optional answer flow. Never put credentials or copied provider responses containing private data in Git.

## Progress log

- **2026-09-26:** Established this tracker and saved the full original brief locally. The brief is ignored by Git; the tracker and ignore rule were published in commit `89600d9`.
- **2026-09-26:** Added upload failure reporting and a configurable Coveo source name (`cee97ed`); readiness checks and a live setup runbook (`3bebd65`); a usable category filter (`37d0a8c`).
- **2026-09-26:** Added reproducible evaluation fingerprints and a CLI runner (`82e13bc`), plus a dry-run-first incremental update/delete workflow (`7bffa5c`). Live service behavior remains pending credentials.
- **2026-09-26:** Saved a private Coveo FDE interview guide in `.local/coveo-fde-interview.md`. It tracks architecture explanations, demo steps, likely questions, and evidence still to gather. The guide is ignored by Git.
- **2026-09-26:** Local verification passed: 16 backend tests, Ruff, frontend formatting/lint/typecheck/unit tests, production build, and all five Playwright flows using installed Chrome, including category filter submission. The browser option is in commit `6e0f895`. Live provider and answer checks remain pending keys.
- **2026-09-26:** Added separate experiment paths for Azure semantic ranking and a Coveo named query pipeline (`4825c95`). The configuration is code-complete and mock-tested; provider account support, actual rules, and results remain to be verified live.
- **2026-09-26:** Before live indexing, revised repeated synthetic records into distinct related scenarios and expanded the retrieval set from 20 to 25 questions (`6c0e548`). Labeled all core records containing each answer, and added an eight-case answer check (`ed2cf5e`). No provider scores were generated from the revised data.
- **2026-09-26:** Rechecked the revised corpus and code: 17 backend tests, Ruff, frontend formatting/lint/typecheck/unit tests, and production build passed. Created ignored local `.env` and `apps/web/.env.local` templates; credentials are still absent.
- **2026-09-26:** Added the planned Case Evidence Trail milestone: explicit, sourced relationships across support records, a case investigation view, and an evaluation against ordinary search. Implementation follows the live provider baselines.
- **2026-09-26:** Refocused the public project story on the support investigation outcome and recorded the live-evidence rule for claims about Coveo usage. Azure remains a comparison implementation, not the product's purpose.
- **2026-09-27:** Implemented the local Case Evidence Trail: three sourced investigations, searchable case IDs in both adapters, case API and UI, and six fixed case evaluation questions. Verification passed: 22 backend tests, Ruff, frontend formatting/lint/typecheck/unit tests, production build, five existing browser flows, and the new case browser flow. Inspected desktop and phone layouts and fixed phone navigation overflow. Live indexing and measured provider results are still pending credentials.
