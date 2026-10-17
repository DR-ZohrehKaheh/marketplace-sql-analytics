# Business case: category, seller and customer intelligence

## Context and objective

A marketplace analytics team needs interpretable metrics before deciding which categories merit deeper investigation, whether seller activity is concentrated, and how often known customers order again. This repository implements a **descriptive historical analytics** layer using SQL rather than claiming an operational forecasting service.

## Decision questions

1. Which product categories account for the greatest delivered item value by state?
2. What share of each state's delivered item value does each category contribute?
3. Which observed sellers account for the largest fractions of purchased item value?
4. How does purchase activity vary by month?
5. What fraction of identified customers are repeat purchasers, and what does a descriptive RFM ranking show?
6. Are missing categories or invalid monetary records material data-quality concerns?

## Business interpretation and validation

- **Unit of analysis matters.** `order_items` is item-grain; `orders` is order-grain. A category can appear multiple times in one order. For an order count, use `COUNT(DISTINCT order_id)` after item joins.
- **Category attribution is non-exclusive.** A multi-category order appears once in each category, so category-level distinct orders are not additive. Item monetary values *are* additive across categories because each item has a single category.
- **Observed seller diversity is not available selection.** Missing inventory, impressions, search positions, out-of-stock rates, and non-purchasers prevent claims about assortment quality or conversion.
- **Item value excludes** freight, refunds, discounts, payments, taxes, commissions and costs. Never call this profit; avoid inferring platform net revenue.
- **RFM and historic customer features are retrospective.** Final `delivered` status may be known only after the analysis cutoff. Do not treat retrospective labels as contemporaneous model features.

## Illustrative next business action

If a state/category has high item value and concentrated observed purchases among few sellers, flag it for *further investigation* by an operations analyst. Real decisions require current seller availability and inventory, unit economics, and customer exposure data absent from Olist.

## Dataset statement

- **Default run:** 100% synthetic, reproducible demonstration data.
- **Optional analysis:** historical Olist public dataset, 2016–2018, downloaded separately; no claim to represent a current market or Wolt.
- Findings from default mode are **demonstrations**, not market insights.
