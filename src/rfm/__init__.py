"""
Aura Retail Analytics - Phase 4 Part 2
Python Customer Intelligence Package: RFM Analysis & Customer Segmentation.
"""

from src.rfm.config import (
    DEFAULT_INPUT_CSV,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_FIGURES_DIR,
    DEFAULT_REPORT_PATH,
    EXPECTED_CUSTOMER_COUNT,
    RANDOM_STATE,
    N_INIT,
    K_EVAL_RANGE,
    SILHOUETTE_TIE_TOLERANCE,
    SEGMENT_PRIORITY_ORDER,
)
from src.rfm.loader import load_customer_data
from src.rfm.rfm_calculation import extract_rfm_dataset, export_customer_rfm
from src.rfm.rfm_scoring import (
    calculate_recency_score,
    calculate_frequency_score,
    calculate_monetary_score,
    compute_rfm_scores,
)
from src.rfm.parity import evaluate_rfm_parity, export_rfm_parity_report
from src.rfm.segmentation import (
    assign_rfm_segment,
    apply_rfm_segmentation,
    export_customer_rfm_segments,
)
from src.rfm.clustering import (
    validate_and_preprocess_features,
    evaluate_kmeans_clusters,
    select_optimal_k,
    fit_final_kmeans,
    export_clustering_outputs,
)
from src.rfm.profiling import (
    profile_rfm_segments,
    profile_kmeans_clusters,
    compare_rfm_and_clusters,
    export_profiling_outputs,
)
from src.rfm.visualization import generate_all_visualizations
from src.rfm.validation import run_rfm_quality_validation, export_rfm_quality_report
from src.rfm.report import generate_rfm_segmentation_report

__all__ = [
    "DEFAULT_INPUT_CSV",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_FIGURES_DIR",
    "DEFAULT_REPORT_PATH",
    "EXPECTED_CUSTOMER_COUNT",
    "RANDOM_STATE",
    "N_INIT",
    "K_EVAL_RANGE",
    "SILHOUETTE_TIE_TOLERANCE",
    "SEGMENT_PRIORITY_ORDER",
    "load_customer_data",
    "extract_rfm_dataset",
    "export_customer_rfm",
    "calculate_recency_score",
    "calculate_frequency_score",
    "calculate_monetary_score",
    "compute_rfm_scores",
    "evaluate_rfm_parity",
    "export_rfm_parity_report",
    "assign_rfm_segment",
    "apply_rfm_segmentation",
    "export_customer_rfm_segments",
    "validate_and_preprocess_features",
    "evaluate_kmeans_clusters",
    "select_optimal_k",
    "fit_final_kmeans",
    "export_clustering_outputs",
    "profile_rfm_segments",
    "profile_kmeans_clusters",
    "compare_rfm_and_clusters",
    "export_profiling_outputs",
    "generate_all_visualizations",
    "run_rfm_quality_validation",
    "export_rfm_quality_report",
    "generate_rfm_segmentation_report",
]
