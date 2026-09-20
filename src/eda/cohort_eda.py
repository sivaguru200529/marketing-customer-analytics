"""
Aura Retail Analytics - Phase 4 Part 1
Cohort Retention Exploratory Data Analysis Module.

Analyzes monthly customer signup cohorts (24 cohorts across 2024-2025),
tracking ongoing purchase retention percentages across 0 to 23 elapsed months.
"""

import os
from typing import Any, Dict, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def analyze_cohort_metrics(df: pd.DataFrame) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """
    Compute factual cohort retention statistics, milestone retention rates,
    average retention curve by month index, and full retention matrix.

    Returns:
        Tuple containing:
        - Dict of scalar cohort metrics.
        - DataFrame of milestone retention and mean retention by months elapsed.
        - DataFrame representing the pivot retention matrix.
    """
    unique_cohorts = df["cohort_month"].nunique()
    cohort_sizes = df[df["months_since_signup"] == 0][["cohort_month", "cohort_size"]].copy()

    min_cohort_size = int(cohort_sizes["cohort_size"].min())
    max_cohort_size = int(cohort_sizes["cohort_size"].max())
    mean_cohort_size = float(cohort_sizes["cohort_size"].mean())
    median_cohort_size = float(cohort_sizes["cohort_size"].median())

    # Milestone retention stats
    milestones = [0, 1, 3, 6, 12]
    milestone_stats = {}
    for m in milestones:
        sub = df[df["months_since_signup"] == m]["purchase_retention_rate_pct"]
        if len(sub) > 0:
            milestone_stats[f"m{m}_count"] = len(sub)
            milestone_stats[f"m{m}_mean_retention_pct"] = round(float(sub.mean()), 2)
            milestone_stats[f"m{m}_median_retention_pct"] = round(float(sub.median()), 2)
            milestone_stats[f"m{m}_min_retention_pct"] = round(float(sub.min()), 2)
            milestone_stats[f"m{m}_max_retention_pct"] = round(float(sub.max()), 2)

    # Average and median retention by month index (0 to 23)
    retention_by_index = df.groupby("months_since_signup", as_index=False).agg(
        evaluable_cohorts=("cohort_month", "count"),
        mean_retention_pct=("purchase_retention_rate_pct", "mean"),
        median_retention_pct=("purchase_retention_rate_pct", "median"),
        min_retention_pct=("purchase_retention_rate_pct", "min"),
        max_retention_pct=("purchase_retention_rate_pct", "max"),
    )
    retention_by_index["mean_retention_pct"] = retention_by_index["mean_retention_pct"].round(2)
    retention_by_index["median_retention_pct"] = retention_by_index["median_retention_pct"].round(2)

    # Full Pivot Matrix: cohort_month (rows) x months_since_signup (cols)
    pivot_matrix = df.pivot(
        index="cohort_month",
        columns="months_since_signup",
        values="purchase_retention_rate_pct"
    )

    metrics = {
        "total_cohorts": unique_cohorts,
        "min_cohort_size": min_cohort_size,
        "max_cohort_size": max_cohort_size,
        "mean_cohort_size": round(mean_cohort_size, 1),
        "median_cohort_size": round(median_cohort_size, 1),
        "m0_mean_retention_pct": milestone_stats.get("m0_mean_retention_pct", 0.0),
        "m1_mean_retention_pct": milestone_stats.get("m1_mean_retention_pct", 0.0),
        "m3_mean_retention_pct": milestone_stats.get("m3_mean_retention_pct", 0.0),
        "m6_mean_retention_pct": milestone_stats.get("m6_mean_retention_pct", 0.0),
        "m12_mean_retention_pct": milestone_stats.get("m12_mean_retention_pct", 0.0),
    }

    return metrics, retention_by_index, pivot_matrix


def plot_cohort_visualizations(pivot_matrix: pd.DataFrame, output_dir: str) -> Dict[str, str]:
    """
    Generate cohort retention heatmap visualization chart using matplotlib.
    """
    os.makedirs(output_dir, exist_ok=True)
    fig_paths = {}

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 8,
        "axes.titlesize": 11,
        "axes.labelsize": 9,
    })

    # Cohort Retention Heatmap
    fig, ax = plt.subplots(figsize=(14, 8), dpi=150)

    # Convert pivot to numpy array, mask NaNs
    data = pivot_matrix.values
    masked_data = np.ma.masked_invalid(data)

    cmap = plt.cm.YlGnBu
    cmap.set_bad(color="#f1f5f9")

    cax = ax.imshow(masked_data, cmap=cmap, aspect="auto", vmin=0, vmax=75)

    # Labels
    cohort_labels = [pd.to_datetime(c).strftime("%b %Y") for c in pivot_matrix.index]
    ax.set_yticks(np.arange(len(pivot_matrix.index)))
    ax.set_yticklabels(cohort_labels, fontsize=8)

    ax.set_xticks(np.arange(pivot_matrix.shape[1]))
    ax.set_xticklabels([f"M+{i}" for i in range(pivot_matrix.shape[1])], fontsize=8)

    # Add numeric labels inside cells
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            if not np.isnan(val):
                text_color = "white" if val > 35 else "#0f172a"
                ax.text(j, i, f"{val:.1f}%", ha="center", va="center", color=text_color, fontsize=6.5)

    ax.set_title("Customer Signup Cohort Purchase Retention Matrix (2024 - 2025)", pad=14, fontweight="bold")
    ax.set_xlabel("Elapsed Months Since Customer Signup", labelpad=8)
    ax.set_ylabel("Customer Signup Cohort Month", labelpad=8)

    cbar = fig.colorbar(cax, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Purchase Retention Rate (%)", rotation=270, labelpad=12, fontsize=8)

    fig.tight_layout()
    p1 = os.path.join(output_dir, "cohort_retention_heatmap.png")
    fig.savefig(p1, bbox_inches="tight")
    plt.close(fig)
    fig_paths["cohort_retention_heatmap"] = p1

    return fig_paths


def export_cohort_summary(retention_by_index: pd.DataFrame, pivot_matrix: pd.DataFrame, output_dir: str) -> str:
    """
    Export unified cohort summary CSV table.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "cohort_summary.csv")
    retention_by_index.to_csv(out_path, index=False)
    return out_path
