# Verification record

Date: **17 October 2026**. This record distinguishes executed local checks from online publication and operational validation.

## Initial review and corrections

The supplied project passed 12 tests, but those tests did not detect several important edge cases. The review reproduced acceptance of an infinite price, negative freight, a blank customer identity and a malformed purchase timestamp. An empty repeat query returned NULL for the repeat count, and rebuilding could delete the existing database before validation succeeded.

Corrections include validated inputs; explicit overwrite consent with atomic database replacement; preservation of the existing database on failure; closed SQLite connections; deterministic tie handling; zero repeat counts for empty populations; read-only query execution; labelled, non-overwriting report directories; CSV formula protection; stronger ignore rules; and expanded regression tests. The category reconciliation test now checks the actual shipped SQL rather than a separate near-duplicate SQL calculation. Python 3.9 instructions were replaced with the verified, supported Python 3.12 baseline.

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

GitHub Actions is configured to run tests, the synthetic CLI and independent reconciliation on Python 3.12 on Ubuntu and Windows. **Remote execution has not yet been verified in this preparation session.** The browser session requires GitHub sign-in before publication. No live repository, successful remote run, commit identifier, release or DOI is claimed by this document until confirmed.

## Remaining limitations

There is no event-time delivery status, complete follow-up guarantee, causal identification, predictive validation or production deployment. The feature and RFM dates are fixed historical examples. Repeat share is not cohort retention, and NTILE bands can split ties. Monetary storage uses binary REAL; this is not financial-ledger software. Large-scale performance, Windows execution and macOS execution have not been verified locally. The workflow will provide Windows evidence after successful online execution.

References: [SQLite window semantics](https://www.sqlite.org/windowfunctions.html), [supported Python versions](https://devguide.python.org/versions/), [Olist source](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
