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

This is a compare-before-write model, not a claim that an in-process check alone provides distributed serialization. A persistent implementation would need an atomic conditional write, transaction, lock, or equivalent coordination primitive appropriate to its storage boundary.

## Run the validation

From the repository root:

```bash
PYTHONPATH=labs/04-web-session-reliability python -m unittest discover -s labs/04-web-session-reliability/tests -v
```

The focused suite retains the three baseline tests and adds three ownership tests: a normal checked refresh rotates once, a second completion from the same observed generation is rejected, and that rejection leaves the current token and generation unchanged.

## What this slice establishes

The baseline apparent logout does not require a randomly failing authentication provider. In this deliberately small model, it follows from allowing two refresh operations to validate the same state and then rotate independently.

The ownership check changes that outcome deterministically: after the first completion advances the session, the stale second completion cannot rotate it again. The token returned to the successful caller therefore remains current within this single-store model.

## Limitations

This is a synthetic state-machine experiment, not an authentication implementation. It does not model JWT signing, access tokens, cookies, browser storage, CSRF, OAuth/OIDC, provider APIs, token theft, revocation across devices, persistence, distributed coordination, clock skew, network retries, or multi-region state. The generated token strings are inert test identifiers and must not be interpreted as production credentials.

The check and mutation are atomic only by construction of this deterministic in-memory method. The next useful experiment should move the ownership rule behind a storage abstraction and model conditional-write success versus conflict without pretending to provide production database semantics.
