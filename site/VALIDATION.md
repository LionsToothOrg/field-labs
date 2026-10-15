# Site validation scope

The public-site checks protect a few intentional presentation and evidence boundaries. They are not screenshot tests and do not claim browser rendering correctness.

- `validate-site.js` checks required public content, evidence/safety language, and the established Field Labs palette tokens.
- `validate-workbench.js` checks the current compact desktop layout budget so the investigation index remains the visual priority.
- `node --check site/app.js` checks JavaScript syntax.
- Lab Python suites remain the evidence for implemented engineering behavior.

Visual review is still required for responsive layout, typography, spacing, and interaction quality.
