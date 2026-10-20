# Lab 19 — Hedged Request Admission

## Question

When a read request is slower than an explicit latency threshold, can a client admit one duplicate attempt, select the first modeled completion, and request cancellation of the loser without treating cancellation as proof that duplicate downstream work never began?

This lab uses synthetic request timings and does not perform network I/O.

## Failure scenario

A naive tail-latency strategy can duplicate every slow request, including mutation requests, or create more and more attempts while the original remains in flight. Even with bounded admission, a race model can overstate cancellation by pretending the losing attempt did no work after it was already started.

## Model

`hedged_requests.py` makes two boundaries explicit.

### Admission

- if the primary completes at or before the hedge threshold, no hedge starts;
- only `GET`, `HEAD`, and `OPTIONS` are treated as replay-safe in this lab;
- an eligible slow request starts exactly one hedge, so the modeled attempt count is capped at two;
- malformed identifiers, methods, timings, and thresholds fail validation.

The equality boundary is intentional: completion exactly at `hedge_after_ms` wins, so no duplicate attempt is admitted.

### Winner selection and loser cancellation

- when a hedge was admitted, the earliest modeled completion wins;
- equal completion times resolve to the primary deterministically;
- the loser receives a modeled cancellation request;
- cancellation is explicitly **not** treated as evidence that the losing attempt never started or performed downstream work;
- a request with no admitted hedge has no loser and no cancellation request;
- inconsistent race inputs fail validation rather than inventing an outcome.

## Evidence

Run the focused tests with:

```bash
PYTHONPATH=labs/19-hedged-requests python -m unittest discover -s labs/19-hedged-requests/tests -v
```

The tests cover admission timing boundaries, replay-safe methods, primary and hedge wins, deterministic ties, non-hedged completion, cancellation semantics, and malformed race inputs.

## What this proves

For this deterministic synthetic model, hedge admission is bounded to one additional attempt and restricted to an explicit replay-safe method set after the configured delay. Once admitted, exactly one modeled completion is selected and cancellation is requested for the loser without claiming that already-started loser work can be undone.

## Limitations

This lab does **not** claim a production hedging implementation or a measured latency improvement. It does not model sockets, asynchronous task scheduling, transport-level cancellation, cancellation acknowledgement, response payload equivalence, downstream capacity, retries, distributed coordination, or measured tail latency. A cancellation request is a modeled intent, not a guarantee that downstream work stops.

All identities and timings in this lab are synthetic.
