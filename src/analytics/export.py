"""
Aura Retail Analytics - Analytical Dataset Exporter
Extracts standardized analytical views into Phase 4-ready CSV datasets using PostgreSQL streaming.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from src.database.connection import get_db_connection

logger = logging.getLogger("aura_retail.analytics.export")

# Mapping of analytical views to their export filenames
ANALYTICAL_VIEWS: List[Tuple[str, str]] = [
    ("view_customer_analytics", "customer_analytics.csv"),
    ("view_product_analytics", "product_analytics.csv"),
    ("view_monthly_revenue", "monthly_revenue.csv"),
    ("view_marketing_performance", "marketing_performance.csv"),
    ("view_cohort_retention", "cohort_retention.csv"),
    ("view_business_kpis", "business_kpis.csv"),
]


def get_default_export_dir() -> str:
    """Return the default export directory path: data/03_analytics."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    export_dir = os.path.join(root_dir, "data", "03_analytics")
    os.makedirs(export_dir, exist_ok=True)
    return export_dir


def export_view_to_csv(
    conn,
    view_name: str,
    output_filepath: str,
    schema_name: str = "aura_retail",
) -> Dict[str, Any]:
    """
    Stream analytical view rows into a CSV file with headers via PostgreSQL COPY.
    Returns metadata on the exported file.
    """
    start_time = time.time()
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

    copy_sql = f"COPY (SELECT * FROM {schema_name}.{view_name}) TO STDOUT WITH (FORMAT csv, HEADER true);"

    with conn.cursor() as cur:
        with open(output_filepath, "w", encoding="utf-8", newline="") as f:
            cur.copy_expert(sql=copy_sql, file=f)

        cur.execute(f"SELECT COUNT(*) FROM {schema_name}.{view_name};")
        row_count = cur.fetchone()[0]

    elapsed = time.time() - start_time
    file_size = os.path.getsize(output_filepath)

    logger.info(
        "Exported '%s.%s' -> '%s' (%d rows, %d bytes in %.2fs)",
        schema_name,
        view_name,
        os.path.basename(output_filepath),
        row_count,
        file_size,
        elapsed,
    )

    return {
        "view_name": view_name,
        "filename": os.path.basename(output_filepath),
        "filepath": output_filepath,
        "row_count": row_count,
        "file_size_bytes": file_size,
        "elapsed_seconds": round(elapsed, 3),
    }


def export_all_datasets(
    output_dir: Optional[str] = None,
    config_path: Optional[str] = None,
    schema_name: str = "aura_retail",
    sync_to_analytical_dir: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """
    Export all 6 analytical datasets to the target analytics directory.
    Optionally syncs copies to data/03_analytical/ for backwards compatibility.
    """
    if output_dir is None:
        output_dir = get_default_export_dir()
    os.makedirs(output_dir, exist_ok=True)

    results: Dict[str, Dict[str, Any]] = {}
    total_start = time.time()

    with get_db_connection(config_path, autocommit=True) as conn:
        for view_name, filename in ANALYTICAL_VIEWS:
            target_path = os.path.join(output_dir, filename)
            meta = export_view_to_csv(conn, view_name, target_path, schema_name=schema_name)
            results[view_name] = meta

            # Also sync to data/03_analytical if different directory
            if sync_to_analytical_dir:
                root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                alt_dir = os.path.join(root_dir, "data", "03_analytical")
                if alt_dir != output_dir:
                    os.makedirs(alt_dir, exist_ok=True)
                    alt_path = os.path.join(alt_dir, filename)
                    with open(target_path, "rb") as src_f, open(alt_path, "wb") as dst_f:
                        dst_f.write(src_f.read())

    total_elapsed = time.time() - total_start
    total_rows = sum(m["row_count"] for m in results.values())
    logger.info(
        "Exported %d total analytical datasets (%d total rows) in %.2f seconds.",
        len(results),
        total_rows,
        total_elapsed,
    )

    return results


if __name__ == "__main__":
    import argparse
    from pprint import pprint

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="Export Analytical Datasets to CSV")
    parser.add_argument("--output-dir", help="Custom output directory for exported CSVs")
    args = parser.parse_args()

    print("Exporting Phase 4 analytical datasets...")
    exported = export_all_datasets(output_dir=args.output_dir)
    print("\nExport Results:")
    pprint(exported)
