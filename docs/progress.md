# ResolveAI progress

Last reviewed: 2026-09-26

This file tracks work that has been implemented and work that still needs live verification. Update it when a milestone is completed, with a link to the relevant commit or evidence. The full original project brief is stored locally in `.local/project-idea.md` and is excluded from Git.

## Done

- [x] Set up the Next.js, TypeScript, FastAPI, lint, test, and CI foundations.
- [x] Generate and normalize 250 synthetic AcmeCloud records across five source types.
- [x] Define one canonical document schema and stable IDs for both search providers.
- [x] Define 20 evaluation questions and expected relevant documents before provider tuning.
- [x] Implement Azure AI Search index creation, upload, keyword search, and filters.
- [x] Implement Coveo Push upload, search, and filters behind the shared provider interface.
- [x] Build the search workspace, provider switch, document view, retrieval diagnostics, and evaluation UI.
- [x] Implement evaluation metrics and an optional answer service with source citations.
- [x] Document the customer brief, architecture, decisions, experiments, and production considerations.
- [x] Create the public GitHub repository with focused commits and passing CI.

## Next: prove the MVP with live services

- [ ] Configure an Azure AI Search service locally; create the index and upload all 250 records.
- [ ] Verify the Azure document count, representative queries, every filter, and error handling; record the service tier and date.
- [ ] Run the 20-question Azure baseline and save actual query-level results and metrics.
- [ ] Configure a Coveo organization and `ResolveAI Knowledge` Push source with the required custom fields.
- [ ] Upload the identical 250 records to Coveo; verify searchable count, metadata mapping, representative queries, and filters.
- [ ] Run the same 20-question Coveo baseline and save actual query-level results and metrics.
- [ ] Fix any issues found by the live runs, then update `docs/experiments.md` and the README with measured results and setup details.

**MVP completion check:** Both providers search the same indexed corpus, and the evaluation page shows real Hit@1, Hit@3, MRR, and latency results for both. No benchmark number should be published before a successful live run.

## After the live baselines

- [ ] Run and document the Azure keyword-versus-semantic experiment if the selected service supports it.
- [ ] Run and document a Coveo query configuration experiment supported by the organization.
- [ ] Review the synthetic corpus and relevance labels; add harder questions, distractors, and missing-answer cases without tuning the data to favor a provider.
- [ ] Exercise live grounded answers, citations, conflicting evidence, and insufficient-evidence fallback; improve the guard where results do not support an answer.
- [ ] Capture actual search and evaluation screenshots and a five-minute demo flow.
- [ ] Check that each resume claim is supported by the running app, recorded results, and repository evidence.

## Later, if needed

- [ ] Add incremental update and delete synchronization.
- [ ] Replace synthetic connectors with real content sources and enforce document permissions.
- [ ] Add production controls such as retries, monitoring, PII handling, and cost limits.

## Current dependency

Live provider verification needs Azure and Coveo accounts and credentials in the local, ignored `.env` file. OpenAI credentials are only needed for the optional answer flow. Never put credentials or copied provider responses containing private data in Git.
