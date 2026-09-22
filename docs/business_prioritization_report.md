# Aura Retail Analytics — Phase 5 Part 2: Business Prioritization & Actionable Customer Intelligence Report

**Project:** Aura Retail Marketing & Customer Analytics  
**Phase:** Phase 5 Part 2 — Business Prioritization & Actionable Customer Intelligence  
**Core Purpose:** Decision-Support Layer Integrating Churn Risk & Business Impact  
**Analytical Population:** Exactly 10,000 Registered Customers  

---

## 1. Executive Summary

Phase 5 Part 2 operationalizes the machine learning churn predictions from Phase 5 Part 1 by creating a transparent, rule-based **decision-support and customer business-prioritization layer**. 

Rather than relying on churn risk in isolation, this phase systematically pairs **churn probability** with **historical delivered value**, **engagement momentum**, and **customer friction signals**. The resulting framework enables marketing, CRM, and retention teams to allocate resources where business impact and retention urgency intersect, identifying **5,623 high-risk customers (56.23%)** associated with **$1,619,864.84** in historical delivered revenue.

---

## 2. Objective

The objective of Phase 5 Part 2 is to answer the fundamental commercial question:
> *"Which customers possess meaningful churn risk and business value, and how should they be categorized for downstream business action?"*

This framework functions strictly as a **decision-support layer** designed to guide campaign planning and intervention budgeting. It is **not** a causal predictive model, and recommendations do not guarantee customer retention outcomes.

---

## 3. Data Sources

This layer ingests and joins two authoritative datasets:
1. **Customer Intelligence Layer (`data/04_customer_intelligence/customer_intelligence.csv`):**
   - 10,000 customers x 47 columns (Phase 4 Part 3).
   - Ingests verified profiles, acquisition channels, delivered revenue, order volume, recency, web sessions, and friction metrics.
2. **Phase 5 Part 1 Churn Predictions (`data/05_churn/churn_predictions.csv`):**
   - 10,000 customers x 4 columns (Phase 5 Part 1 champion Random Forest output).
   - Ingests `churn_probability`, `predicted_churn`, and descriptive `churn_risk_band`.

---

## 4. Input & Join Validation

Data ingestion executed a controlled, verified join strictly on `customer_id`:
- **Customer Intelligence Rows:** 10,000
- **Churn Prediction Rows:** 10,000
- **Primary Key Join Integrity:** 100% matched, exactly 1 row per customer, 0 duplicate keys, 0 unmatched records, 0 customer drops.
- **Missing Value Handling:** Zero missing values in all score, tier, segment, and recommendation columns.

---

## 5. Risk Score (`risk_score`)

- **Formula:** $\text{risk\_score} = \text{churn\_probability}$
- **Basis:** Directly consumes the calibrated churn probabilities from the Phase 5 Part 1 Random Forest champion model.
- **Normalization:** Naturally bounded in $[0.0, 1.0]$ with an empirical mean of **0.5125** and median of **0.6627**.
- **Interpretation:** Reflects model-estimated likelihood of customer dormancy. It does not represent guaranteed future churn.

---

## 6. Value Score (`value_score`)

- **Basis:** Historical delivered net revenue (`delivered_revenue`).
- **Formula:**
  $$\text{value\_score} = \begin{cases} 0.0 & \text{if } \text{delivered\_revenue} = 0 \\ \text{percentile\_rank}(\text{delivered\_revenue}) & \text{if } \text{delivered\_revenue} > 0 \end{cases}$$
- **Properties:** Bounded in $[0.0, 1.0]$. The 860 customers with zero delivered orders receive exactly $0.0$, while positive earners are ranked smoothly, eliminating distortion from high-revenue outliers ($15,000+).

---

## 7. Engagement Score (`engagement_score`)

- **Downstream Formulation:**
  $$\text{recency\_comp} = 1.0 - \frac{\text{recency\_days}}{\max(\text{recency\_days})}$$
  $$\text{session\_comp} = \text{percentile\_rank}(\text{total\_web\_sessions})$$
  $$\text{order\_comp} = \text{percentile\_rank}(\text{delivered\_orders})$$
  $$\text{engagement\_score} = 0.50 \cdot \text{recency\_comp} + 0.30 \cdot \text{session\_comp} + 0.20 \cdot \text{order\_comp}$$
- **Important Methodological Distinction:** While `recency_days` was quarantined from the Phase 5 Part 1 machine learning model to prevent target leakage, it is intentionally and appropriately utilized here as a **downstream descriptive business-prioritization variable**.

---

## 8. Customer Friction Score (`friction_score`)

- **Formulation:**
  $$\text{order\_friction} = \text{friction\_rate} = \frac{\text{returned\_orders} + \text{cancelled\_orders}}{\text{total\_orders}}$$
  $$\text{cart\_friction} = \text{cart\_abandonment\_rate}$$
  $$\text{ticket\_friction} = \min\left(\frac{\text{total\_support\_tickets}}{3.0}, 1.0\right)$$
  $$\text{friction\_score} = 0.40 \cdot \text{order\_friction} + 0.35 \cdot \text{cart\_friction} + 0.25 \cdot \text{ticket\_friction}$$
- **Directionality:** Higher score reflects greater customer friction and fulfillment difficulty.

---

## 9. Composite Priority Score (`priority_score`)

- **Configured Weighted Formula:**
  $$\text{priority\_score} = 0.5 \cdot \text{risk\_score} + 0.3 \cdot \text{value\_score} + 0.1 \cdot \text{engagement\_score} + 0.1 \cdot \text{friction\_score}$$
- **Weight Verification:** $0.50 + 0.30 + 0.10 + 0.10 = 1.00$ (all weights $\ge 0$).
- **No Min-Max Scaling:** In strict accordance with methodological standards, **no min-max scaling is applied**. The weighted sum serves as the final priority score, naturally bounded in $[0.0, 1.0]$:
  - Mean Priority Score: **0.4709**
  - Min / Max Priority Score: **0.3179 / 0.7073**

---

## 10. Priority Tiers (`priority_tier`)

Deterministic business thresholds:
- **High Priority:** $\text{priority\_score} \ge 0.75$
- **Medium Priority:** $0.5 \le \text{priority\_score} < 0.75$
- **Low Priority:** $\text{priority\_score} < 0.5$

### Measured Priority Tier Distribution:
| Priority Tier | Customer Count | Population Share (%) | Total Delivered Revenue | Revenue Share (%) | Mean Priority Score | Mean Churn Prob |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **High Priority** | 0 | 0.00% | $0.00 | 0.00% | 0.0000 | 0.0000 |
| **Medium Priority** | 2,491 | 24.91% | $4,581,028.78 | 31.41% | 0.5387 | 0.6027 |
| **Low Priority** | 7,509 | 75.09% | $10,003,781.46 | 68.59% | 0.4484 | 0.4826 |

---

## 11. Mutually Exclusive Business Segmentation (`business_segment`)

Every customer is deterministically assigned to exactly ONE business segment using a strict 9-step precedence hierarchy:

| Rank | Business Segment | Customer Count | Share (%) | Total Revenue ($) | Revenue Share (%) | Mean Churn Prob |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | **High Risk / High Value / High Friction** | 0 | 0.00% | $0.00 | 0.00% | 0.0000 |
| 2 | **High Risk / High Value** | 167 | 1.67% | $222,920.39 | 1.53% | 0.7950 |
| 3 | **High Risk / Mid Value** | 1,894 | 18.94% | $962,369.06 | 6.60% | 0.6732 |
| 4 | **High Risk / Low Value** | 3,562 | 35.62% | $434,575.39 | 2.98% | 0.6979 |
| 5 | **Medium Risk / High Value** | 119 | 1.19% | $271,560.18 | 1.86% | 0.3824 |
| 6 | **Medium Risk / Developing** | 420 | 4.20% | $169,944.49 | 1.17% | 0.5583 |
| 7 | **Low Risk / High Value** | 3,331 | 33.31% | $12,200,744.02 | 83.65% | 0.2294 |
| 8 | **Low Risk / Developing** | 375 | 3.75% | $282,675.38 | 1.94% | 0.2880 |
| 9 | **Low Value / Inactive** | 49 | 0.49% | $3,032.33 | 0.02% | 0.6300 |
| 10 | **General Monitoring** | 83 | 0.83% | $36,989.00 | 0.25% | 0.5845 |

---

## 12. Recommended Customer Actions (`recommended_action`)

Deterministic rule hierarchy:
1. **High-Value Retention + Friction Resolution:** High Risk + High Value + High Friction.
2. **Retention / High-Value Intervention:** High Risk + High Value.
3. **Targeted Retention:** High Risk + Mid/Low Value.
4. **Friction Resolution:** High Friction across moderate risk.
5. **Engagement Reinforcement:** Medium Priority + Active/Lapsing engagement.
6. **Relationship Development:** Low Risk + High/Mid Value.
7. **Monitor:** Fallback for low-risk, low-priority, or stable accounts.

### Recommended Action Summary:
| Recommended Action Category | Customer Count | Share (%) | Total Revenue ($) | Mean Priority Score | Mean Churn Prob |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **High-Value Retention + Friction Resolution** | 0 | 0.00% | $0.00 | 0.0000 | 0.0000 |
| **Retention / High-Value Intervention** | 167 | 1.67% | $222,920.39 | 0.6515 | 0.7950 |
| **Targeted Retention** | 5,456 | 54.56% | $1,396,944.45 | 0.4772 | 0.6893 |
| **Friction Resolution** | 834 | 8.34% | $1,733,932.51 | 0.4397 | 0.3016 |
| **Engagement Reinforcement** | 419 | 4.19% | $2,502,740.89 | 0.5247 | 0.3410 |
| **Relationship Development** | 2,797 | 27.97% | $8,471,900.68 | 0.4493 | 0.2390 |
| **Monitor** | 327 | 3.27% | $256,371.32 | 0.4672 | 0.5153 |

---

## 13. Recommended Campaign Categories (`recommended_campaign`)

Mapped 1-to-1 from actionable categories for marketing workflow alignment:
- **High-Value Retention Campaign:** Dedicated account management, VIP white-glove re-engagement.
- **Targeted Retention Campaign:** Cost-effective automated discount incentives.
- **Friction Resolution Campaign:** Post-return survey, customer care voucher outreach.
- **Engagement Reinforcement Campaign:** Cart recovery, personalized browsed product alerts.
- **Loyalty & Relationship Campaign:** Early access to new releases, tier-based loyalty perks.
- **Automated Monitoring:** Passive low-touch communication.

---

## 14. High-Risk Customer Analysis

- **High-Risk Definition:** Model-estimated churn probability $\ge 0.65$ (`churn_risk_band == 'High Risk'`).
- **High-Risk Population:** **5,623 accounts (56.23%)**.
- **Historical Spend Distribution Among High-Risk:**
  - High Value ($\ge \$1,000$): 167 customers ($222,920.39)
  - Mid Value ($\$300 - \$1,000$): 1,894 customers ($962,369.06)
  - Low Value ($< \$300$): 2,813 customers ($434,575.39)
  - Zero Value ($0): 749 customers ($0.00)

---

## 15. Revenue Associated With High-Risk Customers

> **Important Terminology & Methodological Constraint:**  
> This metric represents **Historical Delivered Revenue Associated With High-Risk Customers**. It is **NOT** guaranteed revenue loss or a predicted financial deficit.

| Metric | Measured Value |
| :--- | :---: |
| **Total Historical Delivered Revenue (All Customers)** | **$14,584,810.24** |
| **Delivered Revenue Associated With High-Risk Customers** | **$1,619,864.84** |
| **Share of Total Portfolio Revenue** | **11.11%** |
| **High-Risk High-Value Revenue Share** | **$222,920.39 (1.53%)** |

---

## 16. Limitations & Business Interpretation

1. **Decision-Support Framing:** The prioritization score and tiers represent heuristic business-rule frameworks designed for operational triage, not statistical ground truth.
2. **Proxy Churn Constraint:** Churn risk indicates dormancy relative to `10,000` customer snapshot behavior, not contractual subscription cancellation.
3. **Absence of Treatment Effect Measurement:** Recommended campaigns and actions are analytical suggestions. They have not been validated through randomized controlled A/B testing.
4. **Non-Equivalence to Loss:** Revenue associated with high-risk customers reflects historical spend; it must not be treated as revenue guaranteed to disappear.

---

## 17. Conclusion & Next Steps

Phase 5 Part 2 successfully delivers a complete, leak-free, and deterministic decision-support dataset (`data/05_churn/business_prioritization.csv`) containing 22 analytical and prioritization columns across all 10,000 customers.

### Pipeline Reproducibility Command:
```powershell
python -m src.prioritization.runner
```

---
*Report automatically compiled by Aura Retail Phase 5 Part 2 Pipeline.*
