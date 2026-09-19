-- ==============================================================================
-- Aura Retail Analytics - 007: Executive Business KPI Scorecard
-- Purpose: Centralized executive macro metrics synthesizing customers,
--          orders, financial revenue, unit margins, and marketing capital efficiency.
-- ==============================================================================

WITH customers_metric_cte AS (
    SELECT 
        COUNT(customer_id) AS total_registered_customers,
        COUNT(DISTINCT state) AS active_states_count
    FROM aura_retail.dim_customers
),
orders_metric_cte AS (
    SELECT 
        COUNT(order_id) AS total_orders_placed,
        COUNT(DISTINCT customer_id) AS active_ordering_customers,
        COUNT(CASE WHEN order_status = 'Delivered' THEN 1 END) AS delivered_orders,
        COUNT(CASE WHEN order_status = 'Returned' THEN 1 END) AS returned_orders,
        COUNT(CASE WHEN order_status = 'Cancelled' THEN 1 END) AS cancelled_orders,
        ROUND(SUM(total_order_amount), 2) AS total_gross_billed_revenue,
        ROUND(SUM(CASE WHEN order_status = 'Delivered' THEN total_order_amount ELSE 0 END), 2) AS total_delivered_revenue,
        ROUND(SUM(CASE WHEN order_status = 'Returned' THEN total_order_amount ELSE 0 END), 2) AS total_returned_revenue,
        ROUND(SUM(CASE WHEN order_status = 'Cancelled' THEN total_order_amount ELSE 0 END), 2) AS total_cancelled_revenue,
        ROUND(SUM(discount_amount), 2) AS total_discounts_granted,
        ROUND(SUM(shipping_cost), 2) AS total_shipping_revenue
    FROM aura_retail.fact_orders
),
items_metric_cte AS (
    SELECT 
        COALESCE(SUM(quantity), 0) AS total_units_sold,
        COUNT(DISTINCT product_id) AS distinct_products_ordered,
        ROUND(SUM(line_total), 2) AS total_order_items_revenue
    FROM aura_retail.fact_order_items
),
products_economic_cte AS (
    SELECT 
        ROUND(SUM(oi.quantity * p.cost_price), 2) AS total_estimated_cogs
    FROM aura_retail.fact_order_items oi
    JOIN aura_retail.dim_products p ON oi.product_id = p.product_id
),
marketing_metric_cte AS (
    SELECT 
        ROUND(SUM(spend_usd), 2) AS total_marketing_spend_usd,
        SUM(impressions) AS total_ad_impressions,
        SUM(clicks) AS total_ad_clicks
    FROM aura_retail.fact_marketing_spend
),
sessions_metric_cte AS (
    SELECT 
        COUNT(session_id) AS total_web_sessions,
        SUM(CASE WHEN cart_abandoned THEN 1 ELSE 0 END) AS total_cart_abandonments,
        SUM(support_tickets) AS total_support_tickets_opened
    FROM aura_retail.fact_web_sessions
)
SELECT 
    -- 1. Customer Volume
    c.total_registered_customers,
    o.active_ordering_customers,
    ROUND(o.active_ordering_customers * 100.0 / NULLIF(c.total_registered_customers, 0), 2) AS customer_penetration_rate_pct,
    c.active_states_count,

    -- 2. Order Funnel
    o.total_orders_placed,
    o.delivered_orders,
    o.returned_orders,
    o.cancelled_orders,
    ROUND(o.delivered_orders * 100.0 / NULLIF(o.total_orders_placed, 0), 2) AS fulfillment_rate_pct,
    ROUND(o.returned_orders * 100.0 / NULLIF(o.total_orders_placed, 0), 2) AS return_rate_pct,
    ROUND(o.cancelled_orders * 100.0 / NULLIF(o.total_orders_placed, 0), 2) AS cancellation_rate_pct,

    -- 3. Merchandise & Basket Economics
    i.total_units_sold,
    i.distinct_products_ordered,
    ROUND(i.total_units_sold::NUMERIC / NULLIF(o.total_orders_placed, 0), 2) AS avg_units_per_order,

    -- 4. Financial Revenue & Economics
    o.total_gross_billed_revenue,
    o.total_delivered_revenue,
    o.total_returned_revenue,
    o.total_cancelled_revenue,
    o.total_discounts_granted,
    o.total_shipping_revenue,
    pe.total_estimated_cogs,
    ROUND(o.total_delivered_revenue - pe.total_estimated_cogs, 2) AS estimated_gross_profit_usd,
    ROUND(
        (o.total_delivered_revenue - pe.total_estimated_cogs) / 
        NULLIF(o.total_delivered_revenue, 0) * 100, 
        2
    ) AS gross_profit_margin_pct,

    -- 5. Customer Unit Economics
    ROUND(o.total_delivered_revenue / NULLIF(o.delivered_orders, 0), 2) AS average_order_value_usd,
    ROUND(o.total_delivered_revenue / NULLIF(c.total_registered_customers, 0), 2) AS arpu_usd,
    ROUND(o.total_delivered_revenue / NULLIF(o.active_ordering_customers, 0), 2) AS arppu_usd,

    -- 6. Marketing Capital Efficiency
    m.total_marketing_spend_usd,
    m.total_ad_impressions,
    m.total_ad_clicks,
    ROUND(m.total_ad_clicks::NUMERIC / NULLIF(m.total_ad_impressions, 0) * 100, 3) AS blended_ctr_pct,
    ROUND(m.total_marketing_spend_usd / NULLIF(m.total_ad_clicks, 0), 2) AS blended_cpc_usd,
    ROUND(m.total_marketing_spend_usd / NULLIF(c.total_registered_customers, 0), 2) AS blended_cac_usd,
    ROUND(o.total_delivered_revenue / NULLIF(m.total_marketing_spend_usd, 0), 2) AS blended_roas,

    -- 7. Digital Engagement & Friction
    s.total_web_sessions,
    s.total_cart_abandonments,
    ROUND(s.total_cart_abandonments * 100.0 / NULLIF(s.total_web_sessions, 0), 2) AS cart_abandonment_rate_pct,
    s.total_support_tickets_opened
FROM customers_metric_cte c
CROSS JOIN orders_metric_cte o
CROSS JOIN items_metric_cte i
CROSS JOIN products_economic_cte pe
CROSS JOIN marketing_metric_cte m
CROSS JOIN sessions_metric_cte s;
