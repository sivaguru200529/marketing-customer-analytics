# Implementation Plan: Phase 3 Part 1 — PostgreSQL Database Foundation

Build a clean, robust, and reproducible PostgreSQL database foundation for the **Aura Retail Marketing and Customer Analytics** platform, establishing the `aura_retail` schema, loading all Phase 2 synthetic datasets, verifying data integrity, and providing automated test coverage.

## User Review Required

> [!IMPORTANT]
> **Docker Desktop Startup Required:**
> Our preliminary environment check identified that Docker Desktop is installed at `C:\Program Files\Docker\Docker\Docker Desktop.exe`, but its background service (`com.docker.service`) is currently stopped and requires an interactive desktop launch or Windows administrator privilege to initialize its WSL2 engine.
> 
> Please ensure **Docker Desktop is opened and running** on your machine. Once Docker Desktop displays "Engine running", running:
> ```powershell
> docker compose -f docker/docker-compose.yml up -d
> ```
> will bring up the PostgreSQL 16 container (`aura_retail_postgres`) on port `5432`.
> 
> If you are using a standalone local PostgreSQL 16 installation instead of Docker, please set the credentials in `config/database.ini` or environment variables accordingly.

## Proposed Changes

### 1. Database Configuration & Docker Initialization

#### [MODIFY] [docker/init_db.sql](file:///c:/Users/91934/.gemini/antigravity-ide/scratch/marketing-customer-analytics/docker/init_db.sql)
- Add `CREATE SCHEMA IF NOT EXISTS aura_retail;` to guarantee schema creation upon container initialization.

#### [MODIFY] [config/database.ini.example](file:///c:/Users/91934/.gemini/antigravity-ide/scratch/marketing-customer-analytics/config/database.ini.example)
- Update default schema from `public` to `aura_retail`.
- Document environment variable overrides (`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_SCHEMA`).

---

### 2. Numbered Schema DDL Scripts (`sql/schema/`)

#### [NEW] [001_create_schema.sql](file:///c:/Users/91934/.gemini/antigravity-ide/scratch/marketing-customer-analytics/sql/schema/001_create_schema.sql)
- Creates schema `aura_retail`.
- Enables extension `uuid-ossp` if not present.
- Sets search_path comment.

#### [NEW] [002_create_tables.sql](file:///c:/Users/91934/.gemini/antigravity-ide/scratch/marketing-customer-analytics/sql/schema/002_create_tables.sql)
- Creates the 7 core tables under `aura_retail` with precise data types and primary keys:
  1. `dim_channels` (`channel_id` INT PK, `channel_name` VARCHAR(50) NOT NULL UNIQUE, `channel_type` VARCHAR(30) NOT NULL)
  2. `dim_customers` (`customer_id` VARCHAR(20) PK, `first_name` VARCHAR(50), `last_name` VARCHAR(50), `email` VARCHAR(100) UNIQUE, `signup_date` DATE, `acquisition_channel_id` INT, `age` INT, `gender` VARCHAR(20), `city` VARCHAR(50), `state` VARCHAR(50), `device_preference` VARCHAR(20))
  3. `dim_products` (`product_id` VARCHAR(20) PK, `product_name` VARCHAR(100), `category` VARCHAR(50), `sub_category` VARCHAR(50), `cost_price` NUMERIC(10,2), `retail_price` NUMERIC(10,2))
  4. `fact_orders` (`order_id` VARCHAR(20) PK, `customer_id` VARCHAR(20), `order_date` TIMESTAMP, `order_status` VARCHAR(20), `payment_method` VARCHAR(30), `shipping_cost` NUMERIC(10,2), `discount_amount` NUMERIC(10,2), `total_order_amount` NUMERIC(10,2))
  5. `fact_order_items` (`order_item_id` BIGINT PK, `order_id` VARCHAR(20), `product_id` VARCHAR(20), `quantity` INT, `unit_price` NUMERIC(10,2), `line_total` NUMERIC(10,2))
  6. `fact_web_sessions` (`session_id` VARCHAR(30) PK, `customer_id` VARCHAR(20), `session_date` DATE, `page_views` INT, `time_spent_seconds` INT, `cart_abandoned` BOOLEAN, `support_tickets` INT)
  7. `fact_marketing_spend` (`spend_id` INT PK, `spend_date` DATE, `channel_id` INT, `campaign_name` VARCHAR(100), `impressions` INT, `clicks` INT, `spend_usd` NUMERIC(10,2))

#### [NEW] [003_create_constraints.sql](file:///c:/Users/91934/.gemini/antigravity-ide/scratch/marketing-customer-analytics/sql/schema/003_create_constraints.sql)
- **Foreign Keys**:
  - `dim_customers.acquisition_channel_id` → `dim_channels(channel_id)`
  - `fact_orders.customer_id` → `dim_customers(customer_id)`
  - `fact_order_items.order_id` → `fact_orders(order_id)` ON DELETE CASCADE
  - `fact_order_items.product_id` → `dim_products(product_id)`
  - `fact_web_sessions.customer_id` → `dim_customers(customer_id)`
  - `fact_marketing_spend.channel_id` → `dim_channels(channel_id)`
- **Check Constraints**:
  - `dim_customers`: `age >= 18`
  - `dim_products`: `cost_price >= 0`, `retail_price >= 0`
  - `fact_orders`: `shipping_cost >= 0`, `discount_amount >= 0`, `total_order_amount >= 0`
  - `fact_order_items`: `quantity > 0`, `unit_price >= 0`, `line_total >= 0`
  - `fact_web_sessions`: `page_views >= 0`, `time_spent_seconds >= 0`, `support_tickets >= 0`
  - `fact_marketing_spend`: `impressions >= 0`, `clicks >= 0`, `clicks <= impressions`, `spend_usd >= 0`

#### [NEW] [004_create_indexes.sql](file:///c:/Users/91934/.gemini/antigravity-ide/scratch/marketing-customer-analytics/sql/schema/004_create_indexes.sql)
- Performance indexes on analytical query join columns and date partition filters:
  - `idx_customers_acq_channel`: FK to channels
  - `idx_customers_signup_date`: Cohort signup filtering
  - `idx_orders_customer_id`: Joins with dim_customers
  - `idx_orders_order_date`: Time-series and monthly revenue grouping
  - `idx_orders_status`: Order status filtering (Delivered, Returned, Cancelled)
  - `idx_orders_cust_date`: Compound index for RFM recency & cadence calculation
  - `idx_order_items_order_id`: Joins with fact_orders
  - `idx_order_items_product_id`: Joins with dim_products
  - `idx_web_sessions_customer_id`: Joins with dim_customers
  - `idx_web_sessions_session_date`: Time-series web activity
  - `idx_marketing_spend_channel_date`: Channel-level daily attribution and ROAS

---

### 3. Database Python Package (`src/database/`)

#### [MODIFY] [src/database/__init__.py](file:///c:/Users/91934/.gemini/antigravity-ide/scratch/marketing-customer-analytics/src/database/__init__.py)
- Expose primary APIs: `get_connection_params`, `get_engine`, `get_db_connection`, `init_schema`, `load_raw_data`, `validate_database`, `compare_csv_vs_db`.

#### [NEW] [src/database/connection.py](file:///c:/Users/91934/.gemini/antigravity-ide/scratch/marketing-customer-analytics/src/database/connection.py)
- Configuration resolution hierarchy: Environment variables → `config/database.ini` → Default local docker fallback.
- Connection URL generator, SQLAlchemy `create_engine()` with connection pooling, and raw `psycopg2.connect` context manager.
- Connectivity verification helper (`test_connection()`) returning diagnostic status and PostgreSQL server version.

#### [NEW] [src/database/schema.py](file:///c:/Users/91934/.gemini/antigravity-ide/scratch/marketing-customer-analytics/src/database/schema.py)
- Programmatic execution of `sql/schema/*.sql` files in sorted order.
- Supports `init_schema(drop_existing=False)` and `reset_schema()` functions.
- Inspects and verifies table creation in `aura_retail`.

#### [NEW] [src/database/loader.py](file:///c:/Users/91934/.gemini/antigravity-ide/scratch/marketing-customer-analytics/src/database/loader.py)
- High-performance bulk data loading using PostgreSQL `COPY ... FROM STDIN WITH (FORMAT csv, HEADER true)` via psycopg2 `copy_expert`.
- Respects foreign-key dependency order:
  1. `dim_channels`
  2. `dim_customers`
  3. `dim_products`
  4. `fact_orders`
  5. `fact_order_items`
  6. `fact_web_sessions`
  7. `fact_marketing_spend`
- Handles streaming I/O, transaction commit, rollback on error, and progress timing.

#### [NEW] [src/database/validators.py](file:///c:/Users/91934/.gemini/antigravity-ide/scratch/marketing-customer-analytics/src/database/validators.py)
- Post-load validation suite:
  - Table existence & schema qualification in `aura_retail`
  - Exact row count verification:
    - `dim_channels` = 6
    - `dim_customers` = 10,000
    - `dim_products` = 150
    - `fact_orders` = 50,000
    - `fact_order_items` = 127,596
    - `fact_web_sessions` = 150,000
    - `fact_marketing_spend` = 2,193
  - Primary key uniqueness across all 7 tables
  - Foreign key referential integrity (zero orphan records)
  - Zero unexpected NULLs in mandatory fields
  - Check constraint assertions
  - Date window verification (2024-01-01 to 2025-12-31) and relational sanity (`order_date >= signup_date`)
- CSV vs PostgreSQL parity comparator:
  - Exact match of row counts, PK sets, min/max dates, and financial aggregate sums (`total_order_amount`, `line_total`, `spend_usd`).

#### [NEW] [src/database/load_data.py](file:///c:/Users/91934/.gemini/antigravity-ide/scratch/marketing-customer-analytics/src/database/load_data.py)
- Command-line runner (`python -m src.database.load_data [--reset] [--skip-validation]`).
- Orchestrates connection check → schema initialization → bulk load → validation → report generation.

---

### 4. Automated Tests (`tests/`)

#### [NEW] [tests/test_database.py](file:///c:/Users/91934/.gemini/antigravity-ide/scratch/marketing-customer-analytics/tests/test_database.py)
- Non-destructive automated tests:
  - `test_db_connection()`: Asserts connection success.
  - `test_schema_exists()`: Confirms `aura_retail` schema exists.
  - `test_tables_exist()`: Verifies all 7 tables are present.
  - `test_table_row_counts()`: Asserts exact loaded counts.
  - `test_primary_key_uniqueness()`: Asserts 0 duplicate PKs.
  - `test_foreign_key_integrity()`: Asserts 0 orphan FK references.
  - `test_check_constraints()`: Verifies business check constraints.
  - `test_csv_vs_database_parity()`: Asserts financial and date parity between `data/01_raw/` and PostgreSQL.

---

### 5. Documentation (`docs/`)

#### [NEW] [docs/database_setup.md](file:///c:/Users/91934/.gemini/antigravity-ide/scratch/marketing-customer-analytics/docs/database_setup.md)
- Complete database architecture documentation:
  - PostgreSQL container configuration & port mappings
  - Database name (`aura_retail_db`), schema name (`aura_retail`)
  - Full schema entity relationship diagram (Mermaid)
  - Data type rationale and constraint catalog
  - Index strategy and analytical justification
  - Step-by-step instructions for startup, initialization, loading, and validation
  - Reproduction commands

#### [MODIFY] [docs/data_dictionary.md](file:///c:/Users/91934/.gemini/antigravity-ide/scratch/marketing-customer-analytics/docs/data_dictionary.md)
- Update table headers with `aura_retail.` schema prefix.
- Add database-specific constraints and indexing references while preserving all Phase 2 documentation.

---

## Verification Plan

### Automated Tests
1. Existing Phase 2 tests:
   ```powershell
   python -m pytest tests/test_data_generator.py -v
   ```
2. Database test suite:
   ```powershell
   python -m pytest tests/test_database.py -v
   ```

### Manual & CLI Verification
1. Database loading CLI:
   ```powershell
   python -m src.database.load_data --reset
   ```
2. Standalone database validators:
   ```powershell
   python -m src.database.validators
   ```
3. Git status verification:
   ```powershell
   git status
   ```
   (Verify no CSV files are tracked or committed).
