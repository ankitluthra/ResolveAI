# Requirements traceability

| Requirement | Implementation | Verification |
|---|---|---|
| Unified search | `/api/search`, Search workspace | Provider mock tests; live run pending |
| Source, product, category, date, visibility filters | Shared filters; Azure OData and Coveo context query | Filter tests; live run pending |
| Provider switching | URL-backed control | Frontend build; live run pending |
| Grounded answers and fallback | `/api/answer` with returned source ID checks; eight-case answer evaluation | Unit tests; live OpenAI run and human factual review pending |
| Source transparency | `/documents/[id]` | API document test |
| Evaluation | 25 fixed queries, Hit@1, Hit@3, MRR, latency | Unit tests; live runs pending |
| Observability | Structured search event log; retrieval panel | API tests; live run pending |
| Access control | Visibility demonstration only | Explicitly untrusted for real confidential data |
