# Aura Retail: Marketing & Customer Analytics Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16.0-blue.svg)](https://www.postgresql.org/)
[![Power BI](https://img.shields.io/badge/Power_BI-Desktop-yellow.svg)](https://powerbi.microsoft.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status: Foundation Complete](https://img.shields.io/badge/Phase-1_Foundation_Complete-brightgreen.svg)]()

An end-to-end data analytics, machine learning, and business intelligence portfolio project simulating the growth, marketing attribution, customer segmentation, and retention workflows of a high-growth Direct-to-Consumer (D2C) e-commerce brand: **Aura Retail**.

---

## 1. Business Problem
As Aura Retail scaled over the past two years, customer acquisition costs rose while repeat purchase rates fluctuated. Executive leadership (CMO, CCO, and Head of Retention) lacks a unified analytics system to answer core business questions:
- **Channel Inefficiency**: Which acquisition channels generate profitable, high-retaining customers versus one-and-done buyers?
- **Uniform Marketing**: Promotional campaigns treat all customers identically, leading to margin erosion from blanket discounts and unoptimized outreach.
- **Silent Churn**: Non-contractual e-commerce lacks explicit cancellation signals; high-value customers lapse unnoticed until it is too late to win them back profitably.

---

## 2. Project Objectives
This project establishes an enterprise-grade analytics foundation to:
1. **Understand Purchasing Behavior**: Analyze order frequency distributions, repeat velocity, and cohort retention decay over a 24-month horizon.
2. **Measure Marketing Channel Performance**: Compute blended and channel-specific Customer Acquisition Cost (CAC) and Return on Ad Spend (ROAS).
3. **Segment Customers with Dual-Methodology**:
   - **Rule-based RFM**: Standardized Recency, Frequency, and Monetary scoring mapped to 10 actionable business segments for CRM operations.
   - **Unsupervised ML (K-Means)**: Behavioral clustering capturing non-linear interactions across spend, basket variety, return rates, and discount reliance.
4. **Predict Customer Churn**: Develop a supervised classification pipeline to identify customers at risk of lapse before they reach terminal inactivity.
5. **Protect Revenue at Risk**: Cross-reference high-spending segments with high predicted churn probabilities to deliver a prioritized VIP retention action list.
6. **Deliver Executive & Operational Dashboards**: Build an interactive 3-page Power BI report bridging high-level C-suite metrics to granular retention lists.

---

## 3. Technology Stack

| Domain | Tools & Libraries | Role in Architecture |
| :--- | :--- | :--- |
| **Relational Database** | PostgreSQL 16, pgAdmin 4 | Normalized 3NF transactional data store, constraints, and indexes |
| **Data Ingestion & Pipeline** | Python, SQLAlchemy, psycopg2 | Data loading, schema migration, and integrity verification |
| **Data Manipulation** | pandas, NumPy | Data cleaning, feature engineering, and matrix operations |
| **Synthetic Generation** | Faker, NumPy (Deterministic Seeds) | Reproducible e-commerce data generation with realistic skew |
| **Exploratory Analytics** | matplotlib, seaborn | Statistical visualization, correlation analysis, and cohort heatmaps |
| **Machine Learning** | scikit-learn, XGBoost, LightGBM | K-Means clustering, PCA, churn classification models |
| **Model Explainability** | SHAP (SHapley Additive exPlanations) | Feature attribution and individual customer risk drivers |
| **Business Intelligence** | Microsoft Power BI | Star-schema semantic model, DAX measures, and interactive reporting |
| **Testing & Quality** | pytest, flake8, black | Schema assertions, business constraint tests, and code formatting |
| **Containerization** | Docker, Docker Compose | Reproducible local database deployment |

---

## 4. Planned System Architecture

```text
  [Synthetic Generator (Faker + NumPy)]
                 │
                 ▼
        [Raw Data CSVs]
                 │
                 ▼
    [PostgreSQL Relational DB (3NF)]
                 │
                 ├──► [Analytical Views / Star Schema Marts]
                 │            │
                 │            ├──► [Power BI Semantic Model & Dashboards]
                 │            │
                 ▼            ▼
       [Advanced SQL]   [Python Data Science & ML]
       - Cohorts        - Exploratory Data Analysis
       - CAC / ROAS     - RFM Scoring Engine
       - Revenue Trends - K-Means Clustering
                        - XGBoost Churn Classifier + SHAP
                               │
                               ▼
               [High-Value At-Risk Action Matrix]
```

---

## 5. Planned Analytics & SQL Showcase
The `sql/queries/` directory will showcase production-grade SQL scripts:
- **`01_revenue_and_growth.sql`**: Monthly Gross and Net Revenue, MoM growth rates, and Average Order Value (AOV) using window functions.
- **`02_cohort_retention.sql`**: Comprehensive Month-0 to Month-12 monthly customer retention matrix.
- **`03_marketing_performance.sql`**: Multi-touch channel attribution, CAC, and ROAS calculations.
- **`04_rfm_segmentation.sql`**: Pure-SQL RFM quintile calculation using `NTILE(5)` window functions and conditional segment assignment.
- **`05_customer_lifetime_value.sql`**: Historical 365-day customer value and inter-purchase velocity queries.

---

## 6. Planned Machine Learning Components
- **Customer Segmentation (K-Means)**:
  - Log-transformation and standard scaling of skewed behavioral metrics.
  - Objective optimization via Elbow Method (Inertia), Silhouette Scores, and Davies-Bouldin index.
  - Multi-dimensional profiling and persona synthesis.
- **Churn Prediction (Supervised Classification)**:
  - Strict e-commerce churn definition based on 90-day purchase inactivity.
  - Leakage-free feature engineering across recency, cadence, support tickets, and discount usage.
  - Model benchmarking (Logistic Regression vs. Random Forest vs. XGBoost / LightGBM).
  - Model evaluation focused on PR-AUC, ROC-AUC, and Recall @ Top 20% Risk Decile.
  - Global and local explainability using SHAP waterfall and summary plots.
- **Revenue at Risk Integration**:
  - Filter: Monetary Score $\ge 4$ AND Predicted Churn Probability $\ge 0.65$.

---

## 7. Planned Power BI Dashboards
The Power BI reporting layer (`power_bi/aura_retail_analytics.pbix`) will feature a modern, executive luxury UI across three dedicated views:
1. **Executive & Marketing Performance**:
   - High-level KPI cards: Net Revenue, Blended CAC, ROAS, Total Delivered Orders.
   - Monthly Revenue & MoM growth trends.
   - Acquisition channel efficiency matrix (ROAS vs. CAC scatter plot).
2. **Customer Cohorts & RFM Segmentation**:
   - Dynamic monthly cohort retention heatmap.
   - Interactive RFM segment distribution treemap.
   - Segment behavioral comparison (AOV vs. Order Frequency).
3. **Churn Risk & Retention Command Center**:
   - Churn rate, active customer count, and total Revenue at Risk.
   - Churn probability distribution by RFM segment.
   - SHAP-derived top churn risk drivers.
   - Priority Action Table: High-Value Customers at Risk with recommended retention actions.

---

## 8. Repository Structure

```text
marketing-customer-analytics/
├── config/
│   ├── database.ini.example           # Database credentials template
│   └── logging.conf                   # Logging configuration
├── data/
│   ├── 01_raw/                        # Generated raw CSV datasets
│   ├── 02_processed/                  # Cleaned datasets
│   ├── 03_analytical/                 # Dimensional star-schema marts
│   └── sample/                        # Lightweight sample CSVs for quick preview
├── docker/
│   ├── docker-compose.yml             # PostgreSQL 16 & pgAdmin container orchestration
│   └── init_db.sql                    # Initial database and extension setup
├── docs/
│   ├── business_requirements.md       # Stakeholder questions, context, and KPIs
│   ├── data_dictionary.md             # Schema definitions, types, and constraints
│   └── methodology.md                 # Mathematical RFM, K-Means, and ML specifications
├── notebooks/                         # Jupyter analysis & modeling notebooks
├── power_bi/
│   ├── dax_measures.dax               # Centralized DAX formula catalog
│   └── screenshots/                   # Exported report screenshots
├── sql/
│   ├── schema/                        # Table DDL and view definitions
│   └── queries/                       # Analytical business queries
├── src/
│   ├── data_generator/                # Synthetic data generation engine
│   ├── database/                      # Ingestion and database connection management
│   ├── features/                      # ML feature engineering pipelines
│   └── models/                        # Clustering and classification training scripts
├── tests/                             # Automated data quality and schema assertions
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

---

## 9. Getting Started & Verification

### Prerequisites
- Python 3.10 or higher
- Docker Desktop (or local PostgreSQL 16)
- Git

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/your-username/marketing-customer-analytics.git
cd marketing-customer-analytics

# 2. Create and activate a virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Optional: Start PostgreSQL database via Docker
cd docker
docker-compose up -d
cd ..
```

---

## 10. Project Implementation Status
- [x] **Phase 1: Project Foundation & Architecture** (Current)
- [ ] **Phase 2: Synthetic Data Generation Engine**
- [ ] **Phase 3: Database Ingestion & Relational Schema (PostgreSQL)**
- [ ] **Phase 4: Advanced SQL Business Analytics**
- [ ] **Phase 5: Python Exploratory Data Analysis (EDA)**
- [ ] **Phase 6: RFM & K-Means Customer Segmentation**
- [ ] **Phase 7: Predictive Churn Modeling & Risk Identification**
- [ ] **Phase 8: Power BI Dashboards & Executive Storytelling**
- [ ] **Phase 9: Final Quality Assurance, Testing & Portfolio Delivery**

---

## License
Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
