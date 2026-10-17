# Lab 08 — AI Product Discovery

## Question

How can a semantic retrieval step help discover relevant products without being allowed to invent specifications or override hard requirements?

## Synthetic baseline

This lab uses a fabricated product catalog and synthetic retrieval candidates. Product IDs, names, categories, load ratings, and indoor/outdoor flags exist only for this experiment. There are no external catalogs, customer records, production identifiers, or private systems.

The first slice treats semantic retrieval as an untrusted candidate generator. A candidate contributes only a product ID and a synthetic relevance score. Product facts are always hydrated from the authoritative in-memory catalog before any result can be returned.

## Deterministic constraint boundary

`discover` applies hard category, minimum-load, and outdoor-use requirements after candidate hydration. A high semantic score cannot rescue a product that violates a hard requirement. A candidate ID that does not exist in the authoritative catalog is ignored rather than converted into a fabricated product.

If no authoritative candidate satisfies the requested constraints, the result is empty. The experiment deliberately prefers "no match" over invented specifications.

## Evidence-backed explanations

Eligible results include structured qualification evidence for each applied requirement. Every evidence item names the requirement, the authoritative catalog field used to evaluate it, and the observed catalog value. Semantic relevance remains useful for ordering eligible candidates, but it is not presented as evidence about a product's specifications.

This keeps a downstream explanation layer bounded: it can explain why a synthetic product qualified by referring to facts already present in the catalog instead of generating unsupported product claims.

## Run the validation

From the repository root:

```bash
PYTHONPATH=labs/08-ai-product-discovery python -m unittest discover -s labs/08-ai-product-discovery/tests -v
```

The focused suite checks authoritative hydration, hard-constraint precedence over semantic score, rejection of unknown candidate IDs, outdoor-use filtering, an explicit empty result when no candidate qualifies, catalog-backed qualification evidence, and exclusion of semantic score from product-fact evidence.

## What this slice establishes

Semantic relevance and product truth can have separate responsibilities. In this controlled fixture, retrieval can rank possible matches, but only catalog-backed facts and deterministic constraints decide which products are eligible to return. Explanations can then expose the exact catalog observations used for those decisions without turning retrieval scores into product claims.

## Limitations

This slice does not implement embeddings, vector search, natural-language constraint extraction, an LLM, fuzzy units, catalog persistence, catalog freshness, pagination, price or inventory rules, ranking calibration, natural-language explanation generation, citations to external sources, or production recommendation quality. Semantic scores are supplied by the fixture so the experiment can isolate the trust boundary between retrieval and authoritative product data.
