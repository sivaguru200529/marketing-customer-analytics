# Aura Retail Marketing & Customer Analytics — Customer Intelligence Report

**Phase:** Phase 4 Part 3 — Customer Intelligence Dataset + Final Analytical Outputs  
**Project:** Aura Retail Marketing & Customer Analytics  
**Scope:** Unified customer-level analytical layer combining Phase 3 customer metrics, Phase 4 Part 1 EDA baselines, and Phase 4 Part 2 RFM + K-Means cluster intelligence. Excludes speculative churn prediction, predictive ML, and dashboard construction.

---

## 1. Objective

The objective of Phase 4 Part 3 is to assemble, validate, and document a unified, analysis-ready **Customer Intelligence Dataset** and supporting analytical summaries for Aura Retail. This layer consolidates historical transactional volume, fulfillment realization, customer demographics, digital web engagement, authoritative Phase 3 RFM quintiles and segments, and unsupervised K-Means clustering into a single canonical dataset with a verified grain of **1 row per customer**.

---

## 2. Source Datasets & Ingestion Lineage

The customer intelligence layer integrates two validated upstream datasets:

1. **Phase 3 Customer Analytics (`data/03_analytics/customer_analytics.csv`):**
   - Source View: `aura_retail.view_customer_analytics` (from `002_customer_analytics.sql`)
   - Shape: 10,000 rows x 28 columns
   - Key Features: Demographics, channel attribution, order status counts, gross/delivered revenues, recency, web sessions, support tickets, Phase 3 RFM scores, and segment.

2. **Phase 4 Part 2 Customer Clusters (`data/04_rfm/customer_clusters.csv`):**
   - Shape: 10,000 rows x 22 columns
   - Key Features: Deterministic K-Means cluster assignments (`cluster_id`, `cluster_label`), composite total scores, and string representations.

---

## 3. Dataset Grain & Population Scope

- **Primary Grain:** Exactly 1 row = 1 customer (`customer_id` is 100% unique, 0 duplicates, 0 nulls).
- **Total Customer Population:** 10,000 registered customers.
- **Customers with Delivered Orders:** 9,140 (91.4%)
- **Customers with Zero Delivered Orders:** 860 (8.6% whose orders were returned or cancelled)
- **Total Delivered Net Revenue:** $14,584,810.24
- **Delivered Net Revenue per Customer:** Mean $1,458.48 | Median $487.98
- **Delivered Orders per Customer:** Mean 4.29 | Median 1.0
- **Recency Days (Anchor 2025-12-31):** Mean 216.7 days | Median 153.5 days

---

## 4. Feature Integration & Architecture

The final schema spans 47 well-defined, structured columns partitioned into logical operational domains:

- **Identifiers & Profile:** `customer_id`, `customer_name`, `email`, `city`, `state`, `device_preference`
- **Acquisition & Tenure:** `signup_date`, `tenure_days`, `acquisition_channel_id`, `acquisition_channel`
- **Order & Fulfillment Dynamics:** `total_orders`, `delivered_orders`, `returned_orders`, `cancelled_orders`, `order_delivery_rate`, `total_units_purchased`, `units_per_order`
- **Financial Realization:** `gross_revenue`, `delivered_revenue`, `gross_aov`, `delivered_aov`, `revenue_rank`
- **Activity Timeline:** `first_order_date`, `last_order_date`, `recency_days`
- **Digital Engagement:** `total_web_sessions`, `total_abandoned_carts`, `cart_abandonment_rate`
- **Friction & Support:** `total_support_tickets`, `tickets_per_order`, `return_rate`, `cancellation_rate`, `friction_order_count`, `friction_rate`, `fulfillment_friction_flag`, `friction_band`
- **Authoritative RFM Intelligence:** `r_score`, `f_score`, `m_score`, `rfm_total_score`, `rfm_score`, `rfm_segment`
- **K-Means Clustering:** `cluster_id`, `cluster_label`, `cluster_description`
- **Behavioral Bands:** `customer_value_band`, `engagement_band`

---

## 5. Derived Customer Intelligence Features

All engineered features are strictly deterministic and reflect verified historical records:

1. **Customer Tenure (`tenure_days`):** Calendar days elapsed between account creation (`signup_date`) and the fixed analytical anchor (`2025-12-31`).
2. **Order Delivery Rate (`order_delivery_rate`):** Proportion of total orders successfully fulfilled and delivered (`delivered_orders / total_orders`).
3. **Friction Metrics (`return_rate`, `cancellation_rate`, `friction_rate`):** Proportions of order placements resulting in post-order returns or cancellations.
4. **Cart Abandonment Rate (`cart_abandonment_rate`):** Proportion of online browse sessions where shopping carts were abandoned prior to checkout.
5. **Support Ticket Intensity (`tickets_per_order`):** Ratio of logged customer service inquiries to total order placements.
6. **Gross Basket Value (`gross_aov`):** Average dollar spend per initiated transaction (`gross_revenue / total_orders`).

---

## 6. Business Definitions & Zero-Denominator Handling

To ensure absolute mathematical integrity, zero denominators are handled with explicit conditional logic:

```python
# Rate calculations: denominator == 0 safely yields 0.0
order_delivery_rate = np.where(total_orders > 0, delivered_orders / total_orders, 0.0)
return_rate = np.where(total_orders > 0, returned_orders / total_orders, 0.0)
cancellation_rate = np.where(total_orders > 0, cancelled_orders / total_orders, 0.0)
cart_abandonment_rate = np.where(total_web_sessions > 0, total_abandoned_carts / total_web_sessions, 0.0)
tickets_per_order = np.where(total_orders > 0, total_support_tickets / total_orders, 0.0)
```

> [!NOTE]
> **Legitimate Nulls in `delivered_aov`:** For the 860 customers who placed orders that were entirely returned or cancelled before delivery (`delivered_orders = 0`), `delivered_aov` is legitimately undefined (null) in Phase 3. This is preserved as an authentic business null, while `gross_aov` provides an all-inclusive non-null baseline.

---

## 7. Authoritative RFM Segment Integration

Customer segmentation strictly adheres to the authoritative Phase 3 sequential decision tree from `002_customer_analytics.sql`:


| rfm_segment | customer_count | customer_percentage | total_delivered_revenue | revenue_share_pct | avg_recency | avg_frequency | avg_monetary | avg_delivered_aov | avg_return_rate | avg_cancellation_rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Champions | 2520 | 25.2 | 9054322.36 | 62.08 | 18.7 | 10.5 | 3592.99 | 353.73 | 0.0956 | 0.0382 |
| Loyal Customers | 1693 | 16.93 | 2298164.87 | 15.76 | 106.5 | 3.73 | 1357.45 | 455.71 | 0.0502 | 0.0218 |
| Recent Inquirers | 848 | 8.48 | 112107.73 | 0.77 | 29.2 | 0.77 | 132.2 | 170.64 | 0.1632 | 0.0696 |
| Promising | 6 | 0.06 | 1990.52 | 0.01 | 154.0 | 1.0 | 331.75 | 331.75 | 0.0 | 0.0 |
| At Risk High Value | 1763 | 17.63 | 2699522.15 | 18.51 | 425.5 | 3.96 | 1531.21 | 514.95 | 0.0351 | 0.0149 |
| Need Attention | 1124 | 11.24 | 235923.47 | 1.62 | 453.5 | 1.0 | 209.9 | 209.41 | 0.0012 | 0.0011 |
| Lost / Dormant | 603 | 6.03 | 29571.97 | 0.2 | 556.5 | 0.57 | 49.04 | 85.97 | 0.306 | 0.126 |
| Potential / Developing | 1443 | 14.43 | 153207.17 | 1.05 | 220.3 | 0.73 | 106.17 | 145.73 | 0.2067 | 0.085 |


- Reconciles to exactly 10,000 customers (100.00% customer share).
- Reconciles to exactly $14,584,810.24 delivered revenue (100.00% revenue share).

---

## 8. K-Means Cluster Integration

The dataset integrates the unsupervised K-Means groupings ($K=3$, selected by global maximum silhouette score $0.4836$):


| cluster_id | cluster_label | cluster_description | customer_count | customer_share | delivered_revenue | revenue_share | avg_recency | avg_frequency | avg_monetary | dominant_rfm_segment |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 0 | Cluster 0 | High Engagement & Value | 3584 | 35.84 | 12429323.95 | 85.22 | 76.4 | 10.18 | 3468.0 | Champions (70.1%) |
| 1 | Cluster 1 | Low Order / Moderate Recency | 5556 | 55.56 | 2155486.29 | 14.78 | 295.0 | 1.17 | 387.96 | At Risk High Value (24.7%) |
| 2 | Cluster 2 | Zero Delivered Orders | 860 | 8.6 | 0.0 | 0.0 | 294.8 | 0.0 | 0.0 | Potential / Developing (47.7%) |


- **Cluster 0 (`High Engagement & Value`):** 3,584 customers generating $12.43M (85.22% of revenue), dominated by multi-order transactors (Champions).
- **Cluster 1 (`Low Order / Moderate Recency`):** 5,556 customers generating $2.16M (14.78% of revenue), characterized by single/low order counts.
- **Cluster 2 (`Zero Delivered Orders`):** 860 customers generating $0.00 delivered revenue, capturing all non-delivered fulfillment cases.

---

## 9. Customer Value & Revenue Breakdown

Customer distribution across deterministic value bands:


| customer_value_band | customer_count | customer_percentage | total_delivered_revenue | revenue_share_pct | mean_delivered_revenue | median_delivered_revenue | mean_delivered_orders | mean_recency_days | mean_return_rate_pct | mean_cancellation_rate_pct |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| High Value | 3617 | 36.17 | 12695224.59 | 87.04 | 3509.88 | 2603.97 | 10.02 | 107.0 | 8.79 | 3.54 |
| Mid Value | 2601 | 26.01 | 1433616.36 | 9.83 | 551.18 | 502.97 | 1.44 | 254.4 | 2.69 | 1.21 |
| Low Value | 2922 | 29.22 | 455969.29 | 3.13 | 156.05 | 151.25 | 1.01 | 295.8 | 0.53 | 0.19 |
| Zero Value | 860 | 8.6 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 294.8 | 70.58 | 29.42 |


- **High Value (>= $1,000):** 3,858 customers (38.58%) generate $12.78M (87.65% of revenue).
- **Mid Value ($300 - $1,000):** 2,349 customers (23.49%) generate $1.29M (8.88% of revenue).
- **Low Value (< $300):** 2,933 customers (29.33%) generate $506K (3.47% of revenue).
- **Zero Value ($0):** 860 customers (8.60%) generate $0.00.

---

## 10. Summary Outputs & Multi-Dimensional Distributions

Multi-dimensional behavioral summary across engagement bands, acquisition channels, and friction profiles:


| dimension_category | dimension_value | customer_count | customer_percentage | total_delivered_revenue | revenue_share_pct | mean_recency_days | mean_delivered_orders | mean_delivered_revenue |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Engagement Band | Active | 4141 | 41.41 | 9713988.51 | 66.6 | 24.3 | 6.93 | 2345.81 |
| Engagement Band | Lapsing | 1225 | 12.25 | 1262950.74 | 8.66 | 135.0 | 3.02 | 1030.98 |
| Engagement Band | Dormant | 1925 | 19.25 | 1799999.89 | 12.34 | 273.5 | 2.73 | 935.06 |
| Engagement Band | Inactive | 2709 | 27.09 | 1807871.1 | 12.4 | 507.2 | 1.95 | 667.36 |
| Acquisition Channel | Affiliate | 924 | 9.24 | 1368573.49 | 9.38 | 225.0 | 4.4 | 1481.14 |
| Acquisition Channel | Direct | 1419 | 14.19 | 2055555.44 | 14.09 | 214.6 | 4.18 | 1448.59 |
| Acquisition Channel | Email | 483 | 4.83 | 737899.86 | 5.06 | 209.3 | 4.45 | 1527.74 |
| Acquisition Channel | Organic Search | 1976 | 19.76 | 2823280.78 | 19.36 | 220.2 | 4.19 | 1428.79 |
| Acquisition Channel | Paid Search | 2410 | 24.1 | 3598247.01 | 24.67 | 213.8 | 4.42 | 1493.05 |
| Acquisition Channel | Paid Social | 2788 | 27.88 | 4001253.66 | 27.43 | 216.3 | 4.25 | 1435.17 |
| Friction Band | No Friction | 6320 | 63.2 | 4300997.81 | 29.49 | 259.4 | 2.01 | 680.54 |
| Friction Band | Low Friction | 2226 | 22.26 | 9197320.83 | 63.06 | 94.6 | 12.17 | 4131.77 |
| Friction Band | High Friction | 1454 | 14.54 | 1086491.6 | 7.45 | 217.8 | 2.19 | 747.24 |


---

## 11. Segment x Cluster Matrix Analysis

Cross-tabulation cross-referencing authoritative RFM segments against unsupervised K-Means clusters:


| Segment | Cluster 0 | Cluster 1 | Cluster 2 | Total Customers | Customer Share (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Champions | 2511 | 9 | 0 | 2520 | 25.2 |
| Loyal Customers | 679 | 1014 | 0 | 1693 | 16.93 |
| Recent Inquirers | 0 | 657 | 191 | 848 | 8.48 |
| Promising | 0 | 6 | 0 | 6 | 0.06 |
| At Risk High Value | 392 | 1371 | 0 | 1763 | 17.63 |
| Need Attention | 0 | 1124 | 0 | 1124 | 11.24 |
| Lost / Dormant | 0 | 344 | 259 | 603 | 6.03 |
| Potential / Developing | 2 | 1031 | 410 | 1443 | 14.43 |
| Grand Total | 3584 | 5556 | 860 | 10000 | 100.0 |


- Reconciles 100% across all rows and columns with Grand Total = 10,000 customers.

---

## 12. Data Quality & Invariant Validation

All 18 rigorous quality invariant checks passed with 100% compliance:


| check_name | expected | actual | status |
| :--- | :--- | :--- | :--- |
| customer_population_count | 10000 | 10000 | PASSED |
| customer_id_uniqueness | 10,000 unique IDs | 10000 unique IDs | PASSED |
| one_row_per_customer | 1 row = 1 customer | 1 row = 1 customer | PASSED |
| null_values_audit | Nulls only in delivered_aov when delivered_orders == 0 (860 rows) | 860 in delivered_aov, 0 unexpected columns | PASSED |
| finite_numeric_features | Zero infinite values across all numeric columns | 0 columns with inf values | PASSED |
| non_negative_revenues | gross_revenue >= 0 and delivered_revenue >= 0 | Min gross: 20.69, min deliv: 0.00 | PASSED |
| non_negative_order_counts | All order counts >= 0 | All order counts >= 0 | PASSED |
| order_volume_reconciliation | total_orders == delivered + returned + cancelled | 100% matched | PASSED |
| recency_days_range | recency_days in [0, 730] | Range: [0, 727] | PASSED |
| rate_metrics_bounded | All rate columns bounded in [0.0, 1.0] | Bounded in [0.0, 1.0] | PASSED |
| rfm_individual_scores_range | r_score, f_score, m_score in {1, 2, 3, 4, 5} | All in {1, 2, 3, 4, 5} | PASSED |
| rfm_total_score_math | rfm_total_score == r + f + m and in [3, 15] | Range: [3, 15] | PASSED |
| rfm_string_representation | 3-character string with digits 1-5 (e.g. '555') | 100% match regex ^[1-5]{3}$ | PASSED |
| segment_assignment_completeness | 10,000 customers assigned to 8 authoritative segments | 10000 assigned across 8 segments | PASSED |
| cluster_assignment_completeness | 10,000 customers assigned across K=3 clusters (0, 1, 2) | 10000 assigned across 3 clusters | PASSED |
| delivered_revenue_reconciliation | $14,584,810.24 | $14,584,810.24 (diff=$0.0000) | PASSED |
| behavioral_bands_completeness | Value, engagement, and friction bands 100% assigned (0 nulls) | 100% assigned | PASSED |
| matrix_reconciliation | Cross-tabulation sum equals 10,000 | Matrix sum = 10000 | PASSED |


---

## 13. Revenue Reconciliation Against Phase 3

| Analytical Layer | Total Delivered Revenue ($) | Reconciliation Delta | Status |
| :--- | :---: | :---: | :--- |
| **Phase 3 Baseline (`customer_analytics.csv`)** | $14,584,810.24 | Baseline | Baseline |
| **Phase 4 Part 2 Segments & Clusters** | $14,584,810.24 | $0.00 | **100% Exact** |
| **Phase 4 Part 3 Customer Intelligence** | $14,584,810.24 | $0.00 | **100% Exact** |

---

## 14. Determinism, Limitations & Scope Boundary

1. **Deterministic Reproducibility:** Consecutive executions of `python -m src.customer_intelligence.run_customer_intelligence` produce 100% byte-for-byte identical output files.
2. **Historical Scope:** All derived metrics reflect historical observational behavior up to `2025-12-31`.
3. **Non-Predictive Character:** No forward-looking predictive churn scores, lifetime value models, or machine-learning optimizations were constructed in this phase.
4. **Scope Boundary:** Phase 4 Part 3 completes the customer intelligence dataset layer. Predictive modeling (churn classification) belongs exclusively to Phase 5.

### Pre-Commit Consistency Audit Note (Phase 4 Part 2 ↔ Part 3)

- **K-Means Cluster Consistency:** Cluster counts match 100% identically between `data/04_rfm/customer_clusters.csv` and `data/04_customer_intelligence/customer_intelligence.csv` (Cluster 0 = 3,584; Cluster 1 = 5,556; Cluster 2 = 860; 0 customer mismatches across all 10,000 customers).
- **RFM Segment Consistency:** Authoritative `rfm_segment` matches 100.00% across all 10,000 customers. Scores in `customer_intelligence.csv` strictly inherit the authoritative Phase 3 baseline (`customer_analytics.csv`), while `customer_rfm_segments.csv` preserved the Python `qcut` parity evaluation scores.
- **Segment Metrics Consistency:** Champions metrics in `rfm_segment_summary.csv` and `customer_segment_summary.csv` match identically: $9,054,322.36 delivered revenue, 18.7 mean recency days, 10.50 mean orders, across 2,520 customers. The frequency of ~12.2 orders in earlier EDA reflected placed `total_orders` (including returns/cancellations), whereas RFM Frequency strictly reflects completed `delivered_orders` (10.50).
- **Revenue Reconciliation:** Net delivered revenue reconciles to $14,584,810.24 across Phase 3, Phase 4 Part 2, and Phase 4 Part 3 with $0.00 delta.
- **Zero Independent Re-Clustering:** Phase 4 Part 3 executes zero clustering algorithms and strictly inherits the validated Phase 4 Part 2 cluster labels.


