-- ==============================================================================
-- Aura Retail Analytics - 001: Basic Analytics
-- Purpose: Foundational exploratory business queries across orders, customers,
--          products, web sessions, and marketing spend.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. Order Fulfillment Status Distribution
-- ------------------------------------------------------------------------------
SELECT 
    order_status,
    COUNT(*) AS total_orders,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS order_pct,
    ROUND(SUM(total_order_amount), 2) AS total_gross_revenue,
    ROUND(AVG(total_order_amount), 2) AS avg_order_amount
FROM aura_retail.fact_orders
GROUP BY order_status
ORDER BY total_orders DESC;

-- ------------------------------------------------------------------------------
-- 2. Payment Method Popularity and Economics
-- ------------------------------------------------------------------------------
SELECT 
    payment_method,
    COUNT(*) AS order_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS share_of_orders_pct,
    ROUND(SUM(total_order_amount), 2) AS total_billed_amount,
    ROUND(AVG(total_order_amount), 2) AS average_ticket_size,
    ROUND(SUM(discount_amount), 2) AS total_discounts_given
FROM aura_retail.fact_orders
GROUP BY payment_method
ORDER BY order_count DESC;

-- ------------------------------------------------------------------------------
-- 3. Customer Geographic Distribution (Top 10 States & Penetration)
-- ------------------------------------------------------------------------------
SELECT 
    state,
    COUNT(customer_id) AS registered_customers,
    ROUND(COUNT(customer_id) * 100.0 / SUM(COUNT(customer_id)) OVER (), 2) AS customer_share_pct,
    COUNT(DISTINCT city) AS distinct_cities_represented
FROM aura_retail.dim_customers
GROUP BY state
ORDER BY registered_customers DESC
LIMIT 10;

-- ------------------------------------------------------------------------------
-- 4. Product Catalog Pricing & Margin Structure by Category
-- ------------------------------------------------------------------------------
SELECT 
    category,
    COUNT(product_id) AS product_count,
    ROUND(AVG(cost_price), 2) AS avg_cost_price,
    ROUND(AVG(retail_price), 2) AS avg_retail_price,
    ROUND(MIN(retail_price), 2) AS min_retail_price,
    ROUND(MAX(retail_price), 2) AS max_retail_price,
    ROUND(AVG((retail_price - cost_price) / NULLIF(retail_price, 0) * 100), 2) AS avg_margin_pct
FROM aura_retail.dim_products
GROUP BY category
ORDER BY product_count DESC;

-- ------------------------------------------------------------------------------
-- 5. Monthly Order Volume & Delivered Revenue Trend
-- ------------------------------------------------------------------------------
SELECT 
    DATE_TRUNC('month', order_date)::DATE AS order_month,
    COUNT(order_id) AS total_orders,
    COUNT(CASE WHEN order_status = 'Delivered' THEN 1 END) AS delivered_orders,
    ROUND(SUM(total_order_amount), 2) AS gross_revenue,
    ROUND(SUM(CASE WHEN order_status = 'Delivered' THEN total_order_amount ELSE 0 END), 2) AS delivered_net_revenue,
    ROUND(AVG(CASE WHEN order_status = 'Delivered' THEN total_order_amount END), 2) AS delivered_aov
FROM aura_retail.fact_orders
GROUP BY DATE_TRUNC('month', order_date)::DATE
ORDER BY order_month ASC;

-- ------------------------------------------------------------------------------
-- 6. Marketing Channel Traffic & Spend Efficiency Summary
-- ------------------------------------------------------------------------------
SELECT 
    c.channel_name,
    c.channel_type,
    COALESCE(SUM(ms.impressions), 0) AS total_impressions,
    COALESCE(SUM(ms.clicks), 0) AS total_clicks,
    ROUND(
        COALESCE(SUM(ms.clicks), 0)::NUMERIC / NULLIF(SUM(ms.impressions), 0) * 100, 
        3
    ) AS click_through_rate_pct,
    ROUND(COALESCE(SUM(ms.spend_usd), 0), 2) AS total_spend_usd,
    ROUND(
        COALESCE(SUM(ms.spend_usd), 0) / NULLIF(SUM(ms.clicks), 0), 
        2
    ) AS cost_per_click_usd
FROM aura_retail.dim_channels c
LEFT JOIN aura_retail.fact_marketing_spend ms ON c.channel_id = ms.channel_id
GROUP BY c.channel_id, c.channel_name, c.channel_type
ORDER BY total_spend_usd DESC;

-- ------------------------------------------------------------------------------
-- 7. Web Session Engagement & Friction Metrics
-- ------------------------------------------------------------------------------
SELECT 
    DATE_TRUNC('month', session_date)::DATE AS session_month,
    COUNT(session_id) AS total_sessions,
    COUNT(DISTINCT customer_id) AS unique_active_visitors,
    ROUND(AVG(page_views), 2) AS avg_page_views,
    ROUND(AVG(time_spent_seconds), 1) AS avg_duration_seconds,
    SUM(CASE WHEN cart_abandoned THEN 1 ELSE 0 END) AS abandoned_cart_sessions,
    ROUND(SUM(CASE WHEN cart_abandoned THEN 1 ELSE 0 END) * 100.0 / COUNT(session_id), 2) AS cart_abandonment_rate_pct,
    SUM(support_tickets) AS support_tickets_logged
FROM aura_retail.fact_web_sessions
GROUP BY DATE_TRUNC('month', session_date)::DATE
ORDER BY session_month ASC;
