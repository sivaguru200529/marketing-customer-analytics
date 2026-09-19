"""
Aura Retail Analytics - Main Database Loading Entrypoint
Orchestrates schema initialization, high-performance bulk loading, and validation.
Usage:
    python -m src.database.load_data [--reset] [--skip-validation]
"""

import argparse
import logging
import sys
import time

from src.database.connection import test_connection
from src.database.loader import load_raw_data
from src.database.schema import init_schema, verify_schema_objects
from src.database.validators import validate_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("aura_retail.database.load_data")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aura Retail - PostgreSQL Database Initialization and Bulk Data Ingestion"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate the aura_retail schema and all tables before loading",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip post-load database validation and CSV parity checks",
    )
    parser.add_argument(
        "--schema",
        default="aura_retail",
        help="Target database schema name (default: aura_retail)",
    )
    args = parser.parse_args()

    start_time = time.time()
    logger.info("=== Starting Aura Retail Database Pipeline ===")

    # 1. Connection Check
    logger.info("1. Verifying PostgreSQL connectivity...")
    ok, conn_msg = test_connection()
    if not ok:
        logger.error("Database connection failed: %s", conn_msg)
        return 1
    logger.info("Connection confirmed: %s", conn_msg)

    # 2. Schema Initialization
    logger.info("2. Initializing database schema (reset=%s)...", args.reset)
    applied_files = init_schema(drop_existing=args.reset, schema_name=args.schema)
    verified_tables = verify_schema_objects(schema_name=args.schema)
    logger.info(
        "Schema ready. Applied %d DDL files. Discovered %d tables: %s",
        len(applied_files),
        len(verified_tables),
        verified_tables,
    )

    # 3. Bulk Data Ingestion
    logger.info("3. Bulk loading Phase 2 raw CSV datasets into '%s'...", args.schema)
    metrics = load_raw_data(schema_name=args.schema, truncate_first=not args.reset)

    total_rows = sum(m["rows_loaded"] for m in metrics.values())
    logger.info("Bulk load complete: %d total rows inserted across %d tables.", total_rows, len(metrics))

    # 4. Validation Suite
    if not args.skip_validation:
        logger.info("4. Running comprehensive database validation suite...")
        report = validate_database(schema_name=args.schema)
        if not report["all_passed"]:
            logger.error("Validation failed! Some data integrity checks did not pass.")
            return 1
        logger.info("All database validation checks passed successfully! [OK]")
    else:
        logger.info("4. Skipping validation suite as requested.")

    elapsed = time.time() - start_time
    logger.info("=== Database Pipeline Finished Successfully in %.2f seconds ===", elapsed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
