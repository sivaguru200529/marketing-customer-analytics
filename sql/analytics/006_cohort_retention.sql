-- ==============================================================================
-- Aura Retail Analytics - 006: Customer Cohort & Purchase Retention Matrix
-- Purpose: Longitudinal cohort retention tracking customer order activity
--          relative to initial registration month across the 24-month horizon.
-- Definition:
--   - Cohort Month: Month of initial customer signup (dim_customers.signup_date).
--   - Activity Month: Month when the customer committed an order (fact_orders.order_date).
--   - Months Elapsed: Month-index offset (0 = signup month, 1 = month + 1, ...).
--   - Retention Rate (%): Active ordering customers in activity month / Total customers in cohort.
-- ==============================================================================

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
        -- Calculate exact months elapsed between signup and order
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
    -- Retention rate percentage
    ROUND(
        mca.active_ordering_customers::NUMERIC / NULLIF(cs.cohort_size, 0) * 100, 
        2
    ) AS purchase_retention_rate_pct
FROM monthly_cohort_activity_cte mca
JOIN cohort_sizes_cte cs ON mca.cohort_month = cs.cohort_month
ORDER BY 
    mca.cohort_month ASC, 
    mca.months_since_signup ASC;
