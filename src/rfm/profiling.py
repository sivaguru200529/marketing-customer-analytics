"""
Aura Retail Analytics - Phase 4 Part 2
Behavioral Profiling and Cross-Methodological Comparison Module.

Computes comprehensive empirical profiles for rule-based RFM segments and
unsupervised K-Means clusters, reconciling totals to the 10,000 customer base.
"""

import os
from typing import Optional, Tuple
import numpy as np
import pandas as pd

from src.rfm.config import DEFAULT_OUTPUT_DIR, SEGMENT_PRIORITY_ORDER


def profile_rfm_segments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate comprehensive behavioral summary for all 8 RFM segments.

    Reconciles:
    - sum(customer_count) == len(df) (10,000)
    - sum(customer_percentage) ≈ 100.0%
    """
    total_customers = len(df)
    total_delivered_rev = df["monetary"].sum()

    records = []
    # Follow explicit authoritative priority order
    segments = [s for s in SEGMENT_PRIORITY_ORDER if s in df["rfm_segment"].unique()]

    for seg in segments:
        sub = df[df["rfm_segment"] == seg]
        n_cust = len(sub)
        pct_cust = round((n_cust / total_customers) * 100.0, 2)

        tot_rev = float(sub["monetary"].sum())
        rev_share = round((tot_rev / total_delivered_rev) * 100.0, 2) if total_delivered_rev > 0 else 0.0

        tot_orders = sub["total_orders"].sum() if "total_orders" in sub.columns else sub["frequency"].sum()
        tot_ret = sub["returned_orders"].sum() if "returned_orders" in sub.columns else 0
        tot_canc = sub["cancelled_orders"].sum() if "cancelled_orders" in sub.columns else 0

        ret_rate = round((tot_ret / tot_orders) * 100.0, 2) if tot_orders > 0 else 0.0
        canc_rate = round((tot_canc / tot_orders) * 100.0, 2) if tot_orders > 0 else 0.0

        records.append({
            "rfm_segment": seg,
            "customer_count": n_cust,
            "customer_percentage": pct_cust,
            "revenue_share_pct": rev_share,
            "total_delivered_revenue": round(tot_rev, 2),
            "mean_recency_days": round(float(sub["recency"].mean()), 1),
            "median_recency_days": round(float(sub["recency"].median()), 1),
            "mean_frequency_orders": round(float(sub["frequency"].mean()), 2),
            "median_frequency_orders": round(float(sub["frequency"].median()), 1),
            "mean_monetary_revenue": round(float(sub["monetary"].mean()), 2),
            "median_monetary_revenue": round(float(sub["monetary"].median()), 2),
            "mean_delivered_aov": round(float(sub["delivered_aov"].dropna().mean()), 2) if "delivered_aov" in sub.columns and not sub["delivered_aov"].dropna().empty else 0.0,
            "median_delivered_aov": round(float(sub["delivered_aov"].dropna().median()), 2) if "delivered_aov" in sub.columns and not sub["delivered_aov"].dropna().empty else 0.0,
            "mean_units_purchased": round(float(sub["total_units"].mean()), 2) if "total_units" in sub.columns else 0.0,
            "median_units_purchased": round(float(sub["total_units"].median()), 1) if "total_units" in sub.columns else 0.0,
            "return_rate_pct": ret_rate,
            "cancellation_rate_pct": canc_rate,
        })

    seg_summary_df = pd.DataFrame(records)

    # Validate reconciliation
    assert seg_summary_df["customer_count"].sum() == total_customers, "Segment counts must sum to total customers."
    assert abs(seg_summary_df["customer_percentage"].sum() - 100.0) < 0.2, "Segment shares must sum to ~100%."

    return seg_summary_df


def profile_kmeans_clusters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate neutral behavioral summary for all K-Means clusters.
    """
    total_customers = len(df)
    total_delivered_rev = df["monetary"].sum()

    records = []
    cluster_labels = sorted(df["cluster_label"].unique())

    for clus in cluster_labels:
        sub = df[df["cluster_label"] == clus]
        n_cust = len(sub)
        pct_cust = round((n_cust / total_customers) * 100.0, 2)

        tot_rev = float(sub["monetary"].sum())
        rev_share = round((tot_rev / total_delivered_rev) * 100.0, 2) if total_delivered_rev > 0 else 0.0

        tot_orders = sub["total_orders"].sum() if "total_orders" in sub.columns else sub["frequency"].sum()
        tot_ret = sub["returned_orders"].sum() if "returned_orders" in sub.columns else 0
        tot_canc = sub["cancelled_orders"].sum() if "cancelled_orders" in sub.columns else 0

        ret_rate = round((tot_ret / tot_orders) * 100.0, 2) if tot_orders > 0 else 0.0
        canc_rate = round((tot_canc / tot_orders) * 100.0, 2) if tot_orders > 0 else 0.0

        # Dominant RFM segment
        top_segment = sub["rfm_segment"].mode()[0] if "rfm_segment" in sub.columns else "N/A"
        top_segment_count = int((sub["rfm_segment"] == top_segment).sum())
        top_segment_share = round((top_segment_count / n_cust) * 100.0, 1)

        records.append({
            "cluster_label": clus,
            "customer_count": n_cust,
            "customer_percentage": pct_cust,
            "revenue_share_pct": rev_share,
            "total_delivered_revenue": round(tot_rev, 2),
            "mean_recency_days": round(float(sub["recency"].mean()), 1),
            "median_recency_days": round(float(sub["recency"].median()), 1),
            "mean_frequency_orders": round(float(sub["frequency"].mean()), 2),
            "median_frequency_orders": round(float(sub["frequency"].median()), 1),
            "mean_monetary_revenue": round(float(sub["monetary"].mean()), 2),
            "median_monetary_revenue": round(float(sub["monetary"].median()), 2),
            "mean_delivered_aov": round(float(sub["delivered_aov"].dropna().mean()), 2) if "delivered_aov" in sub.columns and not sub["delivered_aov"].dropna().empty else 0.0,
            "median_delivered_aov": round(float(sub["delivered_aov"].dropna().median()), 2) if "delivered_aov" in sub.columns and not sub["delivered_aov"].dropna().empty else 0.0,
            "mean_units_purchased": round(float(sub["total_units"].mean()), 2) if "total_units" in sub.columns else 0.0,
            "median_units_purchased": round(float(sub["total_units"].median()), 1) if "total_units" in sub.columns else 0.0,
            "return_rate_pct": ret_rate,
            "cancellation_rate_pct": canc_rate,
            "dominant_rfm_segment": f"{top_segment} ({top_segment_share}%)",
        })

    clus_summary_df = pd.DataFrame(records)

    # Validate reconciliation
    assert clus_summary_df["customer_count"].sum() == total_customers, "Cluster counts must sum to total customers."
    assert abs(clus_summary_df["customer_percentage"].sum() - 100.0) < 0.2, "Cluster shares must sum to ~100%."

    return clus_summary_df


def compare_rfm_and_clusters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cross-tabulate RFM segments vs K-Means clusters to evaluate alignment and distinctions.
    """
    total = len(df)
    comparison_df = df.groupby(["rfm_segment", "cluster_label"], as_index=False).agg(
        customer_count=("customer_id", "count"),
        average_recency=("recency", "mean"),
        average_frequency=("frequency", "mean"),
        average_monetary=("monetary", "mean"),
        total_revenue=("monetary", "sum"),
    )

    comparison_df["customer_percentage"] = round((comparison_df["customer_count"] / total) * 100.0, 2)
    comparison_df["average_recency"] = comparison_df["average_recency"].round(1)
    comparison_df["average_frequency"] = comparison_df["average_frequency"].round(2)
    comparison_df["average_monetary"] = comparison_df["average_monetary"].round(2)
    comparison_df["total_revenue"] = comparison_df["total_revenue"].round(2)

    # Sort deterministically
    comparison_df = comparison_df.sort_values(
        by=["rfm_segment", "cluster_label"]
    ).reset_index(drop=True)

    return comparison_df


def export_profiling_outputs(
    seg_df: pd.DataFrame,
    clus_df: pd.DataFrame,
    comp_df: pd.DataFrame,
    output_dir: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    Export rfm_segment_summary.csv, cluster_profile.csv, and rfm_cluster_comparison.csv.
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)

    p1 = os.path.join(output_dir, "rfm_segment_summary.csv")
    seg_df.to_csv(p1, index=False)

    p2 = os.path.join(output_dir, "cluster_profile.csv")
    clus_df.to_csv(p2, index=False)

    p3 = os.path.join(output_dir, "rfm_cluster_comparison.csv")
    comp_df.to_csv(p3, index=False)

    return p1, p2, p3
