-- Ranked sellers by state and category using completed purchases.
WITH seller_value AS (
    SELECT c.customer_state,
           COALESCE(NULLIF(TRIM(p.product_category_name), ''), 'unknown') AS product_category,
           oi.seller_id,
           SUM(oi.price) AS seller_item_value
    FROM orders o
    JOIN customers c ON c.customer_id=o.customer_id
    JOIN order_items oi ON oi.order_id=o.order_id
    LEFT JOIN products p ON p.product_id=oi.product_id
    WHERE o.order_status='delivered'
    GROUP BY c.customer_state, COALESCE(NULLIF(TRIM(p.product_category_name), ''), 'unknown'), oi.seller_id
), ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_state, product_category
            ORDER BY ROUND(seller_item_value,2) DESC, seller_id
        ) AS seller_rank,
        SUM(seller_item_value) OVER (
            PARTITION BY customer_state, product_category
        ) AS group_item_value
    FROM seller_value
)
SELECT customer_state, product_category, seller_id, seller_rank,
       ROUND(seller_item_value, 2) AS seller_item_value,
       ROUND(100.0 * seller_item_value / NULLIF(group_item_value, 0), 2) AS share_pct
FROM ranked
WHERE seller_rank <= 3
ORDER BY customer_state, product_category, seller_rank;
