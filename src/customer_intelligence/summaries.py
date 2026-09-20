"""
Aura Retail Analytics - Phase 4 Part 3
Generation of Analytical Summary Outputs & Segment-Cluster Cross-Tabulation.
"""

import os
from typing import Dict
import numpy as np
import pandas as pd

from src.customer_intelligence.config import (
    DEFAULT_OUTPUT_DIR,
    OUTPUT_BEHAVIOR_SUMMARY,
    OUTPUT_CLUSTER_SUMMARY,
    OUTPUT_MATRIX_SUMMARY,
    OUTPUT_SEGMENT_SUMMARY,
    OUTPUT_VALUE_SUMMARY,
    SEGMENT_PRIORITY_ORDER,
)


def generate_all_summaries(
    df_intel: pd.DataFrame,
    output_dir: str = DEFAULT_OUTPUT_DIR,
) -> Dict[str, pd.DataFrame]:
    """
    Generate and export all Phase 4 Part 3 analytical summaries.
    
    Returns:
        Dictionary mapping summary output name to its dataframe.
    """
    os.makedirs(output_dir, exist_ok=True)

    df_value = generate_customer_value_summary(df_intel)
    df_segment = generate_customer_segment_summary(df_intel)
    df_cluster = generate_customer_cluster_summary(df_intel)
    df_matrix = generate_segment_cluster_matrix(df_intel)
    df_behavior = generate_customer_behavior_summary(df_intel)

    df_value.to_csv(os.path.join(output_dir, "customer_value_summary.csv"), index=False)
    df_segment.to_csv(os.path.join(output_dir, "customer_segment_summary.csv"), index=False)
    df_cluster.to_csv(os.path.join(output_dir, "customer_cluster_summary.csv"), index=False)
    df_matrix.to_csv(os.path.join(output_dir, "segment_cluster_matrix.csv"), index=False)
    df_behavior.to_csv(os.path.join(output_dir, "customer_behavior_summary.csv"), index=False)

    return {
        "customer_value_summary": df_value,
        "customer_segment_summary": df_segment,
        "customer_cluster_summary": df_cluster,
        "segment_cluster_matrix": df_matrix,
        "customer_behavior_summary": df_behavior,
    }


def generate_customer_value_summary(df_intel: pd.DataFrame) -> pd.DataFrame:
    """Generate summary aggregated by customer_value_band."""
    total_rev = df_intel["delivered_revenue"].sum()
    total_cust = len(df_intel)

    order = ["High Value", "Mid Value", "Low Value", "Zero Value"]
    rows = []

    for band in order:
        sub = df_intel[df_intel["customer_value_band"] == band]
        count = len(sub)
        rev = sub["delivered_revenue"].sum()
        rows.append({
            "customer_value_band": band,
            "customer_count": count,
            "customer_percentage": round((count / total_cust) * 100.0, 2),
            "total_delivered_revenue": round(rev, 2),
            "revenue_share_pct": round((rev / total_rev) * 100.0, 2) if total_rev > 0 else 0.0,
            "mean_delivered_revenue": round(sub["delivered_revenue"].mean(), 2) if count > 0 else 0.0,
            "median_delivered_revenue": round(sub["delivered_revenue"].median(), 2) if count > 0 else 0.0,
            "mean_delivered_orders": round(sub["delivered_orders"].mean(), 2) if count > 0 else 0.0,
            "mean_recency_days": round(sub["recency_days"].mean(), 1) if count > 0 else 0.0,
            "mean_return_rate_pct": round(sub["return_rate"].mean() * 100.0, 2) if count > 0 else 0.0,
            "mean_cancellation_rate_pct": round(sub["cancellation_rate"].mean() * 100.0, 2) if count > 0 else 0.0,
        })

    return pd.DataFrame(rows)


def generate_customer_segment_summary(df_intel: pd.DataFrame) -> pd.DataFrame:
    """Generate summary aggregated by authoritative rfm_segment."""
    total_rev = df_intel["delivered_revenue"].sum()
    total_cust = len(df_intel)

    rows = []
    for seg in SEGMENT_PRIORITY_ORDER:
        sub = df_intel[df_intel["rfm_segment"] == seg]
        count = len(sub)
        rev = sub["delivered_revenue"].sum()
        aov_series = sub["delivered_aov"].dropna()
        rows.append({
            "rfm_segment": seg,
            "customer_count": count,
            "customer_percentage": round((count / total_cust) * 100.0, 2),
            "total_delivered_revenue": round(rev, 2),
            "revenue_share_pct": round((rev / total_rev) * 100.0, 2) if total_rev > 0 else 0.0,
            "avg_recency": round(sub["recency_days"].mean(), 1) if count > 0 else 0.0,
            "avg_frequency": round(sub["delivered_orders"].mean(), 2) if count > 0 else 0.0,
            "avg_monetary": round(sub["delivered_revenue"].mean(), 2) if count > 0 else 0.0,
            "avg_delivered_aov": round(aov_series.mean(), 2) if len(aov_series) > 0 else 0.0,
            "avg_return_rate": round(sub["return_rate"].mean(), 4) if count > 0 else 0.0,
            "avg_cancellation_rate": round(sub["cancellation_rate"].mean(), 4) if count > 0 else 0.0,
        })

    return pd.DataFrame(rows)


def generate_customer_cluster_summary(df_intel: pd.DataFrame) -> pd.DataFrame:
    """Generate summary aggregated by K-Means cluster."""
    total_rev = df_intel["delivered_revenue"].sum()
    total_cust = len(df_intel)

    rows = []
    for c_id in sorted(df_intel["cluster_id"].unique()):
        sub = df_intel[df_intel["cluster_id"] == c_id]
        count = len(sub)
        rev = sub["delivered_revenue"].sum()
        c_label = sub["cluster_label"].iloc[0]
        c_desc = sub["cluster_description"].iloc[0]
        
        # dominant segment
        dominant_seg = sub["rfm_segment"].value_counts().index[0]
        dom_share = (sub["rfm_segment"].value_counts().iloc[0] / count) * 100.0

        rows.append({
            "cluster_id": c_id,
            "cluster_label": c_label,
            "cluster_description": c_desc,
            "customer_count": count,
            "customer_share": round((count / total_cust) * 100.0, 2),
            "delivered_revenue": round(rev, 2),
            "revenue_share": round((rev / total_rev) * 100.0, 2) if total_rev > 0 else 0.0,
            "avg_recency": round(sub["recency_days"].mean(), 1),
            "avg_frequency": round(sub["delivered_orders"].mean(), 2),
            "avg_monetary": round(sub["delivered_revenue"].mean(), 2),
            "dominant_rfm_segment": f"{dominant_seg} ({dom_share:.1f}%)",
        })

    return pd.DataFrame(rows)


def generate_segment_cluster_matrix(df_intel: pd.DataFrame) -> pd.DataFrame:
    """
    Generate exact cross-tabulation matrix of rfm_segment x cluster_label
    reconciling to 10,000 customers.
    """
    ct = pd.crosstab(
        df_intel["rfm_segment"],
        df_intel["cluster_label"],
    )
    # Reindex to preserve authoritative segment priority
    ct = ct.reindex(SEGMENT_PRIORITY_ORDER).fillna(0).astype(int)

    # Add row total
    ct["Total Customers"] = ct.sum(axis=1)
    ct["Customer Share (%)"] = round((ct["Total Customers"] / len(df_intel)) * 100.0, 2)

    # Convert index to column
    df_matrix = ct.reset_index().rename(columns={"rfm_segment": "Segment"})

    # Add Grand Total row
    totals = {
        "Segment": "Grand Total",
        "Cluster 0": int(df_intel["cluster_label"].eq("Cluster 0").sum()),
        "Cluster 1": int(df_intel["cluster_label"].eq("Cluster 1").sum()),
        "Cluster 2": int(df_intel["cluster_label"].eq("Cluster 2").sum()),
        "Total Customers": len(df_intel),
        "Customer Share (%)": 100.00,
    }
    df_matrix = pd.concat([df_matrix, pd.DataFrame([totals])], ignore_index=True)

    return df_matrix


def generate_customer_behavior_summary(df_intel: pd.DataFrame) -> pd.DataFrame:
    """
    Generate multi-dimensional behavioral summary by engagement band,
    acquisition channel, and friction band.
    """
    total_rev = df_intel["delivered_revenue"].sum()
    total_cust = len(df_intel)

    sections = [
        ("Engagement Band", "engagement_band", ["Active", "Lapsing", "Dormant", "Inactive"]),
        ("Acquisition Channel", "acquisition_channel", sorted(df_intel["acquisition_channel"].unique())),
        ("Friction Band", "friction_band", ["No Friction", "Low Friction", "High Friction"]),
    ]

    rows = []
    for dim_name, col, val_order in sections:
        for val in val_order:
            sub = df_intel[df_intel[col] == val]
            count = len(sub)
            rev = sub["delivered_revenue"].sum()
            rows.append({
                "dimension_category": dim_name,
                "dimension_value": val,
                "customer_count": count,
                "customer_percentage": round((count / total_cust) * 100.0, 2),
                "total_delivered_revenue": round(rev, 2),
                "revenue_share_pct": round((rev / total_rev) * 100.0, 2) if total_rev > 0 else 0.0,
                "mean_recency_days": round(sub["recency_days"].mean(), 1) if count > 0 else 0.0,
                "mean_delivered_orders": round(sub["delivered_orders"].mean(), 2) if count > 0 else 0.0,
                "mean_delivered_revenue": round(sub["delivered_revenue"].mean(), 2) if count > 0 else 0.0,
            })

    return pd.DataFrame(rows)
