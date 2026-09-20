"""
Aura Retail Analytics - Phase 4 Part 3 Test Suite
Automated Verification for Customer Intelligence Dataset & Analytical Outputs.
"""

import os
import numpy as np
import pandas as pd
import pytest

from src.customer_intelligence.config import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPORT_PATH,
    EXPECTED_CUSTOMER_COUNT,
    EXPECTED_TOTAL_DELIVERED_REVENUE,
    OUTPUT_CUSTOMER_INTELLIGENCE,
    SEGMENT_PRIORITY_ORDER,
    SELECTED_K,
)
from src.customer_intelligence.intelligence_dataset import (
    INTELLIGENCE_COLUMN_ORDER,
    build_customer_intelligence_dataset,
)
from src.customer_intelligence.loader import load_and_validate_inputs
from src.customer_intelligence.summaries import generate_all_summaries
from src.customer_intelligence.validation import run_customer_intelligence_quality_checks


@pytest.fixture(scope="module")
def dataset_paths():
    """Paths to generated outputs for Phase 4 Part 3."""
    return {
        "intel": OUTPUT_CUSTOMER_INTELLIGENCE,
        "value_sum": os.path.join(DEFAULT_OUTPUT_DIR, "customer_value_summary.csv"),
        "segment_sum": os.path.join(DEFAULT_OUTPUT_DIR, "customer_segment_summary.csv"),
        "cluster_sum": os.path.join(DEFAULT_OUTPUT_DIR, "customer_cluster_summary.csv"),
        "matrix": os.path.join(DEFAULT_OUTPUT_DIR, "segment_cluster_matrix.csv"),
        "behavior": os.path.join(DEFAULT_OUTPUT_DIR, "customer_behavior_summary.csv"),
        "quality": os.path.join(DEFAULT_OUTPUT_DIR, "customer_intelligence_quality_report.csv"),
        "report": DEFAULT_REPORT_PATH,
    }


@pytest.fixture(scope="module")
def df_intel(dataset_paths):
    """Load the customer intelligence dataset."""
    assert os.path.exists(dataset_paths["intel"]), "customer_intelligence.csv not found!"
    return pd.read_csv(dataset_paths["intel"], dtype={"rfm_score": str})


def test_customer_intelligence_file_exists(dataset_paths):
    """Verify that customer_intelligence.csv exists and is non-empty."""
    path = dataset_paths["intel"]
    assert os.path.exists(path), f"File missing at {path}"
    assert os.path.getsize(path) > 1000, "File is unexpectedly small or empty."


def test_customer_ids_are_unique(df_intel):
    """Verify customer_id is 100% unique with zero duplicates."""
    assert df_intel["customer_id"].nunique() == EXPECTED_CUSTOMER_COUNT
    assert not df_intel["customer_id"].duplicated().any()


def test_customer_count_is_10000(df_intel):
    """Verify exactly 10,000 customers in the dataset."""
    assert len(df_intel) == EXPECTED_CUSTOMER_COUNT


def test_required_columns_exist(df_intel):
    """Verify that all 47 expected columns are present."""
    missing = [col for col in INTELLIGENCE_COLUMN_ORDER if col not in df_intel.columns]
    assert len(missing) == 0, f"Missing required columns: {missing}"


def test_one_row_per_customer(df_intel):
    """Verify dataset grain: exactly 1 row = 1 customer."""
    assert len(df_intel) == df_intel["customer_id"].nunique()


def test_numeric_features_are_finite(df_intel):
    """Verify that numeric columns have no infinite values and unexpected NaNs."""
    numeric_cols = df_intel.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        assert not np.isinf(df_intel[col]).any(), f"Infinite value found in column {col}"
        if col != "delivered_aov":
            assert not df_intel[col].isna().any(), f"Unexpected NaN in column {col}"


def test_revenue_values_are_valid(df_intel):
    """Verify that gross and delivered revenue values are non-negative."""
    assert (df_intel["gross_revenue"] >= 0.0).all()
    assert (df_intel["delivered_revenue"] >= 0.0).all()
    assert (df_intel["gross_revenue"] >= df_intel["delivered_revenue"]).all()


def test_order_counts_are_valid(df_intel):
    """Verify that order counts are non-negative and reconcile."""
    assert (df_intel["total_orders"] >= 0).all()
    assert (df_intel["delivered_orders"] >= 0).all()
    assert (df_intel["returned_orders"] >= 0).all()
    assert (df_intel["cancelled_orders"] >= 0).all()

    # Reconcile sum of parts equals total
    expected_sum = df_intel["delivered_orders"] + df_intel["returned_orders"] + df_intel["cancelled_orders"]
    assert (df_intel["total_orders"] == expected_sum).all()


def test_rfm_values_are_valid(df_intel):
    """Verify recency, frequency, and monetary individual scores are in 1..5."""
    assert df_intel["r_score"].isin([1, 2, 3, 4, 5]).all()
    assert df_intel["f_score"].isin([1, 2, 3, 4, 5]).all()
    assert df_intel["m_score"].isin([1, 2, 3, 4, 5]).all()


def test_rfm_total_is_correct(df_intel):
    """Verify rfm_total_score equals r + f + m and spans [3, 15]."""
    expected_total = df_intel["r_score"] + df_intel["f_score"] + df_intel["m_score"]
    assert (df_intel["rfm_total_score"] == expected_total).all()
    assert ((df_intel["rfm_total_score"] >= 3) & (df_intel["rfm_total_score"] <= 15)).all()


def test_rfm_string_is_valid(df_intel):
    """Verify rfm_score is a valid 3-character string with digits 1-5."""
    str_series = df_intel["rfm_score"].astype(str)
    assert (str_series.str.len() == 3).all()
    assert str_series.str.match(r"^[1-5]{3}$").all()


def test_segment_assignments_are_complete(df_intel):
    """Verify that every customer has an assigned authoritative RFM segment."""
    assert df_intel["rfm_segment"].notna().all()
    assert df_intel["rfm_segment"].isin(SEGMENT_PRIORITY_ORDER).all()


def test_segment_counts_reconcile(df_intel):
    """Verify that segment customer counts sum exactly to 10,000."""
    seg_counts = df_intel["rfm_segment"].value_counts()
    assert seg_counts.sum() == EXPECTED_CUSTOMER_COUNT
    assert len(seg_counts) == len(SEGMENT_PRIORITY_ORDER)


def test_cluster_assignments_are_complete(df_intel):
    """Verify that every customer has an assigned cluster in range 0..K-1."""
    assert df_intel["cluster_id"].notna().all()
    assert set(df_intel["cluster_id"].unique()) == set(range(SELECTED_K))
    assert df_intel["cluster_label"].notna().all()
    assert df_intel["cluster_description"].notna().all()


def test_cluster_counts_reconcile(df_intel):
    """Verify cluster headcounts sum exactly to 10,000."""
    cluster_counts = df_intel["cluster_id"].value_counts()
    assert cluster_counts.sum() == EXPECTED_CUSTOMER_COUNT
    assert len(cluster_counts) == SELECTED_K


def test_segment_cluster_matrix_reconciles(dataset_paths):
    """Verify the segment x cluster cross-tabulation reconciles to 10,000."""
    df_matrix = pd.read_csv(dataset_paths["matrix"])
    grand_total_row = df_matrix[df_matrix["Segment"] == "Grand Total"]
    assert len(grand_total_row) == 1
    assert grand_total_row["Total Customers"].iloc[0] == EXPECTED_CUSTOMER_COUNT
    assert grand_total_row["Customer Share (%)"].iloc[0] == 100.0


def test_revenue_reconciles(df_intel):
    """Verify total delivered revenue reconciles exactly to Phase 3 baseline."""
    total_rev = df_intel["delivered_revenue"].sum()
    diff = abs(total_rev - EXPECTED_TOTAL_DELIVERED_REVENUE)
    assert diff < 0.01, f"Delivered revenue mismatch: ${total_rev:,.2f} vs expected ${EXPECTED_TOTAL_DELIVERED_REVENUE:,.2f}"


def test_summary_outputs_exist(dataset_paths):
    """Verify that all 5 analytical summary CSVs and quality report exist."""
    expected_keys = ["value_sum", "segment_sum", "cluster_sum", "matrix", "behavior", "quality"]
    for k in expected_keys:
        p = dataset_paths[k]
        assert os.path.exists(p), f"Summary output missing: {p}"
        assert os.path.getsize(p) > 50, f"Summary output is empty: {p}"


def test_pipeline_is_deterministic():
    """Verify pipeline builds identical dataset on consecutive runs."""
    df_analytics, df_clusters = load_and_validate_inputs()
    run1 = build_customer_intelligence_dataset(df_analytics, df_clusters)
    run2 = build_customer_intelligence_dataset(df_analytics, df_clusters)
    pd.testing.assert_frame_equal(run1, run2)


def test_quality_report_all_passed(dataset_paths):
    """Verify that customer_intelligence_quality_report.csv has 100% PASSED checks."""
    df_q = pd.read_csv(dataset_paths["quality"])
    assert len(df_q) >= 18, f"Expected at least 18 quality checks, found {len(df_q)}"
    failed = df_q[df_q["status"] != "PASSED"]
    assert len(failed) == 0, f"Failed quality checks: {failed['check_name'].tolist()}"


def test_documentation_report_exists_and_complete(dataset_paths):
    """Verify that docs/customer_intelligence_report.md exists and is complete."""
    p = dataset_paths["report"]
    assert os.path.exists(p), f"Documentation report missing at {p}"
    content = open(p, "r", encoding="utf-8").read()
    assert len(content) > 2000, "Report content is too short"
    for i in range(1, 15):
        assert f"## {i}." in content, f"Section {i} missing from report"
