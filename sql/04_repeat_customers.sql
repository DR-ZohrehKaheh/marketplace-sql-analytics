-- Repeat customer share among identifiable observed DELIVERED orders.
-- Multiple customer_id values may map to one customer_unique_id in Olist.
WITH purchases AS (
    SELECT c.customer_unique_id, o.order_id, date(o.purchase_ts) AS order_date,
           ROW_NUMBER() OVER (
               PARTITION BY c.customer_unique_id
               ORDER BY o.purchase_ts, o.order_id
           ) AS purchase_number
    FROM orders o
    JOIN customers c ON c.customer_id=o.customer_id
    WHERE o.order_status='delivered' AND NULLIF(TRIM(c.customer_unique_id),'') IS NOT NULL
), customer_counts AS (
    SELECT customer_unique_id, COUNT(*) AS order_count, MAX(purchase_number) AS latest_order_index
    FROM purchases
    GROUP BY customer_unique_id
)
SELECT COUNT(*) AS observed_customers,
       COALESCE(SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END),0) AS repeat_customers,
       ROUND(100.0 * SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END)
             / NULLIF(COUNT(*), 0), 2) AS repeat_customer_pct
FROM customer_counts;
