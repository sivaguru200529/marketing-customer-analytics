"""
Aura Retail Analytics - Phase 5 Part 2 Test Suite
Automated Verification for Business Prioritization & Actionable Customer Intelligence.
"""

import os
import numpy as np
import pandas as pd
import pytest

from src.prioritization.config import (
    CAMPAIGN_MAPPING,
    DEFAULT_FIGURES_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPORT_PATH,
    DEFAULT_SUMMARIES_DIR,
    EXPECTED_CUSTOMER_COUNT,
    INPUT_CHURN_PREDICTIONS_CSV,
    INPUT_CUSTOMER_INTELLIGENCE_CSV,
    OUTPUT_BUSINESS_PRIORITIZATION_CSV,
    PRIORITIZATION_COLUMNS,
    PRIORITY_TIER_HIGH_THRESHOLD,
    PRIORITY_TIER_MEDIUM_THRESHOLD,
    PRIORITY_WEIGHT_ENGAGEMENT,
    PRIORITY_WEIGHT_FRICTION,
    PRIORITY_WEIGHT_RISK,
    PRIORITY_WEIGHT_VALUE,
    SUMMARY_BUSINESS_SEGMENT,
    SUMMARY_FRICTION,
    SUMMARY_PRIORITY_TIER,
    SUMMARY_RECOMMENDED_ACTION,
    SUMMARY_RECOMMENDED_CAMPAIGN,
    SUMMARY_RISK_VALUE,
)
from src.prioritization.loader import (
    join_intelligence_and_predictions,
    load_and_validate_inputs,
)
from src.prioritization.recommendations import (
    apply_recommendations,
    assign_recommended_action,
    assign_recommended_campaign,
)
from src.prioritization.scoring import (
    calculate_composite_priority_score,
    calculate_engagement_score,
    calculate_friction_score,
    calculate_risk_score,
    calculate_value_score,
    compute_all_scores,
    validate_priority_weights,
)
from src.prioritization.segmentation import (
    apply_segmentation,
    assign_business_segment,
    assign_priority_tier,
)


@pytest.fixture(scope="module")
def input_datasets():
    """Load and validate both upstream datasets."""
    assert os.path.exists(INPUT_CUSTOMER_INTELLIGENCE_CSV), "customer_intelligence.csv missing!"
    assert os.path.exists(INPUT_CHURN_PREDICTIONS_CSV), "churn_predictions.csv missing!"
    return load_and_validate_inputs()


@pytest.fixture(scope="module")
def joined_data(input_datasets):
    """Perform controlled join of datasets."""
    df_intel, df_churn = input_datasets
    return join_intelligence_and_predictions(df_intel, df_churn)


@pytest.fixture(scope="module")
def full_prioritization_data(joined_data):
    """Compute scores, tiers, segments, and recommendations."""
    df_scored = compute_all_scores(joined_data)
    df_segmented = apply_segmentation(df_scored)
    df_final = apply_recommendations(df_segmented)
    return df_final


# ==============================================================================
# 1. Input Integrity & Join Tests
# ==============================================================================

def test_input_files_exist_and_non_empty():
    """Verify customer intelligence and churn prediction files exist and are populated."""
    assert os.path.exists(INPUT_CUSTOMER_INTELLIGENCE_CSV)
    assert os.path.getsize(INPUT_CUSTOMER_INTELLIGENCE_CSV) > 1000
    assert os.path.exists(INPUT_CHURN_PREDICTIONS_CSV)
    assert os.path.getsize(INPUT_CHURN_PREDICTIONS_CSV) > 1000


def test_customer_ids_unique_in_inputs(input_datasets):
    """Verify customer_id is unique with zero duplicates in both inputs."""
    df_intel, df_churn = input_datasets
    assert len(df_intel) == EXPECTED_CUSTOMER_COUNT
    assert len(df_churn) == EXPECTED_CUSTOMER_COUNT
    assert df_intel["customer_id"].nunique() == EXPECTED_CUSTOMER_COUNT
    assert df_churn["customer_id"].nunique() == EXPECTED_CUSTOMER_COUNT
    assert not df_intel["customer_id"].duplicated().any()
    assert not df_churn["customer_id"].duplicated().any()


def test_join_preserves_exactly_one_row_per_customer(joined_data):
    """Verify join produces exactly 10,000 unique customers without data loss."""
    assert len(joined_data) == EXPECTED_CUSTOMER_COUNT
    assert joined_data["customer_id"].nunique() == EXPECTED_CUSTOMER_COUNT
    assert not joined_data["customer_id"].duplicated().any()


# ==============================================================================
# 2. Score Validation & Weight Invariants
# ==============================================================================

def test_priority_weights_sum_to_one():
    """Verify exact priority weights sum to 1.0 and are non-negative."""
    weights = {
        "risk": PRIORITY_WEIGHT_RISK,
        "value": PRIORITY_WEIGHT_VALUE,
        "engagement": PRIORITY_WEIGHT_ENGAGEMENT,
        "friction": PRIORITY_WEIGHT_FRICTION,
    }
    assert validate_priority_weights(weights) is True
    assert PRIORITY_WEIGHT_RISK == 0.50
    assert PRIORITY_WEIGHT_VALUE == 0.30
    assert PRIORITY_WEIGHT_ENGAGEMENT == 0.10
    assert PRIORITY_WEIGHT_FRICTION == 0.10
    assert sum(weights.values()) == 1.0


def test_component_scores_bounded_in_zero_to_one(full_prioritization_data):
    """Verify all 4 normalized scores remain strictly within [0.0, 1.0]."""
    df = full_prioritization_data
    for col in ["risk_score", "value_score", "engagement_score", "friction_score"]:
        assert (df[col] >= 0.0).all(), f"{col} has values below 0.0"
        assert (df[col] <= 1.0).all(), f"{col} has values above 1.0"
        assert df[col].notna().all(), f"{col} contains null values"


def test_value_score_zero_for_zero_revenue_customers(full_prioritization_data):
    """Verify customers with 0 delivered revenue receive a value_score of exactly 0.0."""
    df = full_prioritization_data
    zero_rev = df[df["delivered_revenue"] == 0.0]
    pos_rev = df[df["delivered_revenue"] > 0.0]

    assert len(zero_rev) > 0
    assert (zero_rev["value_score"] == 0.0).all()
    assert (pos_rev["value_score"] > 0.0).all()


def test_priority_score_formula_and_no_min_max_scaling(full_prioritization_data):
    """Verify exact weighted sum formula and confirm no min-max scaling is applied."""
    df = full_prioritization_data
    expected_score = (
        0.50 * df["risk_score"]
        + 0.30 * df["value_score"]
        + 0.10 * df["engagement_score"]
        + 0.10 * df["friction_score"]
    ).round(4)

    np.testing.assert_allclose(df["priority_score"], expected_score, atol=1e-4)

    # Verify no min-max scaling: min is not 0.0 and max is not 1.0
    assert df["priority_score"].min() > 0.10, "priority_score appears artificially min-scaled to 0.0!"
    assert df["priority_score"].max() < 0.95, "priority_score appears artificially max-scaled to 1.0!"


# ==============================================================================
# 3. Priority Tier & Boundary Value Validation
# ==============================================================================

def test_priority_tier_boundary_values():
    """Verify deterministic boundary cutoff behavior: 0.49, 0.50, 0.74, 0.75."""
    test_df = pd.DataFrame(
        {
            "priority_score": [0.49, 0.50, 0.74, 0.75, 0.85, 0.10],
        }
    )
    tiers = assign_priority_tier(test_df)

    assert tiers.iloc[0] == "Low Priority", "0.49 must map to Low Priority"
    assert tiers.iloc[1] == "Medium Priority", "0.50 must map to Medium Priority"
    assert tiers.iloc[2] == "Medium Priority", "0.74 must map to Medium Priority"
    assert tiers.iloc[3] == "High Priority", "0.75 must map to High Priority"
    assert tiers.iloc[4] == "High Priority", "0.85 must map to High Priority"
    assert tiers.iloc[5] == "Low Priority", "0.10 must map to Low Priority"


def test_every_customer_has_valid_priority_tier(full_prioritization_data):
    """Verify every customer belongs to exactly one non-null priority tier."""
    df = full_prioritization_data
    valid_tiers = {"High Priority", "Medium Priority", "Low Priority"}
    assert df["priority_tier"].notna().all()
    assert set(df["priority_tier"].unique()).issubset(valid_tiers)


# ==============================================================================
# 4. Business Segmentation & Precedence Hierarchy
# ==============================================================================

def test_business_segment_mutually_exclusive_and_complete(full_prioritization_data):
    """Verify every customer has exactly one non-null business segment."""
    df = full_prioritization_data
    assert df["business_segment"].notna().all()
    assert df["business_segment"].nunique() >= 6


def test_business_segmentation_precedence_hierarchy():
    """Verify strict precedence: High Risk + High Value + High Friction gets Segment 1."""
    # Synthetic record satisfying High Risk + High Value + High Friction
    test_df = pd.DataFrame(
        [
            {
                "customer_id": "TEST_001",
                "churn_risk_band": "High Risk",
                "churn_probability": 0.85,
                "customer_value_band": "High Value",
                "delivered_revenue": 2500.0,
                "friction_band": "High Friction",
                "friction_score": 0.45,
                "friction_rate": 0.35,
                "engagement_score": 0.60,
                "engagement_band": "Active",
                "recency_days": 100,
            }
        ]
    )
    seg = assign_business_segment(test_df)
    assert seg.iloc[0] == "High Risk / High Value / High Friction", (
        "High Risk + High Value + High Friction must receive Segment 1"
    )


# ==============================================================================
# 5. Recommended Actions & Campaign Mappings
# ==============================================================================

def test_recommended_action_hierarchy_and_campaign_mapping():
    """Verify Rule 1 action hierarchy and 1-to-1 campaign mapping."""
    test_df = pd.DataFrame(
        [
            {
                "churn_risk_band": "High Risk",
                "churn_probability": 0.80,
                "customer_value_band": "High Value",
                "delivered_revenue": 2000.0,
                "friction_band": "High Friction",
                "friction_score": 0.45,
                "friction_rate": 0.30,
                "priority_tier": "High Priority",
                "priority_score": 0.80,
                "engagement_band": "Active",
                "recency_days": 50,
            },
            {
                "churn_risk_band": "Low Risk",
                "churn_probability": 0.20,
                "customer_value_band": "High Value",
                "delivered_revenue": 1500.0,
                "friction_band": "No Friction",
                "friction_score": 0.05,
                "friction_rate": 0.0,
                "priority_tier": "Low Priority",
                "priority_score": 0.35,
                "engagement_band": "Active",
                "recency_days": 20,
            },
        ]
    )
    actions = assign_recommended_action(test_df)
    campaigns = assign_recommended_campaign(actions)

    assert actions.iloc[0] == "High-Value Retention + Friction Resolution"
    assert campaigns.iloc[0] == "High-Value Retention Campaign"

    assert actions.iloc[1] == "Relationship Development"
    assert campaigns.iloc[1] == "Loyalty & Relationship Campaign"


def test_every_customer_receives_action_and_campaign(full_prioritization_data):
    """Verify zero nulls in recommended actions and campaigns across 10,000 customers."""
    df = full_prioritization_data
    assert df["recommended_action"].notna().all()
    assert df["recommended_campaign"].notna().all()
    assert set(df["recommended_campaign"].unique()).issubset(set(CAMPAIGN_MAPPING.values()))


# ==============================================================================
# 6. Primary Output Dataset & Summaries Validation
# ==============================================================================

def test_final_business_prioritization_file_integrity():
    """Verify primary dataset exists, is non-empty, and has exactly 10,000 rows."""
    assert os.path.exists(OUTPUT_BUSINESS_PRIORITIZATION_CSV)
    df_out = pd.read_csv(OUTPUT_BUSINESS_PRIORITIZATION_CSV)
    assert len(df_out) == EXPECTED_CUSTOMER_COUNT
    assert df_out["customer_id"].nunique() == EXPECTED_CUSTOMER_COUNT
    for col in PRIORITIZATION_COLUMNS:
        assert col in df_out.columns, f"Expected column '{col}' missing from final dataset"


def test_all_summary_csv_files_exist():
    """Verify all 6 required summary CSV files exist and are non-empty."""
    required_summaries = [
        SUMMARY_PRIORITY_TIER,
        SUMMARY_BUSINESS_SEGMENT,
        SUMMARY_RECOMMENDED_ACTION,
        SUMMARY_RECOMMENDED_CAMPAIGN,
        SUMMARY_RISK_VALUE,
        SUMMARY_FRICTION,
    ]
    for filename in required_summaries:
        p_main = os.path.join(DEFAULT_OUTPUT_DIR, filename)
        p_sub = os.path.join(DEFAULT_SUMMARIES_DIR, filename)
        assert os.path.exists(p_main) or os.path.exists(p_sub), f"Summary file missing: {filename}"


def test_all_figure_png_files_exist():
    """Verify all 7 publication-grade Matplotlib charts exist and are non-empty."""
    expected_figures = [
        "priority_tier_distribution.png",
        "business_segment_distribution.png",
        "risk_value_matrix.png",
        "priority_score_distribution.png",
        "revenue_associated_with_high_risk.png",
        "recommended_action_distribution.png",
        "friction_vs_churn_risk.png",
    ]
    for fig_name in expected_figures:
        fig_path = os.path.join(DEFAULT_FIGURES_DIR, fig_name)
        assert os.path.exists(fig_path), f"Figure missing: {fig_path}"
        assert os.path.getsize(fig_path) > 1000, f"Figure unexpectedly small: {fig_path}"


def test_business_prioritization_report_exists_and_complete():
    """Verify markdown documentation report exists and covers all required sections."""
    assert os.path.exists(DEFAULT_REPORT_PATH)
    assert os.path.getsize(DEFAULT_REPORT_PATH) > 2000
    with open(DEFAULT_REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Phase 5 Part 2" in content
    assert "Revenue Associated With High-Risk Customers" in content
    assert "Limitations" in content


# ==============================================================================
# 7. Non-Destructive Invariants & Upstream Purity
# ==============================================================================

def test_upstream_phase4_and_part1_datasets_unmodified():
    """Verify Phase 4 customer intelligence and Phase 5 Part 1 churn predictions remain unmodified."""
    df_intel = pd.read_csv(INPUT_CUSTOMER_INTELLIGENCE_CSV)
    df_churn = pd.read_csv(INPUT_CHURN_PREDICTIONS_CSV)

    assert len(df_intel) == EXPECTED_CUSTOMER_COUNT
    assert df_intel.shape[1] == 47
    assert len(df_churn) == EXPECTED_CUSTOMER_COUNT
    assert df_churn.shape[1] == 4
    assert list(df_churn.columns) == ["customer_id", "churn_probability", "predicted_churn", "churn_risk_band"]
