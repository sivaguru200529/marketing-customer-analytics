"""
Aura Retail Analytics - Phase 4 Part 1
Automated Test Suite for Python EDA & Data Quality Layer.

Validates dataset existence, schemas, row counts, grains, numeric sanity,
temporal continuity, summary outputs, visualizations, and deterministic execution.
"""

import os
import pandas as pd
import pytest

from src.eda.loader import (
    DATASET_FILENAMES,
    REQUIRED_COLUMNS,
    GRAIN_KEYS,
    get_default_data_dir,
    load_dataset,
    load_all_analytics_datasets,
    get_dataset_profiles,
)
from src.eda.quality import (
    audit_completeness,
    audit_uniqueness,
    audit_numeric_ranges,
    audit_temporal_continuity,
    run_full_data_quality_audit,
)
from src.eda.customer_eda import analyze_customer_metrics
from src.eda.product_eda import analyze_product_metrics
from src.eda.revenue_eda import analyze_revenue_metrics
from src.eda.marketing_eda import analyze_marketing_metrics
from src.eda.cohort_eda import analyze_cohort_metrics
from src.eda.kpi_eda import analyze_business_kpis
from src.eda.run_eda import run_eda_pipeline, get_workspace_dir


@pytest.fixture(scope="module")
def loaded_datasets():
    """Load and yield all 6 analytical datasets once for read-only test assertions."""
    return load_all_analytics_datasets()


def test_required_datasets_exist():
    """Verify that all 6 required Phase 3 CSV files exist under data/03_analytics/."""
    data_dir = get_default_data_dir()
    for name, filename in DATASET_FILENAMES.items():
        file_path = os.path.join(data_dir, filename)
        assert os.path.isfile(file_path), f"Required Phase 3 file '{filename}' missing at {file_path}"
        assert os.path.getsize(file_path) > 0, f"File '{filename}' is empty."


def test_required_columns_exist(loaded_datasets):
    """Verify that each loaded dataset contains all expected production columns."""
    for name, df in loaded_datasets.items():
        expected = REQUIRED_COLUMNS[name]
        for col in expected:
            assert col in df.columns, f"Column '{col}' missing from dataset '{name}'"


def test_expected_row_counts_and_grains(loaded_datasets):
    """Verify exact expected row counts and table dimensions."""
    assert len(loaded_datasets["customer_analytics"]) == 10000, "customer_analytics must have 10,000 rows."
    assert len(loaded_datasets["product_analytics"]) == 150, "product_analytics must have 150 rows."
    assert len(loaded_datasets["monthly_revenue"]) == 24, "monthly_revenue must have 24 rows."
    assert len(loaded_datasets["marketing_performance"]) == 6, "marketing_performance must have 6 rows."
    assert len(loaded_datasets["cohort_retention"]) == 300, "cohort_retention must have 300 rows."
    assert len(loaded_datasets["business_kpis"]) == 1, "business_kpis must have exactly 1 row."


def test_no_unexpected_duplicate_keys(loaded_datasets):
    """Verify that each dataset's primary grain is 100% unique without duplicate keys."""
    uniqueness_df = audit_uniqueness(loaded_datasets)
    for _, row in uniqueness_df.iterrows():
        assert row["uniqueness_passed"] is True, (
            f"Grain uniqueness violation in '{row['dataset']}': "
            f"{row['duplicate_grain_rows']} duplicates found for grain {row['grain_definition']}."
        )


def test_numeric_validation(loaded_datasets):
    """Verify numeric boundaries: non-negativity, margins, valid rates, and RFM scores."""
    numeric_df = audit_numeric_ranges(loaded_datasets)
    failed_checks = numeric_df[~numeric_df["passed"]]
    assert len(failed_checks) == 0, f"Numeric sanity checks failed:\n{failed_checks.to_string()}"


def test_date_month_validation(loaded_datasets):
    """Verify date boundaries and continuous 24-month horizon without skipped intervals."""
    temporal_df = audit_temporal_continuity(loaded_datasets)
    for _, row in temporal_df.iterrows():
        assert row["status"] == "PASSED", (
            f"Temporal continuity check failed for '{row['dataset']}': "
            f"Expected {row['expected_periods']}, got {row['actual_periods']}."
        )


def test_kpi_dataset_has_one_row(loaded_datasets):
    """Verify that the business KPI dataset conforms strictly to a single-row executive scorecard."""
    kpi_df = loaded_datasets["business_kpis"]
    assert len(kpi_df) == 1
    assert kpi_df["total_registered_customers"].iloc[0] == 10000
    assert kpi_df["active_ordering_customers"].iloc[0] == 10000
    assert round(kpi_df["total_gross_billed_revenue"].iloc[0], 2) == 17009287.54
    assert round(kpi_df["total_delivered_revenue"].iloc[0], 2) == 14584810.24
    assert round(kpi_df["total_marketing_spend_usd"].iloc[0], 2) == 2224153.85


def test_cohort_grain_is_unique(loaded_datasets):
    """Verify that cohort retention contains 300 unique (cohort_month, activity_month) combinations."""
    cr = loaded_datasets["cohort_retention"]
    dupes = cr.duplicated(subset=["cohort_month", "activity_month"], keep=False).sum()
    assert dupes == 0
    assert len(cr) == 300
    # Exactly 24 unique cohorts
    assert cr["cohort_month"].nunique() == 24


def test_summary_outputs_are_generated():
    """Verify that all 7 required summary CSVs exist and contain non-empty data."""
    workspace = get_workspace_dir()
    summaries_dir = os.path.join(workspace, "data", "04_eda", "summaries")

    expected_summaries = [
        "data_quality_report.csv",
        "customer_summary.csv",
        "product_summary.csv",
        "revenue_summary.csv",
        "marketing_summary.csv",
        "cohort_summary.csv",
        "business_kpi_summary.csv",
    ]

    for summary_file in expected_summaries:
        path = os.path.join(summaries_dir, summary_file)
        assert os.path.isfile(path), f"Expected summary file '{summary_file}' not found at {path}"
        df = pd.read_csv(path)
        assert len(df) > 0, f"Summary file '{summary_file}' is empty."


def test_all_figures_exist_and_valid():
    """Verify that all 14 visualization figures exist and are non-empty image files."""
    workspace = get_workspace_dir()
    figures_dir = os.path.join(workspace, "data", "04_eda", "figures")

    expected_figures = [
        "customer_revenue_distribution.png",
        "customer_order_frequency_distribution.png",
        "rfm_segment_distribution.png",
        "product_revenue_by_category.png",
        "product_gross_margin_by_category.png",
        "product_revenue_distribution.png",
        "monthly_revenue_trend.png",
        "monthly_mom_growth.png",
        "cumulative_revenue.png",
        "marketing_channel_spend.png",
        "marketing_channel_roas.png",
        "marketing_channel_cac.png",
        "marketing_channel_ctr.png",
        "cohort_retention_heatmap.png",
    ]

    for fig_file in expected_figures:
        path = os.path.join(figures_dir, fig_file)
        assert os.path.isfile(path), f"Expected chart '{fig_file}' not found at {path}"
        assert os.path.getsize(path) > 5000, f"Chart '{fig_file}' is smaller than expected (<5KB)."


def test_eda_report_exists_and_complete():
    """Verify that docs/eda_report.md exists and contains all required analytical sections."""
    workspace = get_workspace_dir()
    report_path = os.path.join(workspace, "docs", "eda_report.md")
    assert os.path.isfile(report_path), f"Report missing at {report_path}"

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    required_sections = [
        "## 1. Executive Objective",
        "## 2. Data Sources",
        "## 3. Dataset Dimensions",
        "## 4. Data Quality Findings",
        "## 5. Customer Behavior",
        "## 6. Product Catalog",
        "## 7. Monthly Revenue",
        "## 8. Marketing Channel Performance",
        "## 9. Cohort Retention Dynamics",
        "## 10. Business KPI Summary",
        "## 11. Initial Factual Business Observations",
        "## 12. Methodological Limitations",
        "## 13. Reproducibility Instructions",
    ]

    for sec in required_sections:
        assert sec in content, f"Required section header '{sec}' not found in docs/eda_report.md"


def test_deterministic_reproducibility(loaded_datasets):
    """Verify that multiple executions against identical Phase 3 inputs produce deterministic results."""
    m1, s1, _ = analyze_customer_metrics(loaded_datasets["customer_analytics"])
    m2, s2, _ = analyze_customer_metrics(loaded_datasets["customer_analytics"])
    assert m1 == m2
    pd.testing.assert_frame_equal(s1, s2)

    r1, _ = analyze_revenue_metrics(loaded_datasets["monthly_revenue"])
    r2, _ = analyze_revenue_metrics(loaded_datasets["monthly_revenue"])
    assert r1 == r2


def test_eda_pipeline_run_completes():
    """Verify that the pipeline completes cleanly and returns artifact paths."""
    res = run_eda_pipeline(generate_charts=False)
    assert isinstance(res, dict)
    assert "data_quality_report" in res
    assert os.path.isfile(res["data_quality_report"])
