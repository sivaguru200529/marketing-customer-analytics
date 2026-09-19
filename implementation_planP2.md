# Implementation Plan: Phase 2 — Synthetic Data Generation Engine (Updated)

## Executive Overview
Phase 2 builds a reproducible, realistic synthetic data generation engine for the **Aura Retail Marketing & Customer Analytics** project. The synthetic dataset powers downstream PostgreSQL schema loading, SQL analytical marts, exploratory customer analytics, RFM and K-Means segmentation, churn prediction modeling, and Power BI reporting.

The engine generates:
- **10,000 Customers** (`dim_customers`)
- **150 Products** (`dim_products`)
- **50,000 Orders** (`fact_orders`)
- **120,000+ Order Items** (`fact_order_items`, avg 2.4–2.5 per order)
- **150,000 Web Sessions** (`fact_web_sessions`)
- **2,193 Marketing Spend Records** (`fact_marketing_spend`: 731 calendar days × 3 paid channels)
- **6 Acquisition Channels** (`dim_channels`)

All data generation is strictly deterministic via a controlled random seed (`seed = 42`), enforcing referential integrity, realistic e-commerce behaviors (Pareto repeat buying, Q4 seasonality, cart abandonment, returns/cancellations, marketing ROAS), and strict data quality validation rules before file output.

---

## User Review Required

> [!IMPORTANT]
> **Leap-Year Calendar Window (731 Days)**: The 24-month observation window `2024-01-01` to `2025-12-31` contains **731 days** (2024 is a leap year with 366 days; 2025 has 365 days). Marketing spend is generated exclusively for the 3 paid channels (**Paid Search**, **Paid Social**, **Affiliate**), yielding exactly $731 \times 3 = 2,193$ marketing spend rows.
>
> **Strict Seed-Based Reproducibility**: All random processes use independent, controlled NumPy Random Generators (`np.random.default_rng(seed)`) and seeded Faker instances to eliminate non-deterministic global random state.
>
> **Pre-Export Validation & Git Safety**: Validation runs before CSV creation. `data/01_raw/*.csv` is ignored by Git, while `data/sample/*.csv` is committed and tracked.

---

## Key Specifications & Business Logic

### 1. Acquisition Channels vs Paid Channels
- **`dim_channels`** (6 total channels):
  1. `1`: Organic Search (`Organic`)
  2. `2`: Paid Search (`Paid`)
  3. `3`: Paid Social (`Paid`)
  4. `4`: Affiliate (`Referral`)
  5. `5`: Email (`Owned`)
  6. `6`: Direct (`Organic`)
- Customers are acquired across all 6 channels.
- **`fact_marketing_spend`** tracks daily paid media investments for the 3 paid channels only (`channel_id` $\in \{2, 3, 4\}$):
  - 731 days $\times$ 3 paid channels = **2,193 records** for full dataset.
  - Sample dataset: 731 days $\times$ 3 paid channels = 2,193 records (retaining full continuous marketing time-series for coherent attribution analytics).

### 2. Customer Acquisition & Order Distribution
- **Target Customer Order Distribution**:
  - ~60% Single-purchase customers (1 order)
  - ~22% Casual repeat customers (2–3 orders)
  - ~12% Frequent repeat customers (4–6 orders)
  - ~6% VIP / Champion customers (7–15 orders)
- **Rebalancing Algorithm**: Customers are assigned order counts according to this behavioral distribution, and counts are rebalanced proportionally so the full dataset hits **exactly 50,000 orders** (and **1,500 orders** in the sample dataset).
- **Chronological & Relational Integrity**:
  - Each order belongs to a valid customer (`customer_id` exists).
  - First order is placed on or after the customer's `signup_date`.
  - Subsequent orders follow realistic inter-purchase time deltas (log-normal intervals) bounded by `2025-12-31`.

### 3. Basket Composition & Order Items
- Line items per order: 1 to 6 items (bounded geometric distribution targeting a mean of 2.44 items/order).
- **Full dataset**: $50,000 \times 2.44 \approx \mathbf{122,000}$ items (strictly $\ge 120,000$).
- **Sample dataset**: $1,500 \times 2.44 \approx \mathbf{3,660}$ items (within the 3,600–3,750 range).
- Quantities: $1 \le \text{quantity} \le 10$ (heavily weighted towards 1–2 units).
- Pricing & Math:
  - `line_total = quantity * unit_price`
  - `total_order_amount = sum(line_totals) + shipping_cost - discount_amount`
  - `total_order_amount >= 0`

### 4. Digital Touchpoints (Web Sessions)
- **150,000 sessions** (4,500 for sample):
  - Every order has an associated browsing session on `order_date.date()`.
  - Additional non-purchasing browsing sessions distributed across customer tenure.
  - Page views (1–25), session duration (15–1200 seconds).
  - Cart abandonment: flagged True if items were added to cart but order was not completed.
  - Support tickets: 0–3 tickets, with elevated probability for returned/cancelled orders or session friction.

---

## Proposed Package Architecture

```
src/data_generator/
├── __init__.py                # Package exports & versioning
├── config.py                  # GeneratorConfig dataclass, seeds, target counts, paths
├── channels.py                # Marketing channels (dim_channels)
├── products.py                # Product catalog with realistic margins and categories
├── customers.py               # Customer profiles with demographic and signup distribution
├── marketing_spend.py         # 731 days × 3 paid channels ad spend, impressions, clicks, seasonality
├── orders.py                  # Orders & order items, repeat buying curve, basket sizing, returns
├── web_sessions.py            # Digital touchpoints, cart abandonment, support tickets, order correlation
├── validators.py              # Strict relational, date, numeric, and business integrity validator
└── generate_data.py           # CLI entry point (--seed 42, --sample, formatted console summary)

data/
├── 01_raw/                    # Full generated dataset (ignored in Git)
│   ├── channels.csv
│   ├── customers.csv
│   ├── products.csv
│   ├── orders.csv
│   ├── order_items.csv
│   ├── web_sessions.csv
│   └── marketing_spend.csv
└── sample/                    # Representative sample dataset (tracked in Git)
    ├── channels.csv
    ├── customers.csv
    ├── products.csv
    ├── orders.csv
    ├── order_items.csv
    ├── web_sessions.csv
    └── marketing_spend.csv

tests/
├── __init__.py
└── test_data_generator.py     # Automated test suite (reproducibility, integrity, math, validations)

docs/
├── data_generation.md         # Comprehensive generation documentation & run guide
└── data_dictionary.md         # Synchronized schema, table constraints, and field descriptions
```

---

## Data Validation Engine (`src/data_generator/validators.py`)

Validation executes **before** marking generation as successful or persisting files. Checks include:
1. **Row Counts**: Verified within target bounds (Full: 50,000 orders, $\ge 120,000$ items, 2,193 spend rows; Sample: 1,500 orders, 3,600–3,750 items, 2,193 spend rows).
2. **Primary Key Uniqueness**: Zero duplicate IDs in all 7 entities.
3. **Foreign Key Integrity**:
   - `fact_orders.customer_id` $\in$ `dim_customers.customer_id`
   - `fact_order_items.order_id` $\in$ `fact_orders.order_id`
   - `fact_order_items.product_id` $\in$ `dim_products.product_id`
   - `fact_web_sessions.customer_id` $\in$ `dim_customers.customer_id`
   - `dim_customers.acquisition_channel_id` $\in$ `dim_channels.channel_id`
   - `fact_marketing_spend.channel_id` $\in \{2, 3, 4\}$ (strictly paid channels)
4. **Chronological Validity**:
   - `order_date >= customer.signup_date`
   - `session_date >= customer.signup_date`
   - All events bounded by `2024-01-01` and `2025-12-31`.
5. **Monetary & Math Integrity**:
   - `unit_price > 0`, `cost_price > 0`, `retail_price >= cost_price`
   - `line_total == quantity * unit_price`
   - `total_order_amount == sum(line_totals) + shipping_cost - discount_amount`
   - `total_order_amount >= 0`
6. **Quantity Range**: $1 \le \text{quantity} \le 10$.
7. **Negative Values**: No negative spend, clicks, impressions, pages, or durations.
8. **Null Values**: No unexpected nulls in mandatory fields.

---

## Console Summary Output Specification

Upon completion, `generate_data.py` outputs a structured summary:

```
==================================================
AURA RETAIL DATA GENERATION COMPLETE
====================================

Seed: 42

Channels       : 6
Customers      : 10,000
Products       : 150
Orders         : 50,000
Order Items    : 122,184
Web Sessions   : 150,000
Marketing Rows : 2,193

Validation: PASSED

Output:
data/01_raw/

==================================================
```

And for sample mode:

```
==================================================
AURA RETAIL SAMPLE DATA GENERATION COMPLETE
===========================================

Seed: 42

Channels       : 6
Customers      : 500
Products       : 50
Orders         : 1,500
Order Items    : 3,672
Web Sessions   : 4,500
Marketing Rows : 2,193

Validation: PASSED

Output:
data/sample/

==================================================
```

---

## Verification Plan

### Automated Tests (`pytest tests/test_data_generator.py -v`)
- `test_reproducibility`: Runs generator twice with `seed=42`, asserts DataFrame equality.
- `test_product_catalog_integrity`: Validates category allocations, positive prices, and positive gross margins.
- `test_customer_distributions`: Age limits (18–75), signup dates within 731-day window, channel distribution.
- `test_order_chronology_and_fks`: Verifies all orders have valid customer IDs and order timestamps $\ge$ signup timestamps.
- `test_order_item_math`: Verifies order item count $\ge 120,000$, $1 \le \text{quantity} \le 10$, and exact `line_total` arithmetic.
- `test_customer_order_distribution`: Tests repeat purchase breakdown matches target distribution and rebalancing hits order target.
- `test_marketing_spend_seasonality`: Confirms exactly 2,193 rows (731 days $\times$ 3 paid channels), valid CTR/CPC, and Q4 holiday spend surges.
- `test_web_sessions_linkage`: Checks sessions linked to customers and order events, cart abandonment flags.
- `test_validator_failure_cases`: Injects bad records (duplicate PK, broken FK, negative price, inverted dates) and verifies validator raises descriptive errors.

### Manual Verification
1. Run full generator: `python -m src.data_generator.generate_data --seed 42`
2. Run sample generator: `python -m src.data_generator.generate_data --sample --seed 42`
3. Verify file generation in `data/01_raw/` and `data/sample/`.
4. Inspect `git status` to verify `data/01_raw/*.csv` is ignored while `data/sample/*.csv` is tracked.
5. Verify updated documentation files `docs/data_generation.md` and `docs/data_dictionary.md`.
