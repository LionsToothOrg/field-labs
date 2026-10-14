# Contributing to Field Labs

Field Labs is a public engineering workbench. Contributions should be useful as both technical experiments and portfolio-quality records of engineering reasoning.

Read `AGENTS.md` before making changes. Its public-safety rules apply to every contribution.

## Workflow

1. Create a descriptive branch from `main`.
2. Keep exploratory work local when practical.
3. Never commit secrets, real customer/client data, proprietary code, employer material, or copied job-posting/client content.
4. Use synthetic fixtures and public-safe examples.
5. Run relevant tests and the pre-commit checks before pushing.
6. Clean up noisy exploratory history before merge when practical.
7. Open a focused pull request explaining the problem, reproduction, solution, validation, and limitations.
8. Prefer squash merging so `main` remains a clean engineering narrative.

## Branch naming

Preferred patterns:

- `lab/<experiment>`
- `feat/<capability>`
- `fix/<problem>`
- `test/<scenario>`
- `docs/<topic>`
- `chore/<maintenance>`

Branch names are public. Do not include client names, private project names, credentials, ticket content, or throwaway wording.

## Commit messages

Use concise, meaningful messages. Conventional Commit prefixes are encouraged:

- `feat:` new behavior
- `fix:` defect correction
- `test:` test coverage or reproducible failure scenarios
- `docs:` documentation
- `refactor:` internal restructuring
- `chore:` tooling or maintenance

Good:

`test: reproduce duplicate webhook race`

`fix: enforce idempotent transaction state changes`

Avoid:

`fix`

`ugh`

`try again`

`final final 2`

## Pull request quality bar

A strong PR answers:

- What engineering problem does this lab explore?
- How can the failure or baseline be reproduced?
- What changed?
- What evidence validates the result?
- What tradeoffs or limitations remain?

Do not claim results that were not actually measured or tested.

## Pre-commit checks

This repository includes `pre-commit` configuration with Gitleaks and basic repository-safety checks.

After cloning:

```bash
python -m pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Gitleaks is a guardrail, not permission to skip manual review. Before every push, review the diff as if it were about to appear on a public portfolio site.
