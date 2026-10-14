<div align="center">

# FIELD LABS

### `OFF THE MAP // ENGINEERING UNDER CONTROLLED CONDITIONS`

**Real engineering problems. Rebuilt from scratch. Broken on purpose. Measured honestly.**

[ENTER THE LAB BENCH](#-the-lab-bench) · [READ THE METHOD](#-the-method) · [OPEN ACTIVE EXPERIMENT](labs/01-transaction-reliability/)

<br>

```text
┌──────────────────────────────────────────────────────────────────────┐
│ FIELD LABS CONTROL                                                  │
│                                                                      │
│ SIGNAL        ████████████████████  ACQUIRED                         │
│ ENVIRONMENT   SYNTHETIC             ISOLATED                         │
│ EVIDENCE      TESTS + MEASUREMENTS  REQUIRED                         │
│ ACTIVE LAB    01 // TRANSACTION RELIABILITY                          │
│                                                                      │
│ STATUS        ● EXPERIMENT IN PROGRESS                               │
└──────────────────────────────────────────────────────────────────────┘
```

</div>

---

## ◈ OFF THE MAP

Field Labs started with a simple thought while looking through the kinds of problems people hire engineers to solve:

> ### **I could build that.**

So I started doing it.

Not by copying someone else's work, and not by pretending a tutorial is production experience. Field Labs takes the **engineering idea behind a real-world problem**, rebuilds it from scratch with synthetic data, and turns it into a controlled experiment.

Some labs stay small. Some turn into deeper investigations. Every lab exists for the same reason:

**Build the thing. Find the edge cases. Understand what breaks. Prove what changed.**

<details>
<summary><strong>▸ What Field Labs is not</strong></summary>
<br>

It is not a collection of client clones, copied job postings, production data, mystery benchmarks, or polished demos pretending to be battle-tested systems.

The problem is the inspiration. The implementation and evidence are built here from scratch.

</details>

---

## ⌁ THE METHOD

```text
      SIGNAL
        │
        ▼
   ┌─────────┐      ┌─────────┐      ┌─────────┐
   │ REBUILD │ ───► │  BREAK  │ ───► │  TRACE  │
   └─────────┘      └─────────┘      └────┬────┘
                                          │
                                          ▼
   ┌─────────┐      ┌─────────┐      ┌─────────┐
   │ PUBLISH │ ◄─── │  PROVE  │ ◄─── │   FIX   │
   └─────────┘      └─────────┘      └─────────┘

   question → reproduction → failure → root cause
              evidence ← validation ← smallest defensible change
```

A useful Field Lab has a narrow question, a reproducible baseline, an intentionally triggered failure when appropriate, an improvement, and evidence showing what changed.

> **LAB RULE 00:** If it hasn't been measured, it isn't presented as a result.

---

# ⌬ THE LAB BENCH

| ID | Experiment | State | Signal |
| :-- | :-- | :--: | :-- |
| **[01](labs/01-transaction-reliability/)** | **Transaction Reliability** | 🟢 `ACTIVE` | Duplicate requests + concurrency + idempotency |
| **02** | **AI Workflow Boundaries** | ⚪ `QUEUED` | Deterministic software ↔ AI interpretation |
| **03** | **Email Delivery & Verification** | ⚪ `QUEUED` | Generated ≠ delivered |
| **04** | **Web Session Reliability** | ⚪ `PLANNED` | Concurrent refresh + authentication state |
| **05** | **Document Annotation** | ⚪ `PLANNED` | Persistent comments through changing views |
| **06** | **Verified Document Pipeline** | ⚪ `PLANNED` | Generation + automated verification |
| **07** | **Offline Event Check-In** | ⚪ `PLANNED` | Offline acceptance + eventual reconciliation |
| **08** | **AI Product Discovery** | ⚪ `PLANNED` | Semantic retrieval without invented specs |

<details open>
<summary><strong>🟢 LAB 01 // TRANSACTION RELIABILITY // ACTIVE</strong></summary>
<br>

### The duplicate transaction

```text
                     ┌─────────────────┐
worker A ───────────►│ duplicate check │────┐
                     └─────────────────┘    │
                                            ├──► STATE MUTATION
                     ┌─────────────────┐    │
worker B ───────────►│ duplicate check │────┘
                     └─────────────────┘

request_id: synthetic-award-001

INVARIANT // one logical request must produce at most one state change
QUESTION  // can both workers get through before either one writes?
```

**Current experiment:** reproduce the duplicate-request race deterministically, enforce the idempotency invariant, and prove the changed behavior with automated tests.

**Boundary:** the first implementation demonstrates in-process coordination. It is intentionally not presented as distributed, crash-safe idempotency.

[**ENTER LAB 01 →**](labs/01-transaction-reliability/)

</details>

<details>
<summary><strong>⚪ LAB 02 // AI WORKFLOW BOUNDARIES // QUEUED</strong></summary>
<br>

Where should deterministic software stop and AI interpretation begin? Planned experiments explore structured constraints, retrieval, grounding, conflicting source material, and explicit failure boundaries.

</details>

<details>
<summary><strong>⚪ LAB 03 // EMAIL DELIVERY & VERIFICATION // QUEUED</strong></summary>
<br>

An application says the verification email was sent. The user never receives it. The experiment follows the message through application state, provider acceptance, authentication, suppression, bounce, deferral, and delivery evidence.

</details>

<details>
<summary><strong>▸ Show remaining planned experiments</strong></summary>
<br>

**04 // Web Session Reliability** — concurrent refresh, token rotation, multi-tab behavior, and the difference between authentication bugs and apparent random logout.

**05 // Document Annotation** — keeping comments anchored to the right content through zoom, resize, navigation, persistence, and revision.

**06 // Verified Document Pipeline** — generating documents is easy; proving every generated document contains the right data is the experiment.

**07 // Offline Event Check-In** — two disconnected devices accept the same synthetic credential, reconnect, and have to reconcile reality.

**08 // AI Product Discovery** — semantic discovery over an authoritative synthetic catalog while deterministic constraints prevent invented specifications.

</details>

---

## ⌁ EVIDENCE, NOT VIBES

Field Labs separates **what I expect** from **what I can demonstrate**.

| Evidence | What it proves |
| :-- | :-- |
| **Reproduction** | The failure can actually be triggered under known conditions. |
| **Automated tests** | Behavior can be checked repeatedly instead of judged by appearance. |
| **Measurements** | Performance or reliability claims have observed numbers behind them. |
| **Failure injection** | The system is tested when assumptions stop being true. |
| **Limitations** | The experiment says exactly where its conclusions stop applying. |

A green test is evidence for a claim. It is **not** a magic production-ready stamp.

---

## ⛨ LAB PROTOCOL

<details>
<summary><strong>01 // Synthetic by default</strong></summary>
<br>
Fixtures, identities, transactions, documents, companies, products, and events are fabricated for the experiment.
</details>

<details>
<summary><strong>02 // The original work stays original</strong></summary>
<br>
Field Labs may be inspired by broad engineering problems seen in the market, but client work, job-posting content, proprietary implementations, private systems, employer material, and other non-public information do not belong here.
</details>

<details>
<summary><strong>03 // Failure belongs in the artifact</strong></summary>
<br>
A lab is allowed to start broken. The interesting part is making the failure reproducible, understanding it, and proving the improvement.
</details>

<details>
<summary><strong>04 // Show the receipts</strong></summary>
<br>
Tests, measurements, tradeoffs, and limitations matter more than a polished screenshot with no explanation behind it.
</details>

---

<div align="center">

### `BUILD → BREAK → TRACE → FIX → PROVE → DOCUMENT`

**FIELD LABS // THE WORK IS THE EVIDENCE**

[AGENTS](AGENTS.md) · [CONTRIBUTING](CONTRIBUTING.md) · [SECURITY](SECURITY.md)

</div>
