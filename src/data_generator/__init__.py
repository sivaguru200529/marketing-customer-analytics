"""
Aura Retail Synthetic Data Generation Package.
Provides modules and functions to generate reproducible, realistic e-commerce datasets.
"""

from src.data_generator.config import GeneratorConfig, get_default_config, get_sample_config
from src.data_generator.channels import generate_channels
from src.data_generator.products import generate_products
from src.data_generator.customers import generate_customers
from src.data_generator.marketing_spend import generate_marketing_spend
from src.data_generator.orders import generate_orders_and_items
from src.data_generator.web_sessions import generate_web_sessions
from src.data_generator.validators import DatasetValidator, ValidationError

__all__ = [
    "GeneratorConfig",
    "get_default_config",
    "get_sample_config",
    "generate_channels",
    "generate_products",
    "generate_customers",
    "generate_marketing_spend",
    "generate_orders_and_items",
    "generate_web_sessions",
    "DatasetValidator",
    "ValidationError",
]
