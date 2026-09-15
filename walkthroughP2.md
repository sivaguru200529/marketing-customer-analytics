# Walkthrough: Phase 2 — Synthetic Data Generation Engine

## Phase 2 Completed Successfully
We have implemented and verified the **Synthetic Data Generation Engine** for the **Aura Retail Marketing & Customer Analytics** platform.

The engine deterministically simulates 24 months of multi-channel e-commerce operations across **731 calendar days** (2024 leap year inclusive), enforcing strict referential integrity, Pareto repeat customer behavior, basket size dynamics, Q4 marketing seasonality, and comprehensive pre-export validation.

---

## 1. Automated Test Suite Results

All 9 unit and integration tests passed cleanly:

```bash
$ python -m pytest tests/test_data_generator.py -v
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\91934\.gemini\antigravity-ide\scratch\marketing-customer-analytics
plugins: Faker-40.39.0
collecting ... collected 9 items

tests/test_data_generator.py::test_reproducibility PASSED                [ 11%]
tests/test_data_generator.py::test_product_catalog_integrity PASSED      [ 22%]
tests/test_data_generator.py::test_customer_distributions PASSED         [ 33%]
tests/test_data_generator.py::test_order_chronology_and_fks PASSED       [ 44%]
tests/test_data_generator.py::test_order_item_math PASSED                [ 55%]
tests/test_data_generator.py::test_customer_order_distribution PASSED    [ 66%]
tests/test_data_generator.py::test_marketing_spend_seasonality PASSED    [ 77%]
tests/test_data_generator.py::test_web_sessions_linkage PASSED           [ 88%]
tests/test_data_generator.py::test_validator_failure_cases PASSED        [100%]

============================== 9 passed in 3.58s ==============================
```

---

## 2. Generated Datasets & Final Row Counts

Both full and sample generation pipelines were executed with `seed = 42`:

| Entity | CSV Filename | Full Dataset (`data/01_raw/`) | Sample Dataset (`data/sample/`) | Git Status |
| :--- | :--- | :--- | :--- | :--- |
| **Channels** | `channels.csv` | **6** rows | **6** rows | Tracked in sample, ignored in raw |
| **Customers** | `customers.csv` | **10,000** rows | **500** rows | Tracked in sample, ignored in raw |
| **Products** | `products.csv` | **150** rows | **50** rows | Tracked in sample, ignored in raw |
| **Orders** | `orders.csv` | **50,000** rows | **1,500** rows | Tracked in sample, ignored in raw |
| **Order Items** | `order_items.csv` | **127,596** rows ($\ge 120\text{k}$) | **3,749** rows (target 3.6k–3.75k) | Tracked in sample, ignored in raw |
| **Web Sessions** | `web_sessions.csv` | **150,000** rows | **4,500** rows | Tracked in sample, ignored in raw |
| **Marketing Spend** | `marketing_spend.csv` | **2,193** rows ($731 \times 3$) | **2,193** rows ($731 \times 3$) | Tracked in sample, ignored in raw |

---

## 3. Pre-Export Validation Results

The `DatasetValidator` executed prior to disk persistence and verified:
- [x] **Primary Key Uniqueness**: All 7 entities have 100% unique primary keys.
- [x] **Foreign Key Integrity**:
  - `orders.customer_id` $\in$ `customers.customer_id`
  - `order_items.order_id` $\in$ `orders.order_id`
  - `order_items.product_id` $\in$ `products.product_id`
  - `web_sessions.customer_id` $\in$ `customers.customer_id`
  - `customers.acquisition_channel_id` $\in$ `channels.channel_id`
  - `marketing_spend.channel_id` strictly $\in \{2, 3, 4\}$ (paid media channels).
- [x] **Chronological Integrity**:
  - Customer registration dates within `2024-01-01` to `2025-12-31`.
  - Every order date $\ge$ customer registration date.
  - Every web session date $\ge$ customer registration date.
- [x] **Monetary and Quantitative Consistency**:
  - `retail_price >= cost_price > 0` across all catalog items.
  - Line items quantities strictly within $[1, 10]$.
  - Exact formula: `line_total == quantity * unit_price`.
  - Exact formula: `total_order_amount == sum(line_totals) + shipping_cost - discount_amount`.
  - Zero negative order amounts, shipping fees, or discounts.
- [x] **Marketing Spend & Sessions Sanity**:
  - Clicks $\le$ Impressions across all days.
  - Spend, impressions, clicks, page views, and durations $\ge 0$.

---

## 4. Sample Records Preview

### `dim_channels` (`data/sample/channels.csv`)
```csv
channel_id,channel_name,channel_type
1,Organic Search,Organic
2,Paid Search,Paid
3,Paid Social,Paid
4,Affiliate,Referral
5,Email,Owned
6,Direct,Organic
```

### `dim_customers` (`data/sample/customers.csv`)
```csv
customer_id,first_name,last_name,email,signup_date,acquisition_channel_id,age,gender,city,state,device_preference
CUST_00001,Margaret,Johnson,margaret.johnson1@example.com,2024-01-08,4,26,Female,Miami,FL,Mobile
CUST_00002,Denise,Walker,denise.walker2@example.com,2024-01-11,6,44,Female,San Francisco,CA,Mobile
```

### `dim_products` (`data/sample/products.csv`)
```csv
product_id,product_name,category,sub_category,cost_price,retail_price
PROD_001,Wool Overcoat,Apparel,Outerwear,24.25,54.0
PROD_002,Water-Resistant Bomber,Apparel,Outerwear,47.3,131.99
```

### `fact_orders` (`data/sample/orders.csv`)
```csv
order_id,customer_id,order_date,order_status,payment_method,shipping_cost,discount_amount,total_order_amount
ORD_00001,CUST_00001,2024-01-11 14:41:53,Delivered,Credit Card,0.0,0.0,403.0
ORD_00002,CUST_00002,2024-01-20 18:37:28,Delivered,PayPal,4.99,0.0,382.99
```

### `fact_order_items` (`data/sample/order_items.csv`)
```csv
order_item_id,order_id,product_id,quantity,unit_price,line_total
1,ORD_00001,PROD_039,1,64.5,64.5
2,ORD_00001,PROD_017,1,53.0,53.0
```

### `fact_web_sessions` (`data/sample/web_sessions.csv`)
```csv
session_id,customer_id,session_date,page_views,time_spent_seconds,cart_abandoned,support_tickets
SESS_000001,CUST_00001,2024-01-11,6,783,False,0
SESS_000002,CUST_00002,2024-01-20,12,849,False,0
```

### `fact_marketing_spend` (`data/sample/marketing_spend.csv`)
```csv
spend_id,spend_date,channel_id,campaign_name,impressions,clicks,spend_usd
1001,2024-01-01,2,Search_Brand_Core,15129,638,840.24
1002,2024-01-01,3,Meta_Advantage_Catalog_Ads,78272,1932,1093.26
1003,2024-01-01,4,Affiliate_Creator_Network,16035,420,207.24
```

---

## 5. Updated Workspace Directory Tree

```
marketing-customer-analytics/
├── data/
│   ├── 01_raw/                    # Full 50k-order dataset (ignored in Git)
│   │   ├── channels.csv
│   │   ├── customers.csv
│   │   ├── marketing_spend.csv
│   │   ├── order_items.csv
│   │   ├── orders.csv
│   │   ├── products.csv
│   │   └── web_sessions.csv
│   └── sample/                    # Representative sample (tracked in Git)
│       ├── channels.csv
│       ├── customers.csv
│       ├── marketing_spend.csv
│       ├── order_items.csv
│       ├── orders.csv
│       ├── products.csv
│       └── web_sessions.csv
├── docs/
│   ├── business_requirements.md
│   ├── data_dictionary.md         # Synchronized schema definitions
│   ├── data_generation.md         # Full engine documentation & CLI instructions
│   └── methodology.md
├── src/
│   ├── __init__.py
│   ├── data_generator/            # Modular generation package
│   │   ├── __init__.py
│   │   ├── channels.py            # dim_channels generator
│   │   ├── config.py              # GeneratorConfig dataclass & parameters
│   │   ├── customers.py           # dim_customers generator
│   │   ├── generate_data.py       # Orchestrator & CLI entry point
│   │   ├── marketing_spend.py     # fact_marketing_spend generator
│   │   ├── orders.py              # fact_orders & fact_order_items generator
│   │   ├── products.py            # dim_products catalog generator
│   │   ├── validators.py          # Pre-export validation engine
│   │   └── web_sessions.py        # fact_web_sessions generator
│   ├── database/
│   ├── features/
│   └── models/
└── tests/
    ├── __init__.py
    └── test_data_generator.py     # 9 comprehensive tests
```

---

## 6. Assumptions & Implementation Notes
1. **731 Calendar Days**: 2024 is a leap year (366 days) and 2025 has 365 days, yielding 731 total days.
2. **Paid Channels vs Acquisition Channels**: All 6 channels exist in `dim_channels` and can acquire customers, while `fact_marketing_spend` specifically tracks the 3 paid media channels (Paid Search, Paid Social, Affiliate), totaling $731 \times 3 = 2,193$ rows in both full and sample sets to preserve continuous time-series continuity for attribution modeling.
3. **Repeat-Buyer Rebalancing**: Single-order buyers were preserved at ~60% of total customers, with remaining volume allocated across repeat tiers to reach exactly 50,000 orders (full) and 1,500 orders (sample).
4. **Git Safety**: Checked with `git status` — `data/01_raw/*.csv` is ignored by Git, while `data/sample/*.csv` is tracked.
