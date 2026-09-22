"""
Aura Retail Analytics - Phase 5 Part 2
Publication-Grade Visualizations for Business Prioritization & Customer Intelligence.
"""

import os
from typing import Dict, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.prioritization.config import (
    CHURN_RISK_HIGH_THRESHOLD,
    DEFAULT_FIGURES_DIR,
    PRIORITY_TIER_HIGH_THRESHOLD,
    PRIORITY_TIER_MEDIUM_THRESHOLD,
)


def set_plotting_theme():
    """Configure publication-grade styling for Matplotlib charts."""
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "axes.grid": True,
            "grid.alpha": 0.35,
            "grid.linestyle": "--",
            "figure.autolayout": True,
        }
    )


def generate_all_visualizations(
    df: pd.DataFrame,
    output_dir: Optional[str] = None,
) -> Dict[str, str]:
    """
    Render and save all 7 publication-grade figures under data/05_churn/figures/.

    Returns:
        Dict mapping figure identifier to absolute file path.
    """
    if output_dir is None:
        output_dir = DEFAULT_FIGURES_DIR

    os.makedirs(output_dir, exist_ok=True)
    set_plotting_theme()
    paths = {}

    # 1. Priority Tier Distribution
    fig, ax1 = plt.subplots(figsize=(8, 5), dpi=150)
    tier_counts = df["priority_tier"].value_counts().reindex(["High Priority", "Medium Priority", "Low Priority"]).fillna(0)
    tier_rev = df.groupby("priority_tier")["delivered_revenue"].sum().reindex(["High Priority", "Medium Priority", "Low Priority"]).fillna(0)
    
    x = np.arange(len(tier_counts))
    width = 0.45
    bars = ax1.bar(x, tier_counts.values, width, color=["#ef4444", "#f59e0b", "#10b981"], edgecolor="#1f2937", linewidth=0.8)
    ax1.set_title("Customer Prioritization Tier Distribution (N=10,000)", pad=14)
    ax1.set_ylabel("Customer Count")
    ax1.set_xticks(x)
    ax1.set_xticklabels(tier_counts.index, fontweight="bold")
    ax1.set_ylim(0, max(tier_counts.values.max() * 1.15, 100))

    for bar, count, rev in zip(bars, tier_counts.values, tier_rev.values):
        pct = (count / len(df)) * 100.0
        ax1.annotate(
            f"{count:,} ({pct:.1f}%)\n${rev:,.0f}",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height() / 2 if bar.get_height() > 500 else bar.get_height() + 150),
            ha="center",
            va="center",
            color="white" if bar.get_height() > 500 else "black",
            fontweight="bold",
            fontsize=10,
        )

    p1 = os.path.join(output_dir, "priority_tier_distribution.png")
    fig.savefig(p1, bbox_inches="tight")
    plt.close(fig)
    paths["priority_tier_distribution"] = p1

    # 2. Business Segment Distribution
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    seg_counts = df["business_segment"].value_counts().sort_values(ascending=True)
    y_pos = np.arange(len(seg_counts))
    bars = ax.barh(y_pos, seg_counts.values, color="#3b82f6", edgecolor="#1e40af", height=0.65)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(seg_counts.index, fontsize=9.5)
    ax.set_title("Mutually Exclusive Business Segment Distribution", pad=12)
    ax.set_xlabel("Customer Count")
    ax.set_xlim(0, seg_counts.values.max() * 1.18)

    for idx, count in enumerate(seg_counts.values):
        pct = (count / len(df)) * 100.0
        ax.text(count + 40, idx, f"{count:,} ({pct:.1f}%)", va="center", fontsize=9, fontweight="bold")

    p2 = os.path.join(output_dir, "business_segment_distribution.png")
    fig.savefig(p2, bbox_inches="tight")
    plt.close(fig)
    paths["business_segment_distribution"] = p2

    # 3. Risk vs Value Relationship (Heatmap Matrix)
    risk_order = ["High Risk", "Medium Risk", "Low Risk"]
    val_order = ["High Value", "Mid Value", "Low Value", "Zero Value"]
    matrix_counts = pd.crosstab(df["churn_risk_band"], df["customer_value_band"]).reindex(index=risk_order, columns=val_order, fill_value=0)
    matrix_rev = df.pivot_table(index="churn_risk_band", columns="customer_value_band", values="delivered_revenue", aggfunc="sum").reindex(index=risk_order, columns=val_order, fill_value=0)

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
    cax = ax.matshow(matrix_counts.values, cmap="YlOrRd", alpha=0.85)
    ax.set_xticks(range(len(val_order)))
    ax.set_yticks(range(len(risk_order)))
    ax.set_xticklabels(val_order, fontweight="bold")
    ax.set_yticklabels(risk_order, fontweight="bold")
    ax.set_title("Risk vs Value Matrix (Customer Counts & Delivered Revenue)", pad=20)
    fig.colorbar(cax, label="Customer Count")

    for i in range(len(risk_order)):
        for j in range(len(val_order)):
            cnt = matrix_counts.values[i, j]
            rv = matrix_rev.values[i, j]
            text_color = "white" if cnt > matrix_counts.values.max() / 2 else "black"
            ax.text(
                j,
                i,
                f"{cnt:,} accts\n${rv:,.0f}",
                ha="center",
                va="center",
                color=text_color,
                fontweight="bold",
                fontsize=9.5,
            )

    p3 = os.path.join(output_dir, "risk_value_matrix.png")
    fig.savefig(p3, bbox_inches="tight")
    plt.close(fig)
    paths["risk_value_matrix"] = p3

    # 4. Priority Score Distribution
    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=150)
    scores = df["priority_score"]
    n, bins, patches = ax.hist(scores, bins=35, edgecolor="#1f2937", linewidth=0.5, alpha=0.85)

    for b_left, patch in zip(bins[:-1], patches):
        if b_left < PRIORITY_TIER_MEDIUM_THRESHOLD:
            patch.set_facecolor("#10b981")  # Low
        elif b_left < PRIORITY_TIER_HIGH_THRESHOLD:
            patch.set_facecolor("#f59e0b")  # Medium
        else:
            patch.set_facecolor("#ef4444")  # High

    ax.axvline(
        PRIORITY_TIER_MEDIUM_THRESHOLD,
        color="#047857",
        linestyle="--",
        linewidth=1.8,
        label=f"Medium Priority Threshold ({PRIORITY_TIER_MEDIUM_THRESHOLD})",
    )
    ax.axvline(
        PRIORITY_TIER_HIGH_THRESHOLD,
        color="#b91c1c",
        linestyle="--",
        linewidth=1.8,
        label=f"High Priority Threshold ({PRIORITY_TIER_HIGH_THRESHOLD})",
    )
    ax.set_title("Composite Business Priority Score Distribution (N=10,000)", pad=12)
    ax.set_xlabel("Composite Priority Score (Unscaled Weighted Score in [0, 1])")
    ax.set_ylabel("Customer Count")
    ax.legend(loc="upper right", framealpha=0.9)
    p4 = os.path.join(output_dir, "priority_score_distribution.png")
    fig.savefig(p4, bbox_inches="tight")
    plt.close(fig)
    paths["priority_score_distribution"] = p4

    # 5. Revenue Associated With High-Risk Customers
    high_risk_df = df[df["churn_risk_band"] == "High Risk"]
    hr_rev_by_val = high_risk_df.groupby("customer_value_band")["delivered_revenue"].sum().reindex(["High Value", "Mid Value", "Low Value", "Zero Value"]).fillna(0)

    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=150)
    bars = ax.bar(
        hr_rev_by_val.index,
        hr_rev_by_val.values,
        color=["#dc2626", "#ea580c", "#d97706", "#64748b"],
        edgecolor="#1f2937",
        linewidth=0.8,
        width=0.55,
    )
    total_hr_rev = hr_rev_by_val.sum()
    ax.set_title(
        f"Historical Delivered Revenue Associated With High-Risk Customers\n(Total: ${total_hr_rev:,.2f} across {len(high_risk_df):,} customers)",
        pad=12,
    )
    ax.set_ylabel("Historical Delivered Revenue ($)")
    ax.set_ylim(0, hr_rev_by_val.max() * 1.18)

    for bar, val in zip(bars, hr_rev_by_val.values):
        pct = (val / total_hr_rev) * 100.0 if total_hr_rev > 0 else 0.0
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 15000,
            f"${val:,.0f}\n({pct:.1f}%)",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=9.5,
        )

    p5 = os.path.join(output_dir, "revenue_associated_with_high_risk.png")
    fig.savefig(p5, bbox_inches="tight")
    plt.close(fig)
    paths["revenue_associated_with_high_risk"] = p5

    # 6. Recommended Action Distribution
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
    action_counts = df["recommended_action"].value_counts().sort_values(ascending=True)
    y_pos = np.arange(len(action_counts))
    bars = ax.barh(y_pos, action_counts.values, color="#8b5cf6", edgecolor="#6d28d9", height=0.65)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(action_counts.index, fontsize=9.5)
    ax.set_title("Deterministic Recommended Action Category Distribution", pad=12)
    ax.set_xlabel("Customer Count")
    ax.set_xlim(0, action_counts.values.max() * 1.18)

    for idx, count in enumerate(action_counts.values):
        pct = (count / len(df)) * 100.0
        ax.text(count + 30, idx, f"{count:,} ({pct:.1f}%)", va="center", fontsize=9, fontweight="bold")

    p6 = os.path.join(output_dir, "recommended_action_distribution.png")
    fig.savefig(p6, bbox_inches="tight")
    plt.close(fig)
    paths["recommended_action_distribution"] = p6

    # 7. Friction vs Churn Risk Relationship
    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=150)
    fric_band_order = ["No Friction", "Low Friction", "High Friction"]
    mean_prob_by_fric = df.groupby("friction_band")["churn_probability"].mean().reindex(fric_band_order)
    mean_score_by_fric = df.groupby("friction_band")["friction_score"].mean().reindex(fric_band_order)

    x = np.arange(len(fric_band_order))
    width = 0.35
    b1 = ax.bar(x - width / 2, mean_prob_by_fric.values, width, label="Mean Churn Probability", color="#ef4444", edgecolor="#991b1b")
    b2 = ax.bar(x + width / 2, mean_score_by_fric.values, width, label="Mean Friction Score", color="#f59e0b", edgecolor="#b45309")

    ax.set_xticks(x)
    ax.set_xticklabels(fric_band_order, fontweight="bold")
    ax.set_title("Customer Friction vs Churn Risk Relationship", pad=12)
    ax.set_ylabel("Metric Score [0.0 - 1.0]")
    ax.set_ylim(0, 1.0)
    ax.legend(loc="upper left", framealpha=0.9)

    for bar in b1:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02, f"{bar.get_height():.3f}", ha="center", fontsize=9, fontweight="bold")
    for bar in b2:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02, f"{bar.get_height():.3f}", ha="center", fontsize=9, fontweight="bold")

    p7 = os.path.join(output_dir, "friction_vs_churn_risk.png")
    fig.savefig(p7, bbox_inches="tight")
    plt.close(fig)
    paths["friction_vs_churn_risk"] = p7

    return paths
