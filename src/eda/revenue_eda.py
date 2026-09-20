"""
Aura Retail Analytics - Phase 4 Part 1
Revenue Exploratory Data Analysis Module.

Analyzes 24-month time-series trajectory, gross vs delivered revenue,
fulfillment attrition (returns/cancellations), MoM velocity, volatility, and cumulative totals.
"""

import os
from typing import Any, Dict, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def analyze_revenue_metrics(df: pd.DataFrame) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Compute factual 24-month revenue and order trend statistics.

    Returns:
        Tuple containing:
        - Dict of scalar revenue performance metrics.
        - DataFrame containing monthly summary breakdown.
    """
    total_months = len(df)
    min_month = str(df["order_month"].min())
    max_month = str(df["order_month"].max())

    total_gross = float(df["gross_billed_revenue"].sum())
    total_delivered = float(df["delivered_revenue"].sum())
    total_returned = float(df["returned_revenue"].sum())
    total_cancelled = float(df["cancelled_revenue"].sum())
    total_discounts = float(df["total_discounts_granted"].sum())
    total_shipping = float(df["total_shipping_revenue"].sum())

    total_orders_placed = int(df["total_orders_placed"].sum())
    total_delivered_orders = int(df["delivered_orders"].sum())

    mean_monthly_delivered = float(df["delivered_revenue"].mean())
    median_monthly_delivered = float(df["delivered_revenue"].median())
    std_monthly_delivered = float(df["delivered_revenue"].std())
    cv_monthly_delivered = round(std_monthly_delivered / mean_monthly_delivered, 3) if mean_monthly_delivered > 0 else 0.0

    mean_monthly_gross = float(df["gross_billed_revenue"].mean())
    median_monthly_gross = float(df["gross_billed_revenue"].median())

    # MoM stats (excluding first month where MoM is NaN)
    valid_mom = df["mom_revenue_growth_pct"].dropna()
    mean_mom_growth = float(valid_mom.mean())
    median_mom_growth = float(valid_mom.median())
    std_mom_growth = float(valid_mom.std())
    min_mom_growth = float(valid_mom.min())
    max_mom_growth = float(valid_mom.max())

    # Peak and trough months
    idx_max_rev = df["delivered_revenue"].idxmax()
    max_rev_month = df.loc[idx_max_rev, "order_month"]
    max_rev_val = float(df.loc[idx_max_rev, "delivered_revenue"])

    idx_min_rev = df["delivered_revenue"].idxmin()
    min_rev_month = df.loc[idx_min_rev, "order_month"]
    min_rev_val = float(df.loc[idx_min_rev, "delivered_revenue"])

    idx_max_mom = valid_mom.idxmax()
    max_mom_month = df.loc[idx_max_mom, "order_month"]
    max_mom_val = float(df.loc[idx_max_mom, "mom_revenue_growth_pct"])

    idx_min_mom = valid_mom.idxmin()
    min_mom_month = df.loc[idx_min_mom, "order_month"]
    min_mom_val = float(df.loc[idx_min_mom, "mom_revenue_growth_pct"])

    cumulative_revenue_final = float(df["cumulative_delivered_revenue"].iloc[-1])

    metrics = {
        "total_months": total_months,
        "min_month": min_month,
        "max_month": max_month,
        "total_gross_billed_revenue": round(total_gross, 2),
        "total_delivered_revenue": round(total_delivered, 2),
        "total_returned_revenue": round(total_returned, 2),
        "total_cancelled_revenue": round(total_cancelled, 2),
        "total_discounts_granted": round(total_discounts, 2),
        "total_shipping_revenue": round(total_shipping, 2),
        "total_orders_placed": total_orders_placed,
        "total_delivered_orders": total_delivered_orders,
        "mean_monthly_delivered_revenue": round(mean_monthly_delivered, 2),
        "median_monthly_delivered_revenue": round(median_monthly_delivered, 2),
        "std_monthly_delivered_revenue": round(std_monthly_delivered, 2),
        "coefficient_of_variation_revenue": cv_monthly_delivered,
        "mean_monthly_gross_revenue": round(mean_monthly_gross, 2),
        "median_monthly_gross_revenue": round(median_monthly_gross, 2),
        "mean_mom_revenue_growth_pct": round(mean_mom_growth, 2),
        "median_mom_revenue_growth_pct": round(median_mom_growth, 2),
        "std_mom_revenue_growth_pct": round(std_mom_growth, 2),
        "min_mom_revenue_growth_pct": round(min_mom_growth, 2),
        "max_mom_revenue_growth_pct": round(max_mom_growth, 2),
        "highest_revenue_month": max_rev_month,
        "highest_monthly_revenue": round(max_rev_val, 2),
        "lowest_revenue_month": min_rev_month,
        "lowest_monthly_revenue": round(min_rev_val, 2),
        "highest_mom_growth_month": max_mom_month,
        "highest_mom_growth_pct": round(max_mom_val, 2),
        "lowest_mom_growth_month": min_mom_month,
        "lowest_mom_growth_pct": round(min_mom_val, 2),
        "cumulative_delivered_revenue": round(cumulative_revenue_final, 2),
    }

    return metrics, df.copy()


def plot_revenue_visualizations(df: pd.DataFrame, output_dir: str) -> Dict[str, str]:
    """
    Generate revenue domain visualization charts using matplotlib.
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

    months = pd.to_datetime(df["order_month"]).dt.strftime("%b %y")

    # 1. Monthly Revenue Trend (Delivered vs Gross Billed)
    fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
    x = np.arange(len(df))
    ax.plot(x, df["gross_billed_revenue"] / 1e3, marker="o", color="#94a3b8", linewidth=1.5, label="Gross Billed Revenue", alpha=0.7)
    ax.plot(x, df["delivered_revenue"] / 1e3, marker="s", color="#3b82f6", linewidth=2.5, label="Delivered Net Revenue")
    ax.fill_between(x, df["delivered_revenue"] / 1e3, color="#3b82f6", alpha=0.15)
    ax.set_title("24-Month Monthly Revenue Trajectory (2024 - 2025)", pad=12, fontweight="bold")
    ax.set_xlabel("Order Month")
    ax.set_ylabel("Monthly Revenue ($'000 USD)")
    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45, ha="right", fontsize=8)
    ax.legend(frameon=True, facecolor="white", edgecolor="none")
    fig.tight_layout()
    p1 = os.path.join(output_dir, "monthly_revenue_trend.png")
    fig.savefig(p1, bbox_inches="tight")
    plt.close(fig)
    fig_paths["monthly_revenue_trend"] = p1

    # 2. Month-over-Month Revenue Growth %
    fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
    mom_vals = df["mom_revenue_growth_pct"].fillna(0.0)
    bar_colors = ["#10b981" if v >= 0 else "#ef4444" for v in mom_vals]
    ax.bar(x, mom_vals, color=bar_colors, width=0.6, edgecolor="#334155")
    ax.axhline(0, color="#1e293b", linewidth=1.0)
    ax.set_title("Month-over-Month (MoM) Delivered Revenue Growth %", pad=12, fontweight="bold")
    ax.set_xlabel("Order Month")
    ax.set_ylabel("MoM Growth Percentage (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45, ha="right", fontsize=8)
    fig.tight_layout()
    p2 = os.path.join(output_dir, "monthly_mom_growth.png")
    fig.savefig(p2, bbox_inches="tight")
    plt.close(fig)
    fig_paths["monthly_mom_growth"] = p2

    # 3. Cumulative Revenue Progression
    fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
    cum_millions = df["cumulative_delivered_revenue"] / 1e6
    ax.plot(x, cum_millions, marker="D", color="#8b5cf6", linewidth=2.5, label="Cumulative Delivered Sales")
    ax.fill_between(x, cum_millions, color="#8b5cf6", alpha=0.18)
    for i, val in enumerate(cum_millions):
        if i in [0, 5, 11, 17, 23]:
            ax.text(i, val + 0.35, f"${val:.2f}M", ha="center", va="bottom", fontsize=8, fontweight="bold", color="#1e293b")
    ax.set_title("Cumulative Delivered Revenue Progression ($14.58M Total)", pad=12, fontweight="bold")
    ax.set_xlabel("Order Month")
    ax.set_ylabel("Cumulative Sales ($ Millions USD)")
    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45, ha="right", fontsize=8)
    ax.set_ylim(0, max(cum_millions) * 1.15)
    fig.tight_layout()
    p3 = os.path.join(output_dir, "cumulative_revenue.png")
    fig.savefig(p3, bbox_inches="tight")
    plt.close(fig)
    fig_paths["cumulative_revenue"] = p3

    return fig_paths


def export_revenue_summary(metrics: Dict[str, Any], revenue_df: pd.DataFrame, output_dir: str) -> str:
    """
    Export unified monthly revenue summary CSV table.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "revenue_summary.csv")
    revenue_df.to_csv(out_path, index=False)
    return out_path
