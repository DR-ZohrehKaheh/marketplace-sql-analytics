# Marketplace SQL Analytics

[![Validate SQL portfolio](https://github.com/DR-ZohrehKaheh/marketplace-sql-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/DR-ZohrehKaheh/marketplace-sql-analytics/actions/workflows/ci.yml)

**Customer & Category Intelligence · SQL · SQLite · Python**

A reproducible analytics case study for turning marketplace orders, items, customers, products and sellers into clearly defined business metrics. It demonstrates SQL joins and window functions, customer identity resolution, data-quality controls and independent verification of analytical outputs.

**Author and maintainer:** [Dr Zohreh Kaheh](https://github.com/DR-ZohrehKaheh) · [Personal website](https://dr-zohrehkaheh.github.io/)

## Business problem and objectives

Which categories account for observed purchases? How concentrated are purchases among sellers? How often do identified customers order again? This project builds a descriptive evidence layer for investigating those questions, with explicit definitions of item value, distinct orders and customer identity.

It is an independently developed portfolio project. It is not affiliated with Olist or Wolt, and no operational business impact or production readiness is claimed.

## Verified scope

- **Nine SQL analyses**, exercised on deterministic synthetic data and a separately downloaded historical Olist dataset.
- **36 automated tests** covering the importer, analytical edge cases, file safety, reproducibility and CLI integration.
- **Independent Python/Decimal reconciliation** of every query's output, including customer features and RFM scores.
- The historical run processed **99,441 orders and 112,650 order-item rows**. These are verification counts, not evidence of current marketplace performance.

See [the verification record](docs/VALIDATION.md) for the environment, actual checks and limitations. The [first published CI run](https://github.com/DR-ZohrehKaheh/marketplace-sql-analytics/actions/runs/39019374181) passed all 36 tests, the synthetic pipeline and independent reconciliation on Python 3.12 on both Ubuntu and Windows. Historical Olist verification was performed locally on Linux.

## Quick start

Use **Python 3.12** with SQLite **3.25 or newer**. There are no third-party runtime or test dependencies. From the repository root:

```sh
python -m venv .venv
```

Activate with `source .venv/bin/activate` on Linux/macOS or `.venv\Scripts\Activate.ps1` in Windows PowerShell. Then:

```sh
python -m unittest discover -s tests -v
python src/pipeline.py --mode synthetic
python src/validate_results.py --db data/marketplace.sqlite
```

On systems without a `python` command, use `python3` or the Windows `py -3.12` launcher. The scripts also accept absolute paths and run from outside the repository; module invocation is supported with `python -m src.pipeline`.

The first pipeline run creates `data/marketplace.sqlite` and `reports/synthetic/`. A repeat run never silently replaces either. Choose new locations:

```sh
python src/pipeline.py --mode synthetic --db data/demo-2.sqlite --output-dir reports/demo-2
```

Use `--overwrite` only when intentionally replacing an existing database; a failed build preserves its previous contents. Reports always require a new output directory. `--quiet` suppresses printed result samples.

## Repository structure

```text
src/build_db.py          Validated CSV ingestion, synthetic fixture and safe database creation
src/run_queries.py       Read-only query runner, CSV export and provenance
src/pipeline.py          One-command pipeline
src/validate_results.py  Independent Python/Decimal reconciliation
sql/                    Nine SQLite analyses
tests/                  Standard-library regression and integration tests
docs/                   Business framing, metric definitions and verification record
data/README.md          Data acquisition and provenance instructions
.github/workflows/      Ubuntu and Windows CI configuration
CITATION.cff             Software citation metadata
RIGHTS.md                Source-code and third-party-data rights
```

Generated databases, reports and original CSVs remain local and are ignored by Git.

## Analyses and SQL techniques

| Query | Analytical output | Main techniques |
| --- | --- | --- |
| [01](sql/01_category_demand.sql) | Delivered item value and distinct orders by customer state/category | Joins, CTE, distinct counts |
| [02](sql/02_observed_seller_diversity.sql) | Sellers present in recorded delivered purchases | Multi-table joins, distinct counts |
| [03](sql/03_seller_concentration.sql) | Top three sellers and their shares within state/category | Partitioned ranking, window sums |
| [04](sql/04_repeat_customers.sql) | Observed repeat-customer share | Cross-order customer identity, aggregation |
| [05](sql/05_customer_features.sql) | Historical customer features and a separate observed future-repeat indicator | Pre-aggregation, fixed temporal cutoff, left join |
| [06](sql/06_state_category_share.sql) | Each category's share of a state's delivered item value | Window sums and ranking |
| [07](sql/07_monthly_sales_trend.sql) | Monthly orders, customers, items, value and average order item value | Date grouping, explicit grains |
| [08](sql/08_rfm_customer_segments.sql) | Descriptive recency, frequency and monetary bands | CTEs, `NTILE(4)`, conditional segments |
| [09](sql/09_data_quality_checks.sql) | Twelve data-quality and completeness counts | `UNION ALL`, missing-value and existence checks |

## Historical Olist data

The [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) contains anonymised historical records from 2016–2018. On 17 October 2026, the official source displayed **CC BY-NC-SA 4.0**. Read the [licence terms](https://creativecommons.org/licenses/by-nc-sa/4.0/); attribution, non-commercial use and share-alike obligations are separate from this software's rights.

Obtain the dataset from that source and place its five required CSVs in `data/olist/`, as described in [the data guide](data/README.md). Then run:

```sh
python src/pipeline.py --mode olist --dataset-dir data/olist --db data/olist.sqlite --output-dir reports/olist --quiet
python src/validate_results.py --db data/olist.sqlite
```

The importer uses customers, sellers, products, orders and order items. Payments, reviews, geolocation and category translations are not imported. Category names are retained from the source. Full historical data were processed during verification; the repository does not distribute the raw data or customer-level analytical outputs.

## Methodology and interpretation

- `customer_id` joins an order to its customer record. `customer_unique_id` identifies customers across orders.
- Item value sums `order_items.price` once per item. It excludes freight, payments, refunds, commissions and costs; it is neither profit nor platform net revenue.
- Distinct category orders are non-additive: an order containing two categories appears in both. Item values reconcile across categories. Payments are not joined, avoiding payment/item multiplication.
- Missing or blank categories become `unknown`. Missing purchase timestamps are retained for non-temporal metrics, profiled by QA and excluded from temporal analyses. Invalid nonblank dates, blank identifiers, duplicates, orphan references, non-finite money and negative monetary inputs are rejected.
- Customer feature history ends before **1 July 2018**; its future-repeat indicator uses **[1 July, 31 July 2018)**. RFM history ends before **1 September 2018**. These dates are fixed in the SQL and recorded in report metadata.
- Final delivered status is retrospective. The customer feature table is an analytical example, not a point-in-time feature store; its future-repeat column is an outcome, never a predictor. Incomplete observation windows cannot establish absence of future purchasing.
- RFM scores are relative bands. Ties are resolved by customer ID; small cohorts may not populate all four bands. Labels are descriptive, not validated churn or value segments.

[Metric definitions](docs/METRIC_DEFINITIONS.md) explain denominators, zero handling, rounding and included populations. [Business framing](docs/BUSINESS_CASE.md) explains what the data can support.

## Reports and findings

Each run produces nine CSVs and `run_metadata.json`, recording data mode, input hashes for Olist imports, SQL hashes, software versions, result row counts and analysis cutoffs. Formula-like text is escaped in CSV exports for spreadsheet safety; the SQL values are unchanged.

The [synthetic demonstration](docs/SYNTHETIC_DEMO.md) contains invented, reproducible examples. Historical verification confirmed that all nine SQL outputs match the independent Python calculation. It also found missing categories and orders without items, documented in the verification record. No present-day market recommendations are inferred from this historical sample.

## Limitations and next steps

This is descriptive analytics of observed purchases. It cannot measure exposure, conversion, unmet demand, available inventory, causal effects or customer lifetime value. Repeat share is not cohort retention. Missing timestamps and itemless orders mean different analyses can have different populations. Money is stored as SQLite `REAL` and displayed to two decimals; this is not an accounting ledger.

Useful extensions include parameterised analysis dates with explicit observation-window checks, cohort retention, separately aggregated payments/refunds, and query-performance evaluation on larger data. Each extension needs its own metric definitions and tests.

## Citation and rights

Use [CITATION.cff](CITATION.cff) and a commit identifier when citing a specific revision. No software DOI or tagged release is claimed. No open-source software licence has been assigned; see [RIGHTS.md](RIGHTS.md).


Technical references: [SQLite SQL](https://www.sqlite.org/lang.html), [window functions](https://www.sqlite.org/windowfunctions.html), [Python sqlite3](https://docs.python.org/3.12/library/sqlite3.html).
