# Business Requirements Document (BRD)
## Project: Marketing & Customer Analytics — Aura Retail

---

## 1. Executive Context & Business Problem
**Aura Retail** is a modern, fast-growing Direct-to-Consumer (D2C) e-commerce retailer selling multi-category lifestyle products across North America. Over the past 24 months, the company scaled customer acquisition aggressively across multiple paid and organic marketing channels. 

However, executive leadership (Chief Marketing Officer, Chief Commercial Officer, and Head of Retention) faces three critical strategic challenges:
1. **Lack of Channel Efficiency Visibility**: While total customer acquisition has grown, the blended Customer Acquisition Cost (CAC) has climbed. The marketing team lacks unified attribution to measure which channels yield customers with high long-term value versus one-time bargain hunters.
2. **Homogeneous Customer Engagement**: All customers currently receive broad promotional campaigns. The company lacks empirical customer segmentation (RFM and behavioral clustering) to tailor lifecycle marketing, resulting in wasted ad spend and margin erosion from excessive discounting.
3. **Silent Customer Churn**: Customers stop purchasing without explicit cancellation signals. High-value repeat customers are slipping into dormancy unnoticed until it is too late to win them back profitably.

---

## 2. Project Objectives
The objective of this analytics initiative is to build a robust, reproducible marketing and customer analytics data product that addresses these core challenges:

1. **Purchasing Behavior Analysis**:
   - Quantify repeat purchase cycles, basket composition, seasonal demand spikes, and order value distributions.
   - Establish baseline customer retention rates by monthly acquisition cohorts.
2. **Marketing Attribution & Unit Economics**:
   - Track and report blended and channel-specific Customer Acquisition Cost (CAC) and Return on Ad Spend (ROAS).
   - Evaluate long-term customer value contribution by acquisition source.
3. **Dual-Model Customer Segmentation**:
   - Implement **RFM (Recency, Frequency, Monetary)** rule-based segmentation for immediate operational use by CRM and email marketing teams.
   - Implement **K-Means clustering** to discover multi-dimensional behavioral segments based on discount sensitivity, session activity, and category diversity.
4. **Predictive Churn Modeling**:
   - Formulate a strict business definition for e-commerce churn based on inter-purchase velocity.
   - Train and evaluate a supervised classification model to estimate individual churn probabilities.
5. **High-Value At-Risk Identification**:
   - Cross-reference high-spending customer segments with high predicted churn probabilities to isolate revenue-at-risk.
   - Output an actionable retention watch-list for targeted VIP win-back campaigns.
6. **Executive & Operational BI Reporting**:
   - Deliver an interactive, multi-page Power BI dashboard providing drill-through visibility from high-level executive KPIs down to individual customer retention actions.

---

## 3. Key Stakeholders & Core Business Questions

| Stakeholder Persona | Core Business Questions to Answer |
| :--- | :--- |
| **Chief Marketing Officer (CMO)** | Which marketing channels deliver the highest ROAS? Where should we reallocate next quarter's acquisition budget? What is our blended CAC trend? |
| **Head of Customer Retention / CRM** | What is our month-over-month cohort retention rate? Who are our top-tier "Champion" customers, and how can we prevent high-value customers from churning? |
| **E-Commerce Merchandising Lead** | What are our top-performing product categories? Which categories drive immediate second purchases? How does discount usage impact long-term margins? |
| **Senior Leadership / CCO** | What is our total Net Revenue and MoM growth rate? How much annual recurring revenue is currently at risk of customer attrition? |

---

## 4. Key Performance Indicators (KPIs) & Target Definitions

- **Gross Revenue**: Sum of total sales before returns and discounts.
- **Net Revenue**: Gross revenue minus discount value and refunded return value.
- **Average Order Value (AOV)**: $\frac{\text{Net Revenue}}{\text{Total Orders}}$.
- **Customer Acquisition Cost (CAC)**: $\frac{\text{Total Marketing Channel Spend}}{\text{Total Attributed New Customer Signups}}$.
- **Return on Ad Spend (ROAS)**: $\frac{\text{Attributed Net Revenue}}{\text{Total Marketing Ad Spend}}$.
- **Repeat Purchase Rate**: $\frac{\text{Customers with } \ge 2 \text{ Orders}}{\text{Total Unique Customers}}$.
- **Cohort Retention Rate ($M_k$)**: $\frac{\text{Active Customers in Month } k}{\text{Initial Cohort Size in Month } 0} \times 100\%$.
- **Revenue at Risk**: Total historical spend of active/recent customers whose predicted churn probability exceeds the high-risk threshold ($\ge 0.65$).

---

## 5. Scope & Constraints
- **Scope**: Covers transactional orders, order items, product catalog, multi-channel daily ad spend, and customer web session logs for the 24-month observation window (2024-01-01 to 2025-12-31).
- **Compliance & Privacy**: All customer profiles and transaction records are synthetically generated and deterministic via a fixed random seed. No real PII (Personally Identifiable Information) is stored or processed.
