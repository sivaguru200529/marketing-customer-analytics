"""
Aura Retail Analytics - Database Package
Provides connection management, schema migration, bulk loading, and validation.
"""

from src.database.connection import (
    get_connection_params,
    get_connection_url,
    get_db_connection,
    get_engine,
    test_connection,
)
from src.database.loader import load_raw_data, truncate_tables
from src.database.schema import init_schema, reset_schema, verify_schema_objects
from src.database.validators import (
    compare_csv_vs_db,
    validate_check_constraints,
    validate_database,
    validate_date_integrity,
    validate_foreign_keys,
    validate_primary_keys,
    validate_row_counts,
)

__all__ = [
    "get_connection_params",
    "get_connection_url",
    "get_db_connection",
    "get_engine",
    "test_connection",
    "init_schema",
    "reset_schema",
    "verify_schema_objects",
    "load_raw_data",
    "truncate_tables",
    "validate_database",
    "validate_row_counts",
    "validate_primary_keys",
    "validate_foreign_keys",
    "validate_check_constraints",
    "validate_date_integrity",
    "compare_csv_vs_db",
]
