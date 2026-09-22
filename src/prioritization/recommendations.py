"""
Aura Retail Analytics - Phase 5 Part 2
Customer Action Recommendations & Campaign Mapping Module.
"""

import numpy as np
import pandas as pd

from src.prioritization.config import (
    CAMPAIGN_MAPPING,
    CHURN_RISK_HIGH_THRESHOLD,
    CHURN_RISK_LOW_THRESHOLD,
    FRICTION_HIGH_SCORE_THRESHOLD,
    PRIORITY_TIER_HIGH_THRESHOLD,
    PRIORITY_TIER_MEDIUM_THRESHOLD,
    VALUE_HIGH_THRESHOLD,
    VALUE_MID_THRESHOLD,
)


def assign_recommended_action(df: pd.DataFrame) -> pd.Series:
    """
    Assign recommended customer actions using strict precedence hierarchy.

    Hierarchy:
        Rule 1: High Risk + High Value + High Friction -> High-Value Retention + Friction Resolution
        Rule 2: High Risk + High Value -> Retention / High-Value Intervention
        Rule 3: High Risk + Mid/Low Value -> Targeted Retention
        Rule 4: High Friction -> Friction Resolution
        Rule 5: Medium Priority + Active/Lapsing engagement -> Engagement Reinforcement
        Rule 6: Low Risk + High/Mid Value -> Relationship Development
        Rule 7: Fallback -> Monitor

    Args:
        df: DataFrame containing customer analytical attributes and scores.

    Returns:
        pd.Series of recommended action categories.
    """
    is_high_risk = (
        (df["churn_risk_band"] == "High Risk")
        | (df["churn_probability"] >= CHURN_RISK_HIGH_THRESHOLD)
    )
    is_low_risk = (
        (df["churn_risk_band"] == "Low Risk")
        | (df["churn_probability"] < CHURN_RISK_LOW_THRESHOLD)
    )

    is_high_val = (
        (df["customer_value_band"] == "High Value")
        | (df["delivered_revenue"] >= VALUE_HIGH_THRESHOLD)
    )
    is_mid_low_val = (
        (df["customer_value_band"].isin(["Mid Value", "Low Value", "Zero Value"]))
        | (df["delivered_revenue"] < VALUE_HIGH_THRESHOLD)
    )
    is_high_mid_val = (
        (df["customer_value_band"].isin(["High Value", "Mid Value"]))
        | (df["delivered_revenue"] >= VALUE_MID_THRESHOLD)
    )

    is_high_fric = (
        (df["friction_band"] == "High Friction")
        | (df["friction_score"] >= FRICTION_HIGH_SCORE_THRESHOLD)
        | (df["friction_rate"] > 0.25)
    )

    is_med_priority = (
        (df["priority_tier"] == "Medium Priority")
        | (
            (df["priority_score"] >= PRIORITY_TIER_MEDIUM_THRESHOLD)
            & (df["priority_score"] < PRIORITY_TIER_HIGH_THRESHOLD)
        )
    )

    is_active_lapsing = (
        df["engagement_band"].isin(["Active", "Lapsing"])
        | (df["recency_days"] <= 180)
    )

    conditions = [
        is_high_risk & is_high_val & is_high_fric,
        is_high_risk & is_high_val,
        is_high_risk & is_mid_low_val,
        is_high_fric,
        is_med_priority & is_active_lapsing,
        is_low_risk & is_high_mid_val,
    ]

    choices = [
        "High-Value Retention + Friction Resolution",
        "Retention / High-Value Intervention",
        "Targeted Retention",
        "Friction Resolution",
        "Engagement Reinforcement",
        "Relationship Development",
    ]

    actions = pd.Series(
        np.select(conditions, choices, default="Monitor"),
        index=df.index,
    )

    return actions


def assign_recommended_campaign(action_series: pd.Series) -> pd.Series:
    """
    Map recommended action categories to descriptive campaign planning categories.

    Mappings:
        High-Value Retention + Friction Resolution -> High-Value Retention Campaign
        Retention / High-Value Intervention -> High-Value Retention Campaign
        Targeted Retention -> Targeted Retention Campaign
        Friction Resolution -> Friction Resolution Campaign
        Engagement Reinforcement -> Engagement Reinforcement Campaign
        Relationship Development -> Loyalty & Relationship Campaign
        Monitor -> Automated Monitoring

    Args:
        action_series: Series of recommended action strings.

    Returns:
        pd.Series of campaign category strings.
    """
    campaigns = action_series.map(CAMPAIGN_MAPPING).fillna("Automated Monitoring")
    return campaigns


def apply_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Append 'recommended_action' and 'recommended_campaign' to DataFrame.

    Returns:
        DataFrame with action and campaign recommendations.
    """
    df_out = df.copy()
    actions = assign_recommended_action(df_out)
    df_out["recommended_action"] = actions
    df_out["recommended_campaign"] = assign_recommended_campaign(actions)
    return df_out
