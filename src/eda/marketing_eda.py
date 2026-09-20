"""
Aura Retail Analytics - Phase 4 Part 1
Marketing Exploratory Data Analysis Module.

Analyzes acquisition channels, media spend, impressions, click efficiency (CTR/CPC/CPM),
customer acquisition cost (CAC), attributed revenues, and ROAS.
"""

import os
from typing import Any, Dict, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def analyze_marketing_metrics(df: pd.DataFrame) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Compute factual marketing performance statistics and channel comparison matrix.

    Returns:
        Tuple containing:
        - Dict of aggregate marketing performance metrics.
        - DataFrame with formatted multi-metric channel comparison table.
    """
    total_spend = float(df["total_spend_usd"].sum())
    total_impressions = int(df["total_impressions"].sum())
    total_clicks = int(df["total_clicks"].sum())
    total_acquired = int(df["acquired_customers"].sum())
    total_gross_rev = float(df["gross_attributed_revenue"].sum())
    total_deliv_rev = float(df["delivered_attributed_revenue"].sum())

    blended_ctr = round((total_clicks / total_impressions) * 100.0, 3) if total_impressions > 0 else 0.0
    blended_cpc = round(total_spend / total_clicks, 2) if total_clicks > 0 else 0.0
    blended_cpm = round((total_spend / total_impressions) * 1000.0, 2) if total_impressions > 0 else 0.0
    blended_cac = round(total_spend / total_acquired, 2) if total_acquired > 0 else 0.0
    blended_roas = round(total_deliv_rev / total_spend, 2) if total_spend > 0 else 0.0

    # Aggregate metrics
    metrics = {
        "total_marketing_spend_usd": round(total_spend, 2),
        "total_ad_impressions": total_impressions,
        "total_ad_clicks": total_clicks,
        "total_acquired_customers": total_acquired,
        "blended_ctr_pct": blended_ctr,
        "blended_cpc_usd": blended_cpc,
        "blended_cpm_usd": blended_cpm,
        "blended_cac_usd": blended_cac,
        "blended_roas": blended_roas,
        "total_gross_attributed_revenue": round(total_gross_rev, 2),
        "total_delivered_attributed_revenue": round(total_deliv_rev, 2),
    }

    # Format channel comparison table (strictly factual, multi-dimensional, unranked)
    comparison_table = df[[
        "channel_name", "channel_type", "total_spend_usd", "total_impressions",
        "total_clicks", "ctr_pct", "cpc_usd", "cpm_usd", "acquired_customers",
        "cac_usd", "delivered_attributed_revenue", "roas", "revenue_per_acquired_customer"
    ]].copy()

    comparison_table = comparison_table.rename(columns={
        "channel_name": "Channel",
        "channel_type": "Type",
        "total_spend_usd": "Spend (USD)",
        "total_impressions": "Impressions",
        "total_clicks": "Clicks",
        "ctr_pct": "CTR (%)",
        "cpc_usd": "CPC (USD)",
        "cpm_usd": "CPM (USD)",
        "acquired_customers": "Acquired Customers",
        "cac_usd": "CAC (USD)",
        "delivered_attributed_revenue": "Delivered Attributed Rev (USD)",
        "roas": "ROAS (x)",
        "revenue_per_acquired_customer": "Rev / Customer (USD)",
    })

    return metrics, comparison_table


def plot_marketing_visualizations(df: pd.DataFrame, output_dir: str) -> Dict[str, str]:
    """
    Generate marketing domain visualization charts using matplotlib.
    """
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

    # 1. Channel Spend (USD)
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    sorted_spend = df.sort_values(by="total_spend_usd", ascending=False)
    spend_colors = ["#ec4899", "#3b82f6", "#10b981", "#94a3b8", "#cbd5e1", "#e2e8f0"]
    bars = ax.bar(sorted_spend["channel_name"], sorted_spend["total_spend_usd"] / 1e3, color=spend_colors[:len(df)], edgecolor="#334155")
    for bar, val in zip(bars, sorted_spend["total_spend_usd"] / 1e3):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 15, f"${val:.1f}k", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#1e293b")
    ax.set_title("Marketing Media Spend by Channel (Total: $2.22M)", pad=12, fontweight="bold")
    ax.set_xlabel("Acquisition Channel")
    ax.set_ylabel("Total Spend ($'000 USD)")
    ax.set_ylim(0, max(sorted_spend["total_spend_usd"] / 1e3) * 1.15)
    fig.tight_layout()
    p1 = os.path.join(output_dir, "marketing_channel_spend.png")
    fig.savefig(p1, bbox_inches="tight")
    plt.close(fig)
    fig_paths["marketing_channel_spend"] = p1

    # 2. Channel ROAS (Paid Channels)
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    paid_roas = df[df["roas"].notnull()].sort_values(by="roas", ascending=False)
    roas_bars = ax.bar(paid_roas["channel_name"], paid_roas["roas"], color=["#10b981", "#3b82f6", "#f59e0b"], width=0.55, edgecolor="#334155")
    for bar, val in zip(roas_bars, paid_roas["roas"]):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.1, f"{val:.2f}x", ha="center", va="bottom", fontsize=9, fontweight="bold", color="#1e293b")
    ax.set_title("Return on Ad Spend (ROAS) by Paid Channel", pad=12, fontweight="bold")
    ax.set_xlabel("Ad Channel")
    ax.set_ylabel("ROAS Ratio (Delivered Revenue / Media Spend)")
    ax.set_ylim(0, max(paid_roas["roas"]) * 1.2)
    fig.tight_layout()
    p2 = os.path.join(output_dir, "marketing_channel_roas.png")
    fig.savefig(p2, bbox_inches="tight")
    plt.close(fig)
    fig_paths["marketing_channel_roas"] = p2

    # 3. Channel CAC (Paid & Overall)
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    cac_df = df[df["cac_usd"] > 0].sort_values(by="cac_usd", ascending=False)
    cac_bars = ax.bar(cac_df["channel_name"], cac_df["cac_usd"], color=["#f87171", "#fb923c", "#38bdf8"], width=0.55, edgecolor="#334155")
    for bar, val in zip(cac_bars, cac_df["cac_usd"]):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 8, f"${val:.2f}", ha="center", va="bottom", fontsize=9, fontweight="bold", color="#1e293b")
    ax.axhline(222.42, color="#64748b", linestyle="--", linewidth=1.5, label="Blended CAC (All 10,000 Cust: $222.42)")
    ax.set_title("Customer Acquisition Cost (CAC) Across Paid Channels", pad=12, fontweight="bold")
    ax.set_xlabel("Ad Channel")
    ax.set_ylabel("CAC in USD (Spend / Acquired Customers)")
    ax.legend(frameon=True, facecolor="white", edgecolor="none")
    ax.set_ylim(0, max(cac_df["cac_usd"]) * 1.2)
    fig.tight_layout()
    p3 = os.path.join(output_dir, "marketing_channel_cac.png")
    fig.savefig(p3, bbox_inches="tight")
    plt.close(fig)
    fig_paths["marketing_channel_cac"] = p3

    # 4. Channel CTR (Paid Channels)
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    ctr_df = df[df["ctr_pct"].notnull()].sort_values(by="ctr_pct", ascending=False)
    ctr_bars = ax.bar(ctr_df["channel_name"], ctr_df["ctr_pct"], color=["#6366f1", "#06b6d4", "#ec4899"], width=0.55, edgecolor="#334155")
    for bar, val in zip(ctr_bars, ctr_df["ctr_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.1, f"{val:.3f}%", ha="center", va="bottom", fontsize=9, fontweight="bold", color="#1e293b")
    ax.set_title("Click-Through Rate (CTR %) Across Paid Channels", pad=12, fontweight="bold")
    ax.set_xlabel("Ad Channel")
    ax.set_ylabel("CTR Percentage (%)")
    ax.set_ylim(0, max(ctr_df["ctr_pct"]) * 1.25)
    fig.tight_layout()
    p4 = os.path.join(output_dir, "marketing_channel_ctr.png")
    fig.savefig(p4, bbox_inches="tight")
    plt.close(fig)
    fig_paths["marketing_channel_ctr"] = p4

    return fig_paths


def export_marketing_summary(comparison_table: pd.DataFrame, output_dir: str) -> str:
    """
    Export unified marketing summary CSV table.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "marketing_summary.csv")
    comparison_table.to_csv(out_path, index=False)
    return out_path
