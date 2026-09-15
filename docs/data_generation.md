# Synthetic Data Generation Engine: Aura Retail

## 1. Dataset Purpose
The synthetic data generation engine produces a high-fidelity, deterministic e-commerce dataset modeling the commercial operations of **Aura Retail**, a Direct-to-Consumer (D2C) multi-category lifestyle brand across North America.

This dataset provides the foundational source of truth for:
- PostgreSQL relational database loading (Phase 3)
- Advanced SQL analytical marts and KPI reporting (Phase 4)
- Customer segmentation via RFM and K-Means clustering (Phase 5)
- Supervised machine learning churn classification (Phase 6)
- Executive and operational Power BI dashboards (Phase 7)

---

## 2. Business Entities & Row Counts

The engine models seven relational entities across an observation window of **731 calendar days** (January 1, 2024 through December 31, 2025, accounting for the 2024 leap year):

| Entity Name | Database Table | Full Dataset Rows | Sample Dataset Rows | Primary Key | Foreign Keys |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Channels** | `dim_channels` | 6 | 6 | `channel_id` | — |
| **Customers** | `dim_customers` | 10,000 | 500 | `customer_id` | `acquisition_channel_id` $\to$ `dim_channels` |
| **Products** | `dim_products` | 150 | 50 | `product_id` | — |
| **Orders** | `fact_orders` | 50,000 | 1,500 | `order_id` | `customer_id` $\to$ `dim_customers` |
| **Order Items** | `fact_order_items` | $\ge 120,000$ (actual: ~127,596) | ~3,600–3,750 (actual: ~3,749) | `order_item_id` | `order_id` $\to$ `fact_orders`<br>`product_id` $\to$ `dim_products` |
| **Web Sessions** | `fact_web_sessions` | 150,000 | 4,500 | `session_id` | `customer_id` $\to$ `dim_customers` |
| **Marketing Spend** | `fact_marketing_spend` | 2,193 | 2,193 | `spend_id` | `channel_id` $\to$ `dim_channels` (paid only) |

---

## 3. Channels & Marketing Spend Logic

### 6 Acquisition Channels (`dim_channels`)
Customers can be acquired through six distinct marketing and organic channels:
1. `1`: **Organic Search** (`Organic`) — SEO discovery
2. `2`: **Paid Search** (`Paid`) — Google/Bing Search Ads
3. `3`: **Paid Social** (`Paid`) — Meta (Instagram/Facebook) & TikTok Ads
4. `4`: **Affiliate** (`Referral`) — Creator networks and partner referral sites
5. `5`: **Email** (`Owned`) — Referral links & owned subscriber outreach
6. `6`: **Direct** (`Organic`) — Direct URL navigation & brand recall

### 3 Paid Marketing Spend Channels (`fact_marketing_spend`)
Media capital is invested strictly across the three paid channels (`Paid Search`, `Paid Social`, `Affiliate`).
- **Date Range**: 731 continuous days ($366 \text{ days in 2024} + 365 \text{ days in 2025}$).
- **Total Spend Records**: $731 \text{ days} \times 3 \text{ paid channels} = \mathbf{2,193} \text{ rows}$.
- **Performance Dynamics**:
  - **Paid Search**: High CTR (2.5%–4.5%), higher CPC ($0.90–$1.85), focused on high-intent conversion.
  - **Paid Social**: Broad top-of-funnel reach, moderate CTR (1.2%–2.5%), lower CPC ($0.50–$1.20).
  - **Affiliate**: Performance-based affiliate networks, CTR (1.8%–3.2%), lowest CPC ($0.35–$0.75).
- **Seasonality & Scaling**:
  - Day-of-week surges on Sunday, Monday, and Thursday.
  - Year-over-year commercial growth scaling from 2024 to 2025.
  - Q4 Holiday / Black Friday / Cyber Week surges ($2.4\times$ to $2.85\times$ baseline spend).

---

## 4. Customer Behavior & Order Distribution

### Repeat Purchasing Distribution
The generator implements an empirical e-commerce customer order distribution:
- **~60% Single-Purchase Buyers**: Customers who purchase once and never return (creating realistic new-buyer cohorts and one-time churn profiles).
- **~22% Casual Repeat Buyers**: Customers who purchase 2–3 times.
- **~12% Frequent Repeat Buyers**: Customers who purchase 4–6 times over their tenure.
- **~6% VIP Champions**: High-frequency loyal buyers who purchase 7–15+ times.

### Rebalancing Algorithm
To hit the exact target of **50,000 orders** (full) and **1,500 orders** (sample) without distorting customer behavior:
1. Customers are assigned initial tiers matching the target behavioral ratios.
2. The single-purchase segment (~60%) is locked at 1 order.
3. The remaining order count is distributed across repeat tiers proportionally to tier purchasing frequency.
4. Total order counts strictly match `config.n_orders`.

### Order Chronology & Churn Dynamics
- Every order occurs on or after the customer's `signup_date` and on or before `2025-12-31`.
- For repeat customers, inter-purchase times follow log-normal intervals.
- Approximately 40% of repeat customers stop purchasing after their first 2–8 months (dormant/churned customers), while 60% continue purchasing through late 2025 (retained customers). This enables realistic churn modeling in Phase 6.

### Basket Composition & Pricing Integrity
- **Line Items per Order**: 1 to 6 items (modeled via a bounded distribution averaging ~2.47 items per order, consistently yielding $> 120,000$ line items in full mode and ~3,749 items in sample mode).
- **Quantities**: $1 \le \text{quantity} \le 10$ (heavily weighted towards 1–2 units).
- **Mathematics**:
  $$\text{line\_total} = \text{round}(\text{quantity} \times \text{unit\_price}, 2)$$
  $$\text{total\_order\_amount} = \text{round}(\max(0.00, \sum \text{line\_total} + \text{shipping\_cost} - \text{discount\_amount}), 2)$$

---

## 5. Web Sessions & Digital Touchpoints

The `fact_web_sessions` table (150,000 rows in full, 4,500 rows in sample) models two distinct session types:
1. **Purchasing Sessions**: Every order has an authenticated session on `order_date.date()` with high page views (5–22), high session duration (180–960 seconds), and `cart_abandoned = False`. If an order was Returned or Cancelled, support ticket probability increases to 28%–38%.
2. **Non-Purchasing Browsing Sessions**: Exploration sessions across customer tenure. ~28% exhibit cart abandonment (`cart_abandoned = True`), and casual browsing exhibits lower page views and duration.

---

## 6. Deterministic Reproducibility

To guarantee reproducibility across environments:
- **Seed**: `seed = 42`
- Independent, controlled random number generators (`np.random.default_rng(config.seed)`) and seeded Faker instances (`Faker.seed(42)`, `fake.seed_instance(42)`) are passed into each generator module.
- Running the generator twice with the same seed produces byte-identical CSV datasets.
- Tested automatically via `test_reproducibility` in `tests/test_data_generator.py`.

---

## 7. Pre-Export Data Validation Suite

Before any CSV file is written to disk, `DatasetValidator` enforces eight audit rules:
1. **Row Counts**: Verifies all entity counts against target boundaries (e.g., 50,000 orders, $\ge 120,000$ items, 2,193 spend rows).
2. **Primary Key Uniqueness**: Zero duplicate IDs across all 7 entities.
3. **Foreign Key Integrity**:
   - `orders.customer_id` $\in$ `customers.customer_id`
   - `order_items.order_id` $\in$ `orders.order_id`
   - `order_items.product_id` $\in$ `products.product_id`
   - `web_sessions.customer_id` $\in$ `customers.customer_id`
   - `customers.acquisition_channel_id` $\in$ `channels.channel_id`
   - `marketing_spend.channel_id` $\in \{2, 3, 4\}$ (paid channels only)
4. **Date Boundaries & Chronology**:
   - All event dates bounded within `2024-01-01` to `2025-12-31`.
   - `order_date >= customer.signup_date`.
   - `session_date >= customer.signup_date`.
5. **Monetary & Mathematical Consistency**:
   - `cost_price > 0`, `retail_price >= cost_price`.
   - `line_total == quantity * unit_price`.
   - `total_order_amount == sum(line_totals) + shipping_cost - discount_amount`.
6. **Quantity Sanity**: $1 \le \text{quantity} \le 10$.
7. **Non-Negative Constraints**: No negative spend, clicks, impressions, pages, or durations.
8. **Null Checks**: Mandatory columns contain zero null values.

If any check fails, a descriptive `ValidationError` is raised, halting pipeline execution and preventing data corruption.

---

## 8. Directory Storage & Git Safety

- **Full Datasets (`data/01_raw/`)**:
  Contains the 50k-order, 127k-item full dataset. Ignored by Git via `.gitignore` (`data/01_raw/*.csv`) to keep the repository lightweight.
- **Sample Datasets (`data/sample/`)**:
  Contains the 500-customer, 1.5k-order representative sample dataset. Tracked and committed to GitHub so collaborators can clone and inspect the schema immediately.

---

## 9. How to Regenerate the Dataset

### Full Dataset Generation (50,000 Orders)
```bash
python -m src.data_generator.generate_data --seed 42
```

### Representative Sample Generation (1,500 Orders)
```bash
python -m src.data_generator.generate_data --sample --seed 42
```

### Running Automated Test Suite
```bash
python -m pytest tests/test_data_generator.py -v
```
