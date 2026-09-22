"""
Aura Retail Analytics - Phase 5 Part 2
Priority Tiers & Mutually Exclusive Business Segmentation Module.
"""

from typing import Tuple
import numpy as np
import pandas as pd

from src.prioritization.config import (
    CHURN_RISK_HIGH_THRESHOLD,
    CHURN_RISK_LOW_THRESHOLD,
    ENGAGEMENT_DEVELOPING_THRESHOLD,
    FRICTION_HIGH_SCORE_THRESHOLD,
    PRIORITY_TIER_HIGH_THRESHOLD,
    PRIORITY_TIER_MEDIUM_THRESHOLD,
    VALUE_HIGH_THRESHOLD,
    VALUE_MID_THRESHOLD,
)


def assign_priority_tier(df: pd.DataFrame) -> pd.Series:
    """
    Assign deterministic priority tier based on priority_score.

    Thresholds:
        priority_score >= 0.75 -> High Priority
        0.50 <= priority_score < 0.75 -> Medium Priority
        priority_score < 0.50 -> Low Priority

    Args:
        df: DataFrame containing 'priority_score'.

    Returns:
        pd.Series of priority tiers.
    """
    if "priority_score" not in df.columns:
        raise KeyError("Column 'priority_score' missing from DataFrame.")

    score = df["priority_score"].astype(float)

    conditions = [
        score >= PRIORITY_TIER_HIGH_THRESHOLD,
        (score >= PRIORITY_TIER_MEDIUM_THRESHOLD) & (score < PRIORITY_TIER_HIGH_THRESHOLD),
        score < PRIORITY_TIER_MEDIUM_THRESHOLD,
    ]
    choices = [
        "High Priority",
        "Medium Priority",
        "Low Priority",
    ]

    tier = pd.Series(np.select(conditions, choices, default="Low Priority"), index=df.index)
    return tier


def assign_business_segment(df: pd.DataFrame) -> pd.Series:
    """
    Assign mutually exclusive business segments using strict precedence hierarchy.

    Precedence Hierarchy:
        1. High Risk + High Value + High Friction -> High Risk / High Value / High Friction
        2. High Risk + High Value -> High Risk / High Value
        3. High Risk + Mid Value -> High Risk / Mid Value
        4. High Risk + Low Value -> High Risk / Low Value
        5. Medium Risk + High Value -> Medium Risk / High Value
        6. Medium Risk + Developing Engagement -> Medium Risk / Developing
        7. Low Risk + High Value -> Low Risk / High Value
        8. Low Risk + Developing Engagement -> Low Risk / Developing
        9. Low Value + Inactive -> Low Value / Inactive
        Fallback -> General Monitoring

    Args:
        df: DataFrame containing risk, value, engagement, friction metrics.

    Returns:
        pd.Series of business segments.
    """
    # Core condition evaluations
    is_high_risk = (
        (df["churn_risk_band"] == "High Risk")
        | (df["churn_probability"] >= CHURN_RISK_HIGH_THRESHOLD)
    )
    is_med_risk = (
        (df["churn_risk_band"] == "Medium Risk")
        | (
            (df["churn_probability"] >= CHURN_RISK_LOW_THRESHOLD)
            & (df["churn_probability"] < CHURN_RISK_HIGH_THRESHOLD)
        )
    )
    is_low_risk = (
        (df["churn_risk_band"] == "Low Risk")
        | (df["churn_probability"] < CHURN_RISK_LOW_THRESHOLD)
    )

    is_high_val = (
        (df["customer_value_band"] == "High Value")
        | (df["delivered_revenue"] >= VALUE_HIGH_THRESHOLD)
    )
    is_mid_val = (
        (df["customer_value_band"] == "Mid Value")
        | (
            (df["delivered_revenue"] >= VALUE_MID_THRESHOLD)
            & (df["delivered_revenue"] < VALUE_HIGH_THRESHOLD)
        )
    )
    is_low_val = (
        (df["customer_value_band"].isin(["Low Value", "Zero Value"]))
        | (df["delivered_revenue"] < VALUE_MID_THRESHOLD)
    )

    is_high_fric = (
        (df["friction_band"] == "High Friction")
        | (df["friction_score"] >= FRICTION_HIGH_SCORE_THRESHOLD)
        | (df["friction_rate"] > 0.25)
    )

    is_dev_eng = (
        (df["engagement_score"] >= ENGAGEMENT_DEVELOPING_THRESHOLD)
        | (df["engagement_band"].isin(["Active", "Lapsing"]))
    )

    is_inactive = (
        (df["engagement_band"] == "Inactive")
        | (df["recency_days"] > 365)
    )

    conditions = [
        is_high_risk & is_high_val & is_high_fric,
        is_high_risk & is_high_val,
        is_high_risk & is_mid_val,
        is_high_risk & is_low_val,
        is_med_risk & is_high_val,
        is_med_risk & is_dev_eng,
        is_low_risk & is_high_val,
        is_low_risk & is_dev_eng,
        is_low_val & is_inactive,
    ]

    choices = [
        "High Risk / High Value / High Friction",
        "High Risk / High Value",
        "High Risk / Mid Value",
        "High Risk / Low Value",
        "Medium Risk / High Value",
        "Medium Risk / Developing",
        "Low Risk / High Value",
        "Low Risk / Developing",
        "Low Value / Inactive",
    ]

    segment = pd.Series(
        np.select(conditions, choices, default="General Monitoring"),
        index=df.index,
    )

    return segment


def apply_segmentation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Append 'priority_tier' and 'business_segment' to DataFrame.

    Returns:
        DataFrame with priority_tier and business_segment columns.
    """
    df_out = df.copy()
    df_out["priority_tier"] = assign_priority_tier(df_out)
    df_out["business_segment"] = assign_business_segment(df_out)
    return df_out
