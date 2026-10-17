-- Q8: reproducible RFM-style descriptive bands as of 2018-09-01.
-- Final delivered status is known retrospectively, not necessarily at purchase time.
-- These are rankings for analysis, NOT deployed customer scores or churn labels.
WITH order_item_value AS (
    SELECT order_id, SUM(price) AS item_value FROM order_items GROUP BY order_id
), customer_history AS (
    SELECT c.customer_unique_id, o.order_id, o.purchase_ts, v.item_value
    FROM orders o
    JOIN customers c ON c.customer_id=o.customer_id
    JOIN order_item_value v ON v.order_id=o.order_id
    WHERE o.order_status='delivered' AND o.purchase_ts < '2018-09-01'
), rfm AS (
    SELECT customer_unique_id,
           CAST(julianday('2018-09-01')-julianday(MAX(DATE(purchase_ts))) AS INT) AS recency_days,
           COUNT(DISTINCT order_id) AS order_frequency,
           SUM(item_value) AS monetary_brl
    FROM customer_history
    GROUP BY customer_unique_id
), ranked AS (
    SELECT customer_unique_id, recency_days, order_frequency, monetary_brl,
           NTILE(4) OVER (ORDER BY recency_days DESC, customer_unique_id) AS r_score,
           NTILE(4) OVER (ORDER BY order_frequency, customer_unique_id) AS f_score,
           NTILE(4) OVER (ORDER BY ROUND(monetary_brl,2), customer_unique_id) AS m_score
    FROM rfm
)
SELECT customer_unique_id, recency_days, order_frequency,
       ROUND(monetary_brl, 2) AS monetary_brl,
       r_score, f_score, m_score,
       CASE WHEN r_score=4 AND f_score>=3 THEN 'recent_and_frequent'
            WHEN r_score=4 THEN 'recent'
            WHEN f_score>=3 THEN 'frequent_historical'
            ELSE 'other_historical' END AS descriptive_segment
FROM ranked
ORDER BY monetary_brl DESC, customer_unique_id;
