# Security Policy

Field Labs is a public educational and engineering-experiment repository. It must not contain production secrets, private customer data, proprietary client material, or non-public employer information.

## Reporting a security issue

If you discover a credential, token, private key, personal data, proprietary material, or another sensitive disclosure in this repository, do not open a public issue containing the sensitive value.

Instead, report the problem privately to the repository maintainers using GitHub's private vulnerability reporting feature when it is available for this repository. If no private reporting channel is available, contact LionsTooth Tech through its established private contact channel without reproducing the exposed secret in a public location.

## If a secret is exposed

Removing a secret in a later commit is not sufficient because Git history may retain it.

Treat an exposed secret as compromised:

1. Revoke or rotate the credential immediately.
2. Remove the sensitive material from the current repository state.
3. Determine whether Git history needs to be rewritten and whether cached/forked copies require additional response.
4. Review logs and provider activity where appropriate.
5. Add or improve automated detection to reduce recurrence.

## Repository data policy

All examples and fixtures should use synthetic data. Do not submit real customer, employee, client, family, financial, authentication, or other private records in issues, pull requests, discussions, test fixtures, screenshots, logs, or source files.

## Supported code

Field Labs contains experiments rather than production-supported products. Security fixes to the current default branch are welcome, but no lab should be assumed production-ready unless its documentation explicitly says otherwise.
