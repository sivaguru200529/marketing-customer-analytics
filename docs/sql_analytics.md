# SQL Analytics & Reporting Layer Documentation

This document provides a comprehensive guide to the analytical SQL queries, database views, business definitions, RFM scoring methodologies, cohort retention mechanics, and Phase 4 dataset export pipelines for the **Aura Retail Marketing & Customer Analytics Platform**.

---

## 1. Analytics Architecture & Schema Layering

The analytics layer sits directly on top of the normalized 3NF relational data warehouse in PostgreSQL 16:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Warehouse (aura_retail)                       │
│                                                                             │
│   dim_channels       dim_customers       dim_products       fact_orders     │
│   fact_order_items   fact_web_sessions   fact_marketing_spend               │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Standardized Analytical Views (Views DDL)                 │
│                                                                             │
│   ├── view_customer_analytics    (RFM Quintiles & Customer Profiling)       │
│   ├── view_product_analytics     (Margins, Realized Prices, Category Ranks) │
│   ├── view_monthly_revenue       (Time-Series, MoM Growth & Running Sales)  │
│   ├── view_marketing_performance (CTR, CPC, CPM, CAC, ROAS Attribution)     │
│   ├── view_cohort_retention      (24-Month Customer Purchase Retention)     │
│   └── view_business_kpis         (Executive Macro Performance Scorecard)    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼  src/analytics/export.py
┌─────────────────────────────────────────────────────────────────────────────┐
│             Exported Analytical Datasets (data/03_analytics/)               │
│                                                                             │
│   customer_analytics.csv    (10,000 rows -> Ready for Phase 4 ML)           │
│   product_analytics.csv     (150 rows -> Ready for Category Margin EDA)     │
│   monthly_revenue.csv       (24 rows -> Ready for Revenue Forecasting)      │
│   marketing_performance.csv (6 rows -> Ready for Media Mix Attribution)     │
│   cohort_retention.csv      (300 rows -> Ready for Heatmap Visualization)   │
│   business_kpis.csv         (1 row -> Ready for Executive KPI Cards)        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Business Definitions & Metrics Logic

### A. Revenue Definitions
- **Gross Billed Revenue**: Total order amount transacted across all orders committed in the system (`SUM(total_order_amount)` across all statuses).
- **Delivered Net Revenue**: Realized net revenue exclusively from successfully delivered orders (`SUM(CASE WHEN order_status = 'Delivered' THEN total_order_amount END)`). This represents true cash earnings.
- **Returned Revenue**: Billed value associated with returned orders (`order_status = 'Returned'`).
- **Cancelled Revenue**: Value associated with orders cancelled prior to fulfillment (`order_status = 'Cancelled'`).
- **Average Order Value (AOV)**:
  $$\text{Delivered AOV} = \frac{\text{Delivered Net Revenue}}{\text{Delivered Order Count}}$$

### B. Product Margin & Unit Economics
- **Line Total**: Unit price transacted multiplied by quantity ordered ($\text{quantity} \times \text{unit\_price}$).
- **Estimated Cost of Goods Sold (COGS)**:
  $$\text{Total COGS} = \sum (\text{quantity} \times \text{cost\_price})$$
- **Estimated Gross Profit**:
  $$\text{Gross Profit} = \text{Gross Revenue} - \text{Total COGS}$$
- **Gross Profit Margin (%)**:
  $$\text{Margin \%} = \frac{\text{Gross Revenue} - \text{Total COGS}}{\text{Gross Revenue}} \times 100$$
- **Average Realized Price**:
  $$\text{Avg Realized Price} = \frac{\text{Gross Revenue}}{\text{Total Units Sold}}$$

---

## 3. Customer RFM Scoring & Segmentation Methodology

Recency, Frequency, and Monetary metrics are computed at the individual customer level from transactional order history using the analytical anchor date **`2025-12-31`**:

1. **Recency ($R$)**: Days between `2025-12-31` and the customer's most recent order date (`2025-12-31 - MAX(order_date::DATE)`). Customers with no purchases receive a sentinel penalty score of 731 days.
2. **Frequency ($F$)**: Total count of successfully delivered orders placed by the customer.
3. **Monetary ($M$)**: Total gross dollar volume from delivered orders placed by the customer.

### RFM Quintile Scoring via `NTILE(5)` Window Functions
Using window functions, all 10,000 customers are partitioned into 5 quintiles $[1, 5]$:
- **$R\text{\_Score}$**: `NTILE(5) OVER (ORDER BY recency_days DESC)`. Lowest recency days receive 5 (purchased recently); highest days receive 1.
- **$F\text{\_Score}$**: `NTILE(5) OVER (ORDER BY delivered_orders ASC)`. Highest order counts receive 5; lowest receive 1.
- **$M\text{\_Score}$**: `NTILE(5) OVER (ORDER BY delivered_revenue ASC)`. Highest revenue totals receive 5; lowest receive 1.

### Segment Classification Matrix
| Segment Label | Scoring Criteria | Strategic Marketing Action |
| :--- | :--- | :--- |
| **Champions** | $R \ge 4, F \ge 4, M \ge 4$ | VIP rewards, early access product drops, loyalty brand ambassadors. |
| **Loyal Customers** | $R \ge 3, F \ge 3, M \ge 3$ | Upsell higher-margin products, cross-sell adjacent retail categories. |
| **Recent Inquirers** | $R \ge 4, F \le 2$ | Onboarding nurture email sequences, second-purchase incentives. |
| **Promising** | $R \ge 3, F \le 2, M \ge 3$ | High spenders with low cadence; personalized replenishment offers. |
| **At Risk High Value** | $R \le 2, F \ge 3, M \ge 3$ | Win-back concierge outreach, exclusive discount reactivation codes. |
| **Need Attention** | $R \le 2, F \ge 2$ | Re-engagement campaigns, surveys identifying customer friction. |
| **Lost / Dormant** | $R = 1, F = 1$ | Low-cost automated email retargeting or sunsetting. |
| **Potential / Developing**| All other combinations | Category discovery recommendations, dynamic push notifications. |

---

## 4. Marketing Attribution & Efficiency Methodology

### Attribution Model: First-Touch Customer Acquisition Channel Attribution
Because order transaction headers do not record individual ad click IDs, revenue attribution is anchored to the customer's original acquisition channel (`dim_customers.acquisition_channel_id` $\rightarrow$ `dim_channels.channel_id`). All historical order revenue generated by a customer is attributed to the channel that drove their initial platform signup.

### Formulas:
- **Click-Through Rate (CTR %)**:
  $$\text{CTR} = \frac{\text{Total Clicks}}{\text{Total Impressions}} \times 100$$
- **Cost Per Click (CPC $)**:
  $$\text{CPC} = \frac{\text{Total Spend (USD)}}{\text{Total Clicks}}$$
- **Cost Per Thousand Impressions (CPM $)**:
  $$\text{CPM} = \frac{\text{Total Spend (USD)}}{\text{Total Impressions}} \times 1000$$
- **Customer Acquisition Cost (CAC $)**:
  $$\text{CAC} = \frac{\text{Total Spend (USD)}}{\text{Acquired Customers Count}}$$
- **Return on Ad Spend (ROAS)**:
  $$\text{ROAS} = \frac{\text{Delivered Attributed Revenue}}{\text{Marketing Spend}}$$
  *(Applies strictly to paid media channels where $\text{Marketing Spend} > 0$).*

---

## 5. Customer Cohort Purchase Retention Mechanics

Cohort retention tracks customer purchasing behavior over time relative to their registration month across the 2-year observation period (`2024-01-01` through `2025-12-31`):

- **Cohort Month**: Calendar month when customer registered (`DATE_TRUNC('month', signup_date)::DATE`). Exactly 24 distinct monthly cohorts exist.
- **Activity Month**: Calendar month when customer placed an order (`DATE_TRUNC('month', order_date)::DATE`).
- **Months Since Signup**:
  $$\text{Months Elapsed} = (\text{Year}_{\text{order}} - \text{Year}_{\text{signup}}) \times 12 + (\text{Month}_{\text{order}} - \text{Month}_{\text{signup}})$$
- **Cohort Size**: Total registered customers within the cohort.
- **Active Ordering Customers**: Count of distinct customers in the cohort who completed at least one transaction in that activity month.
- **Purchase Retention Rate (%)**:
  $$\text{Retention Rate} = \frac{\text{Active Ordering Customers in Activity Month}}{\text{Cohort Initial Size}} \times 100$$

---

## 6. Analytical Views Catalog

| View Name | Schema | Primary Key / Granularity | Row Count | Analytical Purpose |
| :--- | :--- | :--- | :---: | :--- |
| `view_customer_analytics` | `aura_retail` | `customer_id` | **10,000** | Customer profiles, LTV, order counts, recency, RFM scores & segments. |
| `view_product_analytics` | `aura_retail` | `product_id` | **150** | Product unit economics, realized prices, gross margins, category rank. |
| `view_monthly_revenue` | `aura_retail` | `order_month` | **24** | Monthly gross/net sales, order volumes, MoM growth %, cumulative sales. |
| `view_marketing_performance` | `aura_retail` | `channel_id` | **6** | Channel ad metrics (CTR, CPC, CPM), CAC, attributed revenue, and ROAS. |
| `view_cohort_retention` | `aura_retail` | `cohort_month, activity_month` | **300** | 24-month customer signup cohort purchase retention matrix. |
| `view_business_kpis` | `aura_retail` | Single-Row Scorecard | **1** | Centralized macro metrics covering sales, customers, margins, and ROAS. |

---

## 7. Python Analytics Modules & CLI Runbook

### Execute Analytics Pipeline and Export Datasets
```powershell
python -m src.analytics.runner
```
This CLI verifies database connectivity, deploys/refreshes the 6 views from `sql/analytics/008_phase4_datasets.sql`, validates row counts, and streams exports to `data/03_analytics/`.

### Export Directly via Dedicated Script
```powershell
python -m src.analytics.export
```

### Run Automated Tests
```powershell
# Run only analytics tests
python -m pytest tests/test_analytics.py -v

# Run entire test suite (data generator, database, analytics)
python -m pytest tests/ -v
```

---

## 8. Exported Phase 4 Datasets

| Export File Path | Records | Byte Size | Downstream Consumer |
| :--- | :---: | :---: | :--- |
| `data/03_analytics/customer_analytics.csv` | 10,000 | 1.89 MB | Phase 4 Exploratory Data Analysis & Phase 5 ML Churn/Clustering. |
| `data/03_analytics/product_analytics.csv` | 150 | 20.2 KB | Category margin analysis & merchandise assortment optimization. |
| `data/03_analytics/monthly_revenue.csv` | 24 | 3.6 KB | Time-series forecasting and executive revenue dashboards. |
| `data/03_analytics/marketing_performance.csv` | 6 | 882 B | Media mix modeling, CAC/ROAS visualization in Power BI. |
| `data/03_analytics/cohort_retention.csv` | 300 | 11.3 KB | Cohort retention heatmaps and customer lifetime decay curves. |
| `data/03_analytics/business_kpis.csv` | 1 | 1.0 KB | Executive high-level KPI cards and summary dashboards. |
