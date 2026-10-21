# Lab 19 — Hedged Request Admission

## Question

When a read request is slower than an explicit latency threshold, can a client admit one duplicate attempt, prefer the first acceptable modeled completion, and request cancellation only when useful without treating cancellation as proof that duplicate downstream work never began?

This lab uses synthetic request timings and outcomes and does not perform network I/O.

## Failure scenario

A naive tail-latency strategy can duplicate every slow request, including mutation requests, or create more and more attempts while the original remains in flight. Even with bounded admission, a race model can overstate cancellation by pretending the losing attempt did no work after it was already started. It can also select the first completion even when that result is known to be unacceptable, discarding a later acceptable result. Finally, a timing model that does not retain the hedge admission time can accept impossible traces where the duplicate completes before it was allowed to start.

## Model

`hedged_requests.py` makes four boundaries explicit.

### Admission

- if the primary completes at or before the hedge threshold, no hedge starts;
- only `GET`, `HEAD`, and `OPTIONS` are treated as replay-safe in this lab;
- an eligible slow request starts exactly one hedge, so the modeled attempt count is capped at two;
- admitted decisions retain the synthetic hedge start time; non-hedged decisions do not;
- malformed identifiers, methods, timings, and thresholds fail validation.

The equality boundary is intentional: completion exactly at `hedge_after_ms` wins, so no duplicate attempt is admitted.

### Winner selection and loser cancellation

- when a hedge was admitted, the earliest modeled completion wins;
- equal completion times resolve to the primary deterministically;
- the loser receives a modeled cancellation request;
- cancellation is explicitly **not** treated as evidence that the losing attempt never started or performed downstream work;
- a request with no admitted hedge has no loser and no cancellation request;
- inconsistent race inputs fail validation rather than inventing an outcome.

### Acceptable completion selection

A separate outcome model adds a minimal result-quality boundary without defining application-specific status codes or payload semantics:

- an acceptable first completion is selected immediately and a later in-flight attempt receives a cancellation request;
- an early rejected completion does not cancel the remaining attempt;
- if the later completion is acceptable, it is selected instead;
- if both completions are rejected, the model waits for the second result before returning a terminal rejected outcome;
- simultaneous completions prefer an acceptable result; if both are acceptable, the primary remains the deterministic tie-break;
- the `acceptable` flag is synthetic policy input, not a claim that all HTTP success responses are equivalent.

### Timeline consistency

Race resolution validates the trace against the admission decision:

- an admitted hedge must have a recorded start time;
- the hedge cannot complete before that start time;
- the primary completion for an admitted hedge must occur after the admission threshold, because a primary completed at or before that boundary would never have admitted the hedge;
- non-hedged decisions cannot carry a hedge start time.

These checks prevent the deterministic model from accepting internally impossible timing evidence.

## Evidence

Run the focused tests with:

```bash
PYTHONPATH=labs/19-hedged-requests python -m unittest discover -s labs/19-hedged-requests/tests -v
```

The tests cover admission timing boundaries, replay-safe methods, primary and hedge wins, deterministic ties, non-hedged completion, cancellation semantics, acceptable-result selection, rejected-first outcomes, terminal rejection, impossible timelines, and malformed race inputs.

## What this proves

For this deterministic synthetic model, hedge admission is bounded to one additional attempt and restricted to an explicit replay-safe method set after the configured delay. Once admitted, the model can either select the earliest completion mechanically or apply an explicit acceptability policy that does not discard a later acceptable result merely because another attempt completed first. Cancellation remains modeled intent and is requested only when the selected acceptable result precedes the other completion. Race inputs must also remain temporally consistent with the admission decision.

## Stopping point

Lab 19 intentionally stops at bounded admission, deterministic race resolution, acceptable-result selection, cancellation intent, and timeline consistency. Real asynchronous execution, transport behavior, adaptive hedge thresholds, downstream-capacity feedback, and distributed coordination belong in separate experiments rather than expanding this deterministic model indefinitely.

## Limitations

This lab does **not** claim a production hedging implementation or a measured latency improvement. It does not model sockets, asynchronous task scheduling, transport-level cancellation, cancellation acknowledgement, HTTP status classification, response payload equivalence, consistency across replicas, downstream capacity, retries, distributed coordination, adaptive latency distributions, or measured tail latency. A cancellation request is a modeled intent, not a guarantee that downstream work stops. The synthetic `acceptable` flag stands in for an application policy that a real system would need to define and test separately.

All identities, timings, and outcomes in this lab are synthetic.
