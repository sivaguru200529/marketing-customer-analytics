"""
Aura Retail Analytics - Phase 5 Part 1
Data Ingestion & Integrity Validation Module for Customer Intelligence Dataset.
"""

import os
from typing import Optional
import pandas as pd

from src.churn.config import (
    CATEGORICAL_FEATURE_COLUMNS,
    DEFAULT_CUSTOMER_INTELLIGENCE_CSV,
    ID_COLUMNS,
    LEAKAGE_COLUMNS,
    NUMERIC_FEATURE_COLUMNS,
    REFERENCE_CUSTOMER_COUNT,
)


def load_customer_intelligence_data(
    filepath: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load the authoritative Phase 4 Part 3 Customer Intelligence dataset and validate integrity.

    Args:
        filepath: Optional path to customer_intelligence.csv. Defaults to config path.

    Returns:
        pd.DataFrame containing the 10,000-customer analytical dataset.

    Raises:
        FileNotFoundError: If the source CSV does not exist.
        ValueError: If invariants (uniqueness, row counts, required columns) fail.
    """
    if filepath is None:
        filepath = DEFAULT_CUSTOMER_INTELLIGENCE_CSV

    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Customer Intelligence dataset not found at: {filepath}. "
            "Ensure Phase 4 Part 3 has been executed successfully."
        )

    df = pd.read_csv(filepath, dtype={"rfm_score": str})

    # Validate row count
    if len(df) == 0:
        raise ValueError(f"Dataset at {filepath} is completely empty.")

    # Validate Primary Key
    if "customer_id" not in df.columns:
        raise ValueError("Critical column 'customer_id' missing from input dataset.")

    if df["customer_id"].duplicated().any():
        num_dupes = df["customer_id"].duplicated().sum()
        raise ValueError(f"Detected {num_dupes} duplicate customer_id values. Grain must be 1 row per customer.")

    # Validate expected column coverage
    required_cols = ID_COLUMNS + NUMERIC_FEATURE_COLUMNS + CATEGORICAL_FEATURE_COLUMNS + LEAKAGE_COLUMNS
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required analytical columns: {missing_cols}")

    return df
