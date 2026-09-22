"""
Aura Retail Analytics - Phase 5 Part 2
Business Scoring & Weighted Priority Score Formulation Module.
"""

from typing import Dict
import numpy as np
import pandas as pd

from src.prioritization.config import (
    ENGAGEMENT_WEIGHT_ORDERS,
    ENGAGEMENT_WEIGHT_RECENCY,
    ENGAGEMENT_WEIGHT_SESSIONS,
    FRICTION_MAX_TICKETS,
    FRICTION_WEIGHT_CART_ABANDON,
    FRICTION_WEIGHT_ORDER_RATE,
    FRICTION_WEIGHT_TICKETS,
    PRIORITY_WEIGHT_ENGAGEMENT,
    PRIORITY_WEIGHT_FRICTION,
    PRIORITY_WEIGHT_RISK,
    PRIORITY_WEIGHT_VALUE,
)


def validate_priority_weights(weights: Dict[str, float]) -> bool:
    """
    Validate that priority weights are non-negative and sum exactly to 1.0.

    Args:
        weights: Dictionary of weights for risk, value, engagement, friction.

    Raises:
        ValueError: If weights are negative or do not sum to 1.0.
    """
    for k, v in weights.items():
        if v < 0:
            raise ValueError(f"Priority weight '{k}' is negative: {v}")

    total_weight = sum(weights.values())
    if not np.isclose(total_weight, 1.0, atol=1e-5):
        raise ValueError(f"Priority weights must sum to 1.0, got: {total_weight}")

    return True


def calculate_risk_score(df: pd.DataFrame) -> pd.Series:
    """
    Calculate normalized risk_score from Phase 5 Part 1 churn probability.

    Formula:
        risk_score = churn_probability
    """
    if "churn_probability" not in df.columns:
        raise KeyError("Column 'churn_probability' missing from DataFrame.")

    risk = df["churn_probability"].astype(float).copy()
    if not ((risk >= 0.0) & (risk <= 1.0)).all():
        raise ValueError("risk_score contains values outside bounded interval [0.0, 1.0].")

    return risk


def calculate_value_score(df: pd.DataFrame) -> pd.Series:
    """
    Calculate normalized value_score from delivered revenue.

    Formula:
        if delivered_revenue == 0:
            value_score = 0.0
        else:
            value_score = percentile_rank(delivered_revenue)
    """
    if "delivered_revenue" not in df.columns:
        raise KeyError("Column 'delivered_revenue' missing from DataFrame.")

    rev = df["delivered_revenue"].astype(float)
    val_score = pd.Series(0.0, index=df.index, dtype=float)

    positive_mask = rev > 0.0
    if positive_mask.any():
        # Percentile rank among positive earners from (1/N) to 1.0
        positive_ranks = rev[positive_mask].rank(method="average", pct=True)
        val_score.loc[positive_mask] = positive_ranks

    if not ((val_score >= 0.0) & (val_score <= 1.0)).all():
        raise ValueError("value_score contains values outside bounded interval [0.0, 1.0].")

    return val_score


def calculate_engagement_score(df: pd.DataFrame) -> pd.Series:
    """
    Calculate normalized engagement_score combining recency, web sessions, and order count.

    Formula:
        recency_component = 1 - recency_days / max(recency_days)
        session_component = percentile_rank(total_web_sessions)
        order_component = percentile_rank(delivered_orders)
        engagement_score = 0.50 * recency_component + 0.30 * session_component + 0.20 * order_component
    """
    for col in ["recency_days", "total_web_sessions", "delivered_orders"]:
        if col not in df.columns:
            raise KeyError(f"Column '{col}' missing from DataFrame.")

    max_recency = float(df["recency_days"].max())
    if max_recency > 0:
        recency_comp = 1.0 - (df["recency_days"].astype(float) / max_recency)
    else:
        recency_comp = pd.Series(1.0, index=df.index)

    session_comp = df["total_web_sessions"].astype(float).rank(method="average", pct=True)
    order_comp = df["delivered_orders"].astype(float).rank(method="average", pct=True)

    eng_score = (
        ENGAGEMENT_WEIGHT_RECENCY * recency_comp
        + ENGAGEMENT_WEIGHT_SESSIONS * session_comp
        + ENGAGEMENT_WEIGHT_ORDERS * order_comp
    )

    if not ((eng_score >= 0.0) & (eng_score <= 1.0)).all():
        raise ValueError("engagement_score contains values outside bounded interval [0.0, 1.0].")

    return eng_score


def calculate_friction_score(df: pd.DataFrame) -> pd.Series:
    """
    Calculate normalized friction_score combining order friction, cart abandonment, and support tickets.

    Formula:
        order_friction = friction_rate
        cart_friction = cart_abandonment_rate
        ticket_friction = min(total_support_tickets / 3, 1)
        friction_score = 0.40 * order_friction + 0.35 * cart_friction + 0.25 * ticket_friction
    """
    for col in ["friction_rate", "cart_abandonment_rate", "total_support_tickets"]:
        if col not in df.columns:
            raise KeyError(f"Column '{col}' missing from DataFrame.")

    order_friction = df["friction_rate"].astype(float).clip(0.0, 1.0)
    cart_friction = df["cart_abandonment_rate"].astype(float).clip(0.0, 1.0)
    ticket_friction = (df["total_support_tickets"].astype(float) / FRICTION_MAX_TICKETS).clip(0.0, 1.0)

    fric_score = (
        FRICTION_WEIGHT_ORDER_RATE * order_friction
        + FRICTION_WEIGHT_CART_ABANDON * cart_friction
        + FRICTION_WEIGHT_TICKETS * ticket_friction
    )

    if not ((fric_score >= 0.0) & (fric_score <= 1.0)).all():
        raise ValueError("friction_score contains values outside bounded interval [0.0, 1.0].")

    return fric_score


def calculate_composite_priority_score(
    risk_score: pd.Series,
    value_score: pd.Series,
    engagement_score: pd.Series,
    friction_score: pd.Series,
    w_risk: float = PRIORITY_WEIGHT_RISK,
    w_value: float = PRIORITY_WEIGHT_VALUE,
    w_eng: float = PRIORITY_WEIGHT_ENGAGEMENT,
    w_fric: float = PRIORITY_WEIGHT_FRICTION,
) -> pd.Series:
    """
    Calculate composite priority_score using the configured weighted formula.

    Formula:
        priority_score = 0.50 * risk_score + 0.30 * value_score + 0.10 * engagement_score + 0.10 * friction_score

    IMPORTANT:
        No min-max scaling is performed after calculating the weighted score.
        The weighted sum itself is the final priority_score and is naturally bounded in [0.0, 1.0].
    """
    weights = {
        "risk": w_risk,
        "value": w_value,
        "engagement": w_eng,
        "friction": w_fric,
    }
    validate_priority_weights(weights)

    raw_priority = (
        w_risk * risk_score
        + w_value * value_score
        + w_eng * engagement_score
        + w_fric * friction_score
    )

    priority_score = raw_priority.round(4)

    if not ((priority_score >= 0.0) & (priority_score <= 1.0)).all():
        raise ValueError("priority_score contains values outside bounded interval [0.0, 1.0].")

    return priority_score


def compute_all_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all 4 business component scores and the composite priority_score, appending them to df.

    Returns:
        DataFrame with risk_score, value_score, engagement_score, friction_score, priority_score.
    """
    df_out = df.copy()

    df_out["risk_score"] = calculate_risk_score(df_out).round(4)
    df_out["value_score"] = calculate_value_score(df_out).round(4)
    df_out["engagement_score"] = calculate_engagement_score(df_out).round(4)
    df_out["friction_score"] = calculate_friction_score(df_out).round(4)

    df_out["priority_score"] = calculate_composite_priority_score(
        risk_score=df_out["risk_score"],
        value_score=df_out["value_score"],
        engagement_score=df_out["engagement_score"],
        friction_score=df_out["friction_score"],
    )

    return df_out
