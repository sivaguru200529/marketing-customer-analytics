"""
Aura Retail Analytics - Phase 5 Part 2
Analytical Summaries & Prioritization Reporting Module.
"""

import os
from typing import Dict, Optional
import numpy as np
import pandas as pd

from src.prioritization.config import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SUMMARIES_DIR,
    SUMMARY_BUSINESS_SEGMENT,
    SUMMARY_FRICTION,
    SUMMARY_PRIORITY_TIER,
    SUMMARY_RECOMMENDED_ACTION,
    SUMMARY_RECOMMENDED_CAMPAIGN,
    SUMMARY_RISK_VALUE,
)


def generate_priority_tier_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate customer volume, revenue, priority scores, and churn risk by priority tier.
    """
    total_customers = len(df)
    total_revenue = float(df["delivered_revenue"].sum())

    tiers = ["High Priority", "Medium Priority", "Low Priority"]

    summary_rows = []
    for tier in tiers:
        sub = df[df["priority_tier"] == tier]
        count = len(sub)
        share = (count / total_customers) * 100.0 if total_customers > 0 else 0.0
        rev = float(sub["delivered_revenue"].sum())
        rev_share = (rev / total_revenue) * 100.0 if total_revenue > 0 else 0.0
        mean_rev = (rev / count) if count > 0 else 0.0
        mean_prio = float(sub["priority_score"].mean()) if count > 0 else 0.0
        mean_prob = float(sub["churn_probability"].mean()) if count > 0 else 0.0

        summary_rows.append(
            {
                "priority_tier": tier,
                "customer_count": count,
                "customer_share_pct": round(share, 2),
                "total_delivered_revenue": round(rev, 2),
                "revenue_share_pct": round(rev_share, 2),
                "mean_delivered_revenue": round(mean_rev, 2),
                "mean_priority_score": round(mean_prio, 4),
                "mean_churn_probability": round(mean_prob, 4),
            }
        )

    return pd.DataFrame(summary_rows)


def generate_business_segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate metrics across the mutually exclusive business segments.
    """
    total_customers = len(df)
    total_revenue = float(df["delivered_revenue"].sum())

    seg_order = [
        "High Risk / High Value / High Friction",
        "High Risk / High Value",
        "High Risk / Mid Value",
        "High Risk / Low Value",
        "Medium Risk / High Value",
        "Medium Risk / Developing",
        "Low Risk / High Value",
        "Low Risk / Developing",
        "Low Value / Inactive",
        "General Monitoring",
    ]

    summary_rows = []
    for seg in seg_order:
        sub = df[df["business_segment"] == seg]
        count = len(sub)
        share = (count / total_customers) * 100.0 if total_customers > 0 else 0.0
        rev = float(sub["delivered_revenue"].sum())
        rev_share = (rev / total_revenue) * 100.0 if total_revenue > 0 else 0.0
        mean_rev = (rev / count) if count > 0 else 0.0
        mean_prio = float(sub["priority_score"].mean()) if count > 0 else 0.0
        mean_prob = float(sub["churn_probability"].mean()) if count > 0 else 0.0

        summary_rows.append(
            {
                "business_segment": seg,
                "customer_count": count,
                "customer_share_pct": round(share, 2),
                "total_delivered_revenue": round(rev, 2),
                "revenue_share_pct": round(rev_share, 2),
                "mean_delivered_revenue": round(mean_rev, 2),
                "mean_priority_score": round(mean_prio, 4),
                "mean_churn_probability": round(mean_prob, 4),
            }
        )

    return pd.DataFrame(summary_rows)


def generate_recommended_action_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate customer counts and revenue across recommended action categories.
    """
    total_customers = len(df)
    total_revenue = float(df["delivered_revenue"].sum())

    action_order = [
        "High-Value Retention + Friction Resolution",
        "Retention / High-Value Intervention",
        "Targeted Retention",
        "Friction Resolution",
        "Engagement Reinforcement",
        "Relationship Development",
        "Monitor",
    ]

    summary_rows = []
    for action in action_order:
        sub = df[df["recommended_action"] == action]
        count = len(sub)
        share = (count / total_customers) * 100.0 if total_customers > 0 else 0.0
        rev = float(sub["delivered_revenue"].sum())
        rev_share = (rev / total_revenue) * 100.0 if total_revenue > 0 else 0.0
        mean_prio = float(sub["priority_score"].mean()) if count > 0 else 0.0
        mean_prob = float(sub["churn_probability"].mean()) if count > 0 else 0.0

        summary_rows.append(
            {
                "recommended_action": action,
                "customer_count": count,
                "customer_share_pct": round(share, 2),
                "total_delivered_revenue": round(rev, 2),
                "revenue_share_pct": round(rev_share, 2),
                "mean_priority_score": round(mean_prio, 4),
                "mean_churn_probability": round(mean_prob, 4),
            }
        )

    return pd.DataFrame(summary_rows)


def generate_recommended_campaign_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate customer volume and revenue across recommended campaign categories.
    """
    total_customers = len(df)
    total_revenue = float(df["delivered_revenue"].sum())

    campaign_order = [
        "High-Value Retention Campaign",
        "Targeted Retention Campaign",
        "Friction Resolution Campaign",
        "Engagement Reinforcement Campaign",
        "Loyalty & Relationship Campaign",
        "Automated Monitoring",
    ]

    summary_rows = []
    for camp in campaign_order:
        sub = df[df["recommended_campaign"] == camp]
        count = len(sub)
        share = (count / total_customers) * 100.0 if total_customers > 0 else 0.0
        rev = float(sub["delivered_revenue"].sum())
        rev_share = (rev / total_revenue) * 100.0 if total_revenue > 0 else 0.0
        mean_prio = float(sub["priority_score"].mean()) if count > 0 else 0.0
        mean_prob = float(sub["churn_probability"].mean()) if count > 0 else 0.0

        summary_rows.append(
            {
                "recommended_campaign": camp,
                "customer_count": count,
                "customer_share_pct": round(share, 2),
                "total_delivered_revenue": round(rev, 2),
                "revenue_share_pct": round(rev_share, 2),
                "mean_priority_score": round(mean_prio, 4),
                "mean_churn_probability": round(mean_prob, 4),
            }
        )

    return pd.DataFrame(summary_rows)


def generate_risk_value_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cross-tabulate churn risk bands against customer value bands.
    """
    risk_order = ["High Risk", "Medium Risk", "Low Risk"]
    val_order = ["High Value", "Mid Value", "Low Value", "Zero Value"]

    summary_rows = []
    for r in risk_order:
        for v in val_order:
            sub = df[(df["churn_risk_band"] == r) & (df["customer_value_band"] == v)]
            count = len(sub)
            rev = float(sub["delivered_revenue"].sum())
            mean_prob = float(sub["churn_probability"].mean()) if count > 0 else 0.0
            mean_prio = float(sub["priority_score"].mean()) if count > 0 else 0.0

            summary_rows.append(
                {
                    "churn_risk_band": r,
                    "customer_value_band": v,
                    "customer_count": count,
                    "total_delivered_revenue": round(rev, 2),
                    "mean_churn_probability": round(mean_prob, 4),
                    "mean_priority_score": round(mean_prio, 4),
                }
            )

    return pd.DataFrame(summary_rows)


def generate_friction_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate customer volume, revenue, and churn risk across friction bands.
    """
    total_customers = len(df)
    fric_order = ["High Friction", "Low Friction", "No Friction"]

    summary_rows = []
    for f in fric_order:
        sub = df[df["friction_band"] == f]
        count = len(sub)
        share = (count / total_customers) * 100.0 if total_customers > 0 else 0.0
        rev = float(sub["delivered_revenue"].sum())
        mean_fric = float(sub["friction_score"].mean()) if count > 0 else 0.0
        mean_tix = float(sub["total_support_tickets"].mean()) if count > 0 else 0.0
        mean_prob = float(sub["churn_probability"].mean()) if count > 0 else 0.0
        mean_prio = float(sub["priority_score"].mean()) if count > 0 else 0.0

        summary_rows.append(
            {
                "friction_band": f,
                "customer_count": count,
                "customer_share_pct": round(share, 2),
                "total_delivered_revenue": round(rev, 2),
                "mean_friction_score": round(mean_fric, 4),
                "mean_support_tickets": round(mean_tix, 2),
                "mean_churn_probability": round(mean_prob, 4),
                "mean_priority_score": round(mean_prio, 4),
            }
        )

    return pd.DataFrame(summary_rows)


def generate_all_summaries(
    df: pd.DataFrame,
    output_dir: Optional[str] = None,
    summaries_dir: Optional[str] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Generate and save all 6 summary datasets to disk.

    Outputs written to both data/05_churn/ and data/05_churn/summaries/.
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    if summaries_dir is None:
        summaries_dir = DEFAULT_SUMMARIES_DIR

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(summaries_dir, exist_ok=True)

    summaries = {
        SUMMARY_PRIORITY_TIER: generate_priority_tier_summary(df),
        SUMMARY_BUSINESS_SEGMENT: generate_business_segment_summary(df),
        SUMMARY_RECOMMENDED_ACTION: generate_recommended_action_summary(df),
        SUMMARY_RECOMMENDED_CAMPAIGN: generate_recommended_campaign_summary(df),
        SUMMARY_RISK_VALUE: generate_risk_value_summary(df),
        SUMMARY_FRICTION: generate_friction_summary(df),
    }

    for filename, df_sum in summaries.items():
        # Export to data/05_churn/
        df_sum.to_csv(os.path.join(output_dir, filename), index=False)
        # Mirror to data/05_churn/summaries/
        df_sum.to_csv(os.path.join(summaries_dir, filename), index=False)

    return summaries
