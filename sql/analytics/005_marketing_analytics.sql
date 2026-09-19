-- ==============================================================================
-- Aura Retail Analytics - 005: Marketing & Acquisition Channel Performance
-- Purpose: Channel-level spend, digital ad efficiency (CTR, CPC, CPM),
--          customer acquisition cost (CAC), first-touch attributed revenue,
--          and Return on Ad Spend (ROAS).
-- Attribution Methodology:
--   First-Touch Acquisition Channel Attribution. Revenue is attributed to
--   the channel that originated the customer registration (dim_customers.acquisition_channel_id).
-- ==============================================================================

WITH channel_spend_cte AS (
    SELECT 
        c.channel_id,
        c.channel_name,
        c.channel_type,
        COALESCE(SUM(ms.impressions), 0) AS total_impressions,
        COALESCE(SUM(ms.clicks), 0) AS total_clicks,
        COALESCE(SUM(ms.spend_usd), 0.00) AS total_spend_usd
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
        COALESCE(SUM(o.total_order_amount), 0.00) AS gross_attributed_revenue,
        COALESCE(SUM(CASE WHEN o.order_status = 'Delivered' THEN o.total_order_amount ELSE 0 END), 0.00) AS delivered_attributed_revenue
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
    -- Click-Through Rate (%)
    ROUND(
        cs.total_clicks::NUMERIC / NULLIF(cs.total_impressions, 0) * 100, 
        3
    ) AS ctr_pct,
    -- Cost Per Click ($)
    ROUND(
        cs.total_spend_usd / NULLIF(cs.total_clicks, 0), 
        2
    ) AS cpc_usd,
    -- Cost Per Thousand Impressions (CPM in $)
    ROUND(
        cs.total_spend_usd / NULLIF(cs.total_impressions, 0) * 1000, 
        2
    ) AS cpm_usd,
    COALESCE(cc.acquired_customers, 0) AS acquired_customers,
    -- Customer Acquisition Cost ($)
    ROUND(
        cs.total_spend_usd / NULLIF(cc.acquired_customers, 0), 
        2
    ) AS cac_usd,
    COALESCE(cr.total_attributed_orders, 0) AS total_attributed_orders,
    COALESCE(cr.delivered_attributed_orders, 0) AS delivered_attributed_orders,
    COALESCE(cr.gross_attributed_revenue, 0.00) AS gross_attributed_revenue,
    COALESCE(cr.delivered_attributed_revenue, 0.00) AS delivered_attributed_revenue,
    -- Return on Ad Spend (ROAS = Delivered Attributed Revenue / Marketing Spend)
    -- Applicable only to paid media channels with spend > 0
    ROUND(
        COALESCE(cr.delivered_attributed_revenue, 0.00) / NULLIF(cs.total_spend_usd, 0), 
        2
    ) AS roas,
    -- Revenue Per Acquired Customer (LTV to date)
    ROUND(
        COALESCE(cr.delivered_attributed_revenue, 0.00) / NULLIF(cc.acquired_customers, 0), 
        2
    ) AS revenue_per_acquired_customer
FROM channel_spend_cte cs
LEFT JOIN channel_customers_cte cc ON cs.channel_id = cc.channel_id
LEFT JOIN channel_revenue_cte cr ON cs.channel_id = cr.channel_id
ORDER BY cs.total_spend_usd DESC, delivered_attributed_revenue DESC;
