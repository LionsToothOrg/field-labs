# Lab 04 — Web Session Reliability

## Question

How can two valid refresh requests from the same browser session make a user appear randomly logged out when refresh-token rotation is handled as an unchecked read-then-write operation?

## Synthetic baseline

This first slice models one fictional session entirely in memory. The only token values are generated strings such as `refresh-synthetic-0`; they are not JWTs, credentials, cookies, or provider artifacts.

`SyntheticSessionStore.begin_refresh` validates the presented refresh token and records the generation observed by that request. `finish_refresh_unchecked` deliberately rotates state without checking whether another request has already advanced the generation.

The deterministic race is:

1. request A validates generation 0;
2. request B validates the same generation 0 before A rotates it;
3. A finishes and receives `refresh-synthetic-1`;
4. B finishes from its stale observation and advances the store to `refresh-synthetic-2`;
5. A's newly returned token is already invalid against current session state.

No threads, sleeps, network calls, or timing guesses are required to reproduce the failure. The split begin/finish boundary makes the interleaving explicit and repeatable.

## Run the validation

From the repository root:

```bash
PYTHONPATH=labs/04-web-session-reliability python -m unittest discover -s labs/04-web-session-reliability/tests -v
```

The focused suite establishes three baseline facts: a normal refresh rotates once, two requests can both validate the same current token before either writes, and unchecked completion can invalidate the token returned to the first caller.

## What this slice establishes

The apparent logout does not require a randomly failing authentication provider. In this deliberately small model, it follows from allowing two refresh operations to validate the same state and then rotate independently. A client can receive a refresh token that was valid when returned but obsolete by the time it is next used.

That is the baseline failure only. This slice intentionally does not present a fix yet; the next experiment should add an ownership or serialization boundary and prove that both requests cannot independently rotate the same observed generation.

## Limitations

This is a synthetic state-machine reproduction, not an authentication implementation. It does not model JWT signing, access tokens, cookies, browser storage, CSRF, OAuth/OIDC, provider APIs, token theft, revocation across devices, persistence, distributed coordination, clock skew, network retries, or multi-region state. The generated token strings are inert test identifiers and must not be interpreted as production credentials.
