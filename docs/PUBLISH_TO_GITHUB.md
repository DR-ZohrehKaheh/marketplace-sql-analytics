# Publication and maintenance checks

Target repository: `DR-ZohrehKaheh/marketplace-sql-analytics`.

1. Run the tests, synthetic pipeline and independent reconciliation in the README from a clean Python 3.12 environment.
2. If using separately sourced Olist data, run the same reconciliation on that database and keep generated reports local.
3. Review the exact file list. Exclude raw CSVs, database files, reports, environments, logs, archives and credentials. Ignore rules are a safeguard, not a substitute for review.
4. Inspect any existing repository before changing it; preserve unrelated work. Publish source files with their directory structure on `main`.
5. Confirm the uploaded files match the reviewed version, inspect the rendered README and verify the GitHub Actions results on Ubuntu and Windows.
6. Once the repository is live, set `repository-code` in `CITATION.cff` to its actual URL and verify GitHub's citation feature. Do not claim a release date or DOI before one exists.

Suggested description: `SQL and Python marketplace analytics: customer identity, category value, seller concentration, historical RFM and independently verified data-quality checks.`

Suggested topics: `sql`, `sqlite`, `python`, `customer-analytics`, `rfm-analysis`, `data-quality`, `marketplace-analytics`.

A software licence or Zenodo deposit requires a separate rights decision. The Olist data licence does not automatically license the source code.
