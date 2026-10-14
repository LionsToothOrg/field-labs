# Field Labs

Field Labs is a public engineering workbench for small, reproducible systems experiments. Each lab starts with a concrete failure mode or engineering question, uses synthetic data, and records the evidence used to validate an improvement.

## Catalog

| Lab | Status | Question |
| --- | --- | --- |
| [01 · Transaction Reliability](labs/01-transaction-reliability/) | Active | How do duplicate requests become duplicate state changes, and where should idempotency be enforced? |
| 02 · AI Workflow Boundaries | Planned | Which workflow decisions should remain deterministic when AI assists with unstructured inputs? |
| 03 · Email Delivery & Verification | Planned | How can an application distinguish generation, provider, delivery, and verification failures? |
| 04 · Web Session Reliability | Planned | What race conditions appear around session refresh and concurrent browser requests? |
| 05 · Document Annotation | Planned | How can annotations remain stable as document views and revisions change? |
| 06 · Verified Document Pipeline | Planned | How can generated documents preserve traceability through transformation and validation? |
| 07 · Offline Event Check-In | Planned | How should an offline client reconcile duplicate and conflicting check-ins? |
| 08 · AI Product Discovery | Planned | How can semantic retrieval remain constrained by authoritative product specifications? |

## Working standard

Labs favor a narrow reproducible scenario over a broad demo. A useful slice includes a baseline, a deliberately reproduced failure when appropriate, an improvement, automated validation, and documented limitations.

All examples are synthetic and self-contained. Read [AGENTS.md](AGENTS.md), [CONTRIBUTING.md](CONTRIBUTING.md), and [SECURITY.md](SECURITY.md) before contributing.
