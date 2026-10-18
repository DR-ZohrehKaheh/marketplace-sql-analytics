# v0.1.0 — Marketplace SQL Analytics

Published on 17 October 2026: [GitHub release v0.1.0](https://github.com/DR-ZohrehKaheh/marketplace-sql-analytics/releases/tag/v0.1.0), [Zenodo archive](https://zenodo.org/records/23435889), version DOI [10.5281/zenodo.23435889](https://doi.org/10.5281/zenodo.23435889). This file was updated after archiving; the archived snapshot retains its original preparation notes.

## Included

- Nine SQLite analyses covering category demand, observed seller diversity and concentration, repeat customers, historical customer features, category shares, monthly trends, RFM bands and data-quality checks.
- Validated CSV ingestion, deterministic synthetic data, safe database creation, read-only query execution and reproducible reporting with provenance.
- Independent Python/Decimal reconciliation of all nine SQL outputs.
- 36 standard-library tests and GitHub Actions on Ubuntu and Windows using Python 3.12; no third-party runtime or test dependencies.
- Business framing, metric definitions, validation documentation and explicit author/rights information.

## Attribution

Author and maintainer: **Dr Zohreh Kaheh**. See [AUTHORS.md](../AUTHORS.md).

## Verification

[GitHub Actions run 39027040535](https://github.com/DR-ZohrehKaheh/marketplace-sql-analytics/actions/runs/39027040535), at commit `d7cafad54af52b07d158a7df330433885ae51445`, passed all 36 tests, the synthetic pipeline and independent reconciliation on Ubuntu and Windows on 17 October 2026.

[docs/VALIDATION.md](VALIDATION.md) separately records earlier local historical Olist verification. Historical execution was not repeated during DOI preparation. The release tag points to `d7cafad54af52b07d158a7df330433885ae51445` and has not been moved.

## Scope, distribution and rights

This is a descriptive portfolio case study, not a production service or validated predictive model. Fixed historical dates, retrospective delivery status and observation-window limitations are documented. No current marketplace recommendations or operational impact are claimed.

The source distribution excludes original datasets, historical databases, customer-level reports, private evaluation outputs, manuscripts, student reports, trained models and local environment files. The synthetic generator creates invented records.

No open-source software licence or additional reuse permission is granted. [RIGHTS.md](../RIGHTS.md) applies to the software; Olist's dataset terms are separate. The archive uses the approved custom statement **No general software reuse licence — rights reserved**. Concept DOI: [10.5281/zenodo.23435888](https://doi.org/10.5281/zenodo.23435888). Citation edits made after archiving are not part of the archived snapshot; see [ARCHIVE.md](ARCHIVE.md).

