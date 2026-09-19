-- ==============================================================================
-- Aura Retail Analytics - 003: Constraints & Foreign Keys
-- Purpose: Apply referential integrity and domain check constraints
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Foreign Keys
-- ------------------------------------------------------------------------------

-- 1. dim_customers -> dim_channels
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_customers_channel') THEN
        ALTER TABLE aura_retail.dim_customers
            ADD CONSTRAINT fk_customers_channel FOREIGN KEY (acquisition_channel_id)
            REFERENCES aura_retail.dim_channels(channel_id);
    END IF;
END $$;

-- 2. fact_orders -> dim_customers
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_orders_customer') THEN
        ALTER TABLE aura_retail.fact_orders
            ADD CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
            REFERENCES aura_retail.dim_customers(customer_id);
    END IF;
END $$;

-- 3. fact_order_items -> fact_orders
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_order_items_order') THEN
        ALTER TABLE aura_retail.fact_order_items
            ADD CONSTRAINT fk_order_items_order FOREIGN KEY (order_id)
            REFERENCES aura_retail.fact_orders(order_id)
            ON DELETE CASCADE;
    END IF;
END $$;

-- 4. fact_order_items -> dim_products
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_order_items_product') THEN
        ALTER TABLE aura_retail.fact_order_items
            ADD CONSTRAINT fk_order_items_product FOREIGN KEY (product_id)
            REFERENCES aura_retail.dim_products(product_id);
    END IF;
END $$;

-- 5. fact_web_sessions -> dim_customers
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_web_sessions_customer') THEN
        ALTER TABLE aura_retail.fact_web_sessions
            ADD CONSTRAINT fk_web_sessions_customer FOREIGN KEY (customer_id)
            REFERENCES aura_retail.dim_customers(customer_id);
    END IF;
END $$;

-- 6. fact_marketing_spend -> dim_channels
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_marketing_spend_channel') THEN
        ALTER TABLE aura_retail.fact_marketing_spend
            ADD CONSTRAINT fk_marketing_spend_channel FOREIGN KEY (channel_id)
            REFERENCES aura_retail.dim_channels(channel_id);
    END IF;
END $$;

-- ------------------------------------------------------------------------------
-- Check Constraints
-- ------------------------------------------------------------------------------

-- Customer age validation
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_customer_age') THEN
        ALTER TABLE aura_retail.dim_customers
            ADD CONSTRAINT chk_customer_age CHECK (age >= 18);
    END IF;
END $$;

-- Product cost and retail pricing economics
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_product_cost') THEN
        ALTER TABLE aura_retail.dim_products
            ADD CONSTRAINT chk_product_cost CHECK (cost_price >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_product_retail') THEN
        ALTER TABLE aura_retail.dim_products
            ADD CONSTRAINT chk_product_retail CHECK (retail_price >= 0);
    END IF;
END $$;

-- Order level monetary values
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_order_shipping') THEN
        ALTER TABLE aura_retail.fact_orders
            ADD CONSTRAINT chk_order_shipping CHECK (shipping_cost >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_order_discount') THEN
        ALTER TABLE aura_retail.fact_orders
            ADD CONSTRAINT chk_order_discount CHECK (discount_amount >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_order_total') THEN
        ALTER TABLE aura_retail.fact_orders
            ADD CONSTRAINT chk_order_total CHECK (total_order_amount >= 0);
    END IF;
END $$;

-- Order item line calculations
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_item_quantity') THEN
        ALTER TABLE aura_retail.fact_order_items
            ADD CONSTRAINT chk_item_quantity CHECK (quantity > 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_item_unit_price') THEN
        ALTER TABLE aura_retail.fact_order_items
            ADD CONSTRAINT chk_item_unit_price CHECK (unit_price >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_item_line_total') THEN
        ALTER TABLE aura_retail.fact_order_items
            ADD CONSTRAINT chk_item_line_total CHECK (line_total >= 0);
    END IF;
END $$;

-- Web sessions engagement values
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_session_page_views') THEN
        ALTER TABLE aura_retail.fact_web_sessions
            ADD CONSTRAINT chk_session_page_views CHECK (page_views >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_session_time_spent') THEN
        ALTER TABLE aura_retail.fact_web_sessions
            ADD CONSTRAINT chk_session_time_spent CHECK (time_spent_seconds >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_session_support_tickets') THEN
        ALTER TABLE aura_retail.fact_web_sessions
            ADD CONSTRAINT chk_session_support_tickets CHECK (support_tickets >= 0);
    END IF;
END $$;

-- Marketing spend impressions and spend values
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_spend_impressions') THEN
        ALTER TABLE aura_retail.fact_marketing_spend
            ADD CONSTRAINT chk_spend_impressions CHECK (impressions >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_spend_clicks') THEN
        ALTER TABLE aura_retail.fact_marketing_spend
            ADD CONSTRAINT chk_spend_clicks CHECK (clicks >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_spend_clicks_le_impressions') THEN
        ALTER TABLE aura_retail.fact_marketing_spend
            ADD CONSTRAINT chk_spend_clicks_le_impressions CHECK (clicks <= impressions);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_spend_usd') THEN
        ALTER TABLE aura_retail.fact_marketing_spend
            ADD CONSTRAINT chk_spend_usd CHECK (spend_usd >= 0);
    END IF;
END $$;
