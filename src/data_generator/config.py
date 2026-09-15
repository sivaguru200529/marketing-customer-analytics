"""
Configuration module for the Aura Retail synthetic data generator.
Defines entity volumes, calendar date boundaries (731 days spanning 2024-2025),
random seeds, and file paths.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass
class GeneratorConfig:
    """Configuration container for synthetic dataset generation."""
    seed: int = 42
    start_date: date = date(2024, 1, 1)
    end_date: date = date(2025, 12, 31)  # 731 days inclusive (2024 leap year)
    
    # Target entity row counts
    n_customers: int = 10_000
    n_products: int = 150
    n_orders: int = 50_000
    n_sessions: int = 150_000
    min_order_items: int = 120_000
    
    # Output path
    output_dir: Path = Path("data/01_raw")
    is_sample: bool = False

    @property
    def total_calendar_days(self) -> int:
        """Returns total calendar days in the observation window (731 days)."""
        return (self.end_date - self.start_date).days + 1


def get_default_config(seed: int = 42, output_dir: Path | None = None) -> GeneratorConfig:
    """Returns standard full-scale configuration (50k orders, 10k customers)."""
    return GeneratorConfig(
        seed=seed,
        output_dir=output_dir or Path("data/01_raw"),
        is_sample=False
    )


def get_sample_config(seed: int = 42, output_dir: Path | None = None) -> GeneratorConfig:
    """Returns lightweight sample configuration (1.5k orders, 500 customers)."""
    return GeneratorConfig(
        seed=seed,
        n_customers=500,
        n_products=50,
        n_orders=1_500,
        n_sessions=4_500,
        min_order_items=3_600,
        output_dir=output_dir or Path("data/sample"),
        is_sample=True
    )
