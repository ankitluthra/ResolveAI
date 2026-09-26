# Production considerations

This is a fictional prototype. Its visibility field is a **UI and retrieval filter**, not authorization. Before indexing confidential records, introduce enterprise identity, role mappings, provider-level document permissions, and server-enforced access checks. Do not rely on a user-selectable visibility filter.

Real connectors need source-specific retention rules, PII classification/redaction, incremental cursors, delete propagation, retry and dead-letter queues, rate-limit handling, idempotency, and reconciliation reports. Provider credentials should live in a managed secret store and rotate independently. Add tenant boundaries before multiple customers share an index.

Operational rollout needs structured telemetry, audit trails, alerting, cost budgets, cache invalidation rules, backups and disaster recovery. Evaluate prompt injection in indexed documents; retrieved text must remain data, not instructions. Large collections need batch indexing, partition strategy, relevance review, and latency targets confirmed with the customer.
