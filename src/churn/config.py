"""
Aura Retail Analytics - Phase 5 Part 1
Configuration & Constants for Behavioral Churn Prediction & Model Evaluation.
"""

import os
from typing import List


def get_workspace_dir() -> str:
    """Return the absolute path to the workspace root."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, "..", ".."))


# Core File Paths
WORKSPACE_DIR = get_workspace_dir()
DEFAULT_CUSTOMER_INTELLIGENCE_CSV = os.path.join(
    WORKSPACE_DIR, "data", "04_customer_intelligence", "customer_intelligence.csv"
)
DEFAULT_OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "data", "05_churn")
DEFAULT_FIGURES_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "figures")
DEFAULT_SUMMARIES_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "summaries")
DEFAULT_REPORTS_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "reports")
DEFAULT_MODELS_DIR = os.path.join(WORKSPACE_DIR, "models")
DEFAULT_REPORT_PATH = os.path.join(WORKSPACE_DIR, "docs", "churn_prediction_report.md")

# Output File Paths
OUTPUT_CHURN_PREDICTIONS = os.path.join(DEFAULT_OUTPUT_DIR, "churn_predictions.csv")
OUTPUT_MODEL_COMPARISON = os.path.join(DEFAULT_OUTPUT_DIR, "model_comparison.csv")
OUTPUT_FEATURE_IMPORTANCE = os.path.join(DEFAULT_OUTPUT_DIR, "feature_importance.csv")
OUTPUT_TARGET_SUMMARY = os.path.join(DEFAULT_OUTPUT_DIR, "target_summary.csv")
OUTPUT_PREDICTION_SUMMARY = os.path.join(DEFAULT_SUMMARIES_DIR, "churn_prediction_summary.csv")
OUTPUT_CV_RESULTS = os.path.join(DEFAULT_SUMMARIES_DIR, "cross_validation_results.csv")
OUTPUT_CONFUSION_MATRIX = os.path.join(DEFAULT_SUMMARIES_DIR, "confusion_matrix.csv")
OUTPUT_MODEL_ARTIFACT = os.path.join(DEFAULT_MODELS_DIR, "churn_model.joblib")

# Pipeline Invariants & Splitting Parameters
RANDOM_SEED: int = 42
TEST_SIZE: float = 0.20
CV_FOLDS: int = 5
ANCHOR_DATE: str = "2025-12-31"

# Proxy Churn Target Definition Parameters
# Behavioral proxy: Inactivity exceeding ~3x mean inter-purchase cycle for mature customers
CHURN_RECENCY_THRESHOLD_DAYS: int = 90
CHURN_TENURE_THRESHOLD_DAYS: int = 120

# Runtime Target Reference Benchmarks (for comparison & logging, not hardcoded forcing)
REFERENCE_CUSTOMER_COUNT: int = 10000
REFERENCE_CHURNED_COUNT: int = 5667
REFERENCE_RETAINED_COUNT: int = 4333
REFERENCE_CHURN_RATE: float = 0.5667

# Descriptive Churn-Risk Probability Bands (purely descriptive, not business prioritization)
CHURN_RISK_BAND_LOW: float = 0.35
CHURN_RISK_BAND_HIGH: float = 0.65

# Model Selection Metric
PRIMARY_SELECTION_METRIC: str = "PR-AUC"

# Explicit Column Registries
ID_COLUMNS: List[str] = [
    "customer_id",
    "customer_name",
    "email",
]

TARGET_COLUMNS: List[str] = [
    "is_churned",
]

LEAKAGE_COLUMNS: List[str] = [
    "recency_days",
    "last_order_date",
    "first_order_date",
    "signup_date",
    "r_score",
    "rfm_score",
    "rfm_total_score",
    "rfm_segment",
    "engagement_band",
    "cluster_id",
    "cluster_label",
    "cluster_description",
    "revenue_rank",
    "customer_value_band",
    "tenure_days",  # STRICTLY QUARANTINED: Prevents model from learning the exact target rule
]

NUMERIC_FEATURE_COLUMNS: List[str] = [
    "total_orders",
    "delivered_orders",
    "returned_orders",
    "cancelled_orders",
    "order_delivery_rate",
    "total_units_purchased",
    "units_per_order",
    "gross_revenue",
    "delivered_revenue",
    "gross_aov",
    "delivered_aov",
    "total_web_sessions",
    "total_abandoned_carts",
    "cart_abandonment_rate",
    "total_support_tickets",
    "tickets_per_order",
    "return_rate",
    "cancellation_rate",
    "friction_order_count",
    "friction_rate",
    "fulfillment_friction_flag",
]

CATEGORICAL_FEATURE_COLUMNS: List[str] = [
    "device_preference",
    "acquisition_channel",
]

FEATURE_COLUMNS: List[str] = NUMERIC_FEATURE_COLUMNS + CATEGORICAL_FEATURE_COLUMNS
