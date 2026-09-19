-- ==============================================================================
-- Aura Retail Analytics - 004: Performance Indexes
-- Purpose: Optimize analytical joins, date partitions, and RFM queries
-- ==============================================================================

-- 1. dim_customers indexes
CREATE INDEX IF NOT EXISTS idx_customers_acq_channel
    ON aura_retail.dim_customers (acquisition_channel_id);

CREATE INDEX IF NOT EXISTS idx_customers_signup_date
    ON aura_retail.dim_customers (signup_date);

-- 2. fact_orders indexes
CREATE INDEX IF NOT EXISTS idx_orders_customer_id
    ON aura_retail.fact_orders (customer_id);

CREATE INDEX IF NOT EXISTS idx_orders_order_date
    ON aura_retail.fact_orders (order_date);

CREATE INDEX IF NOT EXISTS idx_orders_status
    ON aura_retail.fact_orders (order_status);

-- Compound index for RFM recency, cadence, and customer-level order history
CREATE INDEX IF NOT EXISTS idx_orders_cust_date
    ON aura_retail.fact_orders (customer_id, order_date);

-- 3. fact_order_items indexes
CREATE INDEX IF NOT EXISTS idx_order_items_order_id
    ON aura_retail.fact_order_items (order_id);

CREATE INDEX IF NOT EXISTS idx_order_items_product_id
    ON aura_retail.fact_order_items (product_id);

-- 4. fact_web_sessions indexes
CREATE INDEX IF NOT EXISTS idx_web_sessions_customer_id
    ON aura_retail.fact_web_sessions (customer_id);

CREATE INDEX IF NOT EXISTS idx_web_sessions_session_date
    ON aura_retail.fact_web_sessions (session_date);

CREATE INDEX IF NOT EXISTS idx_web_sessions_cust_date
    ON aura_retail.fact_web_sessions (customer_id, session_date);

-- 5. fact_marketing_spend indexes
CREATE INDEX IF NOT EXISTS idx_marketing_spend_channel_date
    ON aura_retail.fact_marketing_spend (channel_id, spend_date);

CREATE INDEX IF NOT EXISTS idx_marketing_spend_date
    ON aura_retail.fact_marketing_spend (spend_date);
