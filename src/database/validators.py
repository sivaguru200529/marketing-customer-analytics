"""
Aura Retail Analytics - Database & Data Integrity Validators
Performs deep structural, referential, constraint, and CSV-to-Database parity validations.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from src.database.connection import get_db_connection

logger = logging.getLogger("aura_retail.database.validators")

EXPECTED_ROW_COUNTS = {
    "dim_channels": 6,
    "dim_customers": 10000,
    "dim_products": 150,
    "fact_orders": 50000,
    "fact_order_items": 127596,
    "fact_web_sessions": 150000,
    "fact_marketing_spend": 2193,
}

PK_MAP = {
    "dim_channels": "channel_id",
    "dim_customers": "customer_id",
    "dim_products": "product_id",
    "fact_orders": "order_id",
    "fact_order_items": "order_item_id",
    "fact_web_sessions": "session_id",
    "fact_marketing_spend": "spend_id",
}


def validate_row_counts(
    conn, schema_name: str = "aura_retail"
) -> Dict[str, Dict[str, Any]]:
    """Validate that every table has the exact expected number of rows."""
    results = {}
    with conn.cursor() as cur:
        for table, expected in EXPECTED_ROW_COUNTS.items():
            cur.execute(f"SELECT COUNT(*) FROM {schema_name}.{table};")
            actual = cur.fetchone()[0]
            passed = actual == expected
            results[table] = {
                "expected": expected,
                "actual": actual,
                "passed": passed,
            }
            if not passed:
                logger.error(
                    "Row count mismatch on %s: expected %d, got %d",
                    table,
                    expected,
                    actual,
                )
    return results


def validate_primary_keys(
    conn, schema_name: str = "aura_retail"
) -> Dict[str, Dict[str, Any]]:
    """Verify primary key uniqueness (zero duplicates) across all tables."""
    results = {}
    with conn.cursor() as cur:
        for table, pk_col in PK_MAP.items():
            query = f"""
                SELECT COUNT(*) - COUNT(DISTINCT {pk_col}) AS duplicates,
                       COUNT(*) AS total_rows,
                       COUNT(DISTINCT {pk_col}) AS distinct_keys
                FROM {schema_name}.{table};
            """
            cur.execute(query)
            duplicates, total_rows, distinct_keys = cur.fetchone()
            passed = duplicates == 0 and total_rows == distinct_keys
            results[table] = {
                "pk_column": pk_col,
                "total_rows": total_rows,
                "distinct_keys": distinct_keys,
                "duplicates": duplicates,
                "passed": passed,
            }
            if not passed:
                logger.error("Duplicate PKs detected in %s.%s: %d", table, pk_col, duplicates)
    return results


def validate_foreign_keys(
    conn, schema_name: str = "aura_retail"
) -> Dict[str, Dict[str, Any]]:
    """Verify referential integrity (zero orphan records)."""
    fk_checks = [
        (
            "dim_customers -> dim_channels",
            f"""
            SELECT COUNT(*) FROM {schema_name}.dim_customers c
            LEFT JOIN {schema_name}.dim_channels p ON c.acquisition_channel_id = p.channel_id
            WHERE p.channel_id IS NULL;
            """,
        ),
        (
            "fact_orders -> dim_customers",
            f"""
            SELECT COUNT(*) FROM {schema_name}.fact_orders o
            LEFT JOIN {schema_name}.dim_customers c ON o.customer_id = c.customer_id
            WHERE c.customer_id IS NULL;
            """,
        ),
        (
            "fact_order_items -> fact_orders",
            f"""
            SELECT COUNT(*) FROM {schema_name}.fact_order_items oi
            LEFT JOIN {schema_name}.fact_orders o ON oi.order_id = o.order_id
            WHERE o.order_id IS NULL;
            """,
        ),
        (
            "fact_order_items -> dim_products",
            f"""
            SELECT COUNT(*) FROM {schema_name}.fact_order_items oi
            LEFT JOIN {schema_name}.dim_products p ON oi.product_id = p.product_id
            WHERE p.product_id IS NULL;
            """,
        ),
        (
            "fact_web_sessions -> dim_customers",
            f"""
            SELECT COUNT(*) FROM {schema_name}.fact_web_sessions s
            LEFT JOIN {schema_name}.dim_customers c ON s.customer_id = c.customer_id
            WHERE c.customer_id IS NULL;
            """,
        ),
        (
            "fact_marketing_spend -> dim_channels",
            f"""
            SELECT COUNT(*) FROM {schema_name}.fact_marketing_spend ms
            LEFT JOIN {schema_name}.dim_channels c ON ms.channel_id = c.channel_id
            WHERE c.channel_id IS NULL;
            """,
        ),
    ]

    results = {}
    with conn.cursor() as cur:
        for rel_name, sql in fk_checks:
            cur.execute(sql)
            orphans = cur.fetchone()[0]
            passed = orphans == 0
            results[rel_name] = {"orphan_count": orphans, "passed": passed}
            if not passed:
                logger.error("Orphan foreign keys found in %s: %d", rel_name, orphans)
    return results


def validate_check_constraints(
    conn, schema_name: str = "aura_retail"
) -> Dict[str, Dict[str, Any]]:
    """Verify business check constraints at the data layer."""
    constraint_checks = [
        ("customers_age_gte_18", f"SELECT COUNT(*) FROM {schema_name}.dim_customers WHERE age < 18;"),
        ("products_cost_gte_0", f"SELECT COUNT(*) FROM {schema_name}.dim_products WHERE cost_price < 0;"),
        ("products_retail_gte_0", f"SELECT COUNT(*) FROM {schema_name}.dim_products WHERE retail_price < 0;"),
        ("orders_shipping_gte_0", f"SELECT COUNT(*) FROM {schema_name}.fact_orders WHERE shipping_cost < 0;"),
        ("orders_discount_gte_0", f"SELECT COUNT(*) FROM {schema_name}.fact_orders WHERE discount_amount < 0;"),
        ("orders_total_gte_0", f"SELECT COUNT(*) FROM {schema_name}.fact_orders WHERE total_order_amount < 0;"),
        ("order_items_qty_gt_0", f"SELECT COUNT(*) FROM {schema_name}.fact_order_items WHERE quantity <= 0;"),
        ("order_items_unit_price_gte_0", f"SELECT COUNT(*) FROM {schema_name}.fact_order_items WHERE unit_price < 0;"),
        ("order_items_line_total_gte_0", f"SELECT COUNT(*) FROM {schema_name}.fact_order_items WHERE line_total < 0;"),
        ("sessions_page_views_gte_0", f"SELECT COUNT(*) FROM {schema_name}.fact_web_sessions WHERE page_views < 0;"),
        ("sessions_time_spent_gte_0", f"SELECT COUNT(*) FROM {schema_name}.fact_web_sessions WHERE time_spent_seconds < 0;"),
        ("sessions_tickets_gte_0", f"SELECT COUNT(*) FROM {schema_name}.fact_web_sessions WHERE support_tickets < 0;"),
        ("spend_impressions_gte_0", f"SELECT COUNT(*) FROM {schema_name}.fact_marketing_spend WHERE impressions < 0;"),
        ("spend_clicks_gte_0", f"SELECT COUNT(*) FROM {schema_name}.fact_marketing_spend WHERE clicks < 0;"),
        ("spend_clicks_le_impressions", f"SELECT COUNT(*) FROM {schema_name}.fact_marketing_spend WHERE clicks > impressions;"),
        ("spend_usd_gte_0", f"SELECT COUNT(*) FROM {schema_name}.fact_marketing_spend WHERE spend_usd < 0;"),
    ]

    results = {}
    with conn.cursor() as cur:
        for name, sql in constraint_checks:
            cur.execute(sql)
            violations = cur.fetchone()[0]
            passed = violations == 0
            results[name] = {"violations": violations, "passed": passed}
            if not passed:
                logger.error("Check constraint violation on %s: %d", name, violations)
    return results


def validate_date_integrity(
    conn, schema_name: str = "aura_retail"
) -> Dict[str, Dict[str, Any]]:
    """
    Verify date integrity:
    1. Dates fall within 2024-01-01 and 2025-12-31.
    2. Customer signup date does not occur after order date.
    """
    results = {}
    with conn.cursor() as cur:
        # Date boundaries
        cur.execute(f"SELECT MIN(signup_date), MAX(signup_date) FROM {schema_name}.dim_customers;")
        min_cust, max_cust = cur.fetchone()

        cur.execute(f"SELECT MIN(order_date::date), MAX(order_date::date) FROM {schema_name}.fact_orders;")
        min_ord, max_ord = cur.fetchone()

        cur.execute(f"SELECT MIN(session_date), MAX(session_date) FROM {schema_name}.fact_web_sessions;")
        min_sess, max_sess = cur.fetchone()

        cur.execute(f"SELECT MIN(spend_date), MAX(spend_date) FROM {schema_name}.fact_marketing_spend;")
        min_sp, max_sp = cur.fetchone()

        # Signup before order check
        cur.execute(f"""
            SELECT COUNT(*)
            FROM {schema_name}.fact_orders o
            JOIN {schema_name}.dim_customers c ON o.customer_id = c.customer_id
            WHERE o.order_date::date < c.signup_date;
        """)
        order_before_signup = cur.fetchone()[0]

    bounds_ok = (
        str(min_cust) >= "2024-01-01" and str(max_cust) <= "2025-12-31" and
        str(min_ord) >= "2024-01-01" and str(max_ord) <= "2025-12-31" and
        str(min_sess) >= "2024-01-01" and str(max_sess) <= "2025-12-31" and
        str(min_sp) >= "2024-01-01" and str(max_sp) <= "2025-12-31"
    )

    results["date_bounds"] = {
        "customers": f"{min_cust} to {max_cust}",
        "orders": f"{min_ord} to {max_ord}",
        "web_sessions": f"{min_sess} to {max_sess}",
        "marketing_spend": f"{min_sp} to {max_sp}",
        "passed": bounds_ok,
    }
    results["order_after_signup"] = {
        "violations": order_before_signup,
        "passed": order_before_signup == 0,
    }
    return results


def compare_csv_vs_db(
    conn,
    raw_data_dir: Optional[str] = None,
    schema_name: str = "aura_retail",
) -> Dict[str, Dict[str, Any]]:
    """
    Deep parity comparison between source CSV files and PostgreSQL tables:
    - Row counts
    - Primary key uniqueness and count
    - Aggregate monetary values (total_order_amount, line_total, spend_usd)
    - Date bounds
    """
    if raw_data_dir is None:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        raw_data_dir = os.path.join(root_dir, "data", "01_raw")

    csv_files = {
        "dim_channels": ("channels.csv", "channel_id"),
        "dim_customers": ("customers.csv", "customer_id"),
        "dim_products": ("products.csv", "product_id"),
        "fact_orders": ("orders.csv", "order_id"),
        "fact_order_items": ("order_items.csv", "order_item_id"),
        "fact_web_sessions": ("web_sessions.csv", "session_id"),
        "fact_marketing_spend": ("marketing_spend.csv", "spend_id"),
    }

    comparison = {}

    with conn.cursor() as cur:
        for table, (filename, pk_col) in csv_files.items():
            csv_path = os.path.join(raw_data_dir, filename)
            df = pd.read_csv(csv_path)

            # DB metrics
            cur.execute(f"SELECT COUNT(*), COUNT(DISTINCT {pk_col}) FROM {schema_name}.{table};")
            db_rows, db_distinct_pk = cur.fetchone()

            csv_rows = len(df)
            csv_distinct_pk = df[pk_col].nunique()

            rows_match = csv_rows == db_rows
            pks_match = csv_distinct_pk == db_distinct_pk

            res: Dict[str, Any] = {
                "csv_rows": csv_rows,
                "db_rows": db_rows,
                "rows_match": rows_match,
                "csv_distinct_pk": csv_distinct_pk,
                "db_distinct_pk": db_distinct_pk,
                "pks_match": pks_match,
            }

            # Table-specific numeric sum checks
            if table == "fact_orders":
                cur.execute(f"SELECT ROUND(SUM(total_order_amount)::numeric, 2) FROM {schema_name}.fact_orders;")
                db_sum = float(cur.fetchone()[0])
                csv_sum = round(float(df["total_order_amount"].sum()), 2)
                res["csv_total_order_amount"] = csv_sum
                res["db_total_order_amount"] = db_sum
                res["amount_match"] = abs(csv_sum - db_sum) < 0.01

            elif table == "fact_order_items":
                cur.execute(f"SELECT ROUND(SUM(line_total)::numeric, 2) FROM {schema_name}.fact_order_items;")
                db_sum = float(cur.fetchone()[0])
                csv_sum = round(float(df["line_total"].sum()), 2)
                res["csv_line_total_sum"] = csv_sum
                res["db_line_total_sum"] = db_sum
                res["line_total_match"] = abs(csv_sum - db_sum) < 0.01

            elif table == "fact_marketing_spend":
                cur.execute(f"SELECT ROUND(SUM(spend_usd)::numeric, 2) FROM {schema_name}.fact_marketing_spend;")
                db_sum = float(cur.fetchone()[0])
                csv_sum = round(float(df["spend_usd"].sum()), 2)
                res["csv_spend_usd_sum"] = csv_sum
                res["db_spend_usd_sum"] = db_sum
                res["spend_match"] = abs(csv_sum - db_sum) < 0.01

            comparison[table] = res

    return comparison


def validate_database(
    config_path: Optional[str] = None,
    schema_name: str = "aura_retail",
) -> Dict[str, Any]:
    """
    Run the complete database validation suite and compile results.
    """
    with get_db_connection(config_path, autocommit=True) as conn:
        row_counts = validate_row_counts(conn, schema_name=schema_name)
        primary_keys = validate_primary_keys(conn, schema_name=schema_name)
        foreign_keys = validate_foreign_keys(conn, schema_name=schema_name)
        constraints = validate_check_constraints(conn, schema_name=schema_name)
        dates = validate_date_integrity(conn, schema_name=schema_name)
        csv_parity = compare_csv_vs_db(conn, schema_name=schema_name)

    all_passed = (
        all(v["passed"] for v in row_counts.values()) and
        all(v["passed"] for v in primary_keys.values()) and
        all(v["passed"] for v in foreign_keys.values()) and
        all(v["passed"] for v in constraints.values()) and
        dates["date_bounds"]["passed"] and
        dates["order_after_signup"]["passed"] and
        all(v["rows_match"] and v["pks_match"] for v in csv_parity.values())
    )

    report = {
        "all_passed": all_passed,
        "row_counts": row_counts,
        "primary_keys": primary_keys,
        "foreign_keys": foreign_keys,
        "constraints": constraints,
        "dates": dates,
        "csv_parity": csv_parity,
    }
    return report


if __name__ == "__main__":
    from pprint import pprint

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    print("Running Aura Retail Database Validation Suite...")
    summary = validate_database()

    print("\n" + "=" * 70)
    print("AURA RETAIL DATABASE VALIDATION REPORT")
    print("=" * 70)
    print(f"Overall Status: {'PASSED [OK]' if summary['all_passed'] else 'FAILED [X]'}\n")

    print("1. Table Row Counts:")
    for tbl, info in summary["row_counts"].items():
        status = "OK" if info["passed"] else "FAIL"
        print(f"   - {tbl:22}: {info['actual']:7d} (Expected: {info['expected']:7d}) [{status}]")

    print("\n2. Primary Key Uniqueness:")
    for tbl, info in summary["primary_keys"].items():
        status = "OK" if info["passed"] else "FAIL"
        print(f"   - {tbl:22} ({info['pk_column']}): {info['distinct_keys']:7d} distinct / {info['duplicates']} duplicates [{status}]")

    print("\n3. Foreign Key Referential Integrity:")
    for rel, info in summary["foreign_keys"].items():
        status = "OK" if info["passed"] else "FAIL"
        print(f"   - {rel:38}: {info['orphan_count']} orphan records [{status}]")

    print("\n4. Check Constraints:")
    for chk, info in summary["constraints"].items():
        status = "OK" if info["passed"] else "FAIL"
        print(f"   - {chk:32}: {info['violations']} violations [{status}]")

    print("\n5. Date Boundaries & Temporal Order:")
    d = summary["dates"]
    print(f"   - Date Bounds Valid (2024-2025): {d['date_bounds']['passed']}")
    print(f"   - Orders placed after Signup:     {d['order_after_signup']['passed']} (Violations: {d['order_after_signup']['violations']})")

    print("\n6. CSV vs PostgreSQL Parity:")
    for tbl, info in summary["csv_parity"].items():
        print(f"   - {tbl:22}: CSV={info['csv_rows']:7d} | DB={info['db_rows']:7d} (Rows Match: {info['rows_match']})")
        if "csv_total_order_amount" in info:
            print(f"     Order Amount Sum: CSV=${info['csv_total_order_amount']:,.2f} | DB=${info['db_total_order_amount']:,.2f} (Match: {info['amount_match']})")
        if "csv_line_total_sum" in info:
            print(f"     Line Total Sum:   CSV=${info['csv_line_total_sum']:,.2f} | DB=${info['db_line_total_sum']:,.2f} (Match: {info['line_total_match']})")
        if "csv_spend_usd_sum" in info:
            print(f"     Marketing Spend:  CSV=${info['csv_spend_usd_sum']:,.2f} | DB=${info['db_spend_usd_sum']:,.2f} (Match: {info['spend_match']})")
    print("=" * 70)
