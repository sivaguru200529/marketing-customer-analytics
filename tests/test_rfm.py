"""
Aura Retail Analytics - Phase 4 Part 2
Automated Test Suite for RFM Analysis & Customer Segmentation.

Validates input dataset integrity, tie-safe scoring, empirical parity reporting,
ordered decision tree segmentation, finite clustering feature preprocessing,
K evaluation (K=2..8), silhouette & inertia validity, neutral cluster profiles,
output files, visualizations, and deterministic pipeline execution.
"""

import os
import numpy as np
import pandas as pd
import pytest

from src.rfm.config import (
    DEFAULT_INPUT_CSV,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_FIGURES_DIR,
    DEFAULT_REPORT_PATH,
    EXPECTED_CUSTOMER_COUNT,
    K_EVAL_RANGE,
    SEGMENT_PRIORITY_ORDER,
)
from src.rfm.loader import load_customer_data
from src.rfm.rfm_calculation import extract_rfm_dataset
from src.rfm.rfm_scoring import (
    calculate_recency_score,
    calculate_frequency_score,
    calculate_monetary_score,
    compute_rfm_scores,
)
from src.rfm.parity import evaluate_rfm_parity
from src.rfm.segmentation import assign_rfm_segment, apply_rfm_segmentation
from src.rfm.clustering import (
    validate_and_preprocess_features,
    evaluate_kmeans_clusters,
    select_optimal_k,
    fit_final_kmeans,
)
from src.rfm.profiling import (
    profile_rfm_segments,
    profile_kmeans_clusters,
    compare_rfm_and_clusters,
)
from src.rfm.run_rfm import run_rfm_pipeline


@pytest.fixture(scope="module")
def base_customer_data():
    """Load customer analytics dataset once for testing."""
    return load_customer_data()


@pytest.fixture(scope="module")
def rfm_extracted_data(base_customer_data):
    """Extract RFM dataset once for testing."""
    return extract_rfm_dataset(base_customer_data)


@pytest.fixture(scope="module")
def rfm_scored_data(rfm_extracted_data):
    """Score RFM dataset once for testing."""
    return compute_rfm_scores(rfm_extracted_data)


@pytest.fixture(scope="module")
def rfm_segmented_data(rfm_scored_data):
    """Segment customer dataset once for testing."""
    return apply_rfm_segmentation(
        rfm_scored_data,
        r_col="p3_r_score",
        f_col="p3_f_score",
        m_col="p3_m_score",
        output_col="rfm_segment",
    )


# 1. Dataset & Input Tests
def test_input_dataset_exists_and_valid(base_customer_data):
    """Verify customer analytics exists, has 10,000 rows, and required columns."""
    assert os.path.isfile(DEFAULT_INPUT_CSV)
    assert len(base_customer_data) == EXPECTED_CUSTOMER_COUNT
    for col in ["customer_id", "recency_days", "delivered_orders", "delivered_revenue"]:
        assert col in base_customer_data.columns


def test_customer_ids_are_unique(base_customer_data):
    """Verify exactly 10,000 unique customer IDs."""
    assert base_customer_data["customer_id"].nunique() == EXPECTED_CUSTOMER_COUNT


def test_rfm_values_valid_and_non_negative(rfm_extracted_data):
    """Verify recency, frequency, and monetary values are non-negative and finite."""
    assert (rfm_extracted_data["recency"] >= 0).all()
    assert (rfm_extracted_data["frequency"] >= 0).all()
    assert (rfm_extracted_data["monetary"] >= 0).all()
    for col in ["recency", "frequency", "monetary"]:
        assert np.isfinite(rfm_extracted_data[col]).all()


# 2. RFM Scoring Tests
def test_rfm_scores_range_1_to_5(rfm_scored_data):
    """Verify individual R, F, M scores are strictly integers from 1 to 5."""
    for col in ["rfm_recency_score", "rfm_frequency_score", "rfm_monetary_score"]:
        assert rfm_scored_data[col].isin([1, 2, 3, 4, 5]).all()


def test_rfm_total_score_math(rfm_scored_data):
    """Verify rfm_total_score equals R + F + M and falls within [3, 15]."""
    expected = (
        rfm_scored_data["rfm_recency_score"]
        + rfm_scored_data["rfm_frequency_score"]
        + rfm_scored_data["rfm_monetary_score"]
    )
    assert (rfm_scored_data["rfm_total_score"] == expected).all()
    assert rfm_scored_data["rfm_total_score"].between(3, 15).all()


def test_rfm_score_string_representation(rfm_scored_data):
    """Verify rfm_score is a valid 3-character string representation."""
    assert (rfm_scored_data["rfm_score"].str.len() == 3).all()
    assert not rfm_scored_data["rfm_score"].isnull().any()


# 3. Parity Validation Tests
def test_rfm_phase3_parity_is_reported(rfm_scored_data):
    """Verify empirical Phase 3 vs Python parity evaluation produces calculated metrics."""
    test_df = rfm_scored_data.copy()
    test_df["rfm_segment"] = test_df["p3_rfm_segment"]
    audit_df, metrics, summary_df = evaluate_rfm_parity(test_df)
    assert len(audit_df) == EXPECTED_CUSTOMER_COUNT
    assert "r_parity_pct" in metrics
    assert "f_parity_pct" in metrics
    assert "m_parity_pct" in metrics
    assert "segment_parity_pct" in metrics
    assert 0.0 <= metrics["r_parity_pct"] <= 100.0
    assert 0.0 <= metrics["f_parity_pct"] <= 100.0
    assert 0.0 <= metrics["m_parity_pct"] <= 100.0


def test_rfm_parity_report_generated():
    """Verify that rfm_parity_report.csv is generated and non-empty."""
    path = os.path.join(DEFAULT_OUTPUT_DIR, "rfm_parity_report.csv")
    assert os.path.isfile(path)
    df = pd.read_csv(path)
    assert len(df) == 4
    for col in ["dimension", "total_evaluated", "matching_records", "mismatch_count", "parity_percentage"]:
        assert col in df.columns


# 4. Segmentation Tests
def test_segmentation_rules_are_deterministic(rfm_scored_data):
    """Verify that repeated segmentation evaluations produce identical results."""
    seg1 = apply_rfm_segmentation(rfm_scored_data, "p3_r_score", "p3_f_score", "p3_m_score")
    seg2 = apply_rfm_segmentation(rfm_scored_data, "p3_r_score", "p3_f_score", "p3_m_score")
    pd.testing.assert_series_equal(seg1["rfm_segment"], seg2["rfm_segment"])


def test_every_customer_has_exactly_one_segment(rfm_segmented_data):
    """Verify 100% of customers have exactly one non-null valid segment."""
    assert not rfm_segmented_data["rfm_segment"].isnull().any()
    invalid = set(rfm_segmented_data["rfm_segment"]) - set(SEGMENT_PRIORITY_ORDER)
    assert len(invalid) == 0


def test_segment_counts_reconcile_to_10000(rfm_segmented_data):
    """Verify customer counts across segments reconcile to exactly 10,000."""
    seg_summary = profile_rfm_segments(rfm_segmented_data)
    assert seg_summary["customer_count"].sum() == EXPECTED_CUSTOMER_COUNT
    assert abs(seg_summary["customer_percentage"].sum() - 100.0) < 0.2


# 5. K-Means Evaluation & Clustering Tests
def test_k_evaluation_contains_2_to_8(rfm_segmented_data):
    """Verify K evaluation contains exactly K=2 through K=8."""
    X_scaled, _, _ = validate_and_preprocess_features(rfm_segmented_data)
    eval_df = evaluate_kmeans_clusters(X_scaled)
    assert sorted(eval_df["k"].tolist()) == K_EVAL_RANGE


def test_selected_k_is_from_evaluated_range(rfm_segmented_data):
    """Verify selected K belongs to the evaluated range [2, 8]."""
    X_scaled, _, _ = validate_and_preprocess_features(rfm_segmented_data)
    eval_df = evaluate_kmeans_clusters(X_scaled)
    selected_k, _ = select_optimal_k(eval_df)
    assert selected_k in K_EVAL_RANGE


def test_silhouette_scores_valid(rfm_segmented_data):
    """Verify all silhouette scores are finite and fall within [-1, 1]."""
    X_scaled, _, _ = validate_and_preprocess_features(rfm_segmented_data)
    eval_df = evaluate_kmeans_clusters(X_scaled)
    assert np.isfinite(eval_df["silhouette_score"]).all()
    assert eval_df["silhouette_score"].between(-1.0, 1.0).all()


def test_inertia_values_valid(rfm_segmented_data):
    """Verify inertia values are strictly positive and finite."""
    X_scaled, _, _ = validate_and_preprocess_features(rfm_segmented_data)
    eval_df = evaluate_kmeans_clusters(X_scaled)
    assert np.isfinite(eval_df["inertia"]).all()
    assert (eval_df["inertia"] > 0).all()


def test_clustering_features_are_finite(rfm_segmented_data):
    """Verify transformed features contain no NaN, +inf, or -inf before fitting."""
    X_scaled, X_df, _ = validate_and_preprocess_features(rfm_segmented_data)
    assert not X_df.isnull().any().any()
    assert np.isfinite(X_df.values).all()
    assert np.isfinite(X_scaled).all()


def test_final_cluster_count_equals_selected_k(rfm_segmented_data):
    """Verify number of assigned clusters matches selected K."""
    X_scaled, _, _ = validate_and_preprocess_features(rfm_segmented_data)
    eval_df = evaluate_kmeans_clusters(X_scaled)
    selected_k, _ = select_optimal_k(eval_df)
    clusters_df, _ = fit_final_kmeans(X_scaled, rfm_segmented_data, selected_k)
    assert clusters_df["cluster_id"].nunique() == selected_k
    assert not clusters_df["cluster_id"].isnull().any()


def test_clustering_is_deterministic(rfm_segmented_data):
    """Verify that clustering produces identical assignments on repeated runs with fixed seed."""
    X_scaled, _, _ = validate_and_preprocess_features(rfm_segmented_data)
    c1, _ = fit_final_kmeans(X_scaled, rfm_segmented_data, k=3)
    c2, _ = fit_final_kmeans(X_scaled, rfm_segmented_data, k=3)
    pd.testing.assert_series_equal(c1["cluster_id"], c2["cluster_id"])


def test_cluster_profiles_reconcile(rfm_segmented_data):
    """Verify cluster profile counts reconcile to 10,000 customers and ~100%."""
    X_scaled, _, _ = validate_and_preprocess_features(rfm_segmented_data)
    clusters_df, _ = fit_final_kmeans(X_scaled, rfm_segmented_data, k=3)
    clus_summary = profile_kmeans_clusters(clusters_df)
    assert clus_summary["customer_count"].sum() == EXPECTED_CUSTOMER_COUNT
    assert abs(clus_summary["customer_percentage"].sum() - 100.0) < 0.2


# 6. Deliverables & Pipeline Tests
def test_expected_output_files_exist():
    """Verify that all 9 required CSV output files exist and are non-empty."""
    expected_files = [
        "customer_rfm.csv",
        "customer_rfm_segments.csv",
        "customer_clusters.csv",
        "rfm_segment_summary.csv",
        "cluster_evaluation.csv",
        "cluster_profile.csv",
        "rfm_cluster_comparison.csv",
        "rfm_quality_report.csv",
        "rfm_parity_report.csv",
    ]
    for filename in expected_files:
        path = os.path.join(DEFAULT_OUTPUT_DIR, filename)
        assert os.path.isfile(path), f"Expected deliverable '{filename}' missing at {path}"
        assert os.path.getsize(path) > 0, f"Deliverable '{filename}' is empty."


def test_figures_exist_and_readable():
    """Verify that all 12 Matplotlib figures exist and are non-empty image files (>5KB)."""
    expected_figs = [
        "rfm_score_distribution.png",
        "recency_distribution.png",
        "frequency_distribution.png",
        "monetary_distribution.png",
        "rfm_segment_distribution.png",
        "cluster_size_distribution.png",
        "elbow_curve.png",
        "silhouette_scores.png",
        "recency_vs_frequency.png",
        "frequency_vs_monetary.png",
        "recency_vs_monetary.png",
        "cluster_profile_comparison.png",
    ]
    for fig_file in expected_figs:
        path = os.path.join(DEFAULT_FIGURES_DIR, fig_file)
        assert os.path.isfile(path), f"Expected figure '{fig_file}' missing at {path}"
        assert os.path.getsize(path) > 5000, f"Figure '{fig_file}' is smaller than 5KB."


def test_rfm_pipeline_completes_successfully():
    """Verify that the end-to-end pipeline execution completes without errors."""
    res = run_rfm_pipeline(generate_charts=False)
    assert isinstance(res, dict)
    assert "customer_clusters" in res
    assert os.path.isfile(res["customer_clusters"])
