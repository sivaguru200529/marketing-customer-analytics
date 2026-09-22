"""
Aura Retail Analytics - Phase 5 Part 1
Model Explainability & Feature Importance Extraction Module.
"""

from typing import Any, List
import numpy as np
import pandas as pd

from src.churn.preprocessing import get_transformed_feature_names

CAUSATION_DISCLAIMER: str = (
    "Feature importance indicates model association/usefulness for prediction "
    "and does not establish causal relationships."
)


def extract_feature_importance(
    fitted_pipeline: Any,
    numeric_cols: List[str],
    categorical_cols: List[str],
) -> pd.DataFrame:
    """
    Extract feature importances or model coefficients from a fitted Scikit-Learn Pipeline.

    Handles:
        - Tree ensembles (RandomForest, GradientBoosting, XGBoost): feature_importances_
        - Linear models (LogisticRegression): absolute values of coefficients

    Args:
        fitted_pipeline: Fitted Pipeline with 'prep' and 'clf' steps.
        numeric_cols: List of numeric feature names.
        categorical_cols: List of categorical feature names.

    Returns:
        pd.DataFrame sorted descending by importance, with columns:
        ['feature', 'importance', 'relative_importance_pct']
    """
    preprocessor = fitted_pipeline.named_steps["prep"]
    classifier = fitted_pipeline.named_steps["clf"]

    feature_names = get_transformed_feature_names(
        fitted_preprocessor=preprocessor,
        numeric_cols=numeric_cols,
        categorical_cols=categorical_cols,
    )

    if hasattr(classifier, "feature_importances_"):
        raw_importances = classifier.feature_importances_
    elif hasattr(classifier, "coef_"):
        raw_importances = np.abs(classifier.coef_[0])
    else:
        # Fallback for models without native importances
        raw_importances = np.ones(len(feature_names)) / len(feature_names)

    total_importance = np.sum(raw_importances)
    if total_importance > 0:
        rel_importance_pct = (raw_importances / total_importance) * 100.0
    else:
        rel_importance_pct = np.zeros(len(raw_importances))

    df_importance = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": np.round(raw_importances, 5),
            "relative_importance_pct": np.round(rel_importance_pct, 2),
        }
    )

    df_importance = df_importance.sort_values(by="importance", ascending=False).reset_index(drop=True)
    return df_importance
