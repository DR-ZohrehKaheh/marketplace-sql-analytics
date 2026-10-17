-- Q6: category mix within each state using a window function.
-- A category's order count is not additive across categories: an order can contain several.
-- Monetary shares use unrounded SUM(price) to avoid intermediate rounding.
WITH category_value AS (
    SELECT c.customer_state,
           COALESCE(NULLIF(TRIM(p.product_category_name), ''), 'unknown') AS product_category,
           COUNT(DISTINCT o.order_id) AS delivered_orders,
           SUM(oi.price) AS item_value_raw
    FROM orders o
    JOIN customers c ON c.customer_id=o.customer_id
    JOIN order_items oi ON oi.order_id=o.order_id
    LEFT JOIN products p ON p.product_id=oi.product_id
    WHERE o.order_status='delivered'
    GROUP BY c.customer_state, COALESCE(NULLIF(TRIM(p.product_category_name), ''), 'unknown')
), with_totals AS (
    SELECT customer_state, product_category, delivered_orders, item_value_raw,
           SUM(item_value_raw) OVER (PARTITION BY customer_state) AS state_value_raw,
           ROW_NUMBER() OVER (
               PARTITION BY customer_state ORDER BY ROUND(item_value_raw,2) DESC, product_category
           ) AS category_rank
    FROM category_value
)
SELECT customer_state, product_category, delivered_orders,
       ROUND(item_value_raw,2) AS item_value_brl,
       ROUND(100.0*item_value_raw/NULLIF(state_value_raw,0),2) AS state_value_percentage,
       category_rank
FROM with_totals
ORDER BY customer_state, category_rank;
