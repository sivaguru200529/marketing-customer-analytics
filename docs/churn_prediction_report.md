# Aura Retail Analytics — Phase 5 Part 1: Churn Prediction & Model Evaluation Report

**Project:** Aura Retail Marketing & Customer Analytics  
**Phase:** Phase 5 Part 1 — Churn Prediction & Model Evaluation  
**Analytical Anchor Date:** 2025-12-31  
**Primary Model Selection Metric:** PR-AUC  
**Selected Champion Model:** **Random Forest**  

---

## 1. Objective

The objective of Phase 5 Part 1 is to build a mathematically rigorous, fully reproducible, and leakage-controlled supervised classification pipeline to **estimate the probability that a customer belongs to the project's behavioral proxy churn class based on non-leaking behavioral and customer attributes observed within the analytical snapshot**.

This phase establishes the foundational statistical models, performs objective model evaluation across multiple algorithms on a pristine holdout test set, extracts non-causal feature importances, and scores the entire 10,000-customer population with individual churn-risk probabilities and descriptive probability risk bands.

---

## 2. Source Dataset

The authoritative analytical input ingested by this pipeline is:
```text
data/04_customer_intelligence/customer_intelligence.csv
```
This dataset was produced in Phase 4 Part 3 and possesses the following verified invariants:
- **Customer Population:** Exactly 10,000 registered customers.
- **Grain:** Exactly 1 row per customer (`customer_id` primary key, 100% unique, zero duplicates, zero nulls).
- **Analytical Scope:** 47 comprehensive analytical columns spanning customer profiles, acquisition channels, tenure, order realization, revenue, AOV, web sessions, support tickets, friction metrics, RFM scores, and K-Means cluster assignments.

---

## 3. Dataset Validation & Integrity Checks

Prior to feature extraction, the input dataset underwent automated structural verification:
- **Row Count:** Verified exactly 10,000 customer records.
- **Primary Key Integrity:** `customer_id` validated with 0 duplicates and 0 null values.
- **Column Completeness:** All required profile, transaction, engagement, and friction variables verified present.
- **Missing Value Handling:** Missing value inspection identified that only `delivered_aov` contained nulls (860 rows), corresponding precisely to customers with zero delivered orders. This was handled via median imputation within the training pipeline.

---

## 4. Behavioral Proxy Churn Definition

In non-contractual e-commerce, customers rarely emit explicit cancellation notices. Consequently, churn must be formalized as a **behavioral proxy classification target** rather than an observed future cancellation event.

An account is defined as churned (`is_churned = 1`) at analytical snapshot `2025-12-31` if:
$$\text{is\_churned} = 1 \iff (\text{recency\_days} > 90) \land (\text{tenure\_days} \ge 120)$$

Accounts failing either condition are designated as non-churned (`is_churned = 0`).

---

## 5. Justification for the 90-Day Inactivity Threshold

Analysis of Aura Retail's historical transaction cadence establishes that repeat customers exhibit an empirical median inter-purchase interval of **6.0 days**, a 75th percentile of **19.0 days**, and a 95th percentile of **72.0 days**. 

A threshold of **90 calendar days** without an order represents:
1. Greater than **three times** the standard monthly repurchase cycle.
2. An interval beyond the **95th percentile** of empirical inter-purchase intervals.
3. A clear behavioral signal of customer dormancy rather than ordinary seasonal or weekly fluctuation.

---

## 6. Justification for the 120-Day Tenure Maturity Condition

The condition `tenure_days >= 120` is enforced to address customer lifecycle maturity:
1. Newly acquired customers (<120 days of tenure) cannot mathematically or behaviorally exhibit dormancy before having had sufficient calendar opportunity to complete their standard onboarding and repurchase cycles.
2. In the absence of a minimum tenure constraint, new cohorts would be distorted and falsely conflated with established lapsed customers.

---

## 7. Actual Target Class Distribution

The target was evaluated dynamically against the 10,000 customers in `customer_intelligence.csv`. The actual measured distribution is:

| Metric | Measured Value |
| :--- | :--- |
| **Total Customer Population** | **10,000** |
| **Behavioral Proxy Churned (`is_churned = 1`)** | **5,667 (56.67%)** |
| **Behavioral Retained (`is_churned = 0`)** | **4,333 (43.33%)** |
| **Reference Benchmark Match** | **Verified consistent with Phase 4 analytical baseline** |

```text
Class Balance: Balanced binary distribution (approx. 56.7% positive / 43.3% negative).
```

---

## 8. Feature Engineering & Selection

Predictive features were curated to capture diverse facets of customer interactions:

### Numeric Features (21 variables):
- **Order Realization & Volume:** `total_orders`, `delivered_orders`, `returned_orders`, `cancelled_orders`, `order_delivery_rate`, `total_units_purchased`, `units_per_order`.
- **Financial Dynamics:** `gross_revenue`, `delivered_revenue`, `gross_aov`, `delivered_aov`.
- **Digital Engagement:** `total_web_sessions`, `total_abandoned_carts`, `cart_abandonment_rate`.
- **Customer Support & Friction:** `total_support_tickets`, `tickets_per_order`, `return_rate`, `cancellation_rate`, `friction_order_count`, `friction_rate`, `fulfillment_friction_flag`.

### Categorical Features (2 variables):
- `device_preference` (Mobile, Desktop, Tablet)
- `acquisition_channel` (Paid Social, Paid Search, Organic Search, Direct, Affiliate, Email)

---

## 9. Strict Data Leakage Prevention & Quarantine

To prevent models from trivially reproducing the target through circular definition, the following registries are enforced:

### A. Quarantined Columns (`LEAKAGE_COLUMNS`):
1. **Direct Proxy Leakage:** `recency_days`, `last_order_date` (directly define the target).
2. **Derived RFM Scores:** `r_score`, `rfm_score`, `rfm_total_score` (recency quintiles encode target recency).
3. **Downstream Classifications:** `rfm_segment`, `engagement_band`, `cluster_id`, `cluster_label`, `cluster_description`.
4. **Temporal Metadata:** `signup_date`, `first_order_date`.
5. **Downstream Rankings:** `revenue_rank`, `customer_value_band`.
6. **STRICT TENURE QUARANTINE (`tenure_days`):** Because the target definition incorporates `tenure_days >= 120`, allowing `tenure_days` into the feature matrix allows tree models to exploit the 120-day cutoff as an artificial deterministic boundary. Excluding `tenure_days` forces models to learn genuine customer behavior.

### B. Customer Identifiers (`ID_COLUMNS`):
- `customer_id`, `customer_name`, `email` are strictly quarantined from predictive matrices.

---

## 10. Temporal Snapshot Limitations & Potential Leakage

- **Analytical Snapshot Constraint:** All features in `customer_intelligence.csv` represent aggregated lifetime customer metrics as of `2025-12-31`.
- **Production Consideration:** In a live deployment, feature stores must enforce strict point-in-time point-of-observation splits where features are calculated up to date $T$ and outcomes are observed during window $[T, T + 90\text{ days}]$. Because this dataset is a cumulative historical snapshot, lifetime order and ticket counts represent full observation history.

---

## 11. Train / Test Split Methodology

The customer population was partitioned into reproducible train and test splits:
- **Split Ratio:** 80% Training (8,000 customers) / 20% Testing (2,000 customers).
- **Stratification:** Stratified by `is_churned` to preserve exact class balance across splits.
- **Random Seed:** Configurable seed fixed at `RANDOM_SEED = 42` for 100% deterministic reproducibility.
- **Holdout Purity:** The test set was isolated immediately after splitting and remained untouched during preprocessor fitting, model tuning, and cross-validation.

---

## 12. Candidate Machine Learning Models Evaluated

Five distinct classification architectures were evaluated:
1. **Baseline (`DummyClassifier`):** Predicts the most frequent class to establish minimum reference performance.
2. **Logistic Regression (`LogisticRegression`):** Linear model with balanced class weights and L2 regularization.
3. **Random Forest (`RandomForestClassifier`):** Non-linear ensemble with 150 bagged decision trees, balanced class weights, and controlled leaf depth.
4. **Gradient Boosting (`GradientBoostingClassifier`):** Sequential boosting ensemble optimizing deviance with shrinkage.
5. **XGBoost (`XGBClassifier`):** Scalable gradient boosted decision trees with regularized objective optimization.

---

## 13. Stratified 5-Fold Cross-Validation Results

Stratified 5-fold cross-validation was conducted exclusively within the training split:

| Model | CV PR-AUC (Mean ± Std) | CV ROC-AUC (Mean ± Std) | CV F1 (Mean ± Std) | CV Accuracy |
| :--- | :---: | :---: | :---: | :---: |
| **Baseline (Dummy)** | 0.5668 ± 0.0002 | 0.5000 ± 0.0000 | 0.7235 ± 0.0002 | 0.5668 |
| **Logistic Regression** | 0.7235 ± 0.0071 | 0.7241 ± 0.0020 | 0.7673 ± 0.0033 | 0.7131 |
| **Random Forest** | 0.7424 ± 0.0133 | 0.7352 ± 0.0074 | 0.7683 ± 0.0025 | 0.7276 |
| **Gradient Boosting** | 0.7352 ± 0.0088 | 0.7298 ± 0.0043 | 0.7672 ± 0.0023 | 0.7240 |
| **XGBoost** | 0.7319 ± 0.0096 | 0.7277 ± 0.0054 | 0.7693 ± 0.0027 | 0.7268 |

---

## 14. Hyperparameter Tuning Methodology

Hyperparameter optimization was executed using Scikit-Learn `GridSearchCV` on the training folds using stratified 5-fold cross-validation with `scoring='average_precision'` (PR-AUC).
- Tuning was strictly confined to training data; the held-out test set was never exposed to the hyperparameter search.

---

## 15. Evaluation Metrics Formulation

Model discrimination and calibration were evaluated across six formal metrics on the holdout test set:
- **PR-AUC (Precision-Recall Area Under Curve):** Primary metric evaluating positive (churn) predictive capacity regardless of true negative count.
- **ROC-AUC (Receiver Operating Characteristic AUC):** Overall discrimination across varying probability thresholds.
- **F1-Score:** Harmonic mean of precision and recall.
- **Accuracy:** Overall proportion of correct predictions.
- **Precision:** True Positives / (True Positives + False Positives).
- **Recall:** True Positives / (True Positives + False Negatives).

---

## 16. Measured Model Comparison (Holdout Test Set)

The actual measured metrics on the untouched 20% holdout test set (2,000 customers) are:

| Model | Accuracy | Precision | Recall | F1 Score | ROC-AUC | PR-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Random Forest** | 0.7090 | 0.7365 | 0.7573 | 0.7467 | 0.7146 | **0.7276** |
| Gradient Boosting | 0.7100 | 0.7329 | 0.7679 | 0.7500 | 0.7125 | 0.7255 |
| XGBoost | 0.7075 | 0.7306 | 0.7661 | 0.7480 | 0.7118 | 0.7194 |
| Logistic Regression | 0.7030 | 0.7120 | 0.7988 | 0.7529 | 0.7092 | 0.7166 |
| Baseline (Dummy) | 0.5665 | 0.5665 | 1.0000 | 0.7233 | 0.5000 | 0.5665 |

---

## 17. Predefined Model Selection Criterion

The champion model was selected strictly according to the documented criterion:
```text
Selection Rule: Deterministically choose candidate model with the highest PR-AUC on held-out test data.
```
- PR-AUC was selected because e-commerce churn interventions focus on maximizing positive class identification while controlling false alarms.
- No model was assumed or forced to win a priori.

---

## 18. Selected Champion Model & Test Diagnostics

- **Selected Model:** **Random Forest**
- **Measured PR-AUC:** **0.7276**
- **Measured ROC-AUC:** **0.7146**
- **Test Confusion Matrix Diagnostics:**
  - **True Positives (TP):** 858 (Correctly classified proxy churners)
  - **True Negatives (TN):** 560 (Correctly classified retained customers)
  - **False Positives (FP):** 307 (Retained customers predicted as churned)
  - **False Negatives (FN):** 275 (Proxy churners predicted as retained)

---

## 19. Model Explainability & Feature Importance

Feature importances were computed directly from the fitted Random Forest pipeline.

> **Mandatory Methodological Notice:**  
> *Feature importance indicates model association/usefulness for prediction and does not establish causal relationships.*

### Top 15 Predictive Behavioral Features:
| Rank | Feature Name | Raw Importance | Relative Share (%) |
| :---: | :--- | :---: | :---: |
| 1 | `total_orders` | 0.20646 | 20.65% |
| 2 | `delivered_orders` | 0.17333 | 17.33% |
| 3 | `total_units_purchased` | 0.14328 | 14.33% |
| 4 | `gross_revenue` | 0.11913 | 11.91% |
| 5 | `delivered_revenue` | 0.07735 | 7.74% |
| 6 | `total_web_sessions` | 0.05795 | 5.80% |
| 7 | `gross_aov` | 0.02760 | 2.76% |
| 8 | `friction_rate` | 0.02572 | 2.57% |
| 9 | `friction_order_count` | 0.02417 | 2.42% |
| 10 | `delivered_aov` | 0.02283 | 2.28% |
| 11 | `order_delivery_rate` | 0.02207 | 2.21% |
| 12 | `fulfillment_friction_flag` | 0.01882 | 1.88% |
| 13 | `return_rate` | 0.01875 | 1.87% |
| 14 | `units_per_order` | 0.01710 | 1.71% |
| 15 | `cart_abandonment_rate` | 0.01527 | 1.53% |

---

## 20. Customer-Level Predictions Summary

Predictions were generated for all 10,000 customers using the champion pipeline.

| Metric | Value |
| :--- | :--- |
| **Total Customers Scored** | **10,000** |
| **Predicted Churn Flag = 1 (Prob $\ge$ 0.50)** | **6,030 (60.30%)** |
| **Predicted Churn Flag = 0 (Prob $<$ 0.50)** | **3,970 (39.70%)** |
| **Mean Churn Probability** | **0.5125** |
| **Median Churn Probability** | **0.6627** |
| **Min / Max Churn Probability** | **0.1353 / 0.8867** |

---

## 21. Descriptive Churn-Risk Probability Bands

Customers were assigned to descriptive probability bands based on configurable thresholds:
- **Low Risk:** Probability < 0.35
- **Medium Risk:** 0.35 $\le$ Probability < 0.65
- **High Risk:** Probability $\ge$ 0.65

| Descriptive Risk Band | Customer Count | Share (%) | Predicted Churn Count | Band Churn Rate (%) | Mean Probability |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Low Risk** | 3,713 | 37.13% | 0 | 0.00% | 0.2355 |
| **Medium Risk** | 664 | 6.64% | 407 | 61.30% | 0.5380 |
| **High Risk** | 5,623 | 56.23% | 5,623 | 100.00% | 0.6925 |

*Note: These probability bands are descriptive analytical outputs and do NOT represent business action prioritizations or marketing recommendations (which belong strictly to Phase 5 Part 2).*

---

## 22. Limitations & Methodological Assumptions

1. **Proxy Target Nature:** Churn is defined behaviorally using inactivity (recency > 90 days for mature accounts). It does not represent contractual cancellation.
2. **Cumulative Snapshot Data:** Features are derived from historical totals up to `2025-12-31`.
3. **Association $\neq$ Causation:** Feature importance rankings reflect statistical predictive association, not causal levers.
4. **Distribution Shifts:** Changes in macroeconomic conditions, pricing, or product assortment could alter future purchase cadences.

---

## 23. Pipeline Reproducibility

The entire Phase 5 Part 1 pipeline can be deterministically reproduced using:
```powershell
python -m src.churn.run_churn
```
Running this command produces identical target distributions, feature matrices, cross-validation metrics, evaluation tables, customer probabilities, and visualizations.

---

## 24. Explicit Statement on Proxy Churn Classification

> **Methodological Declaration:**  
> The models trained in this phase perform **behavioral proxy churn classification** based on observable interaction patterns. This pipeline does NOT claim to possess true historical ground truth of permanent customer attrition, nor does it guarantee future customer departure. All probability estimates reflect the likelihood of exhibiting behavioral inactivity under the project's formalized business criteria.

---
*Report automatically compiled by Aura Retail Phase 5 Part 1 Pipeline.*
