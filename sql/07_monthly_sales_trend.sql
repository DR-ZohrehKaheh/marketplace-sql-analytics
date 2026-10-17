-- Q7: monthly historical purchasing activity, grouped on purchase month.
-- Item value excludes freight; item count and order count have different grains.
SELECT SUBSTR(o.purchase_ts, 1, 7) AS purchase_month,
       COUNT(DISTINCT o.order_id) AS delivered_orders,
       COUNT(DISTINCT c.customer_unique_id) AS observed_customers,
       COUNT(*) AS sold_item_rows,
       ROUND(SUM(oi.price), 2) AS item_value_brl,
       ROUND(SUM(oi.price)/NULLIF(COUNT(DISTINCT o.order_id),0),2)
           AS avg_item_value_per_delivered_order_brl
FROM orders o
JOIN customers c ON c.customer_id=o.customer_id
JOIN order_items oi ON oi.order_id=o.order_id
WHERE o.order_status='delivered' AND o.purchase_ts IS NOT NULL
GROUP BY SUBSTR(o.purchase_ts, 1, 7)
ORDER BY purchase_month;
