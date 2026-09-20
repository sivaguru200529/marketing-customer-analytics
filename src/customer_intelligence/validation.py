"""
Aura Retail Analytics - Phase 4 Part 3
Comprehensive Data Quality Validation & Invariant Auditing for Customer Intelligence.
"""

import os
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

from src.customer_intelligence.config import (
    DEFAULT_OUTPUT_DIR,
    EXPECTED_CUSTOMER_COUNT,
    EXPECTED_TOTAL_DELIVERED_REVENUE,
    OUTPUT_QUALITY_REPORT,
    SEGMENT_PRIORITY_ORDER,
    SELECTED_K,
)


def run_customer_intelligence_quality_checks(
    df_intel: pd.DataFrame,
    output_path: str = OUTPUT_QUALITY_REPORT,
) -> Tuple[bool, pd.DataFrame]:
    """
    Run 18 rigorous quality invariant checks on the customer intelligence dataset.
    
    Returns:
        Tuple of (all_passed, df_report).
    """
    checks: List[Dict[str, str]] = []

    def record_check(name: str, expected: str, actual: str, passed: bool, details: str):
        checks.append({
            "check_name": name,
            "expected": expected,
            "actual": actual,
            "status": "PASSED" if passed else "FAILED",
            "details": details,
        })

    # 1. Customer Population Count
    cust_count = len(df_intel)
    record_check(
        name="customer_population_count",
        expected=f"{EXPECTED_CUSTOMER_COUNT}",
        actual=f"{cust_count}",
        passed=(cust_count == EXPECTED_CUSTOMER_COUNT),
        details="Verified row count equals exact expected population.",
    )

    # 2. Customer ID Uniqueness
    unique_ids = df_intel["customer_id"].nunique()
    record_check(
        name="customer_id_uniqueness",
        expected="10,000 unique IDs",
        actual=f"{unique_ids} unique IDs",
        passed=(unique_ids == EXPECTED_CUSTOMER_COUNT and not df_intel["customer_id"].duplicated().any()),
        details="Primary key customer_id is 100% distinct with zero duplicates.",
    )

    # 3. Exactly One Row Per Customer
    one_row = (cust_count == unique_ids)
    record_check(
        name="one_row_per_customer",
        expected="1 row = 1 customer",
        actual="1 row = 1 customer" if one_row else "Multiple rows detected",
        passed=one_row,
        details="Dataset grain strictly verified at individual customer level.",
    )

    # 4. Null Auditing (Expected vs. Unexpected)
    null_counts = df_intel.isna().sum()
    unexpected_null_cols = [col for col, cnt in null_counts.items() if cnt > 0 and col != "delivered_aov"]
    delivered_aov_nulls = int(null_counts.get("delivered_aov", 0))
    zero_delivered_count = int(df_intel["delivered_orders"].eq(0).sum())
    
    aov_nulls_valid = (delivered_aov_nulls == zero_delivered_count)
    no_unexpected_nulls = (len(unexpected_null_cols) == 0 and aov_nulls_valid)
    record_check(
        name="null_values_audit",
        expected="Nulls only in delivered_aov when delivered_orders == 0 (860 rows)",
        actual=f"{delivered_aov_nulls} in delivered_aov, {len(unexpected_null_cols)} unexpected columns",
        passed=no_unexpected_nulls,
        details="No unexpected nulls in any feature; delivered_aov nulls match 0 delivered orders exactly.",
    )

    # 5. Finite Numeric Features (No NaN / +inf / -inf in non-null fields)
    numeric_cols = df_intel.select_dtypes(include=[np.number]).columns
    inf_cols = [c for c in numeric_cols if np.isinf(df_intel[c]).any()]
    record_check(
        name="finite_numeric_features",
        expected="Zero infinite values across all numeric columns",
        actual=f"{len(inf_cols)} columns with inf values",
        passed=(len(inf_cols) == 0),
        details="All numeric variables are finite real numbers.",
    )

    # 6. Non-Negative Revenues
    rev_valid = (df_intel["gross_revenue"] >= 0).all() and (df_intel["delivered_revenue"] >= 0).all()
    record_check(
        name="non_negative_revenues",
        expected="gross_revenue >= 0 and delivered_revenue >= 0",
        actual=f"Min gross: {df_intel['gross_revenue'].min():.2f}, min deliv: {df_intel['delivered_revenue'].min():.2f}",
        passed=bool(rev_valid),
        details="Revenues non-negative across entire customer base.",
    )

    # 7. Non-Negative Order Counts
    orders_valid = (
        (df_intel["total_orders"] >= 0).all()
        and (df_intel["delivered_orders"] >= 0).all()
        and (df_intel["returned_orders"] >= 0).all()
        and (df_intel["cancelled_orders"] >= 0).all()
    )
    record_check(
        name="non_negative_order_counts",
        expected="All order counts >= 0",
        actual="All order counts >= 0" if orders_valid else "Negative order count found",
        passed=bool(orders_valid),
        details="Order volume non-negative across all stages.",
    )

    # 8. Order Realization Integrity (total_orders == delivered + returned + cancelled)
    order_sum_match = (
        df_intel["total_orders"]
        == (df_intel["delivered_orders"] + df_intel["returned_orders"] + df_intel["cancelled_orders"])
    ).all()
    record_check(
        name="order_volume_reconciliation",
        expected="total_orders == delivered + returned + cancelled",
        actual="100% matched" if order_sum_match else "Order sum mismatch detected",
        passed=bool(order_sum_match),
        details="Delivered, returned, and cancelled order components sum exactly to total orders.",
    )

    # 9. Non-Negative Recency
    recency_valid = (df_intel["recency_days"] >= 0).all() and (df_intel["recency_days"] <= 730).all()
    record_check(
        name="recency_days_range",
        expected="recency_days in [0, 730]",
        actual=f"Range: [{df_intel['recency_days'].min()}, {df_intel['recency_days'].max()}]",
        passed=bool(recency_valid),
        details="Recency values span legitimate 24-month horizon relative to anchor 2025-12-31.",
    )

    # 10. Rate Metrics in [0, 1]
    rate_cols = ["order_delivery_rate", "return_rate", "cancellation_rate", "cart_abandonment_rate"]
    rates_valid = all(
        ((df_intel[c] >= 0.0) & (df_intel[c] <= 1.0)).all()
        for c in rate_cols
    )
    record_check(
        name="rate_metrics_bounded",
        expected="All rate columns bounded in [0.0, 1.0]",
        actual="Bounded in [0.0, 1.0]" if rates_valid else "Out of bounds rate found",
        passed=bool(rates_valid),
        details="Friction, delivery, and cart abandonment rates properly normalized.",
    )

    # 11. RFM Score Ranges
    r_valid = df_intel["r_score"].isin([1, 2, 3, 4, 5]).all()
    f_valid = df_intel["f_score"].isin([1, 2, 3, 4, 5]).all()
    m_valid = df_intel["m_score"].isin([1, 2, 3, 4, 5]).all()
    record_check(
        name="rfm_individual_scores_range",
        expected="r_score, f_score, m_score in {1, 2, 3, 4, 5}",
        actual="All in {1, 2, 3, 4, 5}" if (r_valid and f_valid and m_valid) else "Invalid score found",
        passed=bool(r_valid and f_valid and m_valid),
        details="Authoritative individual scores strictly confined to integers 1 through 5.",
    )

    # 12. RFM Total Score Math
    rfm_math_valid = (df_intel["rfm_total_score"] == (df_intel["r_score"] + df_intel["f_score"] + df_intel["m_score"])).all()
    rfm_range_valid = ((df_intel["rfm_total_score"] >= 3) & (df_intel["rfm_total_score"] <= 15)).all()
    record_check(
        name="rfm_total_score_math",
        expected="rfm_total_score == r + f + m and in [3, 15]",
        actual=f"Range: [{df_intel['rfm_total_score'].min()}, {df_intel['rfm_total_score'].max()}]",
        passed=bool(rfm_math_valid and rfm_range_valid),
        details="Composite RFM total verified as exact algebraic sum.",
    )

    # 13. RFM Score String Representation
    str_valid = df_intel["rfm_score"].str.match(r"^[1-5]{3}$").all()
    record_check(
        name="rfm_string_representation",
        expected="3-character string with digits 1-5 (e.g. '555')",
        actual="100% match regex ^[1-5]{3}$" if str_valid else "Invalid string found",
        passed=bool(str_valid),
        details="Categorical RFM descriptor matches 3-digit format.",
    )

    # 14. Segment Completeness & Reconciliation
    seg_counts = df_intel["rfm_segment"].value_counts()
    seg_sum = int(seg_counts.sum())
    seg_complete = (seg_sum == EXPECTED_CUSTOMER_COUNT and df_intel["rfm_segment"].notna().all())
    seg_valid = df_intel["rfm_segment"].isin(SEGMENT_PRIORITY_ORDER).all()
    record_check(
        name="segment_assignment_completeness",
        expected="10,000 customers assigned to 8 authoritative segments",
        actual=f"{seg_sum} assigned across {len(seg_counts)} segments",
        passed=bool(seg_complete and seg_valid),
        details="All customers uniquely categorized by Phase 3 decision tree.",
    )

    # 15. Cluster Completeness & Reconciliation
    cluster_counts = df_intel["cluster_id"].value_counts()
    cluster_sum = int(cluster_counts.sum())
    cluster_valid = (
        cluster_sum == EXPECTED_CUSTOMER_COUNT
        and set(df_intel["cluster_id"].unique()) == set(range(SELECTED_K))
        and df_intel["cluster_label"].notna().all()
    )
    record_check(
        name="cluster_assignment_completeness",
        expected=f"10,000 customers assigned across K={SELECTED_K} clusters (0, 1, 2)",
        actual=f"{cluster_sum} assigned across {len(cluster_counts)} clusters",
        passed=bool(cluster_valid),
        details="K-Means cluster assignments fully populated with neutral labels.",
    )

    # 16. Revenue Reconciliation Against Phase 3
    total_delivered_rev = float(df_intel["delivered_revenue"].sum())
    diff = abs(total_delivered_rev - EXPECTED_TOTAL_DELIVERED_REVENUE)
    rev_reconciled = (diff < 0.01)
    record_check(
        name="delivered_revenue_reconciliation",
        expected=f"${EXPECTED_TOTAL_DELIVERED_REVENUE:,.2f}",
        actual=f"${total_delivered_rev:,.2f} (diff=${diff:.4f})",
        passed=rev_reconciled,
        details="Total delivered revenue reconciles exactly to Phase 3 customer analytics.",
    )

    # 17. Deterministic Behavioral Bands Completeness
    bands_complete = (
        df_intel["customer_value_band"].notna().all()
        and df_intel["engagement_band"].notna().all()
        and df_intel["friction_band"].notna().all()
    )
    record_check(
        name="behavioral_bands_completeness",
        expected="Value, engagement, and friction bands 100% assigned (0 nulls)",
        actual="100% assigned" if bands_complete else "Missing band assignments",
        passed=bool(bands_complete),
        details="Derived classification bands fully populated with transparent rules.",
    )

    # 18. Cross-Tabulation Matrix Reconciliation
    ct = pd.crosstab(df_intel["rfm_segment"], df_intel["cluster_label"])
    matrix_sum = int(ct.values.sum())
    record_check(
        name="matrix_reconciliation",
        expected="Cross-tabulation sum equals 10,000",
        actual=f"Matrix sum = {matrix_sum}",
        passed=(matrix_sum == EXPECTED_CUSTOMER_COUNT),
        details="Segment x Cluster matrix reconciles 100% across all rows and columns.",
    )

    df_report = pd.DataFrame(checks)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_report.to_csv(output_path, index=False)

    all_passed = (df_report["status"] == "PASSED").all()
    return bool(all_passed), df_report
