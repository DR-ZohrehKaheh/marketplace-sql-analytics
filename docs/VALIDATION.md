# Verification record

Date: **17 October 2026**. This record distinguishes executed local checks from online publication and operational validation.

## Input and output safeguards

The pipeline validates identifiers, money values and timestamps; requires explicit consent before replacing a database; and preserves existing files if a build fails. Reports use a new output directory, deterministic ordering and spreadsheet-safe CSV exports. Automated tests cover these safeguards and the shipped SQL queries.

## Clean-environment checks

Environment: Linux x86-64, Python **3.12.14**, SQLite **3.53.1**, fresh virtual environment with **no third-party dependencies installed**.

- `python -m unittest discover -s tests -v`: **36 tests passed**.
- The synthetic CLI produced all nine CSV reports and run metadata.
- `python src/validate_results.py --db data/marketplace.sqlite`: all nine outputs matched the independent Python/Decimal reference.
- CLI execution outside the repository and `python -m src.pipeline --help` were exercised.
- Deterministic data generation, malformed CSVs, duplicate records, orphan keys, invalid money/dates, exact cutoff boundaries, missing timestamps/categories, empty populations, zero denominators, itemless orders, RFM ties/small cohorts, path rejection, overwrite protection and report provenance are covered.

The independent reference reads the base tables and calculates aggregates, distinct sets, rankings, recency, labels and RFM tiles in Python. It does not re-use the production SQL to compute expected metrics. Comparisons cover every result cell, with numerical tolerance 0.000001, below the displayed monetary precision.

## Historical Olist execution

The original archive was downloaded from the [official Olist dataset on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) on 17 October 2026. Only the five required CSVs were imported locally. File hashes are retained with local run provenance.

| Imported table | Rows |
| --- | ---: |
| Customers | 99,441 |
| Sellers | 3,095 |
| Products | 32,951 |
| Orders | 99,441 |
| Order items | 112,650 |

All selected source values were independently compared with the imported database and matched. SQLite integrity check returned `ok`; foreign-key check returned no violations.

Data-quality checks found **1,603 item rows with missing category**, retained as `unknown`, and **775 orders without items**, none marked delivered. No missing customer identities, orphan product references, missing/invalid purchase timestamps, nonpositive prices or negative freight were found in this imported snapshot. Its purchase timestamps span 4 September 2016 through 17 October 2018.

Every output was reconciled independently:

| SQL analysis | Historical result rows checked |
| --- | ---: |
| Category demand | 1,388 |
| Observed seller diversity | 1,388 |
| Seller concentration | 3,437 |
| Repeat customer summary | 1 |
| Historical customer features | 81,265 |
| State/category share | 1,388 |
| Monthly sales trend | 23 |
| RFM customer bands | 93,358 |
| Data-quality profile | 12 |

These checks validate import fidelity and transformations on the supplied snapshot. They do not independently verify that the source recorded every real-world event or that the metrics predict business outcomes. Raw data, customer-level reports and the historical database remain outside the public distribution.

## CI and publication status

The project was published on `main` in [DR-ZohrehKaheh/marketplace-sql-analytics](https://github.com/DR-ZohrehKaheh/marketplace-sql-analytics). The initial publication commit is [`f7378cdc33783734cc835d230a0294faf2f721a6`](https://github.com/DR-ZohrehKaheh/marketplace-sql-analytics/commit/f7378cdc33783734cc835d230a0294faf2f721a6).

[GitHub Actions run 39019374181](https://github.com/DR-ZohrehKaheh/marketplace-sql-analytics/actions/runs/39019374181) completed successfully on 17 October 2026. Both Ubuntu and Windows jobs passed all 36 tests, generated the synthetic reports and completed independent SQL/Python reconciliation. The uploaded 28-file tree matched the locally validated files by Git blob hash. The rendered README and GitHub's citation control were inspected.

CI uses synthetic data only; historical Olist validation was executed separately and locally. The first source release, [v0.1.0](https://github.com/DR-ZohrehKaheh/marketplace-sql-analytics/releases/tag/v0.1.0), was published on 17 October 2026 at commit `d7cafad54af52b07d158a7df330433885ae51445`. [GitHub Actions run 39027040535](https://github.com/DR-ZohrehKaheh/marketplace-sql-analytics/actions/runs/39027040535) passed on Ubuntu and Windows before publication. The exact 30-file source snapshot was manually archived in [Zenodo](https://zenodo.org/records/23435889), software DOI [10.5281/zenodo.23435889](https://doi.org/10.5281/zenodo.23435889), under the approved rights-reserved statement. The uploaded ZIP checksum matched the reviewed archive; its files matched the release Git tree by Git blob SHA. Historical Olist execution was not repeated during the DOI workflow. Later citation and publication-status edits are outside the archived snapshot; see [ARCHIVE.md](ARCHIVE.md).

## Scope of the published version

This published portfolio version focuses on descriptive SQL analytics, data-quality controls and independent verification of analytical outputs. Event-time delivery-status reconstruction, complete outcome follow-up, causal inference, predictive-model validation and production deployment are outside the scope of this release.

The analyses use a historical snapshot with retrospective delivery status and no guarantee of complete follow-up. Feature and RFM cutoffs are fixed historical examples; repeat share measures observed repeat purchasing rather than cohort retention, and NTILE bands can split ties. Monetary values use SQLite REAL for analytical summaries; financial-ledger functionality is outside this release's scope.

Published verification covers local Linux execution and Windows checks through GitHub Actions. Large-scale performance benchmarking and macOS verification are outside the documented test scope.

References: [SQLite window semantics](https://www.sqlite.org/windowfunctions.html), [supported Python versions](https://devguide.python.org/versions/), [Olist source](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
