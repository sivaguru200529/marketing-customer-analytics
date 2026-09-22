"""
Aura Retail Analytics - Phase 5 Part 1
Behavioral Proxy Churn Target Definition & Validation Module.
"""

import logging
from typing import Dict, Tuple
import pandas as pd

from src.churn.config import (
    ANCHOR_DATE,
    CHURN_RECENCY_THRESHOLD_DAYS,
    CHURN_TENURE_THRESHOLD_DAYS,
    REFERENCE_CHURN_RATE,
    REFERENCE_CHURNED_COUNT,
    REFERENCE_CUSTOMER_COUNT,
    REFERENCE_RETAINED_COUNT,
)

logger = logging.getLogger(__name__)


def create_churn_target(
    df: pd.DataFrame,
    recency_threshold: int = CHURN_RECENCY_THRESHOLD_DAYS,
    tenure_threshold: int = CHURN_TENURE_THRESHOLD_DAYS,
    target_col: str = "is_churned",
) -> pd.DataFrame:
    """
    Define and append the behavioral proxy churn target column.

    Target Definition:
        An account is classified as churned (is_churned = 1) if:
        recency_days > recency_threshold AND tenure_days >= tenure_threshold.

    Args:
        df: Input DataFrame containing recency_days and tenure_days.
        recency_threshold: Threshold in calendar days defining inactivity (default 90).
        tenure_threshold: Threshold in calendar days defining minimum tenure (default 120).
        target_col: Name of binary target column to append.

    Returns:
        DataFrame with target_col appended.
    """
    df_out = df.copy()

    if "recency_days" not in df_out.columns or "tenure_days" not in df_out.columns:
        raise KeyError("Both 'recency_days' and 'tenure_days' must be present to formulate the proxy churn target.")

    condition = (df_out["recency_days"] > recency_threshold) & (df_out["tenure_days"] >= tenure_threshold)
    df_out[target_col] = condition.astype(int)

    return df_out


def validate_target(
    df: pd.DataFrame,
    target_col: str = "is_churned",
) -> Tuple[bool, Dict[str, object]]:
    """
    Validate the generated target column against integrity rules and reference benchmarks.

    Checks:
        1. target column exists and contains no nulls.
        2. target column contains strictly binary values {0, 1}.
        3. Compares actual counts against reference benchmarks and logs differences as warnings
           rather than forcing results.

    Returns:
        Tuple of (is_valid, stats_dict).
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")

    target_series = df[target_col]

    if target_series.isna().any():
        raise ValueError(f"Target column '{target_col}' contains {target_series.isna().sum()} null values.")

    unique_vals = set(target_series.unique())
    if not unique_vals.issubset({0, 1}):
        raise ValueError(f"Target column contains invalid non-binary values: {unique_vals}")

    total_count = len(target_series)
    churned_count = int((target_series == 1).sum())
    retained_count = int((target_series == 0).sum())
    churn_rate = churned_count / total_count if total_count > 0 else 0.0
    retained_rate = retained_count / total_count if total_count > 0 else 0.0

    stats = {
        "total_customers": total_count,
        "churned_customers": churned_count,
        "non_churned_customers": retained_count,
        "churn_rate": churn_rate,
        "non_churn_rate": retained_rate,
        "reference_match": True,
        "warnings": [],
    }

    # Compare against reference values without altering the data
    if total_count != REFERENCE_CUSTOMER_COUNT:
        msg = f"Customer count ({total_count}) differs from reference ({REFERENCE_CUSTOMER_COUNT})."
        stats["warnings"].append(msg)
        stats["reference_match"] = False
        logger.warning(msg)

    if churned_count != REFERENCE_CHURNED_COUNT:
        msg = f"Churned count ({churned_count}) differs from reference ({REFERENCE_CHURNED_COUNT})."
        stats["warnings"].append(msg)
        stats["reference_match"] = False
        logger.warning(msg)

    if retained_count != REFERENCE_RETAINED_COUNT:
        msg = f"Retained count ({retained_count}) differs from reference ({REFERENCE_RETAINED_COUNT})."
        stats["warnings"].append(msg)
        stats["reference_match"] = False
        logger.warning(msg)

    return True, stats


def generate_target_summary(
    df: pd.DataFrame,
    target_col: str = "is_churned",
    recency_threshold: int = CHURN_RECENCY_THRESHOLD_DAYS,
    tenure_threshold: int = CHURN_TENURE_THRESHOLD_DAYS,
) -> pd.DataFrame:
    """
    Generate an authoritative summary DataFrame for the behavioral proxy churn target.
    """
    _, stats = validate_target(df, target_col=target_col)

    summary_data = [
        {"metric": "Target Type", "value": "Behavioral Proxy Classification"},
        {"metric": "Observation Anchor Date", "value": ANCHOR_DATE},
        {"metric": "Inactivity Threshold (Days)", "value": str(recency_threshold)},
        {"metric": "Maturity Tenure Threshold (Days)", "value": str(tenure_threshold)},
        {"metric": "Total Customers", "value": f"{stats['total_customers']:,}"},
        {"metric": "Churned Customers", "value": f"{stats['churned_customers']:,}"},
        {"metric": "Non-Churned Customers", "value": f"{stats['non_churned_customers']:,}"},
        {"metric": "Churn Rate (%)", "value": f"{stats['churn_rate'] * 100:.2f}%"},
        {"metric": "Non-Churn Rate (%)", "value": f"{stats['non_churn_rate'] * 100:.2f}%"},
        {"metric": "Reference Count Match", "value": str(stats["reference_match"])},
    ]

    return pd.DataFrame(summary_data)
