"""
Aura Retail Analytics - Schema Manager
Applies DDL scripts from sql/schema/ to create schemas, tables, constraints, and indexes.
"""

import glob
import logging
import os
from typing import List, Optional

from src.database.connection import get_db_connection

logger = logging.getLogger("aura_retail.database.schema")

EXPECTED_TABLES = [
    "dim_channels",
    "dim_customers",
    "dim_products",
    "fact_orders",
    "fact_order_items",
    "fact_web_sessions",
    "fact_marketing_spend",
]


def get_schema_dir() -> str:
    """Return the absolute path to sql/schema directory."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    schema_dir = os.path.join(root_dir, "sql", "schema")
    if not os.path.isdir(schema_dir):
        raise FileNotFoundError(f"Schema directory not found at: {schema_dir}")
    return schema_dir


def get_schema_files() -> List[str]:
    """Return sorted list of SQL schema migration files."""
    schema_dir = get_schema_dir()
    sql_files = sorted(glob.glob(os.path.join(schema_dir, "*.sql")))
    if not sql_files:
        raise FileNotFoundError(f"No .sql schema files found in: {schema_dir}")
    return sql_files


def reset_schema(config_path: Optional[str] = None, schema_name: str = "aura_retail") -> None:
    """Drop and recreate the dedicated application schema."""
    with get_db_connection(config_path, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE;")
            logger.info("Dropped schema '%s' (CASCADE).", schema_name)


def init_schema(
    config_path: Optional[str] = None,
    drop_existing: bool = False,
    schema_name: str = "aura_retail",
) -> List[str]:
    """
    Execute all SQL schema files in numeric order to establish tables,
    foreign keys, constraints, and performance indexes.
    """
    if drop_existing:
        reset_schema(config_path, schema_name=schema_name)

    applied_files: List[str] = []
    sql_files = get_schema_files()

    with get_db_connection(config_path, autocommit=False) as conn:
        with conn.cursor() as cur:
            for filepath in sql_files:
                filename = os.path.basename(filepath)
                logger.info("Executing schema file: %s", filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    sql_content = f.read()
                cur.execute(sql_content)
                applied_files.append(filename)

    logger.info("Successfully applied %d schema files: %s", len(applied_files), applied_files)
    return applied_files


def verify_schema_objects(
    config_path: Optional[str] = None,
    schema_name: str = "aura_retail",
) -> List[str]:
    """
    Verify that the schema and expected tables exist in PostgreSQL.
    Returns list of discovered tables under the schema.
    """
    with get_db_connection(config_path, autocommit=True) as conn:
        with conn.cursor() as cur:
            # Check schema exists
            cur.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s;",
                (schema_name,),
            )
            if not cur.fetchone():
                raise RuntimeError(f"Schema '{schema_name}' does not exist in database.")

            # List tables in schema
            cur.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name;
                """,
                (schema_name,),
            )
            tables = [row[0] for row in cur.fetchall()]

    missing = set(EXPECTED_TABLES) - set(tables)
    if missing:
        raise RuntimeError(f"Missing expected tables in '{schema_name}': {missing}")

    return tables


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="Aura Retail Schema Initializer")
    parser.add_argument("--reset", action="store_true", help="Drop schema and recreate all tables")
    args = parser.parse_args()

    print(f"Initializing schema (reset={args.reset})...")
    applied = init_schema(drop_existing=args.reset)
    tables = verify_schema_objects()
    print(f"Applied {len(applied)} schema files: {applied}")
    print(f"Verified {len(tables)} tables in 'aura_retail': {tables}")
