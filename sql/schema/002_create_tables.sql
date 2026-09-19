-- ==============================================================================
-- Aura Retail Analytics - 002: Create Tables
-- Purpose: Define core dimension and fact tables in aura_retail schema
-- ==============================================================================

-- 1. Channels Dimension
CREATE TABLE IF NOT EXISTS aura_retail.dim_channels (
    channel_id      INT PRIMARY KEY,
    channel_name    VARCHAR(50) NOT NULL UNIQUE,
    channel_type    VARCHAR(30) NOT NULL
);

COMMENT ON TABLE aura_retail.dim_channels IS 'Standardized marketing channels and traffic attribution sources';

-- 2. Customers Dimension
CREATE TABLE IF NOT EXISTS aura_retail.dim_customers (
    customer_id             VARCHAR(20) PRIMARY KEY,
    first_name              VARCHAR(50) NOT NULL,
    last_name               VARCHAR(50) NOT NULL,
    email                   VARCHAR(100) NOT NULL UNIQUE,
    signup_date             DATE NOT NULL,
    acquisition_channel_id  INT NOT NULL,
    age                     INT NOT NULL,
    gender                  VARCHAR(20),
    city                    VARCHAR(50) NOT NULL,
    state                   VARCHAR(50) NOT NULL,
    device_preference       VARCHAR(20) NOT NULL
);

COMMENT ON TABLE aura_retail.dim_customers IS 'Customer demographic profiles, registration metadata, and acquisition channel attribution';

-- 3. Products Dimension
CREATE TABLE IF NOT EXISTS aura_retail.dim_products (
    product_id      VARCHAR(20) PRIMARY KEY,
    product_name    VARCHAR(100) NOT NULL,
    category        VARCHAR(50) NOT NULL,
    sub_category    VARCHAR(50) NOT NULL,
    cost_price      NUMERIC(10,2) NOT NULL,
    retail_price    NUMERIC(10,2) NOT NULL
);

COMMENT ON TABLE aura_retail.dim_products IS 'Catalog of retail merchandise with category hierarchy and cost/pricing economics';

-- 4. Orders Fact Table (Header level)
CREATE TABLE IF NOT EXISTS aura_retail.fact_orders (
    order_id            VARCHAR(20) PRIMARY KEY,
    customer_id         VARCHAR(20) NOT NULL,
    order_date          TIMESTAMP NOT NULL,
    order_status        VARCHAR(20) NOT NULL,
    payment_method      VARCHAR(30) NOT NULL,
    shipping_cost       NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    discount_amount     NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    total_order_amount  NUMERIC(10,2) NOT NULL
);

COMMENT ON TABLE aura_retail.fact_orders IS 'Transaction header records including fulfillment status, discounts, and gross revenue';

-- 5. Order Items Fact Table (Line item level)
CREATE TABLE IF NOT EXISTS aura_retail.fact_order_items (
    order_item_id   BIGINT PRIMARY KEY,
    order_id        VARCHAR(20) NOT NULL,
    product_id      VARCHAR(20) NOT NULL,
    quantity        INT NOT NULL,
    unit_price      NUMERIC(10,2) NOT NULL,
    line_total      NUMERIC(10,2) NOT NULL
);

COMMENT ON TABLE aura_retail.fact_order_items IS 'Granular order basket items linking transaction headers to product dimensions';

-- 6. Web Sessions Fact Table
CREATE TABLE IF NOT EXISTS aura_retail.fact_web_sessions (
    session_id          VARCHAR(30) PRIMARY KEY,
    customer_id         VARCHAR(20) NOT NULL,
    session_date        DATE NOT NULL,
    page_views          INT NOT NULL DEFAULT 1,
    time_spent_seconds  INT NOT NULL DEFAULT 0,
    cart_abandoned      BOOLEAN NOT NULL DEFAULT FALSE,
    support_tickets     INT NOT NULL DEFAULT 0
);

COMMENT ON TABLE aura_retail.fact_web_sessions IS 'Customer digital touchpoints, engagement depth, abandoned carts, and support tickets';

-- 7. Marketing Spend Fact Table
CREATE TABLE IF NOT EXISTS aura_retail.fact_marketing_spend (
    spend_id        INT PRIMARY KEY,
    spend_date      DATE NOT NULL,
    channel_id      INT NOT NULL,
    campaign_name   VARCHAR(100) NOT NULL,
    impressions     INT NOT NULL DEFAULT 0,
    clicks          INT NOT NULL DEFAULT 0,
    spend_usd       NUMERIC(10,2) NOT NULL DEFAULT 0.00
);

COMMENT ON TABLE aura_retail.fact_marketing_spend IS 'Daily campaign ad deployment, impressions, clicks, and capital spend for paid channels';
