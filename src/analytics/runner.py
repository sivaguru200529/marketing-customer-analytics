"""
Aura Retail Analytics - Analytics Pipeline Runner
Deploys analytical SQL views, validates calculation integrity, and exports Phase 4 datasets.
Usage:
    python -m src.analytics.runner [--export] [--skip-export]
"""

import argparse
import glob
import logging
import os
import sys
import time
from typing import Dict, List, Optional

from src.analytics.export import export_all_datasets
from src.database.connection import get_db_connection, test_connection
from src.database.schema import EXPECTED_TABLES, verify_schema_objects

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("aura_retail.analytics.runner")

EXPECTED_VIEWS = [
    "view_customer_analytics",
    "view_product_analytics",
    "view_monthly_revenue",
    "view_marketing_performance",
    "view_cohort_retention",
    "view_business_kpis",
]


def get_analytics_sql_dir() -> str:
    """Return path to sql/analytics directory."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sql_dir = os.path.join(root_dir, "sql", "analytics")
    if not os.path.isdir(sql_dir):
        raise FileNotFoundError(f"Analytics SQL directory not found at: {sql_dir}")
    return sql_dir


def deploy_analytical_views(
    config_path: Optional[str] = None,
    schema_name: str = "aura_retail",
) -> List[str]:
    """
    Execute 008_phase4_datasets.sql to create or update all production analytical views.
    """
    sql_dir = get_analytics_sql_dir()
    views_file = os.path.join(sql_dir, "008_phase4_datasets.sql")

    if not os.path.isfile(views_file):
        raise FileNotFoundError(f"Views DDL file missing: {views_file}")

    with open(views_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    with get_db_connection(config_path, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_content)
        conn.commit()

    logger.info("Successfully deployed production analytical views from 008_phase4_datasets.sql.")
    return EXPECTED_VIEWS


def verify_analytical_views(
    config_path: Optional[str] = None,
    schema_name: str = "aura_retail",
) -> Dict[str, int]:
    """
    Verify that all expected analytical views exist in PostgreSQL and return their row counts.
    """
    counts: Dict[str, int] = {}
    with get_db_connection(config_path, autocommit=True) as conn:
        with conn.cursor() as cur:
            # Query information_schema.views
            cur.execute(
                """
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = %s
                ORDER BY table_name;
                """,
                (schema_name,),
            )
            existing_views = [row[0] for row in cur.fetchall()]

            missing = set(EXPECTED_VIEWS) - set(existing_views)
            if missing:
                raise RuntimeError(f"Missing expected analytical views in '{schema_name}': {missing}")

            # Get row count for each view
            for view_name in EXPECTED_VIEWS:
                cur.execute(f"SELECT COUNT(*) FROM {schema_name}.{view_name};")
                cnt = cur.fetchone()[0]
                counts[view_name] = cnt

    return counts


def run_analytics_pipeline(
    export_csvs: bool = True,
    output_dir: Optional[str] = None,
    config_path: Optional[str] = None,
    schema_name: str = "aura_retail",
) -> int:
    """
    Orchestrate full analytics execution:
    1. Verify database connectivity & source tables
    2. Deploy analytical views
    3. Verify view existence and row counts
    4. Export Phase 4 datasets
    """
    start_time = time.time()
    logger.info("=== Starting Aura Retail SQL Analytics Pipeline ===")

    # 1. Connection check
    logger.info("1. Verifying PostgreSQL connectivity...")
    ok, conn_msg = test_connection(config_path)
    if not ok:
        logger.error("Database connection failed: %s", conn_msg)
        return 1
    logger.info("Connection confirmed: %s", conn_msg)

    # 2. Source table verification
    logger.info("2. Verifying source relational warehouse tables in '%s'...", schema_name)
    source_tables = verify_schema_objects(config_path, schema_name=schema_name)
    logger.info("Discovered %d source tables: %s", len(source_tables), source_tables)

    # 3. Deploy analytical views
    logger.info("3. Deploying analytical views...")
    deployed = deploy_analytical_views(config_path, schema_name=schema_name)
    logger.info("Deployed %d views: %s", len(deployed), deployed)

    # 4. Verify views and get row counts
    logger.info("4. Validating analytical views & querying row counts...")
    view_counts = verify_analytical_views(config_path, schema_name=schema_name)
    for view_name, cnt in view_counts.items():
        logger.info("   - %s: %d rows", view_name, cnt)

    # 5. Export Phase 4 datasets
    if export_csvs:
        logger.info("5. Exporting Phase 4 analytical CSV datasets...")
        exported = export_all_datasets(output_dir=output_dir, config_path=config_path, schema_name=schema_name)
        for view_name, meta in exported.items():
            logger.info("   - Generated %s (%d rows, %d bytes)", meta["filename"], meta["row_count"], meta["file_size_bytes"])
    else:
        logger.info("5. Skipping dataset export as requested.")

    elapsed = time.time() - start_time
    logger.info("=== Analytics Pipeline Completed Successfully in %.2f seconds ===", elapsed)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Aura Retail SQL Analytics Runner")
    parser.add_argument("--skip-export", action="store_true", help="Skip exporting datasets to CSV")
    parser.add_argument("--output-dir", help="Custom output directory for exported CSVs")
    parser.add_argument("--schema", default="aura_retail", help="Target database schema name")
    args = parser.parse_args()

    return run_analytics_pipeline(
        export_csvs=not args.skip_export,
        output_dir=args.output_dir,
        schema_name=args.schema,
    )


if __name__ == "__main__":
    sys.exit(main())
