"""
Aura Retail Analytics - Phase 4 Part 1
Data Loader Module for Phase 3 Analytical Datasets.

Loads, validates schemas, verifies grains and primary keys, and produces
diagnostic profiles for downstream exploratory data analysis.
"""

import os
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd

# Expected filenames under data/03_analytics/
DATASET_FILENAMES = {
    "customer_analytics": "customer_analytics.csv",
    "product_analytics": "product_analytics.csv",
    "monthly_revenue": "monthly_revenue.csv",
    "marketing_performance": "marketing_performance.csv",
    "cohort_retention": "cohort_retention.csv",
    "business_kpis": "business_kpis.csv",
}

# Required columns for each dataset
REQUIRED_COLUMNS: Dict[str, List[str]] = {
    "customer_analytics": [
        "customer_id", "customer_name", "email", "signup_date",
        "acquisition_channel_id", "acquisition_channel", "city", "state",
        "device_preference", "total_orders", "delivered_orders", "returned_orders",
        "cancelled_orders", "total_units_purchased", "gross_revenue",
        "delivered_revenue", "delivered_aov", "first_order_date",
        "last_order_date", "recency_days", "total_web_sessions",
        "total_abandoned_carts", "total_support_tickets", "r_score",
        "f_score", "m_score", "revenue_rank", "rfm_segment"
    ],
    "product_analytics": [
        "product_id", "product_name", "category", "sub_category",
        "cost_price", "retail_price", "units_sold", "distinct_orders_count",
        "gross_revenue", "total_cogs", "estimated_gross_profit",
        "gross_margin_pct", "avg_realized_price", "category_revenue_rank",
        "overall_revenue_rank", "category_revenue_share_pct"
    ],
    "monthly_revenue": [
        "order_month", "total_orders_placed", "delivered_orders",
        "returned_orders", "cancelled_orders", "gross_billed_revenue",
        "delivered_revenue", "returned_revenue", "cancelled_revenue",
        "total_discounts_granted", "total_shipping_revenue", "delivered_aov",
        "prev_month_delivered_revenue", "mom_revenue_change",
        "mom_revenue_growth_pct", "mom_order_growth_pct",
        "cumulative_delivered_revenue", "cumulative_delivered_orders"
    ],
    "marketing_performance": [
        "channel_id", "channel_name", "channel_type", "total_spend_usd",
        "total_impressions", "total_clicks", "ctr_pct", "cpc_usd", "cpm_usd",
        "acquired_customers", "cac_usd", "total_attributed_orders",
        "delivered_attributed_orders", "gross_attributed_revenue",
        "delivered_attributed_revenue", "roas", "revenue_per_acquired_customer"
    ],
    "cohort_retention": [
        "cohort_month", "cohort_size", "activity_month",
        "months_since_signup", "active_ordering_customers",
        "purchase_retention_rate_pct"
    ],
    "business_kpis": [
        "total_registered_customers", "active_ordering_customers",
        "customer_penetration_rate_pct", "active_states_count",
        "total_orders_placed", "delivered_orders", "returned_orders",
        "cancelled_orders", "fulfillment_rate_pct", "return_rate_pct",
        "cancellation_rate_pct", "total_units_sold",
        "distinct_products_ordered", "avg_units_per_order",
        "total_gross_billed_revenue", "total_delivered_revenue",
        "total_returned_revenue", "total_cancelled_revenue",
        "total_discounts_granted", "total_shipping_revenue",
        "total_estimated_cogs", "estimated_gross_profit_usd",
        "gross_profit_margin_pct", "average_order_value_usd", "arpu_usd",
        "arppu_usd", "total_marketing_spend_usd", "total_ad_impressions",
        "total_ad_clicks", "blended_ctr_pct", "blended_cpc_usd",
        "blended_cac_usd", "blended_roas", "total_web_sessions",
        "total_cart_abandonments", "cart_abandonment_rate_pct",
        "total_support_tickets_opened"
    ],
}

# Primary grain definition for uniqueness validation
GRAIN_KEYS: Dict[str, Union[str, List[str]]] = {
    "customer_analytics": "customer_id",
    "product_analytics": "product_id",
    "monthly_revenue": "order_month",
    "marketing_performance": "channel_id",
    "cohort_retention": ["cohort_month", "activity_month"],
    "business_kpis": [],  # Validated as single row
}


def get_default_data_dir() -> str:
    """Return the absolute path to data/03_analytics/."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    return os.path.join(workspace_root, "data", "03_analytics")


def load_dataset(name: str, data_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load a single Phase 3 analytical dataset by key name.

    Parameters:
        name: Name of the dataset (e.g., 'customer_analytics').
        data_dir: Optional directory containing CSV files. Defaults to data/03_analytics/.

    Returns:
        pd.DataFrame containing the loaded data.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the file is empty, missing required columns, or violates grain uniqueness.
    """
    if name not in DATASET_FILENAMES:
        raise ValueError(f"Unknown dataset '{name}'. Available: {list(DATASET_FILENAMES.keys())}")

    if data_dir is None:
        data_dir = get_default_data_dir()

    filename = DATASET_FILENAMES[name]
    file_path = os.path.join(data_dir, filename)

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Required dataset '{filename}' not found at: {file_path}")

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV at {file_path}: {e}") from e

    if df.empty:
        raise ValueError(f"Dataset '{name}' in {filename} is empty (0 rows).")

    # Column validation
    expected_cols = REQUIRED_COLUMNS.get(name, [])
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Dataset '{name}' is missing required columns: {missing_cols}. "
            f"Present columns: {list(df.columns)}"
        )

    # Grain / Uniqueness validation
    grain = GRAIN_KEYS.get(name)
    if name == "business_kpis":
        if len(df) != 1:
            raise ValueError(f"business_kpis must contain exactly 1 row, found {len(df)} rows.")
    elif grain:
        if isinstance(grain, list):
            duplicates = df.duplicated(subset=grain, keep=False)
        else:
            duplicates = df.duplicated(subset=[grain], keep=False)

        num_dupes = duplicates.sum()
        if num_dupes > 0:
            raise ValueError(
                f"Dataset '{name}' has {num_dupes} duplicate rows violating grain {grain}."
            )

    return df


def load_all_analytics_datasets(data_dir: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """
    Load and validate all 6 Phase 3 analytical CSV datasets.

    Parameters:
        data_dir: Optional directory path. Defaults to data/03_analytics/.

    Returns:
        Dict mapping dataset name to its loaded DataFrame.
    """
    datasets = {}
    for name in DATASET_FILENAMES:
        datasets[name] = load_dataset(name, data_dir=data_dir)
    return datasets


def get_dataset_profiles(datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Produce diagnostic metadata table across all loaded datasets:
    rows, columns, memory usage, and total null values.
    """
    profiles = []
    for name, df in datasets.items():
        profiles.append({
            "dataset": name,
            "filename": DATASET_FILENAMES[name],
            "rows": len(df),
            "columns": len(df.columns),
            "total_null_cells": int(df.isnull().sum().sum()),
            "columns_with_nulls": int((df.isnull().sum() > 0).sum()),
            "memory_usage_kb": round(df.memory_usage(deep=True).sum() / 1024, 2),
        })
    return pd.DataFrame(profiles)
