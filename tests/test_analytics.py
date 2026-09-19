"""
Aura Retail Analytics - Automated SQL Analytics Integration Tests
Validates analytical views, calculations, RFM scoring, cohort retention, and exported CSVs.
"""

import os
import pandas as pd
import pytest

from src.analytics.export import ANALYTICAL_VIEWS, get_default_export_dir
from src.analytics.runner import EXPECTED_VIEWS, verify_analytical_views
from src.database.connection import get_db_connection, test_connection as check_connection


@pytest.fixture(scope="module")
def db_conn():
    """Yield a shared read connection for analytics assertions."""
    ok, msg = check_connection()
    if not ok:
        pytest.skip(f"PostgreSQL container is not reachable: {msg}")

    with get_db_connection(autocommit=True) as conn:
        yield conn


def test_analytics_connection():
    """Verify that PostgreSQL analytics environment is reachable."""
    ok, msg = check_connection()
    assert ok is True, f"Connection failed: {msg}"


def test_analytical_views_exist(db_conn):
    """Verify that all 6 required analytical views exist in aura_retail."""
    counts = verify_analytical_views()
    for view_name in EXPECTED_VIEWS:
        assert view_name in counts, f"View {view_name} missing from database."
        assert counts[view_name] > 0, f"View {view_name} has 0 rows."


def test_customer_analytics_view(db_conn):
    """Validate customer analytics view integrity, uniqueness, and RFM scores."""
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT 
                COUNT(*) AS total_rows,
                COUNT(DISTINCT customer_id) AS distinct_customers,
                MIN(recency_days) AS min_recency,
                MAX(recency_days) AS max_recency,
                MIN(r_score) AS min_r, MAX(r_score) AS max_r,
                MIN(f_score) AS min_f, MAX(f_score) AS max_f,
                MIN(m_score) AS min_m, MAX(m_score) AS max_m,
                COUNT(CASE WHEN rfm_segment IS NULL THEN 1 END) AS null_segments,
                COUNT(CASE WHEN gross_revenue < 0 THEN 1 END) AS negative_rev
            FROM aura_retail.view_customer_analytics;
        """)
        (
            total_rows, distinct_customers, min_recency, max_recency,
            min_r, max_r, min_f, max_f, min_m, max_m,
            null_segments, negative_rev
        ) = cur.fetchone()

    assert total_rows == 10000, f"Expected 10,000 customers, got {total_rows}"
    assert distinct_customers == 10000, "Duplicate customer_id in customer analytics view"
    assert min_recency >= 0, f"Negative recency days found: {min_recency}"
    assert max_recency <= 731, f"Recency exceeds maximum date horizon: {max_recency}"
    assert min_r >= 1 and max_r <= 5, "R_Score out of quintile range [1, 5]"
    assert min_f >= 1 and max_f <= 5, "F_Score out of quintile range [1, 5]"
    assert min_m >= 1 and max_m <= 5, "M_Score out of quintile range [1, 5]"
    assert null_segments == 0, f"Found {null_segments} unclassified RFM customers"
    assert negative_rev == 0, "Negative customer gross revenue detected"


def test_product_analytics_view(db_conn):
    """Validate product performance view economics, ranks, and margins."""
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT 
                COUNT(*) AS total_rows,
                COUNT(DISTINCT product_id) AS distinct_products,
                MIN(units_sold) AS min_units,
                MIN(gross_revenue) AS min_rev,
                MIN(gross_margin_pct) AS min_margin,
                MAX(gross_margin_pct) AS max_margin,
                MIN(category_revenue_rank) AS min_cat_rank,
                MIN(overall_revenue_rank) AS min_overall_rank
            FROM aura_retail.view_product_analytics;
        """)
        (
            total_rows, distinct_products, min_units, min_rev,
            min_margin, max_margin, min_cat_rank, min_overall_rank
        ) = cur.fetchone()

    assert total_rows == 150, f"Expected 150 catalog products, got {total_rows}"
    assert distinct_products == 150, "Duplicate product_id in product analytics view"
    assert min_units > 0, "Found product with 0 units sold"
    assert min_rev > 0, "Found product with 0 gross revenue"
    assert min_margin >= 0, f"Negative gross margin percentage detected: {min_margin}"
    assert max_margin <= 100, f"Margin exceeds 100%: {max_margin}"
    assert min_cat_rank == 1, "Category rank does not start at 1"
    assert min_overall_rank == 1, "Overall revenue rank does not start at 1"


def test_monthly_revenue_view(db_conn):
    """Validate monthly revenue time-series continuity, MoM calculations, and cumulative growth."""
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT 
                COUNT(*) AS month_count,
                MIN(order_month) AS first_month,
                MAX(order_month) AS last_month,
                MIN(delivered_revenue) AS min_rev,
                COUNT(CASE WHEN prev_month_delivered_revenue IS NULL THEN 1 END) AS null_prev_count,
                SUM(gross_billed_revenue) AS total_gross
            FROM aura_retail.view_monthly_revenue;
        """)
        month_count, first_month, last_month, min_rev, null_prev_count, total_gross = cur.fetchone()

    assert month_count == 24, f"Expected 24 monthly periods, got {month_count}"
    assert str(first_month) == "2024-01-01", f"First month should be 2024-01-01, got {first_month}"
    assert str(last_month) == "2025-12-01", f"Last month should be 2025-12-01, got {last_month}"
    assert min_rev > 0, "Found non-positive monthly delivered revenue"
    # Exactly month 1 should have NULL previous month
    assert null_prev_count == 1, f"Expected exactly 1 NULL previous month (month 1), got {null_prev_count}"
    assert abs(float(total_gross) - 17009287.54) < 0.05, f"Monthly gross total mismatch: {total_gross}"


def test_marketing_performance_view(db_conn):
    """Validate marketing channel KPIs, CTR, CPC, CAC, and ROAS calculations."""
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT 
                COUNT(*) AS total_channels,
                SUM(total_spend_usd) AS total_spend,
                MIN(ctr_pct) AS min_ctr,
                MAX(ctr_pct) AS max_ctr,
                COUNT(CASE WHEN total_impressions < total_clicks THEN 1 END) AS click_anomalies,
                COUNT(CASE WHEN channel_type = 'Paid' AND roas <= 0 THEN 1 END) AS zero_roas_paid
            FROM aura_retail.view_marketing_performance;
        """)
        total_channels, total_spend, min_ctr, max_ctr, click_anomalies, zero_roas_paid = cur.fetchone()

    assert total_channels == 6, f"Expected 6 marketing channels, got {total_channels}"
    assert abs(float(total_spend) - 2224153.85) < 0.05, f"Marketing spend mismatch: {total_spend}"
    assert min_ctr >= 0 and max_ctr <= 100, f"CTR out of bounds: [{min_ctr}, {max_ctr}]"
    assert click_anomalies == 0, "Found channels where clicks exceed impressions"
    assert zero_roas_paid == 0, "Found paid channels with non-positive ROAS"


def test_cohort_retention_view(db_conn):
    """Validate customer cohort purchase retention rates and timeline logic."""
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT 
                COUNT(DISTINCT cohort_month) AS cohort_count,
                MIN(months_since_signup) AS min_months,
                MAX(months_since_signup) AS max_months,
                MIN(purchase_retention_rate_pct) AS min_retention,
                MAX(purchase_retention_rate_pct) AS max_retention,
                COUNT(CASE WHEN months_since_signup < 0 THEN 1 END) AS temporal_anomalies
            FROM aura_retail.view_cohort_retention;
        """)
        cohort_count, min_months, max_months, min_retention, max_retention, temporal_anomalies = cur.fetchone()

    assert cohort_count == 24, f"Expected 24 monthly signup cohorts, got {cohort_count}"
    assert min_months == 0, f"Minimum months elapsed should be 0, got {min_months}"
    assert max_months <= 23, f"Maximum months elapsed exceeds 23: {max_months}"
    assert temporal_anomalies == 0, "Found activity before cohort signup month"
    assert min_retention >= 0, f"Negative retention rate: {min_retention}"
    assert max_retention <= 100, f"Retention rate exceeds 100%: {max_retention}"


def test_business_kpis_view(db_conn):
    """Validate centralized executive scorecard macro totals."""
    with db_conn.cursor() as cur:
        cur.execute("""
            SELECT 
                total_registered_customers,
                total_orders_placed,
                total_gross_billed_revenue,
                total_marketing_spend_usd,
                total_units_sold,
                estimated_gross_profit_usd,
                blended_roas
            FROM aura_retail.view_business_kpis;
        """)
        row = cur.fetchone()

    (
        total_customers, total_orders, gross_rev, total_spend,
        units_sold, gross_profit, blended_roas
    ) = row

    assert total_customers == 10000
    assert total_orders == 50000
    assert abs(float(gross_rev) - 17009287.54) < 0.05
    assert abs(float(total_spend) - 2224153.85) < 0.05
    assert units_sold > 100000
    assert gross_profit > 0
    assert blended_roas > 0


def test_exported_csv_datasets():
    """Verify that all 6 exported analytical CSV datasets exist and have expected row counts."""
    export_dir = get_default_export_dir()

    expected_specs = {
        "customer_analytics.csv": 10000,
        "product_analytics.csv": 150,
        "monthly_revenue.csv": 24,
        "marketing_performance.csv": 6,
        "cohort_retention.csv": 300,
        "business_kpis.csv": 1,
    }

    for filename, expected_rows in expected_specs.items():
        file_path = os.path.join(export_dir, filename)
        assert os.path.isfile(file_path), f"Exported file missing: {file_path}"
        assert os.path.getsize(file_path) > 0, f"Exported file is empty: {file_path}"

        df = pd.read_csv(file_path)
        assert len(df) == expected_rows, (
            f"Row count mismatch in {filename}: expected {expected_rows}, got {len(df)}"
        )
        assert not df.empty, f"Dataset {filename} is empty"
