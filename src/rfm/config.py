"""
Aura Retail Analytics - Phase 4 Part 2
Configuration & Constants for RFM Analysis and Customer Segmentation.
"""

import os
from typing import List


def get_workspace_dir() -> str:
    """Return the absolute path to the workspace root."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, "..", ".."))


# Core File Paths
WORKSPACE_DIR = get_workspace_dir()
DEFAULT_INPUT_CSV = os.path.join(WORKSPACE_DIR, "data", "03_analytics", "customer_analytics.csv")
DEFAULT_OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "data", "04_rfm")
DEFAULT_FIGURES_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "figures")
DEFAULT_REPORT_PATH = os.path.join(WORKSPACE_DIR, "docs", "rfm_segmentation_report.md")

# Expected Customer Population
EXPECTED_CUSTOMER_COUNT = 10000

# Primary RFM Feature Names in Source Data
COL_CUSTOMER_ID = "customer_id"
COL_RECENCY = "recency_days"
COL_FREQUENCY = "delivered_orders"
COL_MONETARY = "delivered_revenue"

# Additional Supporting Feature Names
COL_GROSS_REVENUE = "gross_revenue"
COL_TOTAL_ORDERS = "total_orders"
COL_DELIVERED_AOV = "delivered_aov"
COL_TOTAL_UNITS = "total_units_purchased"
COL_RETURNED_ORDERS = "returned_orders"
COL_CANCELLED_ORDERS = "cancelled_orders"

# Phase 3 Baseline Names
COL_P3_R_SCORE = "r_score"
COL_P3_F_SCORE = "f_score"
COL_P3_M_SCORE = "m_score"
COL_P3_SEGMENT = "rfm_segment"

# Defensible Feature Transformation Settings
TRANSFORM_RECENCY = False       # Keep recency in original linear scale (days)
TRANSFORM_FREQUENCY = True      # Apply np.log1p for heavy right-skew
TRANSFORM_MONETARY = True       # Apply np.log1p for heavy right-skew

# K-Means Clustering Settings
RANDOM_STATE = 42
N_INIT = 10
K_EVAL_RANGE: List[int] = list(range(2, 9))  # K = 2 through 8
SILHOUETTE_TIE_TOLERANCE = 0.001            # Near-tie tolerance choosing smaller K

# Authoritative Segmentation Decision Tree Priority Order (from Phase 3 SQL)
SEGMENT_PRIORITY_ORDER = [
    "Champions",
    "Loyal Customers",
    "Recent Inquirers",
    "Promising",
    "At Risk High Value",
    "Need Attention",
    "Lost / Dormant",
    "Potential / Developing",
]
