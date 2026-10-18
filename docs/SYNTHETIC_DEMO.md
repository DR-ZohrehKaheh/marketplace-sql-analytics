# Verified synthetic demonstration only

These outputs were produced locally from the fixed-seed artificial database (seed 47), not from historical Olist or a real marketplace. These figures illustrate the analytical workflow and do not represent commercial findings.

- Total generated orders: **240**
- Orders marked delivered: **211**
- Generated order-item rows (including canceled orders): **469**
- Observed purchasers with ≥1 delivered order: **50**
- Observed repeat purchasers: **45** (**90.0%**). Artificially high simulated repeat rate is not an estimate of real retention.

## Top five state/category combinations by delivered item value

| State | Category | Distinct delivered orders in category | Item value (BRL) |
|---|---|---:|---:|
| PR | home | 15 | 2,704.74 |
| PR | fashion | 16 | 2,245.01 |
| RJ | electronics | 13 | 2,122.36 |
| RJ | fashion | 18 | 2,098.31 |
| SP | home | 17 | 2,083.93 |

These are category-by-customer-state totals; the order counts cannot be summed across categories to obtain marketplace orders.

The demo verifies processing, tests, and metric definitions only. Apply the pipeline to separately downloaded historical Olist data and add a distinct empirically audited analysis before presenting business recommendations.

