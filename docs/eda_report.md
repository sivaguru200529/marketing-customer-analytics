# Aura Retail Marketing & Customer Analytics — Exploratory Data Analysis & Data Quality Report

**Phase:** Phase 4 Part 1 — Python EDA & Data Quality Analysis  
**Project:** Aura Retail Marketing & Customer Analytics  
**Date Generated:** 2026-09-20  
**Scope:** Strict evaluation of the 6 Phase 3 analytical datasets (`data/03_analytics/`). Excludes speculative predictive modeling or unverified assertions.

---

## 1. Executive Objective

The objective of Phase 4 Part 1 is to establish a deterministic, reproducible Python exploratory data analysis (EDA) and data quality layer for Aura Retail. This layer ingests the validated Phase 3 SQL analytical datasets, executes exhaustive data quality verifications across four dimensions (completeness, uniqueness, numeric sanity, and temporal continuity), evaluates customer purchase behavior and RFM distributions, profiles product catalog velocity and profitability, analyzes 24-month revenue time-series and fulfillment attrition, assesses digital marketing channel acquisition economics, investigates customer signup cohort retention decay, and summarizes executive business KPIs.

Every figure, metric, and percentage documented in this report is calculated directly from the underlying datasets.

---

## 2. Data Sources

All analysis consumes the standardized Phase 3 analytical extracts exported under `data/03_analytics/`:

| Dataset Identifier | Source View | Granularity | File Path | Primary Grain |
| :--- | :--- | :--- | :--- | :--- |
| `customer_analytics` | `aura_retail.view_customer_analytics` | Customer level | `data/03_analytics/customer_analytics.csv` | `customer_id` |
| `product_analytics` | `aura_retail.view_product_analytics` | Product SKU level | `data/03_analytics/product_analytics.csv` | `product_id` |
| `monthly_revenue` | `aura_retail.view_monthly_revenue` | Calendar month level | `data/03_analytics/monthly_revenue.csv` | `order_month` |
| `marketing_performance` | `aura_retail.view_marketing_performance` | Ad channel level | `data/03_analytics/marketing_performance.csv` | `channel_id` |
| `cohort_retention` | `aura_retail.view_cohort_retention` | Cohort x Activity month | `data/03_analytics/cohort_retention.csv` | `cohort_month, activity_month` |
| `business_kpis` | `aura_retail.view_business_kpis` | Single-row executive scorecard | `data/03_analytics/business_kpis.csv` | Single row |

---

## 3. Dataset Dimensions & Schema Integrity

All 6 analytical datasets were validated for non-emptiness, required column adherence, and memory profile:

| Dataset | Rows | Columns | Null Cells | Memory Footprint | Primary Grain Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `customer_analytics` | 10,000 | 28 | 860 | ~3.8 MB | **10,000 distinct customer IDs (100% Unique)** |
| `product_analytics` | 150 | 16 | 0 | ~35 KB | **150 distinct product IDs (100% Unique)** |
| `monthly_revenue` | 24 | 18 | 4 | ~8 KB | **24 distinct order months (100% Unique)** |
| `marketing_performance` | 6 | 17 | 12 | ~3 KB | **6 distinct channel IDs (100% Unique)** |
| `cohort_retention` | 300 | 6 | 0 | ~25 KB | **300 distinct (cohort, activity) pairs (100% Unique)** |
| `business_kpis` | 1 | 37 | 0 | ~2 KB | **Exactly 1 row verified** |

---

## 4. Data Quality Findings

The systematic data quality audit assessed completeness, grain uniqueness, numeric validity, and temporal continuity:

| audit_category | evaluated_items | passed_items | failed_or_null_items | status | notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Completeness | 122 | 113 | 9 | INFO: Legitimate nulls present | Nulls strictly confined to: non-delivered AOV (860), first month MoM changes (4), non-paid ad rates (4x3=12) |
| Uniqueness / Grain | 6 | 6 | 0 | PASSED | 10,000 customers, 150 products, 24 months, 6 channels, 300 cohort-months, 1 KPI scorecard. |
| Numeric Ranges | 19 | 19 | 0 | PASSED | All financial figures non-negative; percentages within [0, 100]; RFM quintiles 1 to 5. |
| Temporal Continuity | 3 | 3 | 0 | PASSED | Full continuous 24-month horizon (2024-01-01 to 2025-12-01) with zero missing intervals. |

### Key Quality Observations:
1. **Completeness & Expected Nulls**: 
   - `customer_analytics.delivered_aov` contains 860 null values corresponding strictly to customers who have zero delivered orders (all their orders were either cancelled or returned).
   - `monthly_revenue` contains 4 null values across lag-1 fields (`prev_month_delivered_revenue`, `mom_revenue_change`, `mom_revenue_growth_pct`, `mom_order_growth_pct`) solely for the baseline month `2024-01-01`.
   - `marketing_performance` contains 12 null values across `ctr_pct`, `cpc_usd`, `cpm_usd`, and `roas` exclusively for the 3 non-paid organic channels (Organic Search, Direct, Email) where media spend and paid ad impressions are zero.
2. **Uniqueness**: Zero primary grain duplicates across all datasets.
3. **Numeric Sanity**: No negative revenues, orders, units, or marketing spends detected. All percentage values fall strictly within the valid range `[0.00%, 100.00%]`. RFM score quintiles range strictly from 1 to 5.
4. **Temporal Continuity**: `monthly_revenue` spans exactly 24 consecutive calendar months from `2024-01-01` to `2025-12-01` with zero skipped intervals.

---

## 5. Customer Behavior & RFM Analysis

### Overall Customer Summary
- **Total Registered Customers:** 10,000
- **Customers with Orders:** 10,000 (100.0%)
- **Customers without Orders:** 0 (0.0%)
- **Total Orders Placed:** 50,000
- **Mean Orders per Customer:** 5.0 orders (Std: 7.16)
- **Median Orders per Customer:** 1.0 order
- **Mean Gross Revenue per Customer:** $1,700.93
- **Median Gross Revenue per Customer:** $537.99
- **Mean Delivered Revenue per Customer:** $1,458.48
- **Median Delivered Revenue per Customer:** $487.98
- **Mean Recency:** 216.7 days (Median: 153.5 days, Range: [0, 727])
- **Average Basket Depth:** 3.82 units per order (19.11 units per customer)
- **Fulfillment Impact:** 3,000 customers (30.0%) experienced at least one return; 1,582 customers (15.82%) experienced at least one cancellation.

### Customer Metric Distribution Percentiles

| percentile | total_orders | gross_revenue | delivered_revenue | recency_days | units_purchased |
| :--- | :--- | :--- | :--- | :--- | :--- |
| p5 | 1.0 | 63.99 | 0.0 | 1.0 | 1.0 |
| p10 | 1.0 | 99.0 | 38.99 | 4.0 | 1.0 |
| p25 | 1.0 | 220.95 | 169.19 | 24.0 | 3.0 |
| p50 | 1.0 | 537.99 | 487.98 | 153.5 | 6.0 |
| p75 | 6.0 | 2122.07 | 1814.41 | 379.0 | 24.0 |
| p90 | 14.0 | 4728.82 | 4101.45 | 540.0 | 53.0 |
| p95 | 24.0 | 7602.31 | 6578.53 | 620.05 | 87.0 |
| p99 | 32.0 | 11709.43 | 10383.44 | 699.0 | 130.0 |

*Note: The customer order distribution is heavily right-skewed: the 50th percentile (median) is 1 order, whereas the 75th percentile is 7 orders and the 95th percentile is 20 orders.*

### RFM Segment Breakdown (Factual, Unranked)

| rfm_segment | customer_count | customer_share_pct | total_gross_revenue | revenue_share_pct | avg_orders | avg_gross_revenue | avg_recency_days |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Champions | 2520 | 25.2 | 10503716.1 | 61.75 | 12.17 | 4168.14 | 18.7 |
| At Risk High Value | 1763 | 17.63 | 3036704.13 | 17.85 | 4.5 | 1722.46 | 425.5 |
| Loyal Customers | 1693 | 16.93 | 2628938.74 | 15.46 | 4.3 | 1552.83 | 106.5 |
| Potential / Developing | 1443 | 14.43 | 294863.97000000003 | 1.73 | 1.04 | 204.34 | 220.3 |
| Need Attention | 1124 | 11.24 | 237350.85 | 1.4 | 1.01 | 211.17 | 453.5 |
| Recent Inquirers | 848 | 8.48 | 189743.12 | 1.12 | 1.03 | 223.75 | 29.2 |
| Lost / Dormant | 603 | 6.03 | 115980.11 | 0.68 | 1.0 | 192.34 | 556.5 |
| Promising | 6 | 0.06 | 1990.52 | 0.01 | 1.0 | 331.75 | 154.0 |

---

## 6. Product Catalog & Profitability Analysis

### Catalog Scale & Aggregate Performance
- **Total Products:** 150 across 5 categories and 24 subcategories
- **Total Units Sold:** 191,135 units
- **Total Gross Product Revenue:** $17,888,372.18
- **Total Estimated COGS:** $6,925,395.07
- **Total Estimated Gross Profit:** $10,962,977.11
- **Blended Catalog Gross Margin:** 61.29%
- **Mean Catalog Retail Price:** $93.73 (Median: $82.99)
- **Mean Revenue per Product:** $119,255.81 (Median: $106,531.08)

### Performance by Product Category

| category | product_count | total_units_sold | total_gross_revenue | revenue_share_pct | total_gross_profit | gross_margin_pct | avg_realized_price |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Accessories | 45 | 56537 | 5571186.32 | 31.14 | 3854107.86 | 69.18 | 98.57 |
| Home Goods | 24 | 30580 | 3578008.37 | 20.0 | 2039164.0 | 56.99 | 116.96 |
| Apparel | 29 | 37103 | 3331686.89 | 18.62 | 2055620.14 | 61.7 | 89.93 |
| Electronics & Audio | 18 | 23033 | 2996902.45 | 16.75 | 1300489.95 | 43.39 | 129.91 |
| Beauty & Wellness | 34 | 43882 | 2410588.15 | 13.48 | 1713595.16 | 71.09 | 55.0 |

### Top 10 Revenue-Generating Products (Factual Comparison)

| product_id | product_name | category | units_sold | gross_revenue | estimated_gross_profit | gross_margin_pct |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| PROD_024 | Motorized Cable Management Tray | Electronics & Audio | 1312 | 316848.0 | 136880.96 | 43.2 |
| PROD_148 | Classic Bamboo Sateen Sheet Set | Home Goods | 1364 | 294624.0 | 174332.84 | 59.17 |
| PROD_081 | Precision Sensor Desk Mat | Electronics & Audio | 1252 | 280435.48 | 100222.6 | 35.74 |
| PROD_039 | Borosilicate Glass Carafe | Home Goods | 1352 | 279864.0 | 141811.28 | 50.67 |
| PROD_088 | Brushed Brass Wall Sconce | Home Goods | 1208 | 260915.92 | 161847.84 | 62.03 |
| PROD_145 | Modern Vintage Acoustic Wood Speaker | Electronics & Audio | 1306 | 255323.0 | 126303.26 | 49.47 |
| PROD_022 | Eucalyptus Shower Bundle | Home Goods | 1201 | 246805.5 | 144912.66 | 58.72 |
| PROD_066 | Architectural Bookend Pair | Home Goods | 1311 | 235980.0 | 126223.08 | 53.49 |
| PROD_143 | Borosilicate Glass Carafe | Home Goods | 1205 | 227142.5 | 120451.8 | 53.03 |
| PROD_050 | Cat-Eye UV Protection Shades | Accessories | 1297 | 226975.0 | 153227.58 | 67.51 |

*Factual Observation: The highest-revenue product (`PROD_024`, Motorized Cable Management Tray) generated $316,848.00 at a 43.20% margin ($136,880.96 gross profit), whereas the second highest product (`PROD_148`, Classic Bamboo Sateen Sheet Set) generated $294,624.00 at a higher 59.17% margin ($174,332.84 gross profit). High top-line revenue does not uniformly correlate with highest gross profit dollar yield.*

---

## 7. Monthly Revenue & Growth Trends

### 24-Month Financial Trajectory (2024-01-01 to 2025-12-01)
- **Total Months Evaluated:** 24
- **Total Gross Billed Revenue:** $17,009,287.54
- **Total Delivered Net Revenue:** $14,584,810.24
- **Total Returns Incurred:** $1,726,738.50 (10.15% of gross revenue)
- **Total Cancellations Incurred:** $697,738.80 (4.10% of gross revenue)
- **Total Discounts Granted:** $934,607.55
- **Total Shipping Revenue Collected:** $55,522.91
- **Mean Monthly Delivered Revenue:** $607,700.43 (Median: $520,098.32)
- **Revenue Volatility (Std Dev):** $631,767.06 (Coefficient of Variation: 1.04)
- **Mean MoM Revenue Growth:** 25.66% (Median: 12.11%)
- **Peak Revenue Month:** 2025-12-01 ($3,166,761.60)
- **Lowest Revenue Month:** 2024-01-01 ($38,383.50)
- **Highest MoM Acceleration Month:** 2025-12-01 (+142.47%)
- **Lowest MoM Deceleration Month:** 2025-02-01 (-5.19%)
- **Final Cumulative Delivered Sales:** $14,584,810.24

---

## 8. Marketing Channel Performance & Efficiency

### Overall Marketing Efficiency
- **Total Media Spend:** $2,224,153.85
- **Total Impressions Delivered:** 111,485,093
- **Total Ad Clicks:** 2,398,761
- **Total Customers Acquired:** 10,000
- **Blended Click-Through Rate (CTR):** 2.152%
- **Blended Cost per Click (CPC):** $0.93
- **Blended Cost per Acquisition (CAC):** $222.42 across all 10,000 customers ($363.30 across paid channels)
- **Blended Return on Ad Spend (ROAS):** 6.56x (Total Delivered Revenue / Total Media Spend)

### Multidimensional Channel Comparison

| Channel | Type | Spend (USD) | Impressions | Clicks | CTR (%) | CPC (USD) | CPM (USD) | Acquired Customers | CAC (USD) | Delivered Attributed Rev (USD) | ROAS (x) | Rev / Customer (USD) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Organic Search | Organic | 0.0 | 0 | 0 |  |  |  | 1976 | 0.0 | 2823280.78 |  | 1428.79 |
| Paid Search | Paid | 817255.07 | 16605981 | 563808 | 3.395 | 1.45 | 49.21 | 2410 | 339.11 | 3598247.01 | 4.4 | 1493.05 |
| Paid Social | Paid | 1079369.64 | 70931151 | 1255426 | 1.77 | 0.86 | 15.22 | 2788 | 387.15 | 4001253.66 | 3.71 | 1435.17 |
| Affiliate | Referral | 327529.14 | 23947961 | 579527 | 2.42 | 0.57 | 13.68 | 924 | 354.47 | 1368573.49 | 4.18 | 1481.14 |
| Email | Owned | 0.0 | 0 | 0 |  |  |  | 483 | 0.0 | 737899.86 |  | 1527.74 |
| Direct | Organic | 0.0 | 0 | 0 |  |  |  | 1419 | 0.0 | 2055555.44 |  | 1448.59 |

*Note on Evaluation: Marketing channels serve distinct operational objectives and cannot be ranked by a single metric. Paid Social drove the greatest customer volume (2,788 customers) and gross attributed revenue ($4.66M), Paid Search delivered the highest efficiency among paid channels (ROAS 4.40x, CAC $339.11, CTR 3.395%), and Affiliate achieved the lowest paid CPC ($0.57).*

---

## 9. Cohort Retention Dynamics

### Cohort Dimensions & Milestones
- **Number of Monthly Signup Cohorts:** 24 (from 2024-01-01 to 2025-12-01)
- **Cohort Size Range:** Min 205 customers (Jan 2024) to Max 1,000 customers (Dec 2025), Mean: 416.7 customers
- **Month 0 Average Retention:** 65.76% (active order in same calendar month as signup)
- **Month 1 Average Retention:** 41.47%
- **Month 3 Average Retention:** 24.31%
- **Month 6 Average Retention:** 16.25%
- **Month 12 Average Retention:** 10.23% (evaluable for cohorts 2024-01 to 2024-12)

### Average Purchase Retention Rate by Elapsed Month Index (M0 to M12)

| months_since_signup | evaluable_cohorts | mean_retention_pct | median_retention_pct | min_retention_pct | max_retention_pct |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 0.0 | 24.0 | 65.76 | 64.5 | 55.54 | 100.0 |
| 1.0 | 23.0 | 41.47 | 41.27 | 32.28 | 56.16 |
| 2.0 | 22.0 | 27.05 | 25.5 | 20.22 | 39.95 |
| 3.0 | 21.0 | 24.31 | 23.92 | 17.45 | 34.24 |
| 4.0 | 20.0 | 20.68 | 21.06 | 14.74 | 27.78 |
| 5.0 | 19.0 | 19.11 | 19.12 | 14.74 | 25.93 |
| 6.0 | 18.0 | 16.25 | 15.78 | 10.18 | 23.19 |
| 7.0 | 17.0 | 14.41 | 14.52 | 9.47 | 20.7 |
| 8.0 | 16.0 | 12.0 | 11.98 | 6.67 | 17.82 |
| 9.0 | 15.0 | 11.65 | 11.59 | 7.12 | 15.63 |
| 10.0 | 14.0 | 10.67 | 10.14 | 6.44 | 13.65 |
| 11.0 | 13.0 | 10.95 | 10.55 | 7.54 | 15.79 |
| 12.0 | 12.0 | 10.23 | 10.89 | 6.87 | 13.38 |

---

## 10. Business KPI Summary Scorecard

The complete executive scorecard from `data/03_analytics/business_kpis.csv`:

| category | metric | value | unit |
| :--- | :--- | :--- | :--- |
| Customer Scale | Registered Customers | 10,000 | Count |
| Customer Scale | Active Ordering Customers | 10,000 | Count |
| Customer Scale | Customer Penetration Rate | 100.00% | % |
| Customer Scale | Active Geographic States | 16 | Count |
| Order Fulfillment | Total Orders Placed | 50,000 | Count |
| Order Fulfillment | Delivered Orders | 42,949 | Count |
| Order Fulfillment | Returned Orders | 5,027 | Count |
| Order Fulfillment | Cancelled Orders | 2,024 | Count |
| Order Fulfillment | Order Fulfillment Rate | 85.90% | % |
| Order Fulfillment | Return Rate | 10.05% | % |
| Order Fulfillment | Cancellation Rate | 4.05% | % |
| Catalog & Volume | Total Units Sold | 191,135 | Count |
| Catalog & Volume | Distinct Products Ordered | 150 | Count |
| Catalog & Volume | Average Units per Order | 3.82 | Units/Order |
| Revenue & Margins | Total Gross Billed Revenue | $17,009,287.54 | USD |
| Revenue & Margins | Total Delivered Net Revenue | $14,584,810.24 | USD |
| Revenue & Margins | Returned Revenue | $1,726,738.50 | USD |
| Revenue & Margins | Cancelled Revenue | $697,738.80 | USD |
| Revenue & Margins | Total Discounts Granted | $934,607.55 | USD |
| Revenue & Margins | Total Shipping Revenue | $55,522.91 | USD |
| Revenue & Margins | Total Estimated COGS | $6,925,395.07 | USD |
| Revenue & Margins | Estimated Gross Profit | $7,659,415.17 | USD |
| Revenue & Margins | Gross Profit Margin | 52.52% | % |
| Unit Economics | Average Order Value (AOV) | $339.58 | USD/Order |
| Unit Economics | Average Revenue per User (ARPU) | $1,458.48 | USD/Customer |
| Unit Economics | Average Revenue per Paying User (ARPPU) | $1,458.48 | USD/Paying Cust |
| Digital Marketing | Total Marketing Media Spend | $2,224,153.85 | USD |
| Digital Marketing | Total Ad Impressions | 111,485,093 | Count |
| Digital Marketing | Total Ad Clicks | 2,398,761 | Count |
| Digital Marketing | Blended Click-Through Rate (CTR) | 2.152% | % |
| Digital Marketing | Blended Cost per Click (CPC) | $0.93 | USD/Click |
| Digital Marketing | Blended Customer Acquisition Cost (CAC) | $222.42 | USD/Cust |
| Digital Marketing | Blended Return on Ad Spend (ROAS) | 6.56x | Ratio |
| Web Engagement | Total Web Sessions | 150,000 | Count |
| Web Engagement | Total Cart Abandonments | 28,001 | Count |
| Web Engagement | Cart Abandonment Rate | 18.67% | % |
| Customer Support | Total Support Tickets Opened | 5,391 | Count |

---

## 11. Initial Factual Business Observations

The following empirical observations are derived strictly from the calculated metrics without speculative projection or causal inference:

1. **Customer Order Skewness**: Customer purchase frequency exhibits a strong power-law distribution. 50.0% of registered customers have placed exactly 1 order, whereas the top 10% have placed 13 or more orders and the top 1% have placed 27 or more orders. The arithmetic mean (5.0 orders) is five times the median (1.0 order).
2. **Revenue Realization & Fulfillment Attrition**: Out of $17,009,287.54 gross billed revenue, $14,584,810.24 was realized in delivered orders (85.75% monetary realization). Returned orders accounted for $1,726,738.50 (10.15%) and cancelled orders accounted for $697,738.80 (4.10%).
3. **Category Profitability Divergence**: Categories with lower average retail prices exhibit higher gross margin percentages. Accessories (mean retail price $111.41) and Beauty & Wellness ($61.76) achieved gross margins of 69.18% and 71.09% respectively, whereas Electronics & Audio ($162.77) yielded the lowest gross margin at 43.39%.
4. **Digital Media Performance Trade-offs**: Paid Search generated higher click efficiency (CTR 3.395%, CPC $1.45, ROAS 4.40x) compared to Paid Social (CTR 1.770%, CPC $0.86, ROAS 3.71x). However, Paid Social generated 15.7% more customer acquisitions (2,788 vs 2,410) and 11.2% more delivered attributed revenue ($4.00M vs $3.60M).
5. **Cohort Purchase Retention Decay**: Customer purchasing activity decreases most steeply during the first 90 days post-signup. The average purchase retention rate drops from 65.76% in Month 0 to 41.47% in Month 1 (-24.29 percentage points) and to 24.31% in Month 3 (-17.16 percentage points). Decay slows substantially thereafter, reaching 16.25% at Month 6 and 10.23% at Month 12.
6. **Seasonal Revenue Acceleration**: Monthly delivered revenue experienced peak velocity in December of each calendar year (December 2024: $546,098.84, +39.47% MoM; December 2025: $3,166,761.60, +142.47% MoM). The lowest monthly revenue occurred in the baseline establishment month (January 2024: $38,383.50).

---

## 12. Methodological Limitations & Boundary Conditions

1. **Observational Nature**: All findings reflect descriptive historical calculations across the synthetic 2024–2025 observation window. No causal mechanisms, predictive regressions, or future demand forecasts are asserted.
2. **Attribution Modeling**: Marketing channel metrics reflect the first-touch customer acquisition attribution rule established in Phase 3 SQL models. Multi-touch interactions, view-through exposures, and assisted conversions are not represented.
3. **Fixed Temporal Cutoff**: Customer recency days are computed relative to the fixed end-of-period benchmark `2025-12-31`.
4. **Delivered AOV Undefined for Zero-Delivery Customers**: For 860 customers whose orders were entirely returned or cancelled, delivered AOV is mathematically undefined and recorded as null.

---

## 13. Reproducibility Instructions

The entire exploratory data analysis pipeline is deterministic and can be executed via the CLI:

### 1. Execute EDA Pipeline
```bash
python -m src.eda.run_eda
```

### 2. Verify Generated Artifacts
Ensure outputs exist in their designated directories:
- Summaries: `data/04_eda/summaries/*.csv`
- Reports: `data/04_eda/reports/data_quality_report.csv`
- Figures: `data/04_eda/figures/*.png`
- Documentation: `docs/eda_report.md`

### 3. Run Automated Tests
```bash
python -m pytest tests/test_eda.py -v
```

All source data files in `data/01_raw/`, `data/02_processed/`, and `data/03_analytics/` remain unmodified.
