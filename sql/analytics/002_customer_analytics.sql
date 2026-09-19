-- ==============================================================================
-- Aura Retail Analytics - 002: Customer Analytics & RFM Segmentation
-- Purpose: Detailed customer behavioral profiling, purchase cadence,
--          order disposition, RFM scoring, and cohort segmentation.
-- ==============================================================================

WITH customer_orders_cte AS (
    SELECT 
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        c.email,
        c.signup_date,
        c.acquisition_channel_id,
        ch.channel_name AS acquisition_channel,
        c.city,
        c.state,
        c.device_preference,
        COUNT(o.order_id) AS total_orders,
        COUNT(CASE WHEN o.order_status = 'Delivered' THEN 1 END) AS delivered_orders,
        COUNT(CASE WHEN o.order_status = 'Returned' THEN 1 END) AS returned_orders,
        COUNT(CASE WHEN o.order_status = 'Cancelled' THEN 1 END) AS cancelled_orders,
        COALESCE(SUM(o.total_order_amount), 0.00) AS gross_revenue,
        COALESCE(SUM(CASE WHEN o.order_status = 'Delivered' THEN o.total_order_amount ELSE 0 END), 0.00) AS delivered_revenue,
        COALESCE(SUM(o.discount_amount), 0.00) AS total_discounts_received,
        MIN(o.order_date::DATE) AS first_order_date,
        MAX(o.order_date::DATE) AS last_order_date,
        -- Recency measured relative to the analytical anchor date: 2025-12-31
        -- Customers with 0 orders receive a high sentinel recency penalty (731 days)
        COALESCE(
            DATE '2025-12-31' - MAX(o.order_date::DATE),
            731
        ) AS recency_days
    FROM aura_retail.dim_customers c
    JOIN aura_retail.dim_channels ch ON c.acquisition_channel_id = ch.channel_id
    LEFT JOIN aura_retail.fact_orders o ON c.customer_id = o.customer_id
    GROUP BY 
        c.customer_id, 
        c.first_name, 
        c.last_name, 
        c.email, 
        c.signup_date, 
        c.acquisition_channel_id, 
        ch.channel_name, 
        c.city, 
        c.state, 
        c.device_preference
),
customer_items_cte AS (
    SELECT 
        o.customer_id,
        COALESCE(SUM(oi.quantity), 0) AS total_units_purchased,
        COUNT(DISTINCT oi.product_id) AS distinct_products_bought
    FROM aura_retail.fact_orders o
    JOIN aura_retail.fact_order_items oi ON o.order_id = oi.order_id
    GROUP BY o.customer_id
),
customer_sessions_cte AS (
    SELECT 
        customer_id,
        COUNT(session_id) AS total_web_sessions,
        COALESCE(SUM(page_views), 0) AS total_page_views,
        COALESCE(SUM(time_spent_seconds), 0) AS total_time_spent_seconds,
        SUM(CASE WHEN cart_abandoned THEN 1 ELSE 0 END) AS total_abandoned_carts,
        COALESCE(SUM(support_tickets), 0) AS total_support_tickets
    FROM aura_retail.fact_web_sessions
    GROUP BY customer_id
),
rfm_base_cte AS (
    SELECT 
        co.*,
        COALESCE(ci.total_units_purchased, 0) AS total_units_purchased,
        COALESCE(ci.distinct_products_bought, 0) AS distinct_products_bought,
        COALESCE(cs.total_web_sessions, 0) AS total_web_sessions,
        COALESCE(cs.total_page_views, 0) AS total_page_views,
        COALESCE(cs.total_time_spent_seconds, 0) AS total_time_spent_seconds,
        COALESCE(cs.total_abandoned_carts, 0) AS total_abandoned_carts,
        COALESCE(cs.total_support_tickets, 0) AS total_support_tickets,
        ROUND(
            co.delivered_revenue / NULLIF(co.delivered_orders, 0), 
            2
        ) AS delivered_aov
    FROM customer_orders_cte co
    LEFT JOIN customer_items_cte ci ON co.customer_id = ci.customer_id
    LEFT JOIN customer_sessions_cte cs ON co.customer_id = cs.customer_id
),
rfm_scored_cte AS (
    SELECT 
        *,
        -- R_Score: 5 = lowest recency days (bought very recently), 1 = highest recency days (bought long ago)
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        -- F_Score: 5 = highest delivered order count, 1 = lowest
        NTILE(5) OVER (ORDER BY delivered_orders ASC) AS f_score,
        -- M_Score: 5 = highest delivered revenue, 1 = lowest
        NTILE(5) OVER (ORDER BY delivered_revenue ASC) AS m_score,
        -- Rank customers overall by delivered revenue
        DENSE_RANK() OVER (ORDER BY delivered_revenue DESC) AS revenue_rank
    FROM rfm_base_cte
)
SELECT 
    customer_id,
    customer_name,
    email,
    signup_date,
    acquisition_channel,
    city,
    state,
    device_preference,
    total_orders,
    delivered_orders,
    returned_orders,
    cancelled_orders,
    total_units_purchased,
    gross_revenue,
    delivered_revenue,
    delivered_aov,
    first_order_date,
    last_order_date,
    recency_days,
    total_web_sessions,
    total_abandoned_carts,
    total_support_tickets,
    r_score,
    f_score,
    m_score,
    revenue_rank,
    -- Standardized RFM Segmentation Logic
    CASE 
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'Recent Inquirers'
        WHEN r_score >= 3 AND f_score <= 2 AND m_score >= 3 THEN 'Promising'
        WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 THEN 'At Risk High Value'
        WHEN r_score <= 2 AND f_score >= 2 THEN 'Need Attention'
        WHEN r_score = 1 AND f_score = 1 THEN 'Lost / Dormant'
        ELSE 'Potential / Developing'
    END AS rfm_segment
FROM rfm_scored_cte
ORDER BY delivered_revenue DESC;
