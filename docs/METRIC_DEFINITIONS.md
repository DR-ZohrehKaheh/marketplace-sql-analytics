# Metric definitions and data grains

All metrics are descriptive. Delivered status is the final recorded status, not event-time availability.

| Metric | Numerator / unit | Denominator or population |
| --- | --- | --- |
| `delivered_orders` in category tables | Distinct order IDs per state/category | Delivered orders with items; category counts are not additive |
| `item_value_brl` | Sum of item prices, once per item | Delivered items; excludes freight and payments |
| `observed_sellers` | Distinct sellers present in delivered items | State/category; not available inventory or active marketplace sellers |
| `share_pct` | Seller item value × 100 | All seller item value in the same state/category; only top three sellers displayed |
| `state_value_percentage` | Category item value × 100 | All delivered item value in the state |
| `repeat_customer_pct` | Customers with at least two delivered orders × 100 | Customers with at least one delivered order, including itemless orders |
| Monthly `avg_item_value_per_delivered_order_brl` | Delivered item value in purchase month | Distinct delivered orders with items and a valid purchase timestamp |
| `historical_orders` / `historical_item_value` | Distinct orders / their pre-aggregated item values | Customer purchases strictly before 2018-07-01; delivered, with items and valid timestamps |
| `days_since_last_purchase` | Whole calendar days from latest historical purchase to 2018-07-01 | Historical feature customers |
| `repeat_next_30d` | 1 if a delivered purchase is observed in [2018-07-01, 2018-07-31), otherwise 0 | Historical feature customers; future label, not input feature; 0 is absence in the supplied records only |
| `recency_days` | Whole calendar days from latest purchase to 2018-09-01 | RFM customers: delivered purchases with items before that date |
| `order_frequency` / `monetary_brl` | Distinct orders / item value across those orders | RFM customers |

`customer_id` is the join key for the customer record associated with an order. `customer_unique_id` is the cross-order person identifier. Neither is interchangeable with `order_id`. Customer state describes the order's customer record; a person can appear in different states over time.

## Population and missing-data policy

A missing/blank product category maps to `unknown`. The production importer rejects missing product, seller, customer or order references, while category SQL also uses a defensive `LEFT JOIN` for externally constructed tables. Blank customer identifiers are rejected. Missing state is mapped to `unknown`.

Missing purchase timestamps become SQL NULL. Those orders remain in non-temporal totals and repeat share, but are omitted from feature, RFM and monthly calculations. Nonblank invalid dates are rejected. Itemless delivered orders can contribute to repeat share and future-repeat labels, but not monetary analyses; QA reports them explicitly.

## Money and percentages

Monetary inputs must be finite, non-negative, at most 1e12 BRL and have at most two decimal places. This broad technical bound is not a claim of plausible prices. Zero-priced items are accepted and flagged by QA. Values are stored as SQLite REAL, so binary floating-point arithmetic applies. Monetary outputs are rounded to two decimals; the independent reference uses Decimal sums. Monetary ranking ties use cent-rounded totals and deterministic IDs.

A zero monetary denominator gives NULL percentage, not 0%. An empty customer population returns zero observed/repeat counts and a NULL repeat percentage. Displayed rounded shares may not sum to exactly 100%. The top-three seller shares need not sum to 100% when other sellers exist.

## RFM bands and temporal limits

`NTILE(4)` makes approximately equal-sized groups. Higher scores mean more recent, more frequent or greater monetary value. Equal values may be split by the customer-ID tie-breaker; scores can change with the population. With fewer than four customers, only the first available tile numbers appear. Segments use recency and frequency; monetary scores are provided separately.

Dates are timezone-naive source timestamps. The published schema covers purchase times and retrospective delivery status. Delivery-event history and complete customer follow-up are outside this data model, so the analyses use retrospective status rather than status observed at a historical cutoff. Causal inference, predictive-model validation and operational evaluation are outside the scope of this published version.
