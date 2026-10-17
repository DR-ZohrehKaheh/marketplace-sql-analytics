-- Q1: delivered order item value by customer state and product category.
-- Grain = one row per (customer_state, product_category).
-- Count DISTINCT order_id because a delivered order can have several items.
-- Do not join order-level payments here: that would multiply order totals.
WITH category_totals AS (
    SELECT c.customer_state,
           COALESCE(NULLIF(TRIM(p.product_category_name), ''), 'unknown') AS product_category,
           COUNT(DISTINCT o.order_id) AS delivered_orders,
           SUM(oi.price) AS item_value_brl
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    JOIN order_items AS oi ON oi.order_id = o.order_id
    LEFT JOIN products AS p ON p.product_id = oi.product_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_state,
             COALESCE(NULLIF(TRIM(p.product_category_name), ''), 'unknown')
)
SELECT customer_state, product_category, delivered_orders,
       ROUND(item_value_brl, 2) AS item_value_brl
FROM category_totals
ORDER BY item_value_brl DESC, delivered_orders DESC,
         customer_state, product_category;
