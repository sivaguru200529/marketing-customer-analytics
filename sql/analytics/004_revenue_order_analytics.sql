-- ==============================================================================
-- Aura Retail Analytics - 004: Revenue & Order Analytics
-- Purpose: Time-series revenue trends, Month-over-Month (MoM) growth calculations,
--          running cumulative revenue, and order basket economics.
-- ==============================================================================

WITH monthly_orders_cte AS (
    SELECT 
        DATE_TRUNC('month', order_date)::DATE AS order_month,
        COUNT(order_id) AS total_orders_placed,
        COUNT(CASE WHEN order_status = 'Delivered' THEN 1 END) AS delivered_orders,
        COUNT(CASE WHEN order_status = 'Returned' THEN 1 END) AS returned_orders,
        COUNT(CASE WHEN order_status = 'Cancelled' THEN 1 END) AS cancelled_orders,
        -- Gross billed revenue across all placed orders
        ROUND(SUM(total_order_amount), 2) AS gross_billed_revenue,
        -- Net realized revenue strictly from fulfilled, delivered orders
        ROUND(SUM(CASE WHEN order_status = 'Delivered' THEN total_order_amount ELSE 0 END), 2) AS delivered_revenue,
        -- Revenue impact of returns and cancellations
        ROUND(SUM(CASE WHEN order_status = 'Returned' THEN total_order_amount ELSE 0 END), 2) AS returned_revenue,
        ROUND(SUM(CASE WHEN order_status = 'Cancelled' THEN total_order_amount ELSE 0 END), 2) AS cancelled_revenue,
        ROUND(SUM(discount_amount), 2) AS total_discounts_granted,
        ROUND(SUM(shipping_cost), 2) AS total_shipping_revenue,
        -- Delivered AOV
        ROUND(
            SUM(CASE WHEN order_status = 'Delivered' THEN total_order_amount ELSE 0 END) / 
            NULLIF(COUNT(CASE WHEN order_status = 'Delivered' THEN 1 END), 0), 
            2
        ) AS delivered_aov
    FROM aura_retail.fact_orders
    GROUP BY DATE_TRUNC('month', order_date)::DATE
),
monthly_window_cte AS (
    SELECT 
        *,
        -- Prior month delivered revenue via LAG() window function
        LAG(delivered_revenue, 1) OVER (
            ORDER BY order_month ASC
        ) AS prev_month_delivered_revenue,
        -- Prior month order volume
        LAG(delivered_orders, 1) OVER (
            ORDER BY order_month ASC
        ) AS prev_month_delivered_orders,
        -- Cumulative running revenue across the entire 2-year timeline
        SUM(delivered_revenue) OVER (
            ORDER BY order_month ASC 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_delivered_revenue,
        -- Cumulative delivered order count
        SUM(delivered_orders) OVER (
            ORDER BY order_month ASC 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_delivered_orders
    FROM monthly_orders_cte
)
SELECT 
    order_month,
    total_orders_placed,
    delivered_orders,
    returned_orders,
    cancelled_orders,
    gross_billed_revenue,
    delivered_revenue,
    returned_revenue,
    cancelled_revenue,
    total_discounts_granted,
    total_shipping_revenue,
    delivered_aov,
    prev_month_delivered_revenue,
    -- Month-over-Month (MoM) dollar variance
    ROUND(
        (delivered_revenue - prev_month_delivered_revenue), 
        2
    ) AS mom_revenue_change,
    -- Month-over-Month (MoM) growth percentage (safe against NULL on Month 1)
    ROUND(
        (delivered_revenue - prev_month_delivered_revenue) / 
        NULLIF(prev_month_delivered_revenue, 0) * 100, 
        2
    ) AS mom_revenue_growth_pct,
    -- MoM Delivered Orders growth %
    ROUND(
        (delivered_orders - prev_month_delivered_orders)::NUMERIC / 
        NULLIF(prev_month_delivered_orders, 0) * 100, 
        2
    ) AS mom_order_growth_pct,
    cumulative_delivered_revenue,
    cumulative_delivered_orders
FROM monthly_window_cte
ORDER BY order_month ASC;
