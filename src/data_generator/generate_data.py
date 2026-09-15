"""
Main entry point and orchestrator for Aura Retail synthetic data generation.
Executes deterministic generation pipeline, runs full pre-export validation,
persists CSV datasets, and prints formatted summary metrics.
"""

import argparse
import logging
import logging.config
import os
import sys
import time
from pathlib import Path
from typing import Dict
import pandas as pd

from src.data_generator.config import (
    GeneratorConfig,
    get_default_config,
    get_sample_config
)
from src.data_generator.channels import generate_channels
from src.data_generator.products import generate_products
from src.data_generator.customers import generate_customers
from src.data_generator.marketing_spend import generate_marketing_spend
from src.data_generator.orders import generate_orders_and_items
from src.data_generator.web_sessions import generate_web_sessions
from src.data_generator.validators import DatasetValidator, ValidationError

# Configure logging
logger = logging.getLogger("auraRetail")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def run_pipeline(config: GeneratorConfig) -> Dict[str, pd.DataFrame]:
    """
    Executes the entire data generation and validation pipeline.
    
    Args:
        config: Configured generation parameters.
        
    Returns:
        Dict[str, pd.DataFrame]: Validated table DataFrames.
        
    Raises:
        ValidationError: If pre-export validation fails.
    """
    start_time = time.time()
    mode_name = "SAMPLE" if config.is_sample else "FULL"
    logger.info(f"Starting {mode_name} data generation pipeline [Seed: {config.seed}]...")

    # 1. Channels
    logger.info("Generating dim_channels (6 channels)...")
    channels_df = generate_channels()

    # 2. Products
    logger.info(f"Generating dim_products ({config.n_products} products)...")
    products_df = generate_products(config)

    # 3. Customers
    logger.info(f"Generating dim_customers ({config.n_customers:,} customers across 2024-2025)...")
    customers_df = generate_customers(config)

    # 4. Marketing Spend
    logger.info(f"Generating fact_marketing_spend (731 days x 3 paid channels = {config.total_calendar_days * 3} rows)...")
    marketing_df = generate_marketing_spend(config)

    # 5. Orders & Order Items
    logger.info(f"Generating fact_orders ({config.n_orders:,} orders) and fact_order_items...")
    orders_df, order_items_df = generate_orders_and_items(customers_df, products_df, config)

    # 6. Web Sessions
    logger.info(f"Generating fact_web_sessions ({config.n_sessions:,} sessions)...")
    sessions_df = generate_web_sessions(customers_df, orders_df, config)

    tables = {
        "channels": channels_df,
        "customers": customers_df,
        "products": products_df,
        "orders": orders_df,
        "order_items": order_items_df,
        "web_sessions": sessions_df,
        "marketing_spend": marketing_df
    }

    # 7. Validation
    logger.info("Running comprehensive data validation checks...")
    validator = DatasetValidator(config)
    validator.validate_all(tables)
    logger.info("All data validation checks PASSED successfully.")

    # 8. Export CSVs
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Exporting verified CSV datasets to: {output_dir.resolve()}...")

    file_mapping = {
        "channels.csv": channels_df,
        "customers.csv": customers_df,
        "products.csv": products_df,
        "orders.csv": orders_df,
        "order_items.csv": order_items_df,
        "web_sessions.csv": sessions_df,
        "marketing_spend.csv": marketing_df
    }

    for filename, df in file_mapping.items():
        csv_path = output_dir / filename
        df.to_csv(csv_path, index=False)
        logger.debug(f"Saved {filename} ({len(df):,} rows)")

    elapsed = time.time() - start_time
    logger.info(f"Pipeline completed successfully in {elapsed:.2f} seconds.")

    # Print user-specified formatted console summary
    _print_summary(config, tables)

    return tables


def _print_summary(config: GeneratorConfig, tables: Dict[str, pd.DataFrame]):
    """Prints the exact required console summary format."""
    out_dir_display = str(config.output_dir).replace("\\", "/")
    if not out_dir_display.endswith("/"):
        out_dir_display += "/"

    if config.is_sample:
        print("\n" + "=" * 50)
        print("AURA RETAIL SAMPLE DATA GENERATION COMPLETE")
        print("=" * 43 + "\n")
    else:
        print("\n" + "=" * 50)
        print("AURA RETAIL DATA GENERATION COMPLETE")
        print("=" * 36 + "\n")

    print(f"Seed: {config.seed}\n")
    print(f"Channels       : {len(tables['channels']):,}")
    print(f"Customers      : {len(tables['customers']):,}")
    print(f"Products       : {len(tables['products']):,}")
    print(f"Orders         : {len(tables['orders']):,}")
    print(f"Order Items    : {len(tables['order_items']):,}")
    print(f"Web Sessions   : {len(tables['web_sessions']):,}")
    print(f"Marketing Rows : {len(tables['marketing_spend']):,}\n")
    print("Validation: PASSED\n")
    print("Output:")
    print(out_dir_display + "\n")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Aura Retail Synthetic Data Generator")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed (default: 42)")
    parser.add_argument("--sample", action="store_true", help="Generate representative sample dataset (data/sample/)")
    parser.add_argument("--output-dir", type=str, default=None, help="Custom output directory")
    args = parser.parse_args()

    out_path = Path(args.output_dir) if args.output_dir else None

    if args.sample:
        config = get_sample_config(seed=args.seed, output_dir=out_path)
    else:
        config = get_default_config(seed=args.seed, output_dir=out_path)

    try:
        run_pipeline(config)
    except ValidationError as e:
        logger.error(f"Generation aborted due to validation failure:\n{e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
