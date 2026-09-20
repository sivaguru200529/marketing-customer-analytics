"""
Aura Retail Analytics - Phase 4 Part 3
Feature Engineering & Deterministic Behavioral Classifications for Customer Intelligence.
"""

import numpy as np
import pandas as pd

from src.customer_intelligence.config import (
    ANCHOR_DATE,
    CLUSTER_DESCRIPTIONS,
    ENGAGEMENT_ACTIVE_DAYS,
    ENGAGEMENT_DORMANT_DAYS,
    ENGAGEMENT_LAPSING_DAYS,
    FRICTION_HIGH_RATE,
    VALUE_BAND_HIGH,
    VALUE_BAND_MID,
)


def compute_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute deterministic derived customer intelligence features with safe zero-division handling.
    """
    df_out = df.copy()

    # 1. Customer Tenure
    anchor_dt = pd.to_datetime(ANCHOR_DATE)
    df_out["tenure_days"] = (anchor_dt - pd.to_datetime(df_out["signup_date"])).dt.days

    # 2. Ratios and Rates (Safe zero-denominator handling)
    total_orders = df_out["total_orders"]
    web_sessions = df_out["total_web_sessions"]

    df_out["order_delivery_rate"] = np.where(
        total_orders > 0,
        np.round(df_out["delivered_orders"] / total_orders, 4),
        0.0,
    )

    df_out["return_rate"] = np.where(
        total_orders > 0,
        np.round(df_out["returned_orders"] / total_orders, 4),
        0.0,
    )

    df_out["cancellation_rate"] = np.where(
        total_orders > 0,
        np.round(df_out["cancelled_orders"] / total_orders, 4),
        0.0,
    )

    friction_orders = df_out["returned_orders"] + df_out["cancelled_orders"]
    df_out["friction_order_count"] = friction_orders
    df_out["fulfillment_friction_flag"] = np.where(friction_orders > 0, 1, 0)
    
    df_out["friction_rate"] = np.where(
        total_orders > 0,
        np.round(friction_orders / total_orders, 4),
        0.0,
    )

    df_out["cart_abandonment_rate"] = np.where(
        web_sessions > 0,
        np.round(df_out["total_abandoned_carts"] / web_sessions, 4),
        0.0,
    )

    df_out["tickets_per_order"] = np.where(
        total_orders > 0,
        np.round(df_out["total_support_tickets"] / total_orders, 4),
        0.0,
    )

    df_out["units_per_order"] = np.where(
        total_orders > 0,
        np.round(df_out["total_units_purchased"] / total_orders, 2),
        0.0,
    )

    df_out["gross_aov"] = np.where(
        total_orders > 0,
        np.round(df_out["gross_revenue"] / total_orders, 2),
        0.0,
    )

    # 3. RFM Composite Scores
    df_out["rfm_total_score"] = df_out["r_score"] + df_out["f_score"] + df_out["m_score"]
    df_out["rfm_score"] = (
        df_out["r_score"].astype(str)
        + df_out["f_score"].astype(str)
        + df_out["m_score"].astype(str)
    )

    # 4. Cluster Descriptive Profile
    df_out["cluster_description"] = df_out["cluster_id"].map(CLUSTER_DESCRIPTIONS).fillna("Unclassified")

    # 5. Deterministic Non-Predictive Classification Bands
    df_out["customer_value_band"] = assign_customer_value_band(df_out["delivered_revenue"])
    df_out["engagement_band"] = assign_engagement_band(df_out["recency_days"])
    df_out["friction_band"] = assign_friction_band(df_out["return_rate"], df_out["cancellation_rate"])

    return df_out


def assign_customer_value_band(delivered_revenue: pd.Series) -> pd.Series:
    """
    Assign transparent, deterministic customer value bands based on delivered revenue.
    """
    conditions = [
        delivered_revenue >= VALUE_BAND_HIGH,
        (delivered_revenue >= VALUE_BAND_MID) & (delivered_revenue < VALUE_BAND_HIGH),
        (delivered_revenue > 0.0) & (delivered_revenue < VALUE_BAND_MID),
        delivered_revenue == 0.0,
    ]
    choices = [
        "High Value",
        "Mid Value",
        "Low Value",
        "Zero Value",
    ]
    return pd.Series(np.select(conditions, choices, default="Unclassified"), index=delivered_revenue.index)


def assign_engagement_band(recency_days: pd.Series) -> pd.Series:
    """
    Assign transparent, deterministic customer activity bands based on days since last order.
    """
    conditions = [
        recency_days <= ENGAGEMENT_ACTIVE_DAYS,
        (recency_days > ENGAGEMENT_ACTIVE_DAYS) & (recency_days <= ENGAGEMENT_LAPSING_DAYS),
        (recency_days > ENGAGEMENT_LAPSING_DAYS) & (recency_days <= ENGAGEMENT_DORMANT_DAYS),
        recency_days > ENGAGEMENT_DORMANT_DAYS,
    ]
    choices = [
        "Active",
        "Lapsing",
        "Dormant",
        "Inactive",
    ]
    return pd.Series(np.select(conditions, choices, default="Unclassified"), index=recency_days.index)


def assign_friction_band(return_rate: pd.Series, cancellation_rate: pd.Series) -> pd.Series:
    """
    Assign transparent, deterministic friction bands based on fulfillment disruption rates.
    """
    total_friction_rate = return_rate + cancellation_rate
    conditions = [
        total_friction_rate == 0.0,
        (total_friction_rate > 0.0) & (total_friction_rate <= FRICTION_HIGH_RATE),
        total_friction_rate > FRICTION_HIGH_RATE,
    ]
    choices = [
        "No Friction",
        "Low Friction",
        "High Friction",
    ]
    return pd.Series(np.select(conditions, choices, default="Unclassified"), index=total_friction_rate.index)
