-- Seller diversity among observed DELIVERED orders, not available marketplace selection.
WITH completed_items AS (
    SELECT c.customer_state,
           COALESCE(NULLIF(TRIM(p.product_category_name), ''), 'unknown') AS product_category,
           o.order_id, oi.seller_id, oi.price
    FROM orders o
    JOIN customers c ON c.customer_id=o.customer_id
    JOIN order_items oi ON oi.order_id=o.order_id
    LEFT JOIN products p ON p.product_id=oi.product_id
    WHERE o.order_status='delivered'
)
SELECT customer_state, product_category,
       COUNT(DISTINCT order_id) AS observed_orders,
       COUNT(DISTINCT seller_id) AS observed_sellers,
       ROUND(SUM(price), 2) AS item_value_brl
FROM completed_items
GROUP BY customer_state, product_category
ORDER BY observed_orders DESC, observed_sellers DESC, customer_state, product_category;
