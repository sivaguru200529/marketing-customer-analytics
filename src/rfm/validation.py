"""
Aura Retail Analytics - Phase 4 Part 2
Comprehensive Quality Assurance and Mathematical Invariants Validation Module.
"""

import os
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from src.rfm.config import DEFAULT_OUTPUT_DIR, EXPECTED_CUSTOMER_COUNT, K_EVAL_RANGE


def run_rfm_quality_validation(
    customer_df: pd.DataFrame,
    rfm_df: pd.DataFrame,
    scored_df: pd.DataFrame,
    clusters_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    seg_summary_df: pd.DataFrame,
    parity_summary_df: pd.DataFrame,
    selected_k: int,
    X_scaled: np.ndarray,
) -> pd.DataFrame:
    """
    Execute exhaustive validation across input data, RFM scores, segmentation,
    clustering parameters, and parity reporting.

    Returns:
        pd.DataFrame formatted with columns: [check_name, expected, actual, status, details]
    """
    checks = []

    def add_check(name: str, expected: str, actual: str, passed: bool, details: str):
        checks.append({
            "check_name": name,
            "expected": expected,
            "actual": actual,
            "status": "PASSED" if passed else "FAILED",
            "details": details,
        })

    # 1. Dataset Scale & Grain
    total_cust = len(customer_df)
    unique_ids = customer_df["customer_id"].nunique()
    add_check(
        "customer_population_count",
        f"{EXPECTED_CUSTOMER_COUNT}",
        f"{total_cust}",
        total_cust == EXPECTED_CUSTOMER_COUNT,
        f"Verified customer analytics row count equals {EXPECTED_CUSTOMER_COUNT:,}."
    )
    add_check(
        "customer_id_uniqueness",
        "100% Unique",
        f"{unique_ids} / {total_cust} Unique",
        unique_ids == total_cust,
        "Zero duplicate customer IDs detected."
    )

    # 2. RFM Value Sanity
    non_neg_rfm = (
        (rfm_df["recency"] >= 0).all() and
        (rfm_df["frequency"] >= 0).all() and
        (rfm_df["monetary"] >= 0).all()
    )
    add_check(
        "rfm_values_non_negative",
        "All values >= 0",
        "All values >= 0" if non_neg_rfm else "Negative values found",
        non_neg_rfm,
        f"recency min={rfm_df['recency'].min()}, frequency min={rfm_df['frequency'].min()}, monetary min={rfm_df['monetary'].min():.2f}"
    )

    # 3. RFM Score Ranges & Composite Math
    r_valid = scored_df["rfm_recency_score"].isin([1, 2, 3, 4, 5]).all()
    f_valid = scored_df["rfm_frequency_score"].isin([1, 2, 3, 4, 5]).all()
    m_valid = scored_df["rfm_monetary_score"].isin([1, 2, 3, 4, 5]).all()
    add_check("rfm_r_score_range", "Integers 1 to 5", "Integers 1 to 5" if r_valid else "Invalid", r_valid, f"R min={scored_df['rfm_recency_score'].min()}, max={scored_df['rfm_recency_score'].max()}")
    add_check("rfm_f_score_range", "Integers 1 to 5", "Integers 1 to 5" if f_valid else "Invalid", f_valid, f"F min={scored_df['rfm_frequency_score'].min()}, max={scored_df['rfm_frequency_score'].max()}")
    add_check("rfm_m_score_range", "Integers 1 to 5", "Integers 1 to 5" if m_valid else "Invalid", m_valid, f"M min={scored_df['rfm_monetary_score'].min()}, max={scored_df['rfm_monetary_score'].max()}")

    tot_expected = scored_df["rfm_recency_score"] + scored_df["rfm_frequency_score"] + scored_df["rfm_monetary_score"]
    tot_correct = (scored_df["rfm_total_score"] == tot_expected).all()
    tot_range = scored_df["rfm_total_score"].between(3, 15).all()
    add_check("rfm_total_score_math", "R + F + M in [3, 15]", "R + F + M verified" if (tot_correct and tot_range) else "Math mismatch", tot_correct and tot_range, f"Total score min={scored_df['rfm_total_score'].min()}, max={scored_df['rfm_total_score'].max()}")

    str_repr_valid = (scored_df["rfm_score"].str.len() == 3).all() and not scored_df["rfm_score"].isnull().any()
    add_check("rfm_score_string_representation", "3-character string", "Valid 3-char strings" if str_repr_valid else "Invalid", str_repr_valid, "Verified readable categorical string representations (e.g. '555').")

    # 4. Segmentation Invariants
    seg_assigned = not scored_df["rfm_segment"].isnull().any()
    seg_count_sum = seg_summary_df["customer_count"].sum()
    seg_pct_sum = round(seg_summary_df["customer_percentage"].sum(), 1)
    add_check("segment_completeness", "100% Assigned (0 Nulls)", f"{100.0 if seg_assigned else 0.0}% Assigned", seg_assigned, "Every customer receives exactly one segment.")
    add_check("segment_reconciliation", "Total = 10,000 customers", f"Total = {seg_count_sum:,} customers", seg_count_sum == total_cust, f"Reconciled {len(seg_summary_df)} segments across total customer base.")
    add_check("segment_percentage_reconciliation", "~100.0%", f"{seg_pct_sum}%", abs(seg_pct_sum - 100.0) < 0.2, f"Segment shares sum to {seg_pct_sum}%.")

    # 5. Clustering Invariants
    eval_k_vals = sorted(eval_df["k"].tolist())
    eval_range_valid = (eval_k_vals == K_EVAL_RANGE)
    add_check("k_evaluation_range", f"{K_EVAL_RANGE}", f"{eval_k_vals}", eval_range_valid, "Evaluated K=2 through K=8 inclusive.")

    sil_valid = np.isfinite(eval_df["silhouette_score"]).all() and eval_df["silhouette_score"].between(-1.0, 1.0).all()
    inertia_valid = np.isfinite(eval_df["inertia"]).all() and (eval_df["inertia"] > 0).all()
    add_check("silhouette_scores_valid", "Finite in [-1, 1]", "Finite in [-1, 1]" if sil_valid else "Invalid", sil_valid, f"Silhouette range: [{eval_df['silhouette_score'].min():.4f}, {eval_df['silhouette_score'].max():.4f}]")
    add_check("inertia_values_valid", "Finite > 0", "Finite > 0" if inertia_valid else "Invalid", inertia_valid, f"Inertia range: [{eval_df['inertia'].min():.2f}, {eval_df['inertia'].max():.2f}]")

    features_finite = np.isfinite(X_scaled).all()
    add_check("clustering_features_are_finite", "No NaN, +inf, -inf", "All finite" if features_finite else "Non-finite values present", features_finite, "Transformed standardized feature matrix verified finite before clustering.")

    sel_k_valid = selected_k in K_EVAL_RANGE
    add_check("selected_k_in_range", f"K in {K_EVAL_RANGE}", f"K={selected_k}", sel_k_valid, f"Selected K={selected_k} derived via maximum silhouette score with near-tie tolerance.")

    actual_clusters = clusters_df["cluster_id"].nunique()
    clus_assigned = not clusters_df["cluster_id"].isnull().any()
    add_check("cluster_assignment_completeness", f"K={selected_k} clusters, 0 nulls", f"K={actual_clusters} clusters, 0 nulls", (actual_clusters == selected_k) and clus_assigned, "Every customer assigned to exactly one neutral cluster.")

    # 6. Parity Reporting
    parity_valid = (len(parity_summary_df) == 4) and not parity_summary_df["parity_percentage"].isnull().any()
    add_check("parity_report_generated", "4 Dimensions Evaluated", f"{len(parity_summary_df)} Dimensions Evaluated", parity_valid, "Empirical Phase 3 vs Python comparisons retained for R, F, M, and Segments.")

    return pd.DataFrame(checks)


def export_rfm_quality_report(report_df: pd.DataFrame, output_dir: Optional[str] = None) -> str:
    """
    Export the validation report to data/04_rfm/rfm_quality_report.csv.
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "rfm_quality_report.csv")
    report_df.to_csv(out_path, index=False)
    return out_path
