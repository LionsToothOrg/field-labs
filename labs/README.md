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

## Reading the labs

A lab is evidence for the behavior it actually reproduces or validates, not a claim of production readiness. Start with the lab README, then inspect its implementation and tests together. Limitations are part of the result.

All examples and fixtures in this repository must remain synthetic and public-safe. See the repository-level [AGENTS.md](../AGENTS.md), [CONTRIBUTING.md](../CONTRIBUTING.md), and [SECURITY.md](../SECURITY.md) before contributing.
