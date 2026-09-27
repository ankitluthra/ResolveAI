# Architecture

```text
Synthetic AcmeCloud docs · FAQs · issues · tickets · release notes
                         ↓
              connector → normalization
                         ↓
             KnowledgeDocument (stable ID)
                    ↙         ↘
          Azure AI Search    Coveo Push source
                    ↘         ↙
                SearchProvider contract
                         ↓
           Search UI · Evaluator · RAG
```

The same `KnowledgeDocument` list is uploaded by both sync scripts. Provider adapters translate filters and response shapes at the boundary. The API never sends search or LLM keys to the browser. Evaluation stores real response IDs and timing in `evals/results` only after an explicit run.

The Case Evidence Trail adds a curated relationship file alongside the corpus. Its edges name two stable document IDs and include an excerpt from a source record; local validation rejects missing IDs or excerpts. Selected documents carry a `case_id` field in both indexes. The case page first shows the curated path from local data. When a provider is selected, it runs an ordinary entry query and a case-ID-filtered query, then marks which path records the provider returned. ResolveAI owns relationship traversal and explanations; search providers supply indexed records. A case-filtered query assumes the correct case is already known.

The local connector reads checked-in synthetic JSON. Replacing it with production connectors should preserve the normalization contract. Stable IDs make repeated uploads update existing items. Deletes are a future operation: compare source snapshots and issue provider-specific delete calls for missing IDs.
