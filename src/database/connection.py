"""
Aura Retail Analytics - Database Connection Management
Provides centralized connection pooling, configuration resolution, and health checking.
"""

import configparser
import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional, Tuple

import psycopg2
from psycopg2.extensions import connection as Psycopg2Connection
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

logger = logging.getLogger("aura_retail.database.connection")

# Default fallback development configuration matching Docker setup
DEFAULT_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "aura_retail_db",
    "user": "postgres",
    "password": "postgres_secure_password",
    "schema": "aura_retail",
}


def get_connection_params(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Resolve PostgreSQL connection parameters using hierarchical precedence:
    1. Environment variables (POSTGRES_HOST, POSTGRES_PORT, etc.)
    2. config/database.ini file
    3. Default development settings matching docker-compose.yml
    """
    params = dict(DEFAULT_CONFIG)

    # 1. Check config file
    if config_path is None:
        # Check standard config directory relative to repo root
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        candidate_ini = os.path.join(root_dir, "config", "database.ini")
        candidate_example = os.path.join(root_dir, "config", "database.ini.example")

        if os.path.isfile(candidate_ini):
            config_path = candidate_ini
        elif os.path.isfile(candidate_example):
            config_path = candidate_example

    if config_path and os.path.isfile(config_path):
        parser = configparser.ConfigParser()
        parser.read(config_path)
        if parser.has_section("postgresql"):
            sec = parser["postgresql"]
            params["host"] = sec.get("host", params["host"])
            params["port"] = int(sec.get("port", params["port"]))
            params["database"] = sec.get("database", params["database"])
            params["user"] = sec.get("user", params["user"])
            params["password"] = sec.get("password", params["password"])
            params["schema"] = sec.get("schema", params["schema"])

    # 2. Environment variable overrides take highest priority
    params["host"] = os.getenv("POSTGRES_HOST", params["host"])
    params["port"] = int(os.getenv("POSTGRES_PORT", str(params["port"])))
    params["database"] = os.getenv("POSTGRES_DB", params["database"])
    params["user"] = os.getenv("POSTGRES_USER", params["user"])
    params["password"] = os.getenv("POSTGRES_PASSWORD", params["password"])
    params["schema"] = os.getenv("POSTGRES_SCHEMA", params["schema"])

    return params


def get_connection_url(config_path: Optional[str] = None) -> str:
    """Return an SQLAlchemy-compatible PostgreSQL connection URL."""
    p = get_connection_params(config_path)
    return (
        f"postgresql+psycopg2://{p['user']}:{p['password']}@"
        f"{p['host']}:{p['port']}/{p['database']}"
    )


def get_engine(config_path: Optional[str] = None) -> Engine:
    """
    Create and return an SQLAlchemy Engine configured with connection pooling
    and search_path set to the target schema.
    """
    params = get_connection_params(config_path)
    url = get_connection_url(config_path)
    schema = params.get("schema", "aura_retail")

    engine = create_engine(
        url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        connect_args={"options": f"-csearch_path={schema},public"},
    )
    return engine


@contextmanager
def get_db_connection(
    config_path: Optional[str] = None,
    autocommit: bool = False,
) -> Generator[Psycopg2Connection, None, None]:
    """
    Context manager yielding a raw psycopg2 database connection.
    Automatically commits on normal exit and rolls back on exception.
    """
    params = get_connection_params(config_path)
    conn = psycopg2.connect(
        host=params["host"],
        port=params["port"],
        dbname=params["database"],
        user=params["user"],
        password=params["password"],
        options=f"-csearch_path={params['schema']},public",
    )
    conn.autocommit = autocommit
    try:
        yield conn
        if not autocommit:
            conn.commit()
    except Exception:
        if not autocommit and not conn.closed:
            conn.rollback()
        raise
    finally:
        if not conn.closed:
            conn.close()


def test_connection(config_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Test connectivity to the PostgreSQL instance.
    Returns (True, status_info) or (False, error_message).
    """
    try:
        with get_db_connection(config_path, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                cur.execute("SELECT current_database(), current_schema();")
                db_name, cur_schema = cur.fetchone()
                return (
                    True,
                    f"Connected to database '{db_name}' (schema: '{cur_schema}'). Server: {version}",
                )
    except Exception as exc:
        return False, f"PostgreSQL connection failed: {exc}"
