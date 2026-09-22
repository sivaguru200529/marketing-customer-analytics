"""
Aura Retail Analytics - Phase 5 Part 1
Customer-Level Churn Prediction & Descriptive Risk Banding Module.
"""

from typing import Any
import numpy as np
import pandas as pd

from src.churn.config import (
    CHURN_RISK_BAND_HIGH,
    CHURN_RISK_BAND_LOW,
    REFERENCE_CUSTOMER_COUNT,
)


def generate_customer_predictions(
    fitted_pipeline: Any,
    X_full: pd.DataFrame,
    customer_ids: pd.Series,
    low_risk_threshold: float = CHURN_RISK_BAND_LOW,
    high_risk_threshold: float = CHURN_RISK_BAND_HIGH,
) -> pd.DataFrame:
    """
    Generate customer-level behavioral proxy churn predictions and descriptive probability bands.

    Output Schema:
        customer_id: Unique customer identifier
        churn_probability: Model estimated probability of belonging to proxy churn class [0.0, 1.0]
        predicted_churn: Binary predicted flag (1 if prob >= 0.50, else 0)
        churn_risk_band: Descriptive probability band ('Low Risk', 'Medium Risk', 'High Risk')

    Args:
        fitted_pipeline: Fitted Scikit-Learn Pipeline.
        X_full: Full dataset feature matrix (10,000 rows).
        customer_ids: Series of customer_id matching X_full.
        low_risk_threshold: Cutoff for Low Risk band (default 0.35).
        high_risk_threshold: Cutoff for High Risk band (default 0.65).

    Returns:
        pd.DataFrame containing the verified customer-level predictions.

    Raises:
        ValueError: If any integrity or invariant check fails.
    """
    if len(X_full) != len(customer_ids):
        raise ValueError(f"Feature count ({len(X_full)}) does not match customer ID count ({len(customer_ids)}).")

    # Generate probabilities
    if hasattr(fitted_pipeline.named_steps["clf"], "predict_proba"):
        probs = fitted_pipeline.predict_proba(X_full)[:, 1]
    else:
        probs = fitted_pipeline.predict(X_full).astype(float)

    preds = (probs >= 0.50).astype(int)

    # Assign descriptive probability risk bands
    conditions = [
        probs < low_risk_threshold,
        (probs >= low_risk_threshold) & (probs < high_risk_threshold),
        probs >= high_risk_threshold,
    ]
    choices = ["Low Risk", "Medium Risk", "High Risk"]
    risk_bands = np.select(conditions, choices, default="Medium Risk")

    df_preds = pd.DataFrame(
        {
            "customer_id": customer_ids.values,
            "churn_probability": np.round(probs, 4),
            "predicted_churn": preds,
            "churn_risk_band": risk_bands,
        }
    )

    # Strict Validation
    if len(df_preds) != REFERENCE_CUSTOMER_COUNT:
        raise ValueError(
            f"Prediction row count ({len(df_preds)}) does not equal reference customer count ({REFERENCE_CUSTOMER_COUNT})."
        )

    if df_preds["customer_id"].nunique() != len(df_preds):
        raise ValueError("Detected duplicate customer_id values in prediction output.")

    if df_preds["churn_probability"].isna().any():
        raise ValueError("Found missing (NaN) values in predicted churn probabilities.")

    if not ((df_preds["churn_probability"] >= 0.0) & (df_preds["churn_probability"] <= 1.0)).all():
        raise ValueError("Detected churn probabilities falling outside bounded interval [0.0, 1.0].")

    return df_preds


def generate_prediction_summary(df_predictions: pd.DataFrame) -> pd.DataFrame:
    """
    Generate an analytical summary cross-tabulating descriptive risk bands with predicted churn flags.

    Args:
        df_predictions: Customer predictions DataFrame.

    Returns:
        Summary DataFrame.
    """
    band_order = ["Low Risk", "Medium Risk", "High Risk"]

    summary_rows = []
    total_customers = len(df_predictions)

    for band in band_order:
        band_df = df_predictions[df_predictions["churn_risk_band"] == band]
        count = len(band_df)
        share = (count / total_customers) * 100 if total_customers > 0 else 0.0
        churn_count = int(band_df["predicted_churn"].sum())
        churn_share = (churn_count / count) * 100 if count > 0 else 0.0
        mean_prob = float(band_df["churn_probability"].mean()) if count > 0 else 0.0
        min_prob = float(band_df["churn_probability"].min()) if count > 0 else 0.0
        max_prob = float(band_df["churn_probability"].max()) if count > 0 else 0.0

        summary_rows.append(
            {
                "Churn Risk Band": band,
                "Customer Count": count,
                "Customer Share (%)": round(share, 2),
                "Predicted Churn Count": churn_count,
                "Band Churn Rate (%)": round(churn_share, 2),
                "Mean Probability": round(mean_prob, 4),
                "Min Probability": round(min_prob, 4),
                "Max Probability": round(max_prob, 4),
            }
        )

    return pd.DataFrame(summary_rows)
