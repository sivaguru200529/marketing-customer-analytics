-- ==============================================================================
-- Aura Retail Analytics - 008: Production Analytical Views for Phase 4 Export
-- Purpose: Standardized, tested analytical views created inside the aura_retail
--          schema for direct consumption by Phase 4 Python ML pipelines and Power BI.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. View: Customer Analytics & RFM Profiling
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW aura_retail.view_customer_analytics AS
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
        ROUND(COALESCE(SUM(o.total_order_amount), 0.00), 2) AS gross_revenue,
        ROUND(COALESCE(SUM(CASE WHEN o.order_status = 'Delivered' THEN o.total_order_amount ELSE 0 END), 0.00), 2) AS delivered_revenue,
        ROUND(COALESCE(SUM(o.discount_amount), 0.00), 2) AS total_discounts_received,
        MIN(o.order_date::DATE) AS first_order_date,
        MAX(o.order_date::DATE) AS last_order_date,
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
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY delivered_orders ASC) AS f_score,
        NTILE(5) OVER (ORDER BY delivered_revenue ASC) AS m_score,
        DENSE_RANK() OVER (ORDER BY delivered_revenue DESC) AS revenue_rank
    FROM rfm_base_cte
)
SELECT 
    customer_id,
    customer_name,
    email,
    signup_date,
    acquisition_channel_id,
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
FROM rfm_scored_cte;

COMMENT ON VIEW aura_retail.view_customer_analytics IS 'Customer metrics, purchase history, web interactions, RFM scores, and segment labels';

-- ------------------------------------------------------------------------------
-- 2. View: Product & Category Analytics
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW aura_retail.view_product_analytics AS
WITH product_sales_cte AS (
    SELECT 
        p.product_id,
        p.product_name,
        p.category,
        p.sub_category,
        p.cost_price,
        p.retail_price,
        COUNT(DISTINCT oi.order_id) AS distinct_orders_count,
        COALESCE(SUM(oi.quantity), 0) AS units_sold,
        ROUND(COALESCE(SUM(oi.line_total), 0.00), 2) AS gross_revenue,
        ROUND(COALESCE(SUM(oi.quantity * p.cost_price), 0.00), 2) AS total_cogs
    FROM aura_retail.dim_products p
    LEFT JOIN aura_retail.fact_order_items oi ON p.product_id = oi.product_id
    GROUP BY 
        p.product_id, 
        p.product_name, 
        p.category, 
        p.sub_category, 
        p.cost_price, 
        p.retail_price
),
product_profitability_cte AS (
    SELECT 
        *,
        ROUND(gross_revenue - total_cogs, 2) AS estimated_gross_profit,
        ROUND(
            (gross_revenue - total_cogs) / NULLIF(gross_revenue, 0) * 100, 
            2
        ) AS gross_margin_pct,
        ROUND(
            gross_revenue / NULLIF(units_sold, 0), 
            2
        ) AS avg_realized_price
    FROM product_sales_cte
),
product_ranked_cte AS (
    SELECT 
        *,
        DENSE_RANK() OVER (
            PARTITION BY category 
            ORDER BY gross_revenue DESC
        ) AS category_revenue_rank,
        DENSE_RANK() OVER (
            ORDER BY gross_revenue DESC
        ) AS overall_revenue_rank,
        SUM(gross_revenue) OVER (
            PARTITION BY category
        ) AS category_total_revenue
    FROM product_profitability_cte
)
SELECT 
    product_id,
    product_name,
    category,
    sub_category,
    cost_price,
    retail_price,
    units_sold,
    distinct_orders_count,
    gross_revenue,
    total_cogs,
    estimated_gross_profit,
    gross_margin_pct,
    avg_realized_price,
    category_revenue_rank,
    overall_revenue_rank,
    ROUND(
        gross_revenue / NULLIF(category_total_revenue, 0) * 100, 
        2
    ) AS category_revenue_share_pct
FROM product_ranked_cte;

COMMENT ON VIEW aura_retail.view_product_analytics IS 'Product sales volumes, retail revenues, unit COGS, margin economics, and category rankings';

-- ------------------------------------------------------------------------------
-- 3. View: Monthly Revenue Trends & Growth Analytics
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW aura_retail.view_monthly_revenue AS
WITH monthly_orders_cte AS (
    SELECT 
        DATE_TRUNC('month', order_date)::DATE AS order_month,
        COUNT(order_id) AS total_orders_placed,
        COUNT(CASE WHEN order_status = 'Delivered' THEN 1 END) AS delivered_orders,
        COUNT(CASE WHEN order_status = 'Returned' THEN 1 END) AS returned_orders,
        COUNT(CASE WHEN order_status = 'Cancelled' THEN 1 END) AS cancelled_orders,
        ROUND(SUM(total_order_amount), 2) AS gross_billed_revenue,
        ROUND(SUM(CASE WHEN order_status = 'Delivered' THEN total_order_amount ELSE 0 END), 2) AS delivered_revenue,
        ROUND(SUM(CASE WHEN order_status = 'Returned' THEN total_order_amount ELSE 0 END), 2) AS returned_revenue,
        ROUND(SUM(CASE WHEN order_status = 'Cancelled' THEN total_order_amount ELSE 0 END), 2) AS cancelled_revenue,
        ROUND(SUM(discount_amount), 2) AS total_discounts_granted,
        ROUND(SUM(shipping_cost), 2) AS total_shipping_revenue,
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
        LAG(delivered_revenue, 1) OVER (
            ORDER BY order_month ASC
        ) AS prev_month_delivered_revenue,
        LAG(delivered_orders, 1) OVER (
            ORDER BY order_month ASC
        ) AS prev_month_delivered_orders,
        SUM(delivered_revenue) OVER (
            ORDER BY order_month ASC 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_delivered_revenue,
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
    ROUND((delivered_revenue - prev_month_delivered_revenue), 2) AS mom_revenue_change,
    ROUND(
        (delivered_revenue - prev_month_delivered_revenue) / 
        NULLIF(prev_month_delivered_revenue, 0) * 100, 
        2
    ) AS mom_revenue_growth_pct,
    ROUND(
        (delivered_orders - prev_month_delivered_orders)::NUMERIC / 
        NULLIF(prev_month_delivered_orders, 0) * 100, 
        2
    ) AS mom_order_growth_pct,
    cumulative_delivered_revenue,
    cumulative_delivered_orders
FROM monthly_window_cte;

COMMENT ON VIEW aura_retail.view_monthly_revenue IS 'Monthly gross/net revenues, fulfillment status volume, MoM growth rates, and cumulative sales';

-- ------------------------------------------------------------------------------
-- 4. View: Marketing Channel Performance & Attribution
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW aura_retail.view_marketing_performance AS
WITH channel_spend_cte AS (
    SELECT 
        c.channel_id,
        c.channel_name,
        c.channel_type,
        COALESCE(SUM(ms.impressions), 0) AS total_impressions,
        COALESCE(SUM(ms.clicks), 0) AS total_clicks,
        ROUND(COALESCE(SUM(ms.spend_usd), 0.00), 2) AS total_spend_usd
    FROM aura_retail.dim_channels c
    LEFT JOIN aura_retail.fact_marketing_spend ms ON c.channel_id = ms.channel_id
    GROUP BY c.channel_id, c.channel_name, c.channel_type
),
channel_customers_cte AS (
    SELECT 
        acquisition_channel_id AS channel_id,
        COUNT(customer_id) AS acquired_customers
    FROM aura_retail.dim_customers
    GROUP BY acquisition_channel_id
),
channel_revenue_cte AS (
    SELECT 
        c.acquisition_channel_id AS channel_id,
        COUNT(DISTINCT o.order_id) AS total_attributed_orders,
        COUNT(DISTINCT CASE WHEN o.order_status = 'Delivered' THEN o.order_id END) AS delivered_attributed_orders,
        ROUND(COALESCE(SUM(o.total_order_amount), 0.00), 2) AS gross_attributed_revenue,
        ROUND(COALESCE(SUM(CASE WHEN o.order_status = 'Delivered' THEN o.total_order_amount ELSE 0 END), 0.00), 2) AS delivered_attributed_revenue
    FROM aura_retail.dim_customers c
    JOIN aura_retail.fact_orders o ON c.customer_id = o.customer_id
    GROUP BY c.acquisition_channel_id
)
SELECT 
    cs.channel_id,
    cs.channel_name,
    cs.channel_type,
    cs.total_spend_usd,
    cs.total_impressions,
    cs.total_clicks,
    ROUND(cs.total_clicks::NUMERIC / NULLIF(cs.total_impressions, 0) * 100, 3) AS ctr_pct,
    ROUND(cs.total_spend_usd / NULLIF(cs.total_clicks, 0), 2) AS cpc_usd,
    ROUND(cs.total_spend_usd / NULLIF(cs.total_impressions, 0) * 1000, 2) AS cpm_usd,
    COALESCE(cc.acquired_customers, 0) AS acquired_customers,
    ROUND(cs.total_spend_usd / NULLIF(cc.acquired_customers, 0), 2) AS cac_usd,
    COALESCE(cr.total_attributed_orders, 0) AS total_attributed_orders,
    COALESCE(cr.delivered_attributed_orders, 0) AS delivered_attributed_orders,
    COALESCE(cr.gross_attributed_revenue, 0.00) AS gross_attributed_revenue,
    COALESCE(cr.delivered_attributed_revenue, 0.00) AS delivered_attributed_revenue,
    ROUND(
        COALESCE(cr.delivered_attributed_revenue, 0.00) / NULLIF(cs.total_spend_usd, 0), 
        2
    ) AS roas,
    ROUND(
        COALESCE(cr.delivered_attributed_revenue, 0.00) / NULLIF(cc.acquired_customers, 0), 
        2
    ) AS revenue_per_acquired_customer
FROM channel_spend_cte cs
LEFT JOIN channel_customers_cte cc ON cs.channel_id = cc.channel_id
LEFT JOIN channel_revenue_cte cr ON cs.channel_id = cr.channel_id;

COMMENT ON VIEW aura_retail.view_marketing_performance IS 'Channel ad impressions, clicks, spend, CTR, CPC, CAC, first-touch attributed revenue, and ROAS';

-- ------------------------------------------------------------------------------
-- 5. View: Customer Cohort Purchase Retention Matrix
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW aura_retail.view_cohort_retention AS
WITH customer_cohort_cte AS (
    SELECT 
        customer_id,
        DATE_TRUNC('month', signup_date)::DATE AS cohort_month
    FROM aura_retail.dim_customers
),
cohort_sizes_cte AS (
    SELECT 
        cohort_month,
        COUNT(customer_id) AS cohort_size
    FROM customer_cohort_cte
    GROUP BY cohort_month
),
customer_activity_cte AS (
    SELECT DISTINCT
        o.customer_id,
        cc.cohort_month,
        DATE_TRUNC('month', o.order_date)::DATE AS activity_month,
        (
            (EXTRACT(YEAR FROM o.order_date) - EXTRACT(YEAR FROM cc.cohort_month)) * 12 + 
            (EXTRACT(MONTH FROM o.order_date) - EXTRACT(MONTH FROM cc.cohort_month))
        )::INT AS months_since_signup
    FROM aura_retail.fact_orders o
    JOIN customer_cohort_cte cc ON o.customer_id = cc.customer_id
),
monthly_cohort_activity_cte AS (
    SELECT 
        ca.cohort_month,
        ca.activity_month,
        ca.months_since_signup,
        COUNT(DISTINCT ca.customer_id) AS active_ordering_customers
    FROM customer_activity_cte ca
    GROUP BY 
        ca.cohort_month, 
        ca.activity_month, 
        ca.months_since_signup
)
SELECT 
    mca.cohort_month,
    cs.cohort_size,
    mca.activity_month,
    mca.months_since_signup,
    mca.active_ordering_customers,
    ROUND(
        mca.active_ordering_customers::NUMERIC / NULLIF(cs.cohort_size, 0) * 100, 
        2
    ) AS purchase_retention_rate_pct
FROM monthly_cohort_activity_cte mca
JOIN cohort_sizes_cte cs ON mca.cohort_month = cs.cohort_month;

COMMENT ON VIEW aura_retail.view_cohort_retention IS '24-month customer signup cohort purchase retention matrix and activity rates';

-- ------------------------------------------------------------------------------
-- 6. View: Executive Business KPIs Scorecard
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW aura_retail.view_business_kpis AS
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
    c.total_registered_customers,
    o.active_ordering_customers,
    ROUND(o.active_ordering_customers * 100.0 / NULLIF(c.total_registered_customers, 0), 2) AS customer_penetration_rate_pct,
    c.active_states_count,
    o.total_orders_placed,
    o.delivered_orders,
    o.returned_orders,
    o.cancelled_orders,
    ROUND(o.delivered_orders * 100.0 / NULLIF(o.total_orders_placed, 0), 2) AS fulfillment_rate_pct,
    ROUND(o.returned_orders * 100.0 / NULLIF(o.total_orders_placed, 0), 2) AS return_rate_pct,
    ROUND(o.cancelled_orders * 100.0 / NULLIF(o.total_orders_placed, 0), 2) AS cancellation_rate_pct,
    i.total_units_sold,
    i.distinct_products_ordered,
    ROUND(i.total_units_sold::NUMERIC / NULLIF(o.total_orders_placed, 0), 2) AS avg_units_per_order,
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
    ROUND(o.total_delivered_revenue / NULLIF(o.delivered_orders, 0), 2) AS average_order_value_usd,
    ROUND(o.total_delivered_revenue / NULLIF(c.total_registered_customers, 0), 2) AS arpu_usd,
    ROUND(o.total_delivered_revenue / NULLIF(o.active_ordering_customers, 0), 2) AS arppu_usd,
    m.total_marketing_spend_usd,
    m.total_ad_impressions,
    m.total_ad_clicks,
    ROUND(m.total_ad_clicks::NUMERIC / NULLIF(m.total_ad_impressions, 0) * 100, 3) AS blended_ctr_pct,
    ROUND(m.total_marketing_spend_usd / NULLIF(m.total_ad_clicks, 0), 2) AS blended_cpc_usd,
    ROUND(m.total_marketing_spend_usd / NULLIF(c.total_registered_customers, 0), 2) AS blended_cac_usd,
    ROUND(o.total_delivered_revenue / NULLIF(m.total_marketing_spend_usd, 0), 2) AS blended_roas,
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

COMMENT ON VIEW aura_retail.view_business_kpis IS 'Central executive macro metrics: volumes, revenues, gross margin, unit economics, and marketing efficiency';
