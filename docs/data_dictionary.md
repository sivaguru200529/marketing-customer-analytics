# Data Dictionary: Aura Retail Analytics Platform

This document describes the schema, tables, columns, constraints, and definitions used across the Aura Retail relational database and analytical marts.

---

## 1. Dimensional Tables

### `dim_channels`
Stores marketing acquisition channels and traffic sources.

| Column Name | Data Type | Constraint | Description | Example Values |
| :--- | :--- | :--- | :--- | :--- |
| `channel_id` | `INT` / `SERIAL` | `PRIMARY KEY` | Unique identifier for the marketing channel | `1`, `2`, `3` |
| `channel_name` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Standardized channel name | `'Paid Search'`, `'Organic Search'`, `'Paid Social'` |
| `channel_type` | `VARCHAR(30)` | `NOT NULL` | High-level channel classification | `'Paid'`, `'Organic'`, `'Owned'`, `'Referral'` |

---

### `dim_customers`
Stores demographic and acquisition attributes for registered customers.

| Column Name | Data Type | Constraint | Description | Example Values |
| :--- | :--- | :--- | :--- | :--- |
| `customer_id` | `VARCHAR(20)` | `PRIMARY KEY` | Unique business key for the customer | `'CUST_00001'`, `'CUST_09412'` |
| `first_name` | `VARCHAR(50)` | `NOT NULL` | Customer given name | `'Sarah'`, `'David'` |
| `last_name` | `VARCHAR(50)` | `NOT NULL` | Customer surname | `'Jenkins'`, `'Alvarez'` |
| `email` | `VARCHAR(100)` | `NOT NULL, UNIQUE` | Customer contact email address | `'sarah.j@example.com'` |
| `signup_date` | `DATE` | `NOT NULL` | Registration timestamp | `'2024-03-15'` |
| `acquisition_channel_id` | `INT` | `FOREIGN KEY (dim_channels)` | Channel attributed for customer creation | `1`, `3` |
| `age` | `INT` | `CHECK (age >= 18)` | Customer age in years | `32`, `45` |
| `gender` | `VARCHAR(20)` | `NULLABLE` | Customer self-reported gender | `'Female'`, `'Male'`, `'Non-binary'` |
| `city` | `VARCHAR(50)` | `NOT NULL` | Residence city | `'Chicago'`, `'Austin'` |
| `state` | `VARCHAR(50)` | `NOT NULL` | Residence state or province code | `'IL'`, `'TX'`, `'CA'` |
| `device_preference` | `VARCHAR(20)` | `NOT NULL` | Primary platform used | `'Mobile'`, `'Desktop'`, `'Tablet'` |

---

### `dim_products`
Catalog of merchandise sold on the Aura Retail platform.

| Column Name | Data Type | Constraint | Description | Example Values |
| :--- | :--- | :--- | :--- | :--- |
| `product_id` | `VARCHAR(20)` | `PRIMARY KEY` | Unique product stock identifier | `'PROD_001'`, `'PROD_142'` |
| `product_name` | `VARCHAR(100)` | `NOT NULL` | Public merchandise title | `'Minimalist Linen Duvet Set'` |
| `category` | `VARCHAR(50)` | `NOT NULL` | Top-level retail category | `'Home Goods'`, `'Apparel'`, `'Accessories'` |
| `sub_category` | `VARCHAR(50)` | `NOT NULL` | Granular department classification | `'Bedding'`, `'Outerwear'`, `'Footwear'` |
| `cost_price` | `NUMERIC(10,2)` | `NOT NULL, CHECK (cost_price >= 0)` | Cost of goods sold (COGS) in USD | `34.50`, `12.00` |
| `retail_price` | `NUMERIC(10,2)` | `NOT NULL, CHECK (retail_price >= cost_price)` | Manufacturer's retail price in USD | `89.00`, `28.00` |

---

## 2. Fact Tables

### `fact_marketing_spend`
Daily aggregated marketing campaign spend, impressions, and engagement metrics.

| Column Name | Data Type | Constraint | Description | Example Values |
| :--- | :--- | :--- | :--- | :--- |
| `spend_id` | `INT` / `SERIAL` | `PRIMARY KEY` | Unique record identifier | `1001`, `1002` |
| `spend_date` | `DATE` | `NOT NULL` | Date of marketing ad delivery | `'2024-05-01'` |
| `channel_id` | `INT` | `FOREIGN KEY (dim_channels)` | Reference to marketing channel | `2` |
| `campaign_name` | `VARCHAR(100)` | `NOT NULL` | Strategic campaign tag | `'Summer_Essentials_Search_Q2'` |
| `impressions` | `INT` | `DEFAULT 0, CHECK (impressions >= 0)` | Ad views served | `45200` |
| `clicks` | `INT` | `DEFAULT 0, CHECK (clicks >= 0)` | Inbound link clicks generated | `1320` |
| `spend_usd` | `NUMERIC(10,2)` | `NOT NULL, CHECK (spend_usd >= 0)` | Total capital deployed for day in USD | `784.50` |

---

### `fact_orders`
Header-level transactional order logs.

| Column Name | Data Type | Constraint | Description | Example Values |
| :--- | :--- | :--- | :--- | :--- |
| `order_id` | `VARCHAR(20)` | `PRIMARY KEY` | Unique transaction order number | `'ORD_2024_0001'` |
| `customer_id` | `VARCHAR(20)` | `FOREIGN KEY (dim_customers)` | Customer placing the order | `'CUST_00001'` |
| `order_date` | `TIMESTAMP` | `NOT NULL` | Date and time order was committed | `'2024-04-12 14:32:00'` |
| `order_status` | `VARCHAR(20)` | `NOT NULL` | Fulfillment state | `'Delivered'`, `'Returned'`, `'Cancelled'` |
| `payment_method` | `VARCHAR(30)` | `NOT NULL` | Payment tender utilized | `'Credit Card'`, `'PayPal'`, `'Apple Pay'` |
| `shipping_cost` | `NUMERIC(10,2)` | `DEFAULT 0.00` | Shipping charged to customer in USD | `0.00`, `9.99` |
| `discount_amount` | `NUMERIC(10,2)` | `DEFAULT 0.00` | Dollar discount deducted from order | `15.00`, `0.00` |
| `total_order_amount` | `NUMERIC(10,2)` | `NOT NULL` | Final gross billed amount | `142.50` |

---

### `fact_order_items`
Granular line items contained within each transaction order.

| Column Name | Data Type | Constraint | Description | Example Values |
| :--- | :--- | :--- | :--- | :--- |
| `order_item_id` | `INT` / `SERIAL` | `PRIMARY KEY` | Unique line item identifier | `50001` |
| `order_id` | `VARCHAR(20)` | `FOREIGN KEY (fact_orders)` | Parent order reference | `'ORD_2024_0001'` |
| `product_id` | `VARCHAR(20)` | `FOREIGN KEY (dim_products)` | Merchandise item purchased | `'PROD_045'` |
| `quantity` | `INT` | `NOT NULL, CHECK (quantity > 0)` | Units purchased | `1`, `2`, `4` |
| `unit_price` | `NUMERIC(10,2)` | `NOT NULL` | Transacted unit price in USD | `45.00` |
| `line_total` | `NUMERIC(10,2)` | `NOT NULL` | Calculated as `quantity * unit_price` | `90.00` |

---

### `fact_web_sessions`
Customer digital touchpoints, browsing activity, and customer service interactions.

| Column Name | Data Type | Constraint | Description | Example Values |
| :--- | :--- | :--- | :--- | :--- |
| `session_id` | `VARCHAR(30)` | `PRIMARY KEY` | Unique web browsing session ID | `'SESS_2024_001294'` |
| `customer_id` | `VARCHAR(20)` | `FOREIGN KEY (dim_customers)` | Authenticated customer reference | `'CUST_00001'` |
| `session_date` | `DATE` | `NOT NULL` | Session start date | `'2024-06-18'` |
| `page_views` | `INT` | `DEFAULT 1` | Pages navigated in session | `6`, `14` |
| `time_spent_seconds` | `INT` | `DEFAULT 0` | Total session duration in seconds | `420` |
| `cart_abandoned` | `BOOLEAN` | `DEFAULT FALSE` | True if item added to cart but not purchased | `TRUE`, `FALSE` |
| `support_tickets` | `INT` | `DEFAULT 0` | Customer support cases logged during session | `0`, `1` |

---

## 3. Feature Store / Analytical Mart Columns

For ML modeling and Power BI reporting, the dimensional views aggregate metrics into:

| Column Name | Source / Calculation | Purpose |
| :--- | :--- | :--- |
| `recency_days` | Days from last order to anchor date `2025-12-31` | RFM Scoring & Churn Feature |
| `order_frequency` | Count of distinct delivered orders | RFM Scoring & Churn Feature |
| `monetary_spend` | Net sum of delivered order totals | RFM Scoring & Churn Feature |
| `avg_order_value` | `monetary_spend / order_frequency` | K-Means Clustering Feature |
| `discount_ratio` | Discounted orders divided by total orders | Discount Sensitivity Profiling |
| `return_rate` | Returned orders divided by total orders | Quality / Dissatisfaction Indicator |
| `is_churned` | Binary target: 1 if `recency_days > 90` and tenure $\ge 120$ days | Supervised ML Classification Target |
| `predicted_churn_prob` | Output probability from trained classifier $[0.0, 1.0]$ | Churn Risk Assessment |
| `rfm_segment` | Rule-based classification label (e.g., Champions, At-Risk) | Operational Marketing Cohorts |
