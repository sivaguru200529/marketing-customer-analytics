"""
Aura Retail Analytics - Automated Database Integration Tests
Validates connectivity, schema structure, row counts, constraints, and data parity.
Non-destructive test suite.
"""

import pytest
from src.database.connection import get_db_connection, test_connection as check_connection
from src.database.schema import EXPECTED_TABLES, verify_schema_objects
from src.database.validators import (
    EXPECTED_ROW_COUNTS,
    compare_csv_vs_db,
    validate_check_constraints,
    validate_date_integrity,
    validate_foreign_keys,
    validate_primary_keys,
    validate_row_counts,
)


@pytest.fixture(scope="module")
def db_conn():
    """Yield a shared read connection for test assertions."""
    ok, msg = check_connection()
    if not ok:
        pytest.skip(f"PostgreSQL container is not reachable: {msg}")

    with get_db_connection(autocommit=True) as conn:
        yield conn


def test_database_connection():
    """Verify PostgreSQL connectivity and server responsiveness."""
    ok, msg = check_connection()
    assert ok is True, f"Connection failed: {msg}"
    assert "aura_retail_db" in msg
    assert "PostgreSQL 16" in msg


def test_schema_exists(db_conn):
    """Verify that the dedicated 'aura_retail' schema exists."""
    with db_conn.cursor() as cur:
        cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'aura_retail';")
        row = cur.fetchone()
        assert row is not None, "Schema 'aura_retail' does not exist in PostgreSQL."
        assert row[0] == "aura_retail"


def test_tables_exist():
    """Verify that all 7 required core tables exist under 'aura_retail'."""
    tables = verify_schema_objects(schema_name="aura_retail")
    for tbl in EXPECTED_TABLES:
        assert tbl in tables, f"Expected table '{tbl}' was not found in aura_retail schema."


def test_table_row_counts(db_conn):
    """Verify that each table contains the exact validated Phase 2 row count."""
    results = validate_row_counts(db_conn, schema_name="aura_retail")
    for table, info in results.items():
        assert info["passed"] is True, (
            f"Row count mismatch for {table}: expected {info['expected']}, got {info['actual']}"
        )


def test_primary_key_uniqueness(db_conn):
    """Verify 100% primary key uniqueness (zero duplicates) across all tables."""
    results = validate_primary_keys(db_conn, schema_name="aura_retail")
    for table, info in results.items():
        assert info["passed"] is True, (
            f"Duplicate primary keys detected in {table}.{info['pk_column']}: {info['duplicates']} duplicates"
        )


def test_foreign_key_referential_integrity(db_conn):
    """Verify zero orphan records across all defined foreign-key relationships."""
    results = validate_foreign_keys(db_conn, schema_name="aura_retail")
    for rel_name, info in results.items():
        assert info["passed"] is True, (
            f"Foreign key integrity failed for {rel_name}: found {info['orphan_count']} orphan records"
        )


def test_check_constraints(db_conn):
    """Verify business check constraints across monetary, count, and status fields."""
    results = validate_check_constraints(db_conn, schema_name="aura_retail")
    for name, info in results.items():
        assert info["passed"] is True, (
            f"Check constraint violation for {name}: found {info['violations']} invalid rows"
        )


def test_date_integrity(db_conn):
    """Verify that dates fall within 2024-2025 and orders occur after signup."""
    results = validate_date_integrity(db_conn, schema_name="aura_retail")
    assert results["date_bounds"]["passed"] is True, f"Date bounds invalid: {results['date_bounds']}"
    assert results["order_after_signup"]["passed"] is True, (
        f"Temporal anomaly: {results['order_after_signup']['violations']} orders placed before customer signup"
    )


def test_csv_database_parity(db_conn):
    """Verify exact parity between raw CSV files and loaded PostgreSQL tables."""
    parity = compare_csv_vs_db(db_conn, schema_name="aura_retail")
    for table, info in parity.items():
        assert info["rows_match"] is True, (
            f"Row count disparity for {table}: CSV={info['csv_rows']}, DB={info['db_rows']}"
        )
        assert info["pks_match"] is True, (
            f"PK distinct count disparity for {table}: CSV={info['csv_distinct_pk']}, DB={info['db_distinct_pk']}"
        )
        if "amount_match" in info:
            assert info["amount_match"] is True, (
                f"Gross revenue disparity in {table}: CSV={info['csv_total_order_amount']}, DB={info['db_total_order_amount']}"
            )
        if "line_total_match" in info:
            assert info["line_total_match"] is True, (
                f"Line item total disparity in {table}: CSV={info['csv_line_total_sum']}, DB={info['db_line_total_sum']}"
            )
        if "spend_match" in info:
            assert info["spend_match"] is True, (
                f"Marketing spend disparity in {table}: CSV={info['csv_spend_usd_sum']}, DB={info['db_spend_usd_sum']}"
            )
