"""
Aura Retail Analytics - Phase 4 Part 1
Product Exploratory Data Analysis Module.

Analyzes product catalog metrics, category and subcategory performance,
volume and revenue distributions, margins, and factual top product comparisons.
"""

import os
from typing import Any, Dict, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def analyze_product_metrics(df: pd.DataFrame) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Compute factual product and category performance statistics.

    Returns:
        Tuple containing:
        - Dict of scalar catalog metrics.
        - DataFrame of Category performance summary.
        - DataFrame of Subcategory performance summary.
        - DataFrame of Top 10 revenue-generating products with margins.
    """
    total_products = len(df)
    total_units_sold = int(df["units_sold"].sum())
    total_gross_revenue = float(df["gross_revenue"].sum())
    total_cogs = float(df["total_cogs"].sum())
    total_gross_profit = float(df["estimated_gross_profit"].sum())
    blended_margin_pct = round((total_gross_profit / total_gross_revenue) * 100.0, 2) if total_gross_revenue > 0 else 0.0

    mean_unit_price = float(df["retail_price"].mean())
    median_unit_price = float(df["retail_price"].median())
    mean_product_revenue = float(df["gross_revenue"].mean())
    median_product_revenue = float(df["gross_revenue"].median())
    mean_units_per_product = float(df["units_sold"].mean())
    median_units_per_product = float(df["units_sold"].median())

    # Overall catalog metrics
    metrics = {
        "total_products": total_products,
        "total_categories": int(df["category"].nunique()),
        "total_subcategories": int(df["sub_category"].nunique()),
        "total_units_sold": total_units_sold,
        "total_gross_revenue": round(total_gross_revenue, 2),
        "total_cogs": round(total_cogs, 2),
        "total_estimated_gross_profit": round(total_gross_profit, 2),
        "blended_gross_margin_pct": blended_margin_pct,
        "mean_retail_price": round(mean_unit_price, 2),
        "median_retail_price": round(median_unit_price, 2),
        "mean_product_revenue": round(mean_product_revenue, 2),
        "median_product_revenue": round(median_product_revenue, 2),
        "mean_units_per_product": round(mean_units_per_product, 2),
        "median_units_per_product": round(median_units_per_product, 2),
    }

    # Category Summary Table
    cat_summary = df.groupby("category", as_index=False).agg(
        product_count=("product_id", "count"),
        total_units_sold=("units_sold", "sum"),
        total_gross_revenue=("gross_revenue", "sum"),
        total_cogs=("total_cogs", "sum"),
        total_gross_profit=("estimated_gross_profit", "sum"),
        avg_retail_price=("retail_price", "mean"),
        avg_realized_price=("avg_realized_price", "mean"),
    )
    cat_summary["revenue_share_pct"] = round((cat_summary["total_gross_revenue"] / total_gross_revenue) * 100.0, 2)
    cat_summary["unit_share_pct"] = round((cat_summary["total_units_sold"] / total_units_sold) * 100.0, 2)
    cat_summary["gross_margin_pct"] = round((cat_summary["total_gross_profit"] / cat_summary["total_gross_revenue"]) * 100.0, 2)
    cat_summary["avg_retail_price"] = cat_summary["avg_retail_price"].round(2)
    cat_summary["avg_realized_price"] = cat_summary["avg_realized_price"].round(2)
    cat_summary = cat_summary.sort_values(by="total_gross_revenue", ascending=False).reset_index(drop=True)

    # Subcategory Summary Table
    sub_summary = df.groupby(["category", "sub_category"], as_index=False).agg(
        product_count=("product_id", "count"),
        total_units_sold=("units_sold", "sum"),
        total_gross_revenue=("gross_revenue", "sum"),
        total_gross_profit=("estimated_gross_profit", "sum"),
    )
    sub_summary["gross_margin_pct"] = round((sub_summary["total_gross_profit"] / sub_summary["total_gross_revenue"]) * 100.0, 2)
    sub_summary = sub_summary.sort_values(by="total_gross_revenue", ascending=False).reset_index(drop=True)

    # Top 10 Products by Revenue (with margin comparison, strictly factual)
    top_10 = df.sort_values(by="gross_revenue", ascending=False).head(10)[
        ["product_id", "product_name", "category", "sub_category", "retail_price",
         "units_sold", "gross_revenue", "estimated_gross_profit", "gross_margin_pct",
         "overall_revenue_rank"]
    ].copy().reset_index(drop=True)

    return metrics, cat_summary, sub_summary, top_10


def plot_product_visualizations(df: pd.DataFrame, cat_df: pd.DataFrame, output_dir: str) -> Dict[str, str]:
    """
    Generate product domain visualization charts using matplotlib.
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

    # 1. Product Revenue by Category (Bar Chart)
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    sorted_cat = cat_df.sort_values(by="total_gross_revenue", ascending=True)
    colors = ["#38bdf8", "#818cf8", "#c084fc", "#f472b6", "#fb923c"]
    bars = ax.barh(sorted_cat["category"], sorted_cat["total_gross_revenue"] / 1e6, color=colors[:len(sorted_cat)], height=0.6, edgecolor="#334155")
    for bar, val, share in zip(bars, sorted_cat["total_gross_revenue"] / 1e6, sorted_cat["revenue_share_pct"]):
        ax.text(val + 0.08, bar.get_y() + bar.get_height() / 2, f"${val:.2f}M ({share:.1f}%)",
                va="center", ha="left", fontsize=9, fontweight="bold", color="#1e293b")
    ax.set_title("Total Gross Product Revenue by Category", pad=12, fontweight="bold")
    ax.set_xlabel("Gross Revenue (Millions USD)")
    ax.set_xlim(0, max(sorted_cat["total_gross_revenue"] / 1e6) * 1.25)
    fig.tight_layout()
    p1 = os.path.join(output_dir, "product_revenue_by_category.png")
    fig.savefig(p1, bbox_inches="tight")
    plt.close(fig)
    fig_paths["product_revenue_by_category"] = p1

    # 2. Product Gross Margin by Category
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    sorted_margin = cat_df.sort_values(by="gross_margin_pct", ascending=True)
    margin_colors = ["#f87171", "#fbbf24", "#34d399", "#60a5fa", "#a78bfa"]
    bars = ax.barh(sorted_margin["category"], sorted_margin["gross_margin_pct"], color=margin_colors[:len(sorted_margin)], height=0.6, edgecolor="#334155")
    for bar, val in zip(bars, sorted_margin["gross_margin_pct"]):
        ax.text(val + 1.0, bar.get_y() + bar.get_height() / 2, f"{val:.1f}%",
                va="center", ha="left", fontsize=9, fontweight="bold", color="#1e293b")
    ax.set_title("Aggregate Gross Margin % by Category", pad=12, fontweight="bold")
    ax.set_xlabel("Gross Margin Percentage (%)")
    ax.set_xlim(0, 100)
    fig.tight_layout()
    p2 = os.path.join(output_dir, "product_gross_margin_by_category.png")
    fig.savefig(p2, bbox_inches="tight")
    plt.close(fig)
    fig_paths["product_gross_margin_by_category"] = p2

    # 3. Product Revenue Distribution (Histogram across 150 items)
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    p_rev = df["gross_revenue"] / 1000  # in thousands USD
    bins = np.linspace(0, 350, 25)
    ax.hist(p_rev, bins=bins, color="#10b981", edgecolor="#047857", alpha=0.75, rwidth=0.85)
    ax.axvline(p_rev.median(), color="#ef4444", linestyle="--", linewidth=1.5, label=f"Median (${p_rev.median():.1f}k)")
    ax.axvline(p_rev.mean(), color="#3b82f6", linestyle="-", linewidth=1.5, label=f"Mean (${p_rev.mean():.1f}k)")
    ax.set_title("Catalog Product Gross Revenue Distribution (N=150)", pad=12, fontweight="bold")
    ax.set_xlabel("Gross Revenue per Product ($'000 USD)")
    ax.set_ylabel("Number of Products")
    ax.legend(frameon=True, facecolor="white", edgecolor="none")
    fig.tight_layout()
    p3 = os.path.join(output_dir, "product_revenue_distribution.png")
    fig.savefig(p3, bbox_inches="tight")
    plt.close(fig)
    fig_paths["product_revenue_distribution"] = p3

    return fig_paths


def export_product_summary(cat_summary: pd.DataFrame, output_dir: str) -> str:
    """
    Export unified product summary CSV table.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "product_summary.csv")
    cat_summary.to_csv(out_path, index=False)
    return out_path
