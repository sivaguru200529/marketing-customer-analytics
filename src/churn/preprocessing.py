"""
Aura Retail Analytics - Phase 5 Part 1
Data Preprocessing, Transformation & Train/Test Splitting Module.
"""

from typing import List, Tuple
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.churn.config import (
    CATEGORICAL_FEATURE_COLUMNS,
    NUMERIC_FEATURE_COLUMNS,
    RANDOM_SEED,
    TEST_SIZE,
)


def build_preprocessor(
    numeric_cols: List[str] = NUMERIC_FEATURE_COLUMNS,
    categorical_cols: List[str] = CATEGORICAL_FEATURE_COLUMNS,
) -> ColumnTransformer:
    """
    Construct a scikit-learn ColumnTransformer for numeric and categorical features.

    Transforms:
        - Numeric: Median imputation (for columns like delivered_aov) followed by StandardScaler.
        - Categorical: OneHotEncoder with drop='first' and handle_unknown='ignore'.

    Returns:
        Configured ColumnTransformer instance.
    """
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            (
                "onehot",
                OneHotEncoder(
                    drop="first",
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_cols),
            ("cat", categorical_transformer, categorical_cols),
        ],
        remainder="drop",
    )

    return preprocessor


def get_transformed_feature_names(
    fitted_preprocessor: ColumnTransformer,
    numeric_cols: List[str] = NUMERIC_FEATURE_COLUMNS,
    categorical_cols: List[str] = CATEGORICAL_FEATURE_COLUMNS,
) -> List[str]:
    """
    Extract readable feature names from a fitted ColumnTransformer.

    Returns:
        List of feature names matching the transformed array columns.
    """
    feature_names = list(numeric_cols)

    # Extract one-hot encoded categories
    cat_transformer = fitted_preprocessor.named_transformers_.get("cat")
    if cat_transformer is not None:
        ohe = cat_transformer.named_steps.get("onehot")
        if ohe is not None and hasattr(ohe, "get_feature_names_out"):
            cat_encoded_names = list(ohe.get_feature_names_out(categorical_cols))
            feature_names.extend(cat_encoded_names)

    return feature_names


def split_data(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_SEED,
    stratify: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Perform a reproducible stratified train/test split.

    Args:
        X: Feature DataFrame.
        y: Target Series.
        test_size: Proportion of dataset to hold out as test set (default 0.20).
        random_state: Configurable random seed for deterministic reproduction (default 42).
        stratify: Whether to preserve class proportions in train and test splits (default True).

    Returns:
        Tuple of (X_train, X_test, y_train, y_test).
    """
    stratify_target = y if stratify else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_target,
    )

    return X_train, X_test, y_train, y_test
