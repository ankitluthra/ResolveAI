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

The local connector reads checked-in synthetic JSON. Replacing it with production connectors should preserve the normalization contract. Stable IDs make repeated uploads update existing items. Deletes are a future operation: compare source snapshots and issue provider-specific delete calls for missing IDs.
