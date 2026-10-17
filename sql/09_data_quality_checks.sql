-- Q9: explicit dataset-quality profile. Missing product records are retained in Q1/Q6.
SELECT 'orders_total' AS check_name, COUNT(*) AS observed_count FROM orders
UNION ALL
SELECT 'orders_delivered', COUNT(*) FROM orders WHERE order_status='delivered'
UNION ALL
SELECT 'items_total', COUNT(*) FROM order_items
UNION ALL
SELECT 'items_missing_product_record', COUNT(*)
FROM order_items oi LEFT JOIN products p ON p.product_id=oi.product_id
WHERE p.product_id IS NULL
UNION ALL
SELECT 'items_missing_category', COUNT(*)
FROM order_items oi LEFT JOIN products p ON p.product_id=oi.product_id
WHERE p.product_id IS NULL OR NULLIF(TRIM(p.product_category_name),'') IS NULL
UNION ALL
SELECT 'items_nonpositive_price', COUNT(*) FROM order_items WHERE price <= 0
UNION ALL
SELECT 'orders_missing_purchase_timestamp', COUNT(*) FROM orders
WHERE purchase_ts IS NULL OR TRIM(purchase_ts)=''
UNION ALL
SELECT 'orders_invalid_purchase_timestamp', COUNT(*) FROM orders
WHERE NULLIF(TRIM(purchase_ts),'') IS NOT NULL
  AND (strftime('%Y-%m-%d %H:%M:%S',purchase_ts) IS NULL
       OR strftime('%Y-%m-%d %H:%M:%S',purchase_ts) != purchase_ts)
UNION ALL
SELECT 'orders_without_items', COUNT(*) FROM orders o
WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_id=o.order_id)
UNION ALL
SELECT 'delivered_orders_without_items', COUNT(*) FROM orders o
WHERE o.order_status='delivered'
  AND NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_id=o.order_id)
UNION ALL
SELECT 'items_negative_freight', COUNT(*) FROM order_items WHERE freight_value<0
UNION ALL
SELECT 'customers_missing_unique_id', COUNT(*) FROM customers
WHERE NULLIF(TRIM(customer_unique_id),'') IS NULL
ORDER BY check_name;
