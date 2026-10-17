# v0.1.0 — Marketplace SQL Analytics

Prepared notes for the first source-code release. The custom rights statement for manual Zenodo archiving was approved on 17 October 2026. Publication and DOI registration remain pending account access.

## Included

- Nine SQLite analyses covering category demand, observed seller diversity and concentration, repeat customers, historical customer features, category shares, monthly trends, RFM bands and data-quality checks.
- Validated CSV ingestion, deterministic synthetic data, safe database creation, read-only query execution and reproducible reporting with provenance.
- Independent Python/Decimal reconciliation of all nine SQL outputs.
- 36 standard-library tests and GitHub Actions on Ubuntu and Windows using Python 3.12; no third-party runtime or test dependencies.
- Business framing, metric definitions, validation documentation and explicit author/rights information.

## Attribution

Author and maintainer: **Dr Zohreh Kaheh**. The implementation and documentation were prepared and revised with AI assistance under her direction. No student collaborator or commercial affiliation is claimed. See [AUTHORS.md](../AUTHORS.md).

## Verification

[GitHub Actions run 39019619673](https://github.com/DR-ZohrehKaheh/marketplace-sql-analytics/actions/runs/39019619673), at commit `bcdb6a9874c0cd3cf813b0c7bbf25f431d0521e0`, passed all 36 tests, the synthetic pipeline and independent reconciliation on Ubuntu and Windows on 17 October 2026.

[docs/VALIDATION.md](VALIDATION.md) separately records earlier local historical Olist verification. Historical execution was not repeated during DOI preparation. The final release commit and its CI result must be recorded when the release is published.

## Scope, distribution and rights

This is a descriptive portfolio case study, not a production service or validated predictive model. Fixed historical dates, retrospective delivery status and observation-window limitations are documented. No current marketplace recommendations or operational impact are claimed.

The source distribution excludes original datasets, historical databases, customer-level reports, private evaluation outputs, manuscripts, student reports, trained models and local environment files. The synthetic generator creates invented records.

No open-source software licence or additional reuse permission is granted. [RIGHTS.md](../RIGHTS.md) applies to the software; Olist's dataset terms are separate. A software DOI has not yet been issued. Any citation changes made after archiving must be distinguished from the archived snapshot; an existing release tag must not be moved.
