# Lab 08 — AI Product Discovery

## Question

How can a semantic retrieval step help discover relevant products without being allowed to invent specifications or override hard requirements?

## Synthetic baseline

This lab uses a fabricated product catalog and synthetic retrieval candidates. Product IDs, names, categories, load ratings, and indoor/outdoor flags exist only for this experiment. There are no external catalogs, customer records, production identifiers, or private systems.

The first slice treats semantic retrieval as an untrusted candidate generator. A candidate contributes only a product ID and a synthetic relevance score. Product facts are always hydrated from the authoritative in-memory catalog before any result can be returned.

## Deterministic constraint boundary

`discover` applies hard category, minimum-load, and outdoor-use requirements after candidate hydration. A high semantic score cannot rescue a product that violates a hard requirement. A candidate ID that does not exist in the authoritative catalog is ignored rather than converted into a fabricated product.

If no authoritative candidate satisfies the requested constraints, the result is empty. The experiment deliberately prefers "no match" over invented specifications.

## Run the validation

From the repository root:

```bash
PYTHONPATH=labs/08-ai-product-discovery python -m unittest discover -s labs/08-ai-product-discovery/tests -v
```

The focused suite checks authoritative hydration, hard-constraint precedence over semantic score, rejection of unknown candidate IDs, outdoor-use filtering, and an explicit empty result when no candidate qualifies.

## What this slice establishes

Semantic relevance and product truth can have separate responsibilities. In this controlled fixture, retrieval can rank possible matches, but only catalog-backed facts and deterministic constraints decide which products are eligible to return.

## Limitations

This slice does not implement embeddings, vector search, natural-language constraint extraction, an LLM, fuzzy units, catalog persistence, catalog freshness, pagination, price or inventory rules, ranking calibration, explanations, or production recommendation quality. Semantic scores are supplied by the fixture so the experiment can isolate the trust boundary between retrieval and authoritative product data.
