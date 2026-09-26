# Retrieval experiments

The evaluation set was fixed before any provider tuning. No provider credentials are configured in this workspace, so there are **no measured results yet**. Do not interpret the empty dashboard as zero relevance.

## Experiment A — Azure keyword baseline versus semantic ranking

- **Hypothesis:** Semantic ranking may improve natural-language support questions that use terms different from the guide.
- **Configuration:** Baseline uses the checked-in `searchFields=title,content` keyword request. Variant will add an account-supported semantic configuration only after verifying tier support.
- **Dataset:** `evals/dataset.json`, 20 queries, identical index content.
- **Metrics:** Hit@1, Hit@3, MRR, average latency.
- **Baseline:** Pending first live Azure run.
- **Experiment result:** Pending. No numbers are asserted.
- **Observation:** Pending.
- **Decision:** Pending evidence and cost review.

## Experiment B — Coveo baseline versus query pipeline configuration

- **Hypothesis:** A customer-specific query pipeline may improve ranking of maintained docs relative to duplicate case content.
- **Configuration:** Baseline uses the default Search API query on the `ResolveAI Knowledge` source. Variant will be defined only after trial features and available pipeline controls are inspected; the exact configuration must be recorded here.
- **Dataset and metrics:** Same 20 queries and metrics as Experiment A.
- **Baseline / result / observation / decision:** Pending live access. No numbers are asserted.

Run both baselines first; then record the exact variant setup, timestamps, provider tier, query-level results, and measured tradeoffs in this file.
