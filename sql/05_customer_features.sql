-- TRAINING EXAMPLE: features calculated from purchases strictly before cutoff.
-- WARNING: delivered status in Olist is a final retrospective attribute, not
-- provably known as of cutoff. This is NOT a point-in-time production feature set.
-- For valid operational features, event-time delivery status history is needed.
WITH order_values AS (
    SELECT order_id, SUM(price) AS item_value
    FROM order_items GROUP BY order_id
), historic AS (
    SELECT c.customer_unique_id, o.order_id,
           date(o.purchase_ts) AS purchase_date,
           v.item_value
    FROM orders o
    JOIN customers c ON c.customer_id=o.customer_id
    JOIN order_values v ON v.order_id=o.order_id
    WHERE o.order_status='delivered' AND o.purchase_ts < '2018-07-01'
), features AS (
    SELECT customer_unique_id,
           COUNT(DISTINCT order_id) AS historical_orders,
           ROUND(SUM(item_value), 2) AS historical_item_value,
           CAST(julianday('2018-07-01') - julianday(MAX(purchase_date)) AS INTEGER) AS days_since_last_purchase
    FROM historic GROUP BY customer_unique_id
), subsequent AS (
    SELECT c.customer_unique_id, COUNT(*) AS orders_next_30d
    FROM orders o
    JOIN customers c ON c.customer_id=o.customer_id
    WHERE o.order_status='delivered'
      AND o.purchase_ts >= '2018-07-01'
      AND o.purchase_ts < '2018-07-31'
    GROUP BY c.customer_unique_id
)
SELECT f.customer_unique_id, f.historical_orders,
       f.historical_item_value, f.days_since_last_purchase,
       CASE WHEN COALESCE(s.orders_next_30d, 0) > 0 THEN 1 ELSE 0 END AS repeat_next_30d
FROM features f LEFT JOIN subsequent s ON s.customer_unique_id=f.customer_unique_id
ORDER BY f.customer_unique_id;
