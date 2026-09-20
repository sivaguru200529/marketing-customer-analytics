"""
Aura Retail Analytics - Phase 4 Part 2
Unsupervised K-Means Customer Clustering and Parameter Evaluation Module.

Implements finite-feature validation, defensible transformations (unscaled recency + log1p
frequency/monetary followed by standard scaling), deterministic K evaluation across K=2..8,
and dynamic K selection based on maximum silhouette score with a 0.001 near-tie smaller-K rule.
"""

import os
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from src.rfm.config import (
    DEFAULT_OUTPUT_DIR,
    RANDOM_STATE,
    N_INIT,
    K_EVAL_RANGE,
    SILHOUETTE_TIE_TOLERANCE,
    TRANSFORM_RECENCY,
    TRANSFORM_FREQUENCY,
    TRANSFORM_MONETARY,
)


def validate_and_preprocess_features(
    df: pd.DataFrame
) -> Tuple[np.ndarray, pd.DataFrame, StandardScaler]:
    """
    Validate and preprocess features for K-Means clustering.

    Steps:
    1. Validate source RFM values are non-negative and finite.
    2. Apply defensible transformations (unscaled recency + log1p on frequency and monetary).
    3. Validate transformed feature matrix contains no NaN, +inf, or -inf.
    4. Fit and apply StandardScaler.

    Returns:
        Tuple containing:
        - X_scaled: np.ndarray of shape (N, 3), scaled features.
        - X_df: pd.DataFrame of transformed unscaled features.
        - scaler: fitted StandardScaler instance.
    """
    # 1. Source validation
    if (df["recency"] < 0).any():
        raise ValueError("Source recency values must be >= 0.")
    if (df["frequency"] < 0).any():
        raise ValueError("Source frequency values must be >= 0.")
    if (df["monetary"] < 0).any():
        raise ValueError("Source monetary values must be >= 0.")

    # 2. Apply transformations according to config
    X_df = pd.DataFrame(index=df.index)

    if TRANSFORM_RECENCY:
        X_df["recency_feat"] = np.log1p(df["recency"].astype(float))
    else:
        X_df["recency_feat"] = df["recency"].astype(float)

    if TRANSFORM_FREQUENCY:
        X_df["frequency_feat"] = np.log1p(df["frequency"].astype(float))
    else:
        X_df["frequency_feat"] = df["frequency"].astype(float)

    if TRANSFORM_MONETARY:
        X_df["monetary_feat"] = np.log1p(df["monetary"].astype(float))
    else:
        X_df["monetary_feat"] = df["monetary"].astype(float)

    # 3. Finite validation before scaling and clustering
    for col in X_df.columns:
        if X_df[col].isnull().any():
            raise ValueError(f"Feature '{col}' contains NaN values after transformation.")
        if np.isinf(X_df[col]).any():
            raise ValueError(f"Feature '{col}' contains infinite values after transformation.")

    # 4. Standard scaling
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_df)

    if not np.isfinite(X_scaled).all():
        raise ValueError("Scaled feature matrix contains non-finite values.")

    return X_scaled, X_df, scaler


def evaluate_kmeans_clusters(
    X_scaled: np.ndarray,
    k_range: Optional[List[int]] = None,
    random_state: int = RANDOM_STATE,
    n_init: int = N_INIT,
) -> pd.DataFrame:
    """
    Evaluate K-Means across specified range of K values computing inertia and silhouette scores.

    Parameters:
        X_scaled: Preprocessed and scaled feature array.
        k_range: List of K values to evaluate. Defaults to [2, 3, 4, 5, 6, 7, 8].
        random_state: Fixed seed for reproducibility.
        n_init: Number of random initializations per K.

    Returns:
        pd.DataFrame containing columns: [k, inertia, silhouette_score].
    """
    if k_range is None:
        k_range = K_EVAL_RANGE

    records = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=n_init)
        cluster_labels = km.fit_predict(X_scaled)
        sil = float(silhouette_score(X_scaled, cluster_labels))
        inertia = float(km.inertia_)

        if not np.isfinite(inertia):
            raise ValueError(f"Non-finite inertia encountered for K={k}.")
        if not np.isfinite(sil) or not (-1.0 <= sil <= 1.0):
            raise ValueError(f"Invalid silhouette score {sil} encountered for K={k}.")

        records.append({
            "k": int(k),
            "inertia": round(inertia, 2),
            "silhouette_score": round(sil, 4),
        })

    eval_df = pd.DataFrame(records)
    return eval_df


def select_optimal_k(
    eval_df: pd.DataFrame,
    tie_tolerance: float = SILHOUETTE_TIE_TOLERANCE
) -> Tuple[int, str]:
    """
    Select optimal K using the predefined deterministic selection methodology:
    1. Primary criterion: Highest silhouette score.
    2. Near-tie rule: If another K is within tie_tolerance (0.001) of max, select smaller K.

    Returns:
        Tuple containing:
        - selected_k: int
        - rationale: str explaining the quantitative selection
    """
    max_sil = eval_df["silhouette_score"].max()
    # Near-tie candidates within tolerance of the highest silhouette score
    candidates = eval_df[eval_df["silhouette_score"] >= (max_sil - tie_tolerance)]
    selected_row = candidates.sort_values(by="k", ascending=True).iloc[0]
    selected_k = int(selected_row["k"])
    selected_sil = float(selected_row["silhouette_score"])

    rationale = (
        f"K={selected_k} selected based on maximum silhouette score criterion "
        f"({selected_sil:.4f}, max={max_sil:.4f}) with near-tie tolerance {tie_tolerance} "
        f"favoring parsimony (smaller K)."
    )

    return selected_k, rationale


def fit_final_kmeans(
    X_scaled: np.ndarray,
    df: pd.DataFrame,
    k: int,
    random_state: int = RANDOM_STATE,
    n_init: int = N_INIT,
) -> Tuple[pd.DataFrame, KMeans]:
    """
    Train final K-Means model for selected K, assigning neutral cluster labels.

    Returns:
        Tuple containing:
        - pd.DataFrame with 'cluster_id' (int 0..k-1) and 'cluster_label' (str 'Cluster 0'..).
        - fitted KMeans instance.
    """
    km = KMeans(n_clusters=k, random_state=random_state, n_init=n_init)
    labels = km.fit_predict(X_scaled)

    res = df.copy()
    res["cluster_id"] = labels
    res["cluster_label"] = [f"Cluster {i}" for i in labels]

    return res, km


def export_clustering_outputs(
    eval_df: pd.DataFrame,
    clusters_df: pd.DataFrame,
    output_dir: Optional[str] = None
) -> Tuple[str, str]:
    """
    Export cluster_evaluation.csv and customer_clusters.csv.
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)

    eval_path = os.path.join(output_dir, "cluster_evaluation.csv")
    eval_df.to_csv(eval_path, index=False)

    clusters_path = os.path.join(output_dir, "customer_clusters.csv")
    # Deterministic export sorted by customer_id
    clusters_df.sort_values("customer_id").to_csv(clusters_path, index=False)

    return eval_path, clusters_path
