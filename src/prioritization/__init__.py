"""
Aura Retail Analytics - Phase 5 Part 2
Business Prioritization & Actionable Customer Intelligence Package.
"""

from src.prioritization.config import (
    CAMPAIGN_MAPPING,
    PRIORITIZATION_COLUMNS,
    PRIORITY_TIER_HIGH_THRESHOLD,
    PRIORITY_TIER_MEDIUM_THRESHOLD,
    PRIORITY_WEIGHT_ENGAGEMENT,
    PRIORITY_WEIGHT_FRICTION,
    PRIORITY_WEIGHT_RISK,
    PRIORITY_WEIGHT_VALUE,
)
from src.prioritization.loader import (
    join_intelligence_and_predictions,
    load_and_validate_inputs,
)
from src.prioritization.recommendations import (
    apply_recommendations,
    assign_recommended_action,
    assign_recommended_campaign,
)
from src.prioritization.report import generate_business_prioritization_report
from src.prioritization.runner import run_prioritization_pipeline
from src.prioritization.scoring import (
    calculate_composite_priority_score,
    calculate_engagement_score,
    calculate_friction_score,
    calculate_risk_score,
    calculate_value_score,
    compute_all_scores,
    validate_priority_weights,
)
from src.prioritization.segmentation import (
    apply_segmentation,
    assign_business_segment,
    assign_priority_tier,
)
from src.prioritization.summaries import generate_all_summaries
from src.prioritization.visualization import generate_all_visualizations

__all__ = [
    "PRIORITY_WEIGHT_RISK",
    "PRIORITY_WEIGHT_VALUE",
    "PRIORITY_WEIGHT_ENGAGEMENT",
    "PRIORITY_WEIGHT_FRICTION",
    "PRIORITY_TIER_HIGH_THRESHOLD",
    "PRIORITY_TIER_MEDIUM_THRESHOLD",
    "CAMPAIGN_MAPPING",
    "PRIORITIZATION_COLUMNS",
    "load_and_validate_inputs",
    "join_intelligence_and_predictions",
    "validate_priority_weights",
    "calculate_risk_score",
    "calculate_value_score",
    "calculate_engagement_score",
    "calculate_friction_score",
    "calculate_composite_priority_score",
    "compute_all_scores",
    "assign_priority_tier",
    "assign_business_segment",
    "apply_segmentation",
    "assign_recommended_action",
    "assign_recommended_campaign",
    "apply_recommendations",
    "generate_all_summaries",
    "generate_all_visualizations",
    "generate_business_prioritization_report",
    "run_prioritization_pipeline",
]
