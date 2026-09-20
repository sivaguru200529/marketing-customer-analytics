"""
Aura Retail Analytics - Phase 4 Part 1
Customer Exploratory Data Analysis Module.

Analyzes customer-level behaviors, order frequency distributions, revenue/monetary
metrics, basket depth, return/cancellation impact, and RFM segmentation.
"""

import os
from typing import Any, Dict, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def analyze_customer_metrics(df: pd.DataFrame) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """
    Compute factual customer behavior and segmentation statistics.

    Returns:
        Tuple containing:
        - Dict of scalar customer metrics.
        - DataFrame of RFM segment breakdowns.
        - DataFrame of percentiles / distributions.
    """
    total_customers = len(df)
    customers_with_orders = int((df["total_orders"] > 0).sum())
    customers_without_orders = total_customers - customers_with_orders

    total_orders = int(df["total_orders"].sum())
    delivered_orders = int(df["delivered_orders"].sum())
    returned_orders = int(df["returned_orders"].sum())
    cancelled_orders = int(df["cancelled_orders"].sum())
    total_units = int(df["total_units_purchased"].sum())

    total_gross_rev = float(df["gross_revenue"].sum())
    total_deliv_rev = float(df["delivered_revenue"].sum())

    mean_orders = float(df["total_orders"].mean())
    median_orders = float(df["total_orders"].median())
    std_orders = float(df["total_orders"].std())

    mean_gross_rev = float(df["gross_revenue"].mean())
    median_gross_rev = float(df["gross_revenue"].median())
    std_gross_rev = float(df["gross_revenue"].std())

    mean_deliv_rev = float(df["delivered_revenue"].mean())
    median_deliv_rev = float(df["delivered_revenue"].median())

    mean_recency = float(df["recency_days"].mean())
    median_recency = float(df["recency_days"].median())
    min_recency = int(df["recency_days"].min())
    max_recency = int(df["recency_days"].max())

    basket_depth_per_order = round(total_units / total_orders, 2) if total_orders > 0 else 0.0
    basket_depth_per_customer = round(total_units / total_customers, 2) if total_customers > 0 else 0.0

    customers_with_returns = int((df["returned_orders"] > 0).sum())
    customers_with_cancellations = int((df["cancelled_orders"] > 0).sum())
    pct_cust_with_returns = round((customers_with_returns / total_customers) * 100.0, 2)
    pct_cust_with_cancellations = round((customers_with_cancellations / total_customers) * 100.0, 2)

    # Metric dictionary
    metrics = {
        "total_customers": total_customers,
        "customers_with_orders": customers_with_orders,
        "customers_without_orders": customers_without_orders,
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "returned_orders": returned_orders,
        "cancelled_orders": cancelled_orders,
        "total_units_purchased": total_units,
        "total_gross_revenue": total_gross_rev,
        "total_delivered_revenue": total_deliv_rev,
        "mean_orders_per_customer": round(mean_orders, 2),
        "median_orders_per_customer": round(median_orders, 2),
        "std_orders_per_customer": round(std_orders, 2),
        "mean_gross_revenue_per_customer": round(mean_gross_rev, 2),
        "median_gross_revenue_per_customer": round(median_gross_rev, 2),
        "std_gross_revenue_per_customer": round(std_gross_rev, 2),
        "mean_delivered_revenue_per_customer": round(mean_deliv_rev, 2),
        "median_delivered_revenue_per_customer": round(median_deliv_rev, 2),
        "mean_recency_days": round(mean_recency, 1),
        "median_recency_days": round(median_recency, 1),
        "min_recency_days": min_recency,
        "max_recency_days": max_recency,
        "avg_basket_depth_units_per_order": basket_depth_per_order,
        "avg_units_per_customer": basket_depth_per_customer,
        "customers_with_returns": customers_with_returns,
        "pct_customers_with_returns": pct_cust_with_returns,
        "customers_with_cancellations": customers_with_cancellations,
        "pct_customers_with_cancellations": pct_cust_with_cancellations,
    }

    # Percentiles table for distribution analysis
    percentiles = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
    dist_df = pd.DataFrame({
        "percentile": [f"p{int(p*100)}" for p in percentiles],
        "total_orders": [round(float(df["total_orders"].quantile(p)), 2) for p in percentiles],
        "gross_revenue": [round(float(df["gross_revenue"].quantile(p)), 2) for p in percentiles],
        "delivered_revenue": [round(float(df["delivered_revenue"].quantile(p)), 2) for p in percentiles],
        "recency_days": [round(float(df["recency_days"].quantile(p)), 2) for p in percentiles],
        "units_purchased": [round(float(df["total_units_purchased"].quantile(p)), 2) for p in percentiles],
    })

    # RFM Segment Summary (unranked, factual)
    seg_group = df.groupby("rfm_segment", as_index=False).agg(
        customer_count=("customer_id", "count"),
        total_gross_revenue=("gross_revenue", "sum"),
        total_delivered_revenue=("delivered_revenue", "sum"),
        total_orders=("total_orders", "sum"),
        avg_orders=("total_orders", "mean"),
        avg_gross_revenue=("gross_revenue", "mean"),
        avg_recency_days=("recency_days", "mean"),
        avg_r_score=("r_score", "mean"),
        avg_f_score=("f_score", "mean"),
        avg_m_score=("m_score", "mean"),
    )
    seg_group["customer_share_pct"] = round((seg_group["customer_count"] / total_customers) * 100.0, 2)
    seg_group["revenue_share_pct"] = round((seg_group["total_gross_revenue"] / total_gross_rev) * 100.0, 2)
    seg_group["avg_orders"] = seg_group["avg_orders"].round(2)
    seg_group["avg_gross_revenue"] = seg_group["avg_gross_revenue"].round(2)
    seg_group["avg_recency_days"] = seg_group["avg_recency_days"].round(1)
    seg_group["avg_r_score"] = seg_group["avg_r_score"].round(2)
    seg_group["avg_f_score"] = seg_group["avg_f_score"].round(2)
    seg_group["avg_m_score"] = seg_group["avg_m_score"].round(2)

    # Sort deterministically by customer count descending
    seg_group = seg_group.sort_values(by="customer_count", ascending=False).reset_index(drop=True)

    return metrics, seg_group, dist_df


def plot_customer_visualizations(df: pd.DataFrame, output_dir: str) -> Dict[str, str]:
    """
    Generate customer domain visualization charts using matplotlib.
    """
    os.makedirs(output_dir, exist_ok=True)
    fig_paths = {}

    # Setup aesthetic standards
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "axes.grid": True,
        "grid.alpha": 0.35,
        "grid.linestyle": "--",
    })

    # 1. Customer Revenue Distribution
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    rev_data = df["gross_revenue"]
    bins = np.linspace(0, 8000, 41)
    ax.hist(rev_data, bins=bins, color="#3b82f6", edgecolor="#1d4ed8", alpha=0.75, rwidth=0.85)
    ax.axvline(rev_data.median(), color="#ef4444", linestyle="--", linewidth=1.5, label=f"Median (${rev_data.median():,.2f})")
    ax.axvline(rev_data.mean(), color="#10b981", linestyle="-", linewidth=1.5, label=f"Mean (${rev_data.mean():,.2f})")
    ax.set_title("Customer Gross Revenue Distribution (N=10,000)", pad=12, fontweight="bold")
    ax.set_xlabel("Customer Gross Lifetime Revenue (USD)")
    ax.set_ylabel("Number of Customers")
    ax.legend(frameon=True, facecolor="white", edgecolor="none")
    ax.set_xlim(0, 8000)
    fig.tight_layout()
    p1 = os.path.join(output_dir, "customer_revenue_distribution.png")
    fig.savefig(p1, bbox_inches="tight")
    plt.close(fig)
    fig_paths["customer_revenue_distribution"] = p1

    # 2. Customer Order Frequency Distribution
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    freq_counts = df["total_orders"].value_counts().sort_index()
    ax.bar(freq_counts.index, freq_counts.values, color="#6366f1", edgecolor="#4338ca", width=0.7)
    for x, y in zip(freq_counts.index, freq_counts.values):
        ax.text(x, y + 80, f"{y:,}", ha="center", va="bottom", fontsize=8, color="#1e293b")
    ax.set_title("Customer Order Frequency Distribution (Orders Placed)", pad=12, fontweight="bold")
    ax.set_xlabel("Total Orders per Customer")
    ax.set_ylabel("Customer Count")
    ax.set_xticks(freq_counts.index)
    ax.set_ylim(0, max(freq_counts.values) * 1.12)
    fig.tight_layout()
    p2 = os.path.join(output_dir, "customer_order_frequency_distribution.png")
    fig.savefig(p2, bbox_inches="tight")
    plt.close(fig)
    fig_paths["customer_order_frequency_distribution"] = p2

    # 3. RFM Segment Distribution
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    seg_counts = df["rfm_segment"].value_counts(ascending=True)
    y_pos = np.arange(len(seg_counts))
    colors = ["#94a3b8", "#f59e0b", "#06b6d4", "#ec4899", "#8b5cf6", "#3b82f6", "#10b981", "#6366f1"]
    bars = ax.barh(y_pos, seg_counts.values, color=colors[:len(seg_counts)], edgecolor="#334155", alpha=0.85, height=0.65)
    for bar, count in zip(bars, seg_counts.values):
        pct = (count / len(df)) * 100.0
        ax.text(count + 35, bar.get_y() + bar.get_height() / 2, f"{count:,} ({pct:.1f}%)",
                va="center", ha="left", fontsize=9, fontweight="bold", color="#1e293b")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(seg_counts.index)
    ax.set_title("RFM Customer Segment Distribution (Counts and Share)", pad=12, fontweight="bold")
    ax.set_xlabel("Number of Customers")
    ax.set_xlim(0, max(seg_counts.values) * 1.22)
    fig.tight_layout()
    p3 = os.path.join(output_dir, "rfm_segment_distribution.png")
    fig.savefig(p3, bbox_inches="tight")
    plt.close(fig)
    fig_paths["rfm_segment_distribution"] = p3

    return fig_paths


def export_customer_summary(
    metrics: Dict[str, Any],
    seg_df: pd.DataFrame,
    output_dir: str
) -> str:
    """
    Export unified customer summary CSV table.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "customer_summary.csv")

    # Save segment breakdown as primary table with meta header row
    seg_df.to_csv(out_path, index=False)
    return out_path
