# Field Labs — Public Repository Steering

This repository is intentionally public. Treat every tracked file, commit message, branch name, pull request, review, issue, comment, screenshot, log, fixture, and generated artifact as public-facing portfolio material.

## Non-negotiable public-safety rules

Before committing or pushing anything, assume it may be indexed, cached, forked, quoted, or viewed permanently.

Never commit or publish:

- API keys, access tokens, passwords, private keys, certificates, session tokens, cookies, webhook secrets, database credentials, connection strings, or other secrets.
- `.env` files or real environment-variable values. Commit only sanitized examples such as `.env.example`.
- Customer, client, prospect, employee, family, or other real-person data. Use synthetic identities and synthetic records only.
- Proprietary source code, configuration, architecture, documentation, prompts, datasets, screenshots, logs, or implementation details copied from private LionsTooth Tech projects.
- Employer source code, internal documentation, architecture, tickets, logs, screenshots, credentials, URLs, names, operational details, or other non-public employer information.
- Client or prospective-client proprietary material.
- Copied Upwork job descriptions, client names, client data, attachments, repositories, screen recordings, or private messages. A public lab may be inspired by a general engineering problem seen in the market, but its implementation, wording, data, and documentation must be original.
- Production URLs, private/internal hostnames, account IDs, tenant IDs, resource IDs, IP addresses, email addresses, phone numbers, or other identifiers unless they were intentionally created as safe public examples.
- Unredacted screenshots, terminal output, stack traces, HTTP dumps, database dumps, or logs that may expose any of the above.

If there is any doubt about whether material is safe to publish, do not commit it. Replace it with a synthetic example or keep it outside this repository.

## Synthetic-by-default

All labs must be self-contained demonstrations using fabricated systems and data.

- Use example domains such as `example.com`, `example.org`, and `.test` where appropriate.
- Use fictional people, organizations, transactions, products, and identifiers.
- Generate fixtures specifically for the lab rather than copying real records.
- Do not reuse production data merely because fields have been partially redacted.
- Do not depend on private LionsTooth systems for a public lab to function.

## Secrets and configuration

- Secrets belong in environment variables or an appropriate secret manager, never source control.
- Local secret files must be ignored by Git.
- Provide `.env.example` files containing placeholder values when configuration documentation is useful.
- Never put secrets in test fixtures, example commands, Docker files, CI configuration, Terraform variables, screenshots, or documentation.
- Before publishing logs or screenshots, inspect and redact them manually.
- Secret-scanning/pre-commit checks supplement these rules; they do not replace human review.

## Portfolio-quality Git hygiene

Everything visible on GitHub should look intentional and professional.

### Branches

Use descriptive branches such as:

- `lab/webhook-idempotency`
- `lab/jwt-refresh-race`
- `feat/email-header-analyzer`
- `docs/transaction-findings`
- `fix/concurrent-refresh`

Avoid branch names such as `test`, `stuff`, `ugh`, `try-again`, `final-final`, or names containing private/client information.

### Commits

Use concise conventional-style commit messages that explain the engineering change, for example:

- `feat: add webhook idempotency lab`
- `test: reproduce concurrent transaction race`
- `fix: serialize refresh token rotation`
- `docs: document deliverability audit workflow`

Avoid noisy public commit history such as `fix`, `oops`, `ugh`, `again`, or repeated trial-and-error commits.

For exploratory work, make as many local commits as useful, but squash/rebase into a clean story before merging when practical.

### Pull requests

PR titles and descriptions are portfolio material. They should explain:

1. The engineering problem being investigated.
2. How the failure was reproduced or measured.
3. The approach taken.
4. How the result was validated.
5. Remaining limitations or follow-up experiments.

Do not include copied client/job-posting text or private context in PR descriptions.

## Lab standard

A Field Lab should demonstrate engineering reasoning, not just a finished toy application. Prefer this progression:

1. Define the failure scenario or question.
2. Build the smallest reproducible system.
3. Establish a baseline and, when useful, deliberately reproduce the failure.
4. Investigate and explain the underlying behavior.
5. Implement the improvement or fix.
6. Validate it with tests, measurements, or repeatable evidence.
7. Document what changed, what was learned, and what remains uncertain.

Do not fabricate benchmarks, incidents, client outcomes, production experience, or test results. Clearly label simulated scenarios and synthetic data.

## Pre-push public review

Before pushing, check:

- Is every file safe for a public repository?
- Did any secret, `.env`, token, credential, private URL, or identifier slip in?
- Is all data synthetic?
- Did any private LionsTooth, employer, client, or Upwork material get copied into the repo?
- Are screenshots and logs sanitized?
- Are branch and commit names professional and non-sensitive?
- Are claims in the README supported by actual tests or measurements?

When uncertain, stop and sanitize before publishing.
