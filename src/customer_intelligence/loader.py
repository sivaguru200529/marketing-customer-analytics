"""
Aura Retail Analytics - Phase 4 Part 3
Data Ingestion and Schema Validation for Customer Intelligence.
"""

import os
from typing import Tuple
import pandas as pd

from src.customer_intelligence.config import (
    DEFAULT_CUSTOMER_ANALYTICS_CSV,
    DEFAULT_CUSTOMER_CLUSTERS_CSV,
    EXPECTED_CUSTOMER_COUNT,
)


REQUIRED_PHASE3_COLUMNS = [
    "customer_id",
    "customer_name",
    "email",
    "signup_date",
    "acquisition_channel_id",
    "acquisition_channel",
    "city",
    "state",
    "device_preference",
    "total_orders",
    "delivered_orders",
    "returned_orders",
    "cancelled_orders",
    "total_units_purchased",
    "gross_revenue",
    "delivered_revenue",
    "delivered_aov",
    "first_order_date",
    "last_order_date",
    "recency_days",
    "total_web_sessions",
    "total_abandoned_carts",
    "total_support_tickets",
    "r_score",
    "f_score",
    "m_score",
    "revenue_rank",
    "rfm_segment",
]

REQUIRED_RFM_COLUMNS = [
    "customer_id",
    "cluster_id",
    "cluster_label",
    "rfm_total_score",
    "rfm_score",
]


def load_and_validate_inputs(
    analytics_path: str = DEFAULT_CUSTOMER_ANALYTICS_CSV,
    clusters_path: str = DEFAULT_CUSTOMER_CLUSTERS_CSV,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load and validate Phase 3 customer analytics and Phase 4 Part 2 cluster datasets.
    
    Returns:
        Tuple of (df_analytics, df_clusters).
        
    Raises:
        FileNotFoundError: If any input file is missing.
        ValueError: If schema, row count, or uniqueness invariants fail.
    """
    if not os.path.exists(analytics_path):
        raise FileNotFoundError(f"Missing Phase 3 customer analytics input at: {analytics_path}")
    if not os.path.exists(clusters_path):
        raise FileNotFoundError(f"Missing Phase 4 Part 2 customer clusters input at: {clusters_path}")

    df_analytics = pd.read_csv(analytics_path)
    df_clusters = pd.read_csv(clusters_path)

    # 1. Row count validation
    if len(df_analytics) != EXPECTED_CUSTOMER_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_CUSTOMER_COUNT} rows in customer analytics, found {len(df_analytics)}"
        )
    if len(df_clusters) != EXPECTED_CUSTOMER_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_CUSTOMER_COUNT} rows in customer clusters, found {len(df_clusters)}"
        )

    # 2. Schema check
    missing_p3 = [c for c in REQUIRED_PHASE3_COLUMNS if c not in df_analytics.columns]
    if missing_p3:
        raise ValueError(f"Missing required Phase 3 columns: {missing_p3}")

    missing_rfm = [c for c in REQUIRED_RFM_COLUMNS if c not in df_clusters.columns]
    if missing_rfm:
        raise ValueError(f"Missing required RFM/cluster columns: {missing_rfm}")

    # 3. Uniqueness of primary key
    if df_analytics["customer_id"].duplicated().any():
        raise ValueError("Duplicate customer_id values detected in customer analytics dataset.")
    if df_clusters["customer_id"].duplicated().any():
        raise ValueError("Duplicate customer_id values detected in customer clusters dataset.")

    # 4. Null checks on primary keys
    if df_analytics["customer_id"].isna().any():
        raise ValueError("Null customer_id values detected in customer analytics dataset.")
    if df_clusters["customer_id"].isna().any():
        raise ValueError("Null customer_id values detected in customer clusters dataset.")

    return df_analytics, df_clusters
