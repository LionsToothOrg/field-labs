# Field Labs Catalog

This directory is the current index of implemented Field Labs. Each lab is a self-contained, synthetic experiment; its README defines the question, evidence, and limitations for that slice.

| Lab | Experiment | Engineering focus |
| --- | --- | --- |
| [01](01-transaction-reliability/) | Transaction Reliability | Duplicate requests, concurrency, and idempotency |
| [02](02-ai-workflow-boundaries/) | AI Workflow Boundaries | Deterministic software and bounded AI interpretation |
| [03](03-email-delivery-verification/) | Email Delivery & Verification | Distinguishing generation, provider acceptance, and delivery evidence |
| [04](04-web-session-reliability/) | Web Session Reliability | Concurrent refresh and authentication state |
| [05](05-document-annotation/) | Document Annotation | Keeping annotations anchored through changing views |
| [06](06-verified-document-pipeline/) | Verified Document Pipeline | Verifying generated document data and serialized artifacts |
| [07](07-offline-event-check-in/) | Offline Event Check-In | Offline acceptance, reconciliation, and idempotent replay |
| [08](08-ai-product-discovery/) | AI Product Discovery | Semantic retrieval bounded by authoritative catalog facts |
| [09](09-bounded-api-retries/) | Bounded API Retries | Transient failure classification, backoff, and retry exhaustion |
| [10](10-circuit-breaker-recovery/) | Circuit Breaker Recovery | Failure isolation, recovery timeout, and bounded probe admission |
| [11](11-bulkhead-isolation/) | Bulkhead Isolation | Partitioned concurrency limits and saturation containment |
| [12](12-token-bucket-rate-limiting/) | Token Bucket Rate Limiting | Burst admission, refill accounting, and bounded request rates |
| [13](13-request-deadline-budgeting/) | Request Deadline Budgeting | End-to-end deadlines, downstream timeout bounds, and reserved completion time |
| [14](14-cooperative-cancellation/) | Cooperative Cancellation | Cancellation propagation, abandoned work, and bounded detection delay |
| [15](15-load-shedding/) | Load Shedding Under Saturation | Bounded admission, queue capacity, and overload rejection |
| [16](16-graceful-degradation/) | Graceful Degradation | Required dependencies, optional capabilities, and reduced response modes |
| [17](17-request-coalescing/) | Request Coalescing | Duplicate in-flight demand and bounded downstream work |
| [18](18-stale-cache-fallback/) | Stale Cache Fallback | Freshness boundaries, bounded stale delivery, and revalidation intent |
| [19](19-hedged-requests/) | Hedged Requests | Bounded duplicate admission, race outcomes, and timeline consistency |
| [20](20-adaptive-concurrency-limits/) | Adaptive Concurrency Limits | Bounded feedback, window aggregation, controller state, and stabilization |

## Reading the labs

A lab is evidence for the behavior it actually reproduces or validates, not a claim of production readiness. Start with the lab README, then inspect its implementation and tests together. Limitations are part of the result.

All examples and fixtures in this repository must remain synthetic and public-safe. See the repository-level [AGENTS.md](../AGENTS.md), [CONTRIBUTING.md](../CONTRIBUTING.md), and [SECURITY.md](../SECURITY.md) before contributing.
