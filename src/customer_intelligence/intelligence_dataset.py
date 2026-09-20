"""
Aura Retail Analytics - Phase 4 Part 3
Assembly & Export of the Unified Customer Intelligence Dataset.
"""

import os
from typing import List
import pandas as pd

from src.customer_intelligence.config import (
    DEFAULT_OUTPUT_DIR,
    OUTPUT_CUSTOMER_INTELLIGENCE,
)
from src.customer_intelligence.feature_engineering import compute_derived_features


INTELLIGENCE_COLUMN_ORDER: List[str] = [
    # Customer Identifiers
    "customer_id",
    "customer_name",
    "email",
    # Geography & Device Preference
    "city",
    "state",
    "device_preference",
    # Acquisition & Tenure
    "signup_date",
    "tenure_days",
    "acquisition_channel_id",
    "acquisition_channel",
    # Order Metrics & Fulfillment Realization
    "total_orders",
    "delivered_orders",
    "returned_orders",
    "cancelled_orders",
    "order_delivery_rate",
    "total_units_purchased",
    "units_per_order",
    # Revenue & Financial Realization
    "gross_revenue",
    "delivered_revenue",
    "gross_aov",
    "delivered_aov",
    "revenue_rank",
    # Activity Timeline
    "first_order_date",
    "last_order_date",
    "recency_days",
    # Digital & Web Engagement
    "total_web_sessions",
    "total_abandoned_carts",
    "cart_abandonment_rate",
    # Customer Friction & Support
    "total_support_tickets",
    "tickets_per_order",
    "return_rate",
    "cancellation_rate",
    "friction_order_count",
    "friction_rate",
    "fulfillment_friction_flag",
    "friction_band",
    # Authoritative RFM Segmentation
    "r_score",
    "f_score",
    "m_score",
    "rfm_total_score",
    "rfm_score",
    "rfm_segment",
    # K-Means Cluster Intelligence
    "cluster_id",
    "cluster_label",
    "cluster_description",
    # Behavioral Classification Bands
    "customer_value_band",
    "engagement_band",
]


def build_customer_intelligence_dataset(
    df_analytics: pd.DataFrame,
    df_clusters: pd.DataFrame,
    output_path: str = OUTPUT_CUSTOMER_INTELLIGENCE,
) -> pd.DataFrame:
    """
    Assemble the unified customer intelligence dataset by integrating Phase 3 customer
    analytics with Phase 4 Part 2 clusters and derived behavioral features.
    
    Args:
        df_analytics: Phase 3 customer analytics dataframe (10,000 rows).
        df_clusters: Phase 4 Part 2 customer clusters dataframe (10,000 rows).
        output_path: Path to save the final CSV.
        
    Returns:
        Unified customer intelligence dataframe.
    """
    # Merge cluster features
    cluster_cols = ["customer_id", "cluster_id", "cluster_label"]
    df_merged = df_analytics.merge(
        df_clusters[cluster_cols],
        on="customer_id",
        how="inner",
    )

    if len(df_merged) != len(df_analytics):
        raise ValueError(
            f"Inner merge resulted in row count mismatch: {len(df_merged)} vs {len(df_analytics)}"
        )

    # Compute derived features
    df_intel = compute_derived_features(df_merged)

    # Reorder columns
    df_final = df_intel[INTELLIGENCE_COLUMN_ORDER].copy()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_final.to_csv(output_path, index=False)

    return df_final
