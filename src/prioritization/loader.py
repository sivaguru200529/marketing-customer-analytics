"""
Aura Retail Analytics - Phase 5 Part 2
Data Ingestion & Controlled Join Validation Module.
"""

import logging
import os
from typing import Optional, Tuple
import pandas as pd

from src.prioritization.config import (
    INPUT_CHURN_PREDICTIONS_CSV,
    INPUT_CUSTOMER_INTELLIGENCE_CSV,
)

logger = logging.getLogger(__name__)


def load_and_validate_inputs(
    intelligence_path: Optional[str] = None,
    churn_path: Optional[str] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load and validate the two input datasets prior to joining.

    Args:
        intelligence_path: Path to customer_intelligence.csv.
        churn_path: Path to churn_predictions.csv.

    Returns:
        Tuple of (df_intelligence, df_churn).

    Raises:
        FileNotFoundError: If either file is missing.
        ValueError: If invariants (uniqueness, column presence, probability bounds) fail.
    """
    if intelligence_path is None:
        intelligence_path = INPUT_CUSTOMER_INTELLIGENCE_CSV
    if churn_path is None:
        churn_path = INPUT_CHURN_PREDICTIONS_CSV

    # 1. Verify existence
    if not os.path.exists(intelligence_path):
        raise FileNotFoundError(f"Customer Intelligence dataset missing at: {intelligence_path}")
    if not os.path.exists(churn_path):
        raise FileNotFoundError(f"Churn predictions dataset missing at: {churn_path}")

    # 2. Ingest
    df_intel = pd.read_csv(intelligence_path, dtype={"rfm_score": str})
    df_churn = pd.read_csv(churn_path)

    # 3. Validate Customer Intelligence
    if len(df_intel) == 0:
        raise ValueError(f"Customer intelligence dataset at {intelligence_path} is empty.")
    if "customer_id" not in df_intel.columns:
        raise ValueError("Critical column 'customer_id' missing from customer intelligence.")
    if df_intel["customer_id"].duplicated().any():
        num_dupes = df_intel["customer_id"].duplicated().sum()
        raise ValueError(f"Detected {num_dupes} duplicate customer_id values in customer intelligence.")

    required_intel_cols = [
        "customer_id",
        "delivered_revenue",
        "delivered_orders",
        "recency_days",
        "total_web_sessions",
        "friction_rate",
        "cart_abandonment_rate",
        "total_support_tickets",
        "customer_value_band",
        "engagement_band",
        "friction_band",
    ]
    missing_intel = [c for c in required_intel_cols if c not in df_intel.columns]
    if missing_intel:
        raise ValueError(f"Missing required columns in customer intelligence: {missing_intel}")

    # 4. Validate Churn Predictions
    if len(df_churn) == 0:
        raise ValueError(f"Churn predictions dataset at {churn_path} is empty.")
    if "customer_id" not in df_churn.columns:
        raise ValueError("Critical column 'customer_id' missing from churn predictions.")
    if df_churn["customer_id"].duplicated().any():
        num_dupes = df_churn["customer_id"].duplicated().sum()
        raise ValueError(f"Detected {num_dupes} duplicate customer_id values in churn predictions.")

    required_churn_cols = ["customer_id", "churn_probability", "predicted_churn", "churn_risk_band"]
    missing_churn = [c for c in required_churn_cols if c not in df_churn.columns]
    if missing_churn:
        raise ValueError(f"Missing required columns in churn predictions: {missing_churn}")

    if df_churn["churn_probability"].isna().any():
        raise ValueError("Found NaN values in churn_probability.")

    if not ((df_churn["churn_probability"] >= 0.0) & (df_churn["churn_probability"] <= 1.0)).all():
        raise ValueError("Found churn_probability values outside [0, 1].")

    return df_intel, df_churn


def join_intelligence_and_predictions(
    df_intel: pd.DataFrame,
    df_churn: pd.DataFrame,
) -> pd.DataFrame:
    """
    Perform a controlled, verified join strictly on customer_id.

    Args:
        df_intel: Validated customer intelligence DataFrame.
        df_churn: Validated churn predictions DataFrame.

    Returns:
        pd.DataFrame containing the joined customer records.

    Raises:
        ValueError: If populations do not match 1-to-1 or duplicates arise.
    """
    intel_count = len(df_intel)
    churn_count = len(df_churn)

    # Check key sets
    intel_ids = set(df_intel["customer_id"])
    churn_ids = set(df_churn["customer_id"])

    matched_ids = intel_ids.intersection(churn_ids)
    unmatched_intel = intel_ids - churn_ids
    unmatched_churn = churn_ids - intel_ids

    logger.info(
        f"Join stats: Intel rows={intel_count:,}, Churn rows={churn_count:,}, "
        f"Matched={len(matched_ids):,}, Unmatched Intel={len(unmatched_intel):,}, "
        f"Unmatched Churn={len(unmatched_churn):,}"
    )

    if len(unmatched_intel) > 0 or len(unmatched_churn) > 0:
        raise ValueError(
            f"Population mismatch during join! "
            f"Unmatched intelligence: {len(unmatched_intel)}, Unmatched predictions: {len(unmatched_churn)}"
        )

    df_joined = pd.merge(df_intel, df_churn, on="customer_id", how="inner")

    if len(df_joined) != len(df_intel):
        raise ValueError(
            f"Row count mismatch after join: {len(df_joined):,} joined vs {len(df_intel):,} intelligence rows."
        )

    if df_joined["customer_id"].duplicated().any():
        raise ValueError("Duplicate customer_id records detected in joined dataset.")

    return df_joined
