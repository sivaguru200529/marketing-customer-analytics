"""
Aura Retail Analytics - Phase 4 Part 3
Configuration & Constants for Customer Intelligence Dataset and Analytical Outputs.
"""

import os
from typing import Dict, List


def get_workspace_dir() -> str:
    """Return the absolute path to the workspace root."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, "..", ".."))


# Core File Paths
WORKSPACE_DIR = get_workspace_dir()
DEFAULT_CUSTOMER_ANALYTICS_CSV = os.path.join(
    WORKSPACE_DIR, "data", "03_analytics", "customer_analytics.csv"
)
DEFAULT_CUSTOMER_CLUSTERS_CSV = os.path.join(
    WORKSPACE_DIR, "data", "04_rfm", "customer_clusters.csv"
)
DEFAULT_OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "data", "04_customer_intelligence")
DEFAULT_REPORT_PATH = os.path.join(WORKSPACE_DIR, "docs", "customer_intelligence_report.md")

# Output File Paths
OUTPUT_CUSTOMER_INTELLIGENCE = os.path.join(DEFAULT_OUTPUT_DIR, "customer_intelligence.csv")
OUTPUT_VALUE_SUMMARY = os.path.join(DEFAULT_OUTPUT_DIR, "customer_value_summary.csv")
OUTPUT_SEGMENT_SUMMARY = os.path.join(DEFAULT_OUTPUT_DIR, "customer_segment_summary.csv")
OUTPUT_CLUSTER_SUMMARY = os.path.join(DEFAULT_OUTPUT_DIR, "customer_cluster_summary.csv")
OUTPUT_MATRIX_SUMMARY = os.path.join(DEFAULT_OUTPUT_DIR, "segment_cluster_matrix.csv")
OUTPUT_BEHAVIOR_SUMMARY = os.path.join(DEFAULT_OUTPUT_DIR, "customer_behavior_summary.csv")
OUTPUT_QUALITY_REPORT = os.path.join(DEFAULT_OUTPUT_DIR, "customer_intelligence_quality_report.csv")

# Baseline Invariants & Target Parameters
EXPECTED_CUSTOMER_COUNT = 10000
EXPECTED_TOTAL_DELIVERED_REVENUE = 14584810.24
ANCHOR_DATE = "2025-12-31"
SELECTED_K = 3

# Segment Ordering (authoritative from Phase 3 SQL)
SEGMENT_PRIORITY_ORDER: List[str] = [
    "Champions",
    "Loyal Customers",
    "Recent Inquirers",
    "Promising",
    "At Risk High Value",
    "Need Attention",
    "Lost / Dormant",
    "Potential / Developing",
]

# Neutral Cluster Descriptions
CLUSTER_DESCRIPTIONS: Dict[int, str] = {
    0: "High Engagement & Value",
    1: "Low Order / Moderate Recency",
    2: "Zero Delivered Orders",
}

# Deterministic Classification Band Thresholds
VALUE_BAND_HIGH = 1000.0
VALUE_BAND_MID = 300.0

ENGAGEMENT_ACTIVE_DAYS = 90
ENGAGEMENT_LAPSING_DAYS = 180
ENGAGEMENT_DORMANT_DAYS = 365

FRICTION_HIGH_RATE = 0.25
