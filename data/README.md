# Data acquisition and provenance

The repository distributes no original Olist data. The synthetic generator creates fictitious records with Python's `random.Random(47)`; these are illustrative records, not observed marketplace transactions.

Obtain the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) from its official Kaggle page. Extract these five files locally into `data/olist/`:

- `olist_customers_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_products_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`

Use the original CSV headers. The importer handles UTF-8 with or without a BOM and tolerates additional source columns. Missing/duplicate headers and malformed records are rejected. No category translation file is needed.

The source displayed [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) on 17 October 2026. Attribute Olist, link the source and licence, identify transformations, and follow the terms for your intended use and any redistribution. The code's rights statement does not override these data terms.

The importer selects the documented columns, trims text, normalises missing categories/timestamps/state as documented, validates rows and writes a local SQLite database. Input file SHA-256 hashes are retained in database provenance and exported run metadata. Hashes identify the actual local files; a later source download may differ.

Downloaded CSVs, databases, reports and customer-level outputs are ignored by Git. Review staged files before publication. Synthetic and historical outputs must be labelled separately. No Kaggle credentials are needed for the default synthetic workflow or CI.

