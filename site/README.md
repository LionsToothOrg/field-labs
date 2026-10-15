# Field Labs public site

The public site is a static explanatory layer over the repository's synthetic engineering investigations.

## Local validation

From the repository root:

```bash
node --check site/app.js
node site/validate-site.js
node site/validate-workbench.js
```

`validate-site.js` checks the public structure, safety/evidence language, and established palette tokens. `validate-workbench.js` guards the compact desktop presentation so the investigation index remains the focus rather than drifting back into an oversized landing-page hero.

The Python lab suites remain the evidence for implemented lab behavior. Browser interactions are explanatory models only.
