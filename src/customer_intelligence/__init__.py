"""
Aura Retail Analytics - Phase 4 Part 3
Customer Intelligence Package Interface.
"""

from src.customer_intelligence.config import (
    DEFAULT_CUSTOMER_ANALYTICS_CSV,
    DEFAULT_CUSTOMER_CLUSTERS_CSV,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPORT_PATH,
    EXPECTED_CUSTOMER_COUNT,
    EXPECTED_TOTAL_DELIVERED_REVENUE,
    OUTPUT_CUSTOMER_INTELLIGENCE,
    SEGMENT_PRIORITY_ORDER,
)
from src.customer_intelligence.feature_engineering import compute_derived_features
from src.customer_intelligence.intelligence_dataset import build_customer_intelligence_dataset
from src.customer_intelligence.loader import load_and_validate_inputs
from src.customer_intelligence.report import generate_customer_intelligence_report
from src.customer_intelligence.summaries import generate_all_summaries
from src.customer_intelligence.validation import run_customer_intelligence_quality_checks

__all__ = [
    "DEFAULT_CUSTOMER_ANALYTICS_CSV",
    "DEFAULT_CUSTOMER_CLUSTERS_CSV",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_REPORT_PATH",
    "EXPECTED_CUSTOMER_COUNT",
    "EXPECTED_TOTAL_DELIVERED_REVENUE",
    "OUTPUT_CUSTOMER_INTELLIGENCE",
    "SEGMENT_PRIORITY_ORDER",
    "build_customer_intelligence_dataset",
    "compute_derived_features",
    "generate_all_summaries",
    "generate_customer_intelligence_report",
    "load_and_validate_inputs",
    "run_customer_intelligence_quality_checks",
]
