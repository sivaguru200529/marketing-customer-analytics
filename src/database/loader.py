"""
Aura Retail Analytics - High-Performance Bulk Data Loader
Loads Phase 2 synthetic CSV datasets into PostgreSQL using native COPY streaming.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from src.database.connection import get_db_connection

logger = logging.getLogger("aura_retail.database.loader")

# Strict dependency-safe load order: parent dimension tables first, then child fact tables
LOAD_PIPELINE: List[Tuple[str, str]] = [
    ("dim_channels", "channels.csv"),
    ("dim_customers", "customers.csv"),
    ("dim_products", "products.csv"),
    ("fact_orders", "orders.csv"),
    ("fact_order_items", "order_items.csv"),
    ("fact_web_sessions", "web_sessions.csv"),
    ("fact_marketing_spend", "marketing_spend.csv"),
]


def get_raw_data_dir() -> str:
    """Return the absolute path to data/01_raw directory."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    raw_dir = os.path.join(root_dir, "data", "01_raw")
    if not os.path.isdir(raw_dir):
        raise FileNotFoundError(f"Raw data directory not found at: {raw_dir}")
    return raw_dir


def truncate_tables(config_path: Optional[str] = None, schema_name: str = "aura_retail") -> None:
    """
    Truncate all application tables in safe reverse dependency order.
    """
    with get_db_connection(config_path, autocommit=False) as conn:
        with conn.cursor() as cur:
            # Truncate all tables in one statement with CASCADE
            tables = [f"{schema_name}.{tbl}" for tbl, _ in reversed(LOAD_PIPELINE)]
            cur.execute(f"TRUNCATE TABLE {', '.join(tables)} CASCADE;")
            logger.info("Truncated all %d tables in '%s'.", len(tables), schema_name)


def load_table_csv(
    conn,
    table_name: str,
    csv_path: str,
    schema_name: str = "aura_retail",
) -> int:
    """
    Bulk load a single CSV file into the target PostgreSQL table using copy_expert.
    Returns the count of rows currently in the table after loading.
    """
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV data file not found: {csv_path}")

    start_time = time.time()
    copy_sql = f"COPY {schema_name}.{table_name} FROM STDIN WITH (FORMAT csv, HEADER true);"

    with conn.cursor() as cur:
        with open(csv_path, "r", encoding="utf-8") as f:
            cur.copy_expert(sql=copy_sql, file=f)

        cur.execute(f"SELECT COUNT(*) FROM {schema_name}.{table_name};")
        row_count = cur.fetchone()[0]

    elapsed = time.time() - start_time
    rate = row_count / elapsed if elapsed > 0 else row_count
    logger.info(
        "Loaded '%s.%s' <- '%s': %d rows (%.2fs, %.0f rows/s)",
        schema_name,
        table_name,
        os.path.basename(csv_path),
        row_count,
        elapsed,
        rate,
    )
    return row_count


def load_raw_data(
    config_path: Optional[str] = None,
    schema_name: str = "aura_retail",
    truncate_first: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """
    Execute full bulk loading pipeline across all 7 tables in dependency-safe order.
    Returns a dictionary of load metrics per table.
    """
    raw_dir = get_raw_data_dir()

    if truncate_first:
        truncate_tables(config_path, schema_name=schema_name)

    results: Dict[str, Dict[str, Any]] = {}
    total_start = time.time()

    with get_db_connection(config_path, autocommit=False) as conn:
        for table_name, csv_filename in LOAD_PIPELINE:
            csv_path = os.path.join(raw_dir, csv_filename)
            t_start = time.time()
            count = load_table_csv(conn, table_name, csv_path, schema_name=schema_name)
            t_elapsed = time.time() - t_start

            results[table_name] = {
                "csv_file": csv_filename,
                "rows_loaded": count,
                "elapsed_seconds": round(t_elapsed, 3),
                "throughput_rows_per_sec": round(count / t_elapsed if t_elapsed > 0 else count, 1),
            }

    total_elapsed = time.time() - total_start
    total_rows = sum(r["rows_loaded"] for r in results.values())
    logger.info(
        "Complete bulk load finished: %d total rows across %d tables in %.2f seconds.",
        total_rows,
        len(results),
        total_elapsed,
    )
    return results


if __name__ == "__main__":
    import argparse
    from pprint import pprint

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="Aura Retail Bulk Data Loader")
    parser.add_argument("--no-truncate", action="store_true", help="Do not truncate tables before loading")
    args = parser.parse_args()

    print("Starting bulk loading...")
    metrics = load_raw_data(truncate_first=not args.no_truncate)
    print("\nBulk Load Results:")
    pprint(metrics)
