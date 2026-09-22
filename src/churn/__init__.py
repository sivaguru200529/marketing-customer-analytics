"""
Aura Retail Analytics - Phase 5 Part 1
Behavioral Churn Prediction & Model Evaluation Package.
"""

from src.churn.config import (
    CHURN_RECENCY_THRESHOLD_DAYS,
    CHURN_RISK_BAND_HIGH,
    CHURN_RISK_BAND_LOW,
    CHURN_TENURE_THRESHOLD_DAYS,
    FEATURE_COLUMNS,
    ID_COLUMNS,
    LEAKAGE_COLUMNS,
    PRIMARY_SELECTION_METRIC,
    RANDOM_SEED,
    TEST_SIZE,
)
from src.churn.evaluation import compare_models, evaluate_model, select_best_model
from src.churn.explainability import CAUSATION_DISCLAIMER, extract_feature_importance
from src.churn.features import prepare_feature_dataset, verify_leakage_controls
from src.churn.loader import load_customer_intelligence_data
from src.churn.models import get_candidate_models, load_model, save_model
from src.churn.prediction import generate_customer_predictions, generate_prediction_summary
from src.churn.preprocessing import build_preprocessor, split_data
from src.churn.target import create_churn_target, generate_target_summary, validate_target

__all__ = [
    "CHURN_RECENCY_THRESHOLD_DAYS",
    "CHURN_TENURE_THRESHOLD_DAYS",
    "CHURN_RISK_BAND_LOW",
    "CHURN_RISK_BAND_HIGH",
    "FEATURE_COLUMNS",
    "ID_COLUMNS",
    "LEAKAGE_COLUMNS",
    "PRIMARY_SELECTION_METRIC",
    "RANDOM_SEED",
    "TEST_SIZE",
    "CAUSATION_DISCLAIMER",
    "load_customer_intelligence_data",
    "create_churn_target",
    "validate_target",
    "generate_target_summary",
    "prepare_feature_dataset",
    "verify_leakage_controls",
    "build_preprocessor",
    "split_data",
    "get_candidate_models",
    "save_model",
    "load_model",
    "evaluate_model",
    "compare_models",
    "select_best_model",
    "generate_customer_predictions",
    "generate_prediction_summary",
    "extract_feature_importance",
]
