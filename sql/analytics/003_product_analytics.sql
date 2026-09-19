-- ==============================================================================
-- Aura Retail Analytics - 003: Product Performance & Category Economics
-- Purpose: Sales volume, gross revenue, COGS, margin profitability,
--          and intra-category performance rankings.
-- ==============================================================================

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
        COALESCE(SUM(oi.line_total), 0.00) AS gross_revenue,
        COALESCE(SUM(oi.quantity * p.cost_price), 0.00) AS total_cogs
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
        (gross_revenue - total_cogs) AS estimated_gross_profit,
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
        -- Rank products within their category by gross revenue
        DENSE_RANK() OVER (
            PARTITION BY category 
            ORDER BY gross_revenue DESC
        ) AS category_revenue_rank,
        -- Overall product revenue rank across the entire catalog
        DENSE_RANK() OVER (
            ORDER BY gross_revenue DESC
        ) AS overall_revenue_rank,
        -- Category total revenue for share-of-category calculation
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
FROM product_ranked_cte
ORDER BY gross_revenue DESC;
