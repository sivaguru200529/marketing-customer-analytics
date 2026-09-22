"""
Aura Retail Analytics - Phase 5 Part 2
Configuration & Constants for Business Prioritization & Actionable Customer Intelligence.
"""

import os
from typing import Dict, List


def get_workspace_dir() -> str:
    """Return the absolute path to the workspace root."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, "..", ".."))


# Core File Paths
WORKSPACE_DIR = get_workspace_dir()
INPUT_CUSTOMER_INTELLIGENCE_CSV = os.path.join(
    WORKSPACE_DIR, "data", "04_customer_intelligence", "customer_intelligence.csv"
)
INPUT_CHURN_PREDICTIONS_CSV = os.path.join(
    WORKSPACE_DIR, "data", "05_churn", "churn_predictions.csv"
)
DEFAULT_OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "data", "05_churn")
DEFAULT_SUMMARIES_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "summaries")
DEFAULT_FIGURES_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "figures")
DEFAULT_REPORT_PATH = os.path.join(WORKSPACE_DIR, "docs", "business_prioritization_report.md")

# Primary Output File
OUTPUT_BUSINESS_PRIORITIZATION_CSV = os.path.join(
    DEFAULT_OUTPUT_DIR, "business_prioritization.csv"
)

# Summary Output Files (in data/05_churn/ and data/05_churn/summaries/)
SUMMARY_PRIORITY_TIER = "priority_tier_summary.csv"
SUMMARY_BUSINESS_SEGMENT = "business_segment_summary.csv"
SUMMARY_RECOMMENDED_ACTION = "recommended_action_summary.csv"
SUMMARY_RECOMMENDED_CAMPAIGN = "recommended_campaign_summary.csv"
SUMMARY_RISK_VALUE = "risk_value_summary.csv"
SUMMARY_FRICTION = "friction_summary.csv"

# Invariants & Reference Benchmarks
EXPECTED_CUSTOMER_COUNT: int = 10000

# Priority Score Weights (Strictly must sum to 1.0, all non-negative)
PRIORITY_WEIGHT_RISK: float = 0.50
PRIORITY_WEIGHT_VALUE: float = 0.30
PRIORITY_WEIGHT_ENGAGEMENT: float = 0.10
PRIORITY_WEIGHT_FRICTION: float = 0.10

# Priority Tier Deterministic Thresholds
PRIORITY_TIER_HIGH_THRESHOLD: float = 0.75
PRIORITY_TIER_MEDIUM_THRESHOLD: float = 0.50

# Churn Risk Cutoffs (from Phase 5 Part 1)
CHURN_RISK_HIGH_THRESHOLD: float = 0.65
CHURN_RISK_LOW_THRESHOLD: float = 0.35

# Value Band Cutoffs (from Phase 4 Customer Intelligence)
VALUE_HIGH_THRESHOLD: float = 1000.0
VALUE_MID_THRESHOLD: float = 300.0

# Friction Cutoff for High Friction Segment / Action
FRICTION_HIGH_SCORE_THRESHOLD: float = 0.35

# Developing Engagement Cutoff
ENGAGEMENT_DEVELOPING_THRESHOLD: float = 0.45

# Engagement Component Weights
ENGAGEMENT_WEIGHT_RECENCY: float = 0.50
ENGAGEMENT_WEIGHT_SESSIONS: float = 0.30
ENGAGEMENT_WEIGHT_ORDERS: float = 0.20

# Friction Component Weights
FRICTION_WEIGHT_ORDER_RATE: float = 0.40
FRICTION_WEIGHT_CART_ABANDON: float = 0.35
FRICTION_WEIGHT_TICKETS: float = 0.25
FRICTION_MAX_TICKETS: float = 3.0

# Campaign Action Mappings
CAMPAIGN_MAPPING: Dict[str, str] = {
    "High-Value Retention + Friction Resolution": "High-Value Retention Campaign",
    "Retention / High-Value Intervention": "High-Value Retention Campaign",
    "Targeted Retention": "Targeted Retention Campaign",
    "Friction Resolution": "Friction Resolution Campaign",
    "Engagement Reinforcement": "Engagement Reinforcement Campaign",
    "Relationship Development": "Loyalty & Relationship Campaign",
    "Monitor": "Automated Monitoring",
}

# Final Dataset Column Order
PRIORITIZATION_COLUMNS: List[str] = [
    "customer_id",
    "churn_probability",
    "predicted_churn",
    "churn_risk_band",
    "customer_value_band",
    "engagement_band",
    "friction_band",
    "delivered_revenue",
    "delivered_orders",
    "recency_days",
    "total_web_sessions",
    "friction_rate",
    "cart_abandonment_rate",
    "total_support_tickets",
    "risk_score",
    "value_score",
    "engagement_score",
    "friction_score",
    "priority_score",
    "priority_tier",
    "business_segment",
    "recommended_action",
    "recommended_campaign",
]
