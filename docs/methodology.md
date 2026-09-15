# Analytics & Machine Learning Methodology
## Aura Retail Analytics Platform

This document outlines the theoretical, mathematical, and algorithmic methodologies utilized throughout the Aura Retail project for customer segmentation, cohort retention, and predictive churn modeling.

---

## 1. RFM (Recency, Frequency, Monetary) Segmentation

### 1.1 Conceptual Definition
RFM is a proven marketing analysis framework used to quantitatively evaluate customer lifetime value and transaction patterns:
- **Recency ($R$)**: Days since the customer's most recent purchase relative to the reference anchor date ($T_{\text{anchor}} = \text{2025-12-31}$). Lower values denote higher engagement.
- **Frequency ($F$)**: Total number of distinct delivered orders placed across the customer's lifespan. Higher values denote repeat loyalty.
- **Monetary ($M$)**: Cumulative net dollar spend (delivered gross sales minus applied discounts and returns). Higher values denote commercial value.

### 1.2 Quintile Scoring Engine
Each customer $i$ receives scores $R_i, F_i, M_i \in \{1, 2, 3, 4, 5\}$ based on empirical quintiles:
- **Recency Scoring**: Inverted rank. Customers with the shortest duration since last purchase receive score 5; customers with the longest duration receive score 1.
- **Frequency Scoring**: Customers in the 80th-100th percentile of order volume receive score 5; single-purchase customers typically receive score 1 or 2 depending on distribution ties.
- **Monetary Scoring**: Standard quintiles based on cumulative net spend.

### 1.3 Segment Classification Rules
Using a composite RFM key, customers are mapped into 10 mutually exclusive business segments:

```text
+-----------------------+---------------------+---------------------+---------------------+
| Segment Name          | Recency Score (R)   | Frequency Score (F) | Monetary Score (M)  |
+-----------------------+---------------------+---------------------+---------------------+
| Champions             | 4 - 5               | 4 - 5               | 4 - 5               |
| Loyal Customers       | 3 - 5               | 3 - 5               | 3 - 4               |
| Potential Loyalists   | 4 - 5               | 1 - 2               | 2 - 4               |
| New Customers         | 4 - 5               | 1                   | 1 - 3               |
| Promising             | 3 - 4               | 1 - 2               | 1 - 2               |
| Need Attention        | 2 - 3               | 2 - 3               | 2 - 3               |
| About to Sleep        | 2 - 3               | 1 - 2               | 1 - 2               |
| At Risk               | 1 - 2               | 3 - 5               | 3 - 5               |
| Cannot Lose Them      | 1                   | 4 - 5               | 4 - 5               |
| Hibernating / Lost    | 1 - 2               | 1 - 2               | 1 - 2               |
+-----------------------+---------------------+---------------------+---------------------+
```

---

## 2. Unsupervised Machine Learning: K-Means Clustering

While rule-based RFM is powerful, it treats dimensions in discrete ordinal buckets and ignores auxiliary signals. K-Means clustering is implemented to discover latent multivariate groupings.

### 2.1 Feature Pipeline & Transformation
1. **Feature Vector**:
   $$\mathbf{x}_i = [ \text{recency}, \text{frequency}, \text{monetary}, \text{AOV}, \text{discount\_share}, \text{return\_rate}, \text{web\_sessions} ]$$
2. **Skew Mitigation**:
   E-commerce transactional metrics exhibit heavy right-skewed Pareto distributions. We apply logarithmic transformation:
   $$x' = \ln(x + 1)$$
   or Yeo-Johnson Power Transformation to stabilize variance and normalize distributions.
3. **Standardization**:
   Features are standardized using z-score normalization:
   $$z = \frac{x' - \mu}{\sigma}$$
   ensuring Euclidean distances are not dominated by large-magnitude variables (such as monetary spend).

### 2.2 Mathematical Objective & Optimization
K-Means partitions $N$ observations into $K$ disjoint clusters $S = \{S_1, S_2, \dots, S_K\}$ by minimizing the Within-Cluster Sum of Squares (WCSS / Inertia):
$$\arg\min_S \sum_{k=1}^K \sum_{\mathbf{x} \in S_k} \|\mathbf{x} - \boldsymbol{\mu}_k\|^2$$
where $\boldsymbol{\mu}_k$ is the centroid of cluster $S_k$. We employ `k-means++` initialization with multiple random restarts to guarantee convergence to optimal local minima.

### 2.3 Optimal Cluster Validation ($K$)
- **Elbow Curve**: Plotting WCSS across $k \in [2, 10]$ to identify the point of diminishing marginal returns.
- **Silhouette Coefficient ($s$)**:
  $$s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}$$
  where $a(i)$ is mean intra-cluster distance and $b(i)$ is mean nearest-cluster distance. High average silhouette score indicates well-separated, dense clusters.
- **Davies-Bouldin Index**: Validates that intra-cluster distances are small relative to inter-cluster centroid separation.

---

## 3. Supervised Machine Learning: Predictive Churn Modeling

### 3.1 Business Definition of Churn
Unlike subscription services (SaaS/telecom) where churn is an explicit event (contract cancellation), non-contractual e-commerce exhibits "silent churn." 
- **Repurchase Baseline**: Aura Retail customers exhibit a mean inter-purchase cycle of ~28 days.
- **Churn Threshold**: An account is defined as **Churned (`is_churned = 1`)** if:
  $$\text{Days Since Last Order} > 90 \quad \text{AND} \quad \text{Tenure} \ge 120 \text{ days}$$
  This window ensures seasonal or occasional buyers are not falsely classified as churned before having an opportunity to complete their standard purchasing cycle.

### 3.2 Target Feature Store & Data Leakage Prevention
To ensure zero data leakage:
- Features are engineered strictly using historical observations prior to the observation cutoff date.
- Target labels reflect customer activity status evaluated during the subsequent 90-day evaluation window.

### 3.3 Candidate Classifiers & Evaluation Strategy
1. **Model Hierarchy**:
   - Baseline: `LogisticRegression` (with balanced class weights for baseline interpretability).
   - Tree Ensemble: `RandomForestClassifier`.
   - Gradient Boosting: `XGBoostClassifier` and `LightGBMClassifier`.
2. **Handling Class Imbalance**:
   E-commerce churn typically exhibits class imbalance (e.g., 20–30% churned). We evaluate:
   - Scale position weights (`scale_pos_weight` in XGBoost).
   - Synthetic Minority Over-sampling (`SMOTE`) strictly on training splits.
3. **Primary Evaluation Metrics**:
   - **PR-AUC (Precision-Recall Area Under Curve)**: Superior to ROC-AUC for imbalanced classification as it focuses heavily on the minority churn class.
   - **ROC-AUC**: Measures overall discriminatory rank-ordering capacity.
   - **Recall @ Top 20% Risk Decile**: Evaluates what percentage of total actual churners can be captured if marketing only budgets outreach for the top 20% highest-risk customers.

### 3.4 Model Explainability (SHAP)
We apply TreeSHAP (SHapley Additive exPlanations) based on cooperative game theory:
$$\phi_j(x) = \sum_{S \subseteq F \setminus \{j\}} \frac{|S|!(|F| - |S| - 1)!}{|F|!} \left[ f(S \cup \{j\}) - f(S) \right]$$
SHAP decomposes individual customer churn probabilities into exact directional feature contributions (e.g., customer churn probability $+28\%$ driven by support tickets, $-12\%$ offset by lifetime order frequency).

---

## 4. The Actionable Integration: High-Value At-Risk Matrix

The analytical intersection that delivers commercial ROI:

```text
                      PREDICTED CHURN RISK (Supervised ML)
                         Low (< 0.35)           High (>= 0.65)
                   +-----------------------+-----------------------+
   High Spender    |      SAFE CHAMPION    |  HIGH-VALUE AT RISK   |
   (RFM M >= 4)    |   Reward & Cross-sell |  URGENT INTERVENTION  |
                   |   (VIP concierge)     |  ($$$ Revenue Saving) |
CUSTOMER           +-----------------------+-----------------------+
VALUE              |     OCCASIONAL        |      LOW-VALUE        |
   Low Spender     |   Nurture & Upsell    |      HIBERNATING      |
   (RFM M <= 2)    |   (Automated drip)    |  Exclude from paid ads|
                   +-----------------------+-----------------------+
```

By filtering for:
$$\text{Monetary Score} \ge 4 \quad \land \quad P(\text{Churn}) \ge 0.65$$
the platform isolates the exact cohort of valuable customers drifting away, providing the CRM team with a prioritized target list ranked by potential revenue loss.
