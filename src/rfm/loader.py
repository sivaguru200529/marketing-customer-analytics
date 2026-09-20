"""
Aura Retail Analytics - Phase 4 Part 2
Data Ingestion and Schema Validation for Customer Analytics.
"""

import os
from typing import Optional
import pandas as pd

from src.rfm.config import (
    DEFAULT_INPUT_CSV,
    EXPECTED_CUSTOMER_COUNT,
    COL_CUSTOMER_ID,
    COL_RECENCY,
    COL_FREQUENCY,
    COL_MONETARY,
    COL_GROSS_REVENUE,
    COL_TOTAL_ORDERS,
    COL_DELIVERED_AOV,
    COL_TOTAL_UNITS,
    COL_RETURNED_ORDERS,
    COL_CANCELLED_ORDERS,
    COL_P3_R_SCORE,
    COL_P3_F_SCORE,
    COL_P3_M_SCORE,
    COL_P3_SEGMENT,
)

REQUIRED_COLUMNS = [
    COL_CUSTOMER_ID,
    COL_RECENCY,
    COL_FREQUENCY,
    COL_MONETARY,
    COL_GROSS_REVENUE,
    COL_TOTAL_ORDERS,
    COL_DELIVERED_AOV,
    COL_TOTAL_UNITS,
    COL_RETURNED_ORDERS,
    COL_CANCELLED_ORDERS,
    COL_P3_R_SCORE,
    COL_P3_F_SCORE,
    COL_P3_M_SCORE,
    COL_P3_SEGMENT,
]


def load_customer_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load and programmatically validate the customer analytics dataset.

    Parameters:
        input_path: Optional custom path to customer_analytics.csv.

    Returns:
        pd.DataFrame containing 10,000 validated customer records.

    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If file is empty, missing required columns, or contains duplicate IDs.
    """
    if input_path is None:
        input_path = DEFAULT_INPUT_CSV

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Customer analytics dataset not found at: {input_path}")

    df = pd.read_csv(input_path)

    if df.empty:
        raise ValueError(f"Customer analytics dataset at {input_path} is empty.")

    # Check required columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Customer analytics dataset is missing required columns: {missing_cols}. "
            f"Found: {list(df.columns)}"
        )

    # Validate customer uniqueness
    total_rows = len(df)
    unique_ids = df[COL_CUSTOMER_ID].nunique()
    if unique_ids != total_rows:
        duplicates = total_rows - unique_ids
        raise ValueError(
            f"Customer ID uniqueness violated in {input_path}: {duplicates} duplicate IDs found."
        )

    if total_rows != EXPECTED_CUSTOMER_COUNT:
        # Warning/informational check
        print(f"[INFO] Customer count is {total_rows:,} (expected standard: {EXPECTED_CUSTOMER_COUNT:,}).")

    return df
