"""
Aura Retail Analytics - Phase 4 Part 2
Customer Segmentation and RFM Visualization Module.

Generates 12 publication-grade Matplotlib charts under data/04_rfm/figures/.
"""

import os
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.rfm.config import DEFAULT_FIGURES_DIR


def generate_all_visualizations(
    df: pd.DataFrame,
    eval_df: pd.DataFrame,
    selected_k: int,
    output_dir: Optional[str] = None,
) -> Dict[str, str]:
    """
    Generate the 12 required visualization charts.

    Returns:
        Dict mapping figure name to absolute file path.
    """
    if output_dir is None:
        output_dir = DEFAULT_FIGURES_DIR

    os.makedirs(output_dir, exist_ok=True)
    fig_paths = {}

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "axes.grid": True,
        "grid.alpha": 0.35,
        "grid.linestyle": "--",
    })

    # 1. RFM Score Distribution
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    score_levels = [1, 2, 3, 4, 5]
    r_counts = df["rfm_recency_score"].value_counts().reindex(score_levels, fill_value=0)
    f_counts = df["rfm_frequency_score"].value_counts().reindex(score_levels, fill_value=0)
    m_counts = df["rfm_monetary_score"].value_counts().reindex(score_levels, fill_value=0)

    x = np.arange(len(score_levels))
    width = 0.25
    ax.bar(x - width, r_counts, width, label="Recency (R)", color="#3b82f6", edgecolor="#1d4ed8")
    ax.bar(x, f_counts, width, label="Frequency (F)", color="#10b981", edgecolor="#047857")
    ax.bar(x + width, m_counts, width, label="Monetary (M)", color="#f59e0b", edgecolor="#b45309")

    ax.set_title("RFM Score Component Distributions (Quintiles 1 to 5)", pad=12, fontweight="bold")
    ax.set_xlabel("Assigned Score Quintile (1 = Lowest, 5 = Highest)")
    ax.set_ylabel("Customer Count")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Score {s}" for s in score_levels])
    ax.legend(frameon=True, facecolor="white")
    ax.set_ylim(0, 2500)
    fig.tight_layout()
    p1 = os.path.join(output_dir, "rfm_score_distribution.png")
    fig.savefig(p1, bbox_inches="tight")
    plt.close(fig)
    fig_paths["rfm_score_distribution"] = p1

    # 2. Recency Distribution
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    ax.hist(df["recency"], bins=30, color="#6366f1", edgecolor="#4338ca", alpha=0.75, rwidth=0.85)
    ax.axvline(df["recency"].median(), color="#ef4444", linestyle="--", linewidth=1.5, label=f"Median ({df['recency'].median():.1f} days)")
    ax.axvline(df["recency"].mean(), color="#10b981", linestyle="-", linewidth=1.5, label=f"Mean ({df['recency'].mean():.1f} days)")
    ax.set_title("Customer Recency Distribution (Days Since Last Order)", pad=12, fontweight="bold")
    ax.set_xlabel("Recency (Days relative to 2025-12-31)")
    ax.set_ylabel("Customer Count")
    ax.legend(frameon=True, facecolor="white")
    fig.tight_layout()
    p2 = os.path.join(output_dir, "recency_distribution.png")
    fig.savefig(p2, bbox_inches="tight")
    plt.close(fig)
    fig_paths["recency_distribution"] = p2

    # 3. Frequency Distribution
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    f_val = df["frequency"].clip(upper=25)
    f_counts = f_val.value_counts().sort_index()
    ax.bar(f_counts.index, f_counts.values, color="#06b6d4", edgecolor="#0891b2", width=0.7)
    ax.set_title("Customer Frequency Distribution (Delivered Orders, Top-Clipped at 25)", pad=12, fontweight="bold")
    ax.set_xlabel("Delivered Orders per Customer")
    ax.set_ylabel("Customer Count")
    ax.axvline(df["frequency"].median(), color="#ef4444", linestyle="--", linewidth=1.5, label=f"Median ({df['frequency'].median():.0f} order)")
    ax.axvline(df["frequency"].mean(), color="#1e293b", linestyle="-", linewidth=1.5, label=f"Mean ({df['frequency'].mean():.1f} orders)")
    ax.legend(frameon=True, facecolor="white")
    fig.tight_layout()
    p3 = os.path.join(output_dir, "frequency_distribution.png")
    fig.savefig(p3, bbox_inches="tight")
    plt.close(fig)
    fig_paths["frequency_distribution"] = p3

    # 4. Monetary Distribution
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    mon_clipped = df["monetary"].clip(upper=6000)
    ax.hist(mon_clipped, bins=35, color="#f59e0b", edgecolor="#d97706", alpha=0.8, rwidth=0.85)
    ax.axvline(df["monetary"].median(), color="#ef4444", linestyle="--", linewidth=1.5, label=f"Median (${df['monetary'].median():,.2f})")
    ax.axvline(df["monetary"].mean(), color="#3b82f6", linestyle="-", linewidth=1.5, label=f"Mean (${df['monetary'].mean():,.2f})")
    ax.set_title("Customer Monetary Distribution (Delivered Revenue, Clipped at $6,000)", pad=12, fontweight="bold")
    ax.set_xlabel("Delivered Net Revenue ($ USD)")
    ax.set_ylabel("Customer Count")
    ax.legend(frameon=True, facecolor="white")
    fig.tight_layout()
    p4 = os.path.join(output_dir, "monetary_distribution.png")
    fig.savefig(p4, bbox_inches="tight")
    plt.close(fig)
    fig_paths["monetary_distribution"] = p4

    # 5. RFM Segment Distribution
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    seg_counts = df["rfm_segment"].value_counts(ascending=True)
    colors = ["#94a3b8", "#fbbf24", "#38bdf8", "#f472b6", "#a78bfa", "#60a5fa", "#34d399", "#818cf8"]
    bars = ax.barh(seg_counts.index, seg_counts.values, color=colors[:len(seg_counts)], height=0.65, edgecolor="#334155")
    for bar, count in zip(bars, seg_counts.values):
        pct = (count / len(df)) * 100.0
        ax.text(count + 35, bar.get_y() + bar.get_height() / 2, f"{count:,} ({pct:.1f}%)",
                va="center", ha="left", fontsize=9, fontweight="bold", color="#1e293b")
    ax.set_title("Rule-Based RFM Customer Segment Breakdown (N=10,000)", pad=12, fontweight="bold")
    ax.set_xlabel("Customer Count")
    ax.set_xlim(0, max(seg_counts.values) * 1.25)
    fig.tight_layout()
    p5 = os.path.join(output_dir, "rfm_segment_distribution.png")
    fig.savefig(p5, bbox_inches="tight")
    plt.close(fig)
    fig_paths["rfm_segment_distribution"] = p5

    # 6. Cluster Size Distribution
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    clus_counts = df["cluster_label"].value_counts().sort_index()
    clus_colors = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#64748b"]
    bars = ax.bar(clus_counts.index, clus_counts.values, color=clus_colors[:len(clus_counts)], edgecolor="#334155", width=0.55)
    for bar, val in zip(bars, clus_counts.values):
        pct = (val / len(df)) * 100.0
        ax.text(bar.get_x() + bar.get_width() / 2, val + 50, f"{val:,}\n({pct:.1f}%)",
                ha="center", va="bottom", fontsize=9, fontweight="bold", color="#1e293b")
    ax.set_title(f"Unsupervised K-Means Customer Cluster Sizes (K={selected_k})", pad=12, fontweight="bold")
    ax.set_xlabel("Assigned Cluster")
    ax.set_ylabel("Customer Count")
    ax.set_ylim(0, max(clus_counts.values) * 1.22)
    fig.tight_layout()
    p6 = os.path.join(output_dir, "cluster_size_distribution.png")
    fig.savefig(p6, bbox_inches="tight")
    plt.close(fig)
    fig_paths["cluster_size_distribution"] = p6

    # 7. Elbow Curve
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    ax.plot(eval_df["k"], eval_df["inertia"], marker="o", color="#3b82f6", linewidth=2.0)
    sel_inertia = eval_df[eval_df["k"] == selected_k]["inertia"].values[0]
    ax.scatter([selected_k], [sel_inertia], color="#ef4444", s=120, zorder=5, label=f"Selected K={selected_k}")
    ax.set_title("K-Means Inertia / Elbow Curve Evaluation", pad=12, fontweight="bold")
    ax.set_xlabel("Number of Clusters (K)")
    ax.set_ylabel("Within-Cluster Sum of Squares (Inertia)")
    ax.set_xticks(eval_df["k"])
    ax.legend(frameon=True, facecolor="white")
    fig.tight_layout()
    p7 = os.path.join(output_dir, "elbow_curve.png")
    fig.savefig(p7, bbox_inches="tight")
    plt.close(fig)
    fig_paths["elbow_curve"] = p7

    # 8. Silhouette Scores by K
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    ax.plot(eval_df["k"], eval_df["silhouette_score"], marker="s", color="#10b981", linewidth=2.0)
    sel_sil = eval_df[eval_df["k"] == selected_k]["silhouette_score"].values[0]
    ax.scatter([selected_k], [sel_sil], color="#ef4444", s=120, zorder=5, label=f"Selected K={selected_k} (Sil: {sel_sil:.4f})")
    for _, row in eval_df.iterrows():
        ax.text(row["k"], row["silhouette_score"] + 0.008, f"{row['silhouette_score']:.4f}", ha="center", fontsize=8)
    ax.set_title("K-Means Silhouette Score by Cluster Count K", pad=12, fontweight="bold")
    ax.set_xlabel("Number of Clusters (K)")
    ax.set_ylabel("Mean Silhouette Coefficient")
    ax.set_xticks(eval_df["k"])
    ax.set_ylim(min(eval_df["silhouette_score"]) * 0.9, max(eval_df["silhouette_score"]) * 1.08)
    ax.legend(frameon=True, facecolor="white")
    fig.tight_layout()
    p8 = os.path.join(output_dir, "silhouette_scores.png")
    fig.savefig(p8, bbox_inches="tight")
    plt.close(fig)
    fig_paths["silhouette_scores"] = p8

    # 9. Recency vs Frequency by Cluster
    fig, ax = plt.subplots(figsize=(9, 6), dpi=150)
    for i, clus in enumerate(sorted(df["cluster_label"].unique())):
        sub = df[df["cluster_label"] == clus]
        ax.scatter(sub["recency"], sub["frequency"], label=clus, color=clus_colors[i % len(clus_colors)], alpha=0.35, s=16)
    ax.set_title(f"Recency vs Frequency by Cluster (K={selected_k})", pad=12, fontweight="bold")
    ax.set_xlabel("Recency (Days)")
    ax.set_ylabel("Delivered Orders (Frequency)")
    ax.legend(frameon=True, facecolor="white")
    fig.tight_layout()
    p9 = os.path.join(output_dir, "recency_vs_frequency.png")
    fig.savefig(p9, bbox_inches="tight")
    plt.close(fig)
    fig_paths["recency_vs_frequency"] = p9

    # 10. Frequency vs Monetary by Cluster
    fig, ax = plt.subplots(figsize=(9, 6), dpi=150)
    for i, clus in enumerate(sorted(df["cluster_label"].unique())):
        sub = df[df["cluster_label"] == clus]
        ax.scatter(sub["frequency"], sub["monetary"] + 1, label=clus, color=clus_colors[i % len(clus_colors)], alpha=0.35, s=16)
    ax.set_yscale("log")
    ax.set_title(f"Frequency vs Monetary (Log Scale) by Cluster (K={selected_k})", pad=12, fontweight="bold")
    ax.set_xlabel("Delivered Orders (Frequency)")
    ax.set_ylabel("Delivered Revenue ($ USD, Log Scale)")
    ax.legend(frameon=True, facecolor="white")
    fig.tight_layout()
    p10 = os.path.join(output_dir, "frequency_vs_monetary.png")
    fig.savefig(p10, bbox_inches="tight")
    plt.close(fig)
    fig_paths["frequency_vs_monetary"] = p10

    # 11. Recency vs Monetary by Cluster
    fig, ax = plt.subplots(figsize=(9, 6), dpi=150)
    for i, clus in enumerate(sorted(df["cluster_label"].unique())):
        sub = df[df["cluster_label"] == clus]
        ax.scatter(sub["recency"], sub["monetary"] + 1, label=clus, color=clus_colors[i % len(clus_colors)], alpha=0.35, s=16)
    ax.set_yscale("log")
    ax.set_title(f"Recency vs Monetary (Log Scale) by Cluster (K={selected_k})", pad=12, fontweight="bold")
    ax.set_xlabel("Recency (Days)")
    ax.set_ylabel("Delivered Revenue ($ USD, Log Scale)")
    ax.legend(frameon=True, facecolor="white")
    fig.tight_layout()
    p11 = os.path.join(output_dir, "recency_vs_monetary.png")
    fig.savefig(p11, bbox_inches="tight")
    plt.close(fig)
    fig_paths["recency_vs_monetary"] = p11

    # 12. Cluster Profile Comparison (Normalized Means Bar Chart)
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    metrics_to_plot = ["recency", "frequency", "monetary"]
    labels = ["Recency (Days)", "Frequency (Orders)", "Monetary ($)"]
    clusters = sorted(df["cluster_label"].unique())
    x = np.arange(len(metrics_to_plot))
    w = 0.8 / len(clusters)

    for i, clus in enumerate(clusters):
        sub = df[df["cluster_label"] == clus]
        # Normalize relative to overall dataset max to allow on same axis
        norm_vals = [
            sub["recency"].mean() / df["recency"].max(),
            sub["frequency"].mean() / df["frequency"].max(),
            sub["monetary"].mean() / df["monetary"].max(),
        ]
        ax.bar(x + i * w - (len(clusters) * w) / 2 + w / 2, norm_vals, w, label=clus, color=clus_colors[i % len(clus_colors)], edgecolor="#334155")

    ax.set_title(f"Cluster Comparative Behavioral Profile (Normalized Means)", pad=12, fontweight="bold")
    ax.set_xlabel("Behavioral Metric")
    ax.set_ylabel("Normalized Mean Index (0.0 to 1.0)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(frameon=True, facecolor="white")
    fig.tight_layout()
    p12 = os.path.join(output_dir, "cluster_profile_comparison.png")
    fig.savefig(p12, bbox_inches="tight")
    plt.close(fig)
    fig_paths["cluster_profile_comparison"] = p12

    return fig_paths
