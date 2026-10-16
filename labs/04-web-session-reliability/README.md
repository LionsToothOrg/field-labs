# Lab 04 — Web Session Reliability

## Question

How can two valid refresh requests from the same browser session make a user appear randomly logged out when refresh-token rotation is handled as an unchecked read-then-write operation?

## Synthetic baseline

This lab models one fictional session entirely in memory. The only token values are generated strings such as `refresh-synthetic-0`; they are not JWTs, credentials, cookies, or provider artifacts.

`SyntheticSessionStore.begin_refresh` validates the presented refresh token and records the generation observed by that request. `finish_refresh_unchecked` deliberately rotates state without checking whether another request has already advanced the generation.

The deterministic race is:

1. request A validates generation 0;
2. request B validates the same generation 0 before A rotates it;
3. A finishes and receives `refresh-synthetic-1`;
4. B finishes from its stale observation and advances the store to `refresh-synthetic-2`;
5. A's newly returned token is already invalid against current session state.

No threads, sleeps, network calls, or timing guesses are required to reproduce the failure. The split begin/finish boundary makes the interleaving explicit and repeatable.

## Ownership boundary

`finish_refresh` adds the smallest useful constraint: a request may rotate the session only while the generation and token it observed are still current. Once one request completes, a second request that began from the same generation is rejected with `StaleRefreshAttempt` before it can mutate session state.

## Conditional storage boundary

`InMemorySessionStore` now owns the compare-and-write operation. The session workflow supplies the token and generation observed when refresh began; the store either returns the next synthetic generation or reports a conflict without mutation. This keeps the ownership decision at the same boundary as the state change instead of splitting a check from a later write.

The abstraction is intentionally small: `read()` returns an immutable snapshot and `conditional_rotate(...)` returns either a `RefreshResult` or `None` for conflict. Tests exercise successful rotation plus conflicts caused by a stale generation and by a mismatched token.

This models the contract a persistent adapter would need, not the database mechanism that would satisfy it. A real implementation would require an atomic conditional write, transaction, lock, or equivalent primitive appropriate to its storage system.

## Run the validation

From the repository root:

```bash
PYTHONPATH=labs/04-web-session-reliability python -m unittest discover -s labs/04-web-session-reliability/tests -v
```

The focused suite retains the baseline and ownership cases and adds storage-contract coverage for conditional-write success and conflict-without-mutation behavior.

## What this slice establishes

The baseline apparent logout does not require a randomly failing authentication provider. In this deliberately small model, it follows from allowing two refresh operations to validate the same state and then rotate independently.

The checked path now delegates ownership enforcement to the synthetic storage boundary. After one completion advances the stored snapshot, the same expectation cannot rotate it again. The stale caller receives a conflict outcome while the successful caller's token remains current within this single-store model.

## Limitations

This is a synthetic state-machine experiment, not an authentication implementation. It does not model JWT signing, access tokens, cookies, browser storage, CSRF, OAuth/OIDC, provider APIs, token theft, revocation across devices, persistence, distributed coordination, clock skew, network retries, or multi-region state. The generated token strings are inert test identifiers and must not be interpreted as production credentials.

`InMemorySessionStore` is deterministic and single-process. Its conditional operation is atomic only by construction of one Python method; the lab does not claim database isolation, cross-process locking, or distributed serialization. A later experiment can introduce a second synthetic adapter or retry policy if doing so answers a distinct reliability question rather than merely expanding the abstraction.
