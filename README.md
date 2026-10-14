<div align="center">

# FIELD LABS

### Engineering, under controlled conditions.

**Real engineering problems. Rebuilt from scratch. Broken on purpose. Measured honestly.**

[Explore the Labs](#the-lab-bench) · [How It Works](#the-method) · [Enter Lab 01](labs/01-transaction-reliability/)

</div>

---

## OFF THE MAP

Field Labs started with a simple thought while looking through the kinds of problems people hire engineers to solve:

> **I could build that.**

So I started doing it.

Not by copying someone else's work, and not by pretending a tutorial is production experience. Field Labs takes the **engineering idea behind a real-world problem**, rebuilds it from scratch with synthetic data, and turns it into a controlled experiment.

Some labs are small. Some become deeper investigations. Every lab exists for the same reason: **build the thing, find the edge cases, understand what breaks, and get better by actually doing the work.**

---

## THE METHOD

```text
   SIGNAL          REBUILD           BREAK            INVESTIGATE
     │                │                │                   │
     ▼                ▼                ▼                   ▼
real problem  →  synthetic system  →  failure case  →  root cause
                                                           │
                                                           ▼
   PUBLISH    ←     PROVE          ←      FIX
      │                │                   │
      ▼                ▼                   ▼
 findings +       tests + real         smallest
 limitations      measurements       defensible change
```

A useful Field Lab has a narrow question, a reproducible baseline, an intentionally triggered failure when appropriate, an improvement, and evidence showing what changed.

No invented benchmarks. No borrowed client data. No mystery success claims.

**If it hasn't been measured, it isn't presented as a result.**

---

# THE LAB BENCH

| Lab | Status | Experiment |
| :--- | :---: | :--- |
| **[01 · Transaction Reliability](labs/01-transaction-reliability/)** | 🟢 **ACTIVE** | When two copies of the same request arrive together, how do you stop one logical action from becoming two state changes? |
| **02 · AI Workflow Boundaries** | ⚪ PLANNED | Where should deterministic software end when AI starts interpreting unstructured information? |
| **03 · Email Delivery & Verification** | ⚪ PLANNED | The app says it sent the email. The user never got it. Where did the workflow actually fail? |
| **04 · Web Session Reliability** | ⚪ PLANNED | What happens when multiple browser requests try to refresh authentication state at the same time? |
| **05 · Document Annotation** | ⚪ PLANNED | How do comments stay attached to the right content through zooming, resizing, navigation, and revision? |
| **06 · Verified Document Pipeline** | ⚪ PLANNED | Generating a document is easy. How do you prove every generated document contains the right data? |
| **07 · Offline Event Check-In** | ⚪ PLANNED | Two offline devices accept the same credential. Connectivity returns. Now what? |
| **08 · AI Product Discovery** | ⚪ PLANNED | Can semantic retrieval help find the right product without allowing AI to invent or violate authoritative specifications? |

---

## LAB 01 // TRANSACTION RELIABILITY

```text
REQUEST: synthetic-award-001

worker A ──┐
           ├──► duplicate check ──► state mutation
worker B ──┘

Question: can both workers get through?
```

**Current experiment:** reproduce a duplicate-request race deterministically, then enforce the idempotency invariant and prove the changed behavior with automated tests.

[**ENTER LAB 01 →**](labs/01-transaction-reliability/)

---

## WHAT COUNTS AS EVIDENCE?

Field Labs separates **what I expect** from **what I can demonstrate**.

| Evidence | What it tells us |
| :--- | :--- |
| Reproduction | The failure can actually be triggered under known conditions. |
| Automated tests | The behavior can be checked repeatedly instead of judged by appearance. |
| Measurements | Performance or reliability claims have observed numbers behind them. |
| Failure injection | The system is tested when assumptions stop being true. |
| Limitations | The experiment says where its conclusions stop applying. |

That last one matters. A green test does not magically make an experiment production-ready.

---

## RULES OF THE LAB

**Synthetic by default.** Fixtures, identities, transactions, documents, companies, products, and events are fabricated for the experiment.

**The original work stays original.** Field Labs may be inspired by broad engineering problems seen in the market, but client work, job-posting content, proprietary implementations, private systems, and non-public material do not belong here.

**Failure is part of the artifact.** A lab is allowed to start broken. The interesting part is making the failure reproducible, understanding it, and proving the improvement.

**The receipts matter.** Tests, measurements, tradeoffs, and limitations are more valuable here than a polished screenshot with no explanation behind it.

---

<div align="center">

### BUILD → BREAK → INVESTIGATE → PROVE → DOCUMENT

**Field Labs** is an ongoing engineering practice, not a finished collection.

Read the repository standards before contributing: [AGENTS.md](AGENTS.md) · [CONTRIBUTING.md](CONTRIBUTING.md) · [SECURITY.md](SECURITY.md)

</div>
