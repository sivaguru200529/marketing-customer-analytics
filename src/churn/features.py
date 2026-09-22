"""
Aura Retail Analytics - Phase 5 Part 1
Feature Matrix Assembly & Data Leakage Prevention Module.
"""

from typing import List, Tuple
import numpy as np
import pandas as pd

from src.churn.config import (
    CATEGORICAL_FEATURE_COLUMNS,
    FEATURE_COLUMNS,
    ID_COLUMNS,
    LEAKAGE_COLUMNS,
    NUMERIC_FEATURE_COLUMNS,
    TARGET_COLUMNS,
)


def verify_leakage_controls(feature_cols: List[str]) -> bool:
    """
    Verify that no leakage columns or identifiers enter the predictive feature matrix.

    Specifically verifies:
        - 'tenure_days' is NOT in feature_cols (Strict Tenure Leakage Rule)
        - None of LEAKAGE_COLUMNS are in feature_cols
        - None of ID_COLUMNS are in feature_cols
        - None of TARGET_COLUMNS are in feature_cols

    Raises:
        ValueError: If any prohibited column is present.
    """
    # Strict tenure leakage rule
    if "tenure_days" in feature_cols:
        raise ValueError(
            "CRITICAL DATA LEAKAGE VIOLATION: 'tenure_days' is present in feature columns! "
            "Because the proxy churn target is defined using (tenure_days >= 120), including "
            "tenure_days allows models to learn the exact cutoff rule rather than customer behavior."
        )

    # Check leakage columns
    leakage_overlap = set(feature_cols).intersection(set(LEAKAGE_COLUMNS))
    if leakage_overlap:
        raise ValueError(f"CRITICAL DATA LEAKAGE: Prohibited columns detected in feature set: {sorted(leakage_overlap)}")

    # Check identifier columns
    id_overlap = set(feature_cols).intersection(set(ID_COLUMNS))
    if id_overlap:
        raise ValueError(f"IDENTIFIER LEAKAGE: Customer identifiers detected in feature set: {sorted(id_overlap)}")

    # Check target columns
    target_overlap = set(feature_cols).intersection(set(TARGET_COLUMNS))
    if target_overlap:
        raise ValueError(f"TARGET LEAKAGE: Target column detected in feature set: {sorted(target_overlap)}")

    return True


def prepare_feature_dataset(
    df: pd.DataFrame,
    target_col: str = "is_churned",
) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Assemble the predictive feature matrix X, target vector y, and customer identifier series.

    Enforces strict leakage isolation:
        1. Validates that feature columns do NOT contain any quarantined leakage features.
        2. Verifies that 'tenure_days' is strictly excluded.
        3. Verifies numeric columns have no infinite values.

    Args:
        df: Input DataFrame containing features, identifiers, and target.
        target_col: Name of the binary target column.

    Returns:
        Tuple of (X, y, customer_ids):
            X: pd.DataFrame of predictive features (NUMERIC_FEATURE_COLUMNS + CATEGORICAL_FEATURE_COLUMNS).
            y: pd.Series of binary target (0 or 1).
            customer_ids: pd.Series of unique customer_id strings.
    """
    verify_leakage_controls(FEATURE_COLUMNS)

    if target_col not in df.columns:
        raise KeyError(f"Target column '{target_col}' not found in DataFrame.")

    if "customer_id" not in df.columns:
        raise KeyError("Identifier column 'customer_id' not found in DataFrame.")

    # Validate presence of all defined feature columns
    missing_features = [col for col in FEATURE_COLUMNS if col not in df.columns]
    if missing_features:
        raise KeyError(f"Missing required feature columns: {missing_features}")

    # Extract components
    customer_ids = df["customer_id"].copy()
    y = df[target_col].copy()
    X = df[FEATURE_COLUMNS].copy()

    # Verify no infinite values in numeric columns
    for num_col in NUMERIC_FEATURE_COLUMNS:
        if np.isinf(X[num_col]).any():
            raise ValueError(f"Infinite value found in numeric feature '{num_col}'.")

    return X, y, customer_ids
