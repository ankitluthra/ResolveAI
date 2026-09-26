# Live provider setup and verification

This runbook is for the synthetic AcmeCloud corpus. Run commands from the repository root. Keep credentials in the root `.env`, which Git ignores. Do not paste keys into issues, screenshots, or evaluation reports.

## 1. Local preparation

```bash
cp .env.example .env
uv sync --project apps/api --extra dev
npm install --prefix apps/web
apps/api/.venv/bin/python -m scripts.seed_data
apps/api/.venv/bin/python -m scripts.check_readiness
```

The last command should report 250 documents and 20 questions. It checks local data only; it does not contact either search service.

## 2. Azure AI Search

1. Create an [Azure AI Search service](https://learn.microsoft.com/en-us/azure/search/search-create-service-portal) in a supported region. Confirm the service tier and any cost before creating it. The small keyword baseline does not require semantic ranking.
2. Copy the service endpoint and an **admin** key into `AZURE_SEARCH_ENDPOINT` and `AZURE_SEARCH_API_KEY` in `.env`. Keep `AZURE_SEARCH_INDEX=resolveai-knowledge` unless you choose another index name. Index creation and upload require an admin key; a query key is insufficient for these operations.
3. Run `apps/api/.venv/bin/python -m scripts.sync_azure`. The script creates or updates the index and uploads all 250 stable IDs. It reports per-item upload failures.
4. Run `apps/api/.venv/bin/python -m scripts.check_readiness --live --provider azure`. It checks the searchable count, a source-type filter, and an OAuth query. If the count is short, allow indexing to finish and inspect the Azure service before retrying.

The adapter uses Azure AI Search REST API version `2024-07-01`. Its initial search mode is keyword search across title and content. Keep the baseline unchanged until its result has been recorded.

## 3. Coveo

1. Create a Coveo organization whose license permits a [Push source](https://docs.coveo.com/en/1546/). In the Coveo Administration Console, create a Push source named `ResolveAI Knowledge` with **Everyone** access. This visibility choice is only appropriate for the fictional synthetic corpus.
2. Create fields with these exact names: `ra_id`, `ra_source_type`, `ra_product`, `ra_category`, `ra_visibility`, `ra_tags`, and `ra_updated_at`. The last field must be a Date field. Configure fields used by filters to support search operators; check that pushed metadata is actually mapped in the Content Browser. Coveo [automaps Push metadata only when a matching field exists](https://docs.coveo.com/en/115/).
3. Create an API key allowed to push items to this source and execute Search API queries. Store the organization ID, source ID, and key in `COVEO_ORG_ID`, `COVEO_SOURCE_ID`, and `COVEO_API_KEY` in `.env`. Set `COVEO_SOURCE_NAME` if you used a different name.
4. Set `COVEO_PUSH_BASE_URL` for the organization's region: US `https://api.cloud.coveo.com`, Canada `https://api-ca.cloud.coveo.com`, Europe `https://api-eu.cloud.coveo.com`, or Australia `https://api-au.cloud.coveo.com`. Coveo's [Push source documentation](https://docs.coveo.com/en/1546/) lists the current endpoint patterns. The Search API defaults to the organization endpoint; set `COVEO_SEARCH_ENDPOINT` only if the organization requires a different URL.
5. Run `apps/api/.venv/bin/python -m scripts.sync_coveo`. Its success count means requests were **accepted for processing**, not that all items are searchable. Inspect the source status and Content Browser for indexing errors.
6. Once the source is indexed, run `apps/api/.venv/bin/python -m scripts.check_readiness --live --provider coveo`. It expects 250 searchable items, a working source-type filter, and results for the OAuth query.

If the count or filters fail, inspect the source name, key privileges, field mappings, indexing logs, and endpoint region before changing relevance settings. The Push source must use the same 250 normalized IDs as Azure.

## 4. Application and baseline evaluation

```bash
apps/api/.venv/bin/uvicorn apps.api.app.main:app --reload --port 8000
npm run dev --prefix apps/web
```

Open `http://localhost:3000`. Search for an OAuth rotation question, inspect results and diagnostics, switch providers, and test source, product, category, date, and visibility filters. The root `.env` serves the API; add `NEXT_PUBLIC_API_URL=http://localhost:8000` to `apps/web/.env.local` if needed.

After **both** readiness checks pass, run the fixed baseline set. The command line path works without starting the API:

```bash
apps/api/.venv/bin/python -m scripts.run_evaluation --provider azure
apps/api/.venv/bin/python -m scripts.run_evaluation --provider coveo
```

The API provides the same operation if the server is already running:

```bash
curl -X POST 'http://localhost:8000/api/evaluations/run?provider=azure'
curl -X POST 'http://localhost:8000/api/evaluations/run?provider=coveo'
```

Inspect `evals/results/azure.json`, `evals/results/coveo.json`, and the Evaluation page. Both result files record SHA-256 fingerprints of the corpus and question set; confirm they match before comparing scores. Record the date, region, service tier, source/index configuration, and any failed questions in `docs/experiments.md`. Commit measured results only after reviewing them. Do not compare runs made against different corpus versions or query sets.

## 5. Optional answer flow

Set `OPENAI_API_KEY` locally, restart the API, and generate answers for a supported question and an unsupported question. Check that every cited document opens and that unsupported questions return the fallback. The key is sent only by the FastAPI server. Live answer behavior must be checked before claiming it in a demo or resume entry.

## 6. Troubleshooting checklist

- **401/403:** Check key type, key privileges, organization/source IDs, and endpoint region.
- **Accepted but count is short:** Wait for asynchronous indexing; inspect per-item errors in the provider console.
- **Count is 250 but filters are empty:** Check field names, field capabilities, and Coveo metadata mapping.
- **Different ranking:** Confirm identical IDs and corpus revisions before changing relevance settings.
- **No evaluation numbers:** A live evaluation run must complete; the dashboard intentionally has no placeholder scores.

Never use synthetic visibility metadata as a security boundary. Production content needs identity and enforceable document permissions.
