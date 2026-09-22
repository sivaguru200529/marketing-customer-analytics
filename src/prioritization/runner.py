"""
Aura Retail Analytics - Phase 5 Part 2
CLI Pipeline Runner & Orchestrator for Business Prioritization & Customer Intelligence.

Usage:
    python -m src.prioritization.runner
"""

import logging
import os
import sys
import time
from typing import Optional

from src.prioritization.config import (
    DEFAULT_FIGURES_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPORT_PATH,
    DEFAULT_SUMMARIES_DIR,
    INPUT_CHURN_PREDICTIONS_CSV,
    INPUT_CUSTOMER_INTELLIGENCE_CSV,
    OUTPUT_BUSINESS_PRIORITIZATION_CSV,
    PRIORITIZATION_COLUMNS,
)
from src.prioritization.loader import (
    join_intelligence_and_predictions,
    load_and_validate_inputs,
)
from src.prioritization.recommendations import apply_recommendations
from src.prioritization.report import generate_business_prioritization_report
from src.prioritization.scoring import compute_all_scores
from src.prioritization.segmentation import apply_segmentation
from src.prioritization.summaries import generate_all_summaries
from src.prioritization.visualization import generate_all_visualizations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("src.prioritization.runner")


def run_prioritization_pipeline(
    intelligence_path: Optional[str] = None,
    churn_path: Optional[str] = None,
    output_path: Optional[str] = None,
) -> int:
    """Execute the end-to-end business prioritization pipeline."""
    start_time = time.time()
    print("================================================================================")
    print("AURA RETAIL ANALYTICS — PHASE 5 PART 2: BUSINESS PRIORITIZATION PIPELINE")
    print("================================================================================")

    if intelligence_path is None:
        intelligence_path = INPUT_CUSTOMER_INTELLIGENCE_CSV
    if churn_path is None:
        churn_path = INPUT_CHURN_PREDICTIONS_CSV
    if output_path is None:
        output_path = OUTPUT_BUSINESS_PRIORITIZATION_CSV

    # 1. Load Inputs & Validate
    print("\n[1/10] Loading and validating Phase 4 & Phase 5 Part 1 inputs...")
    df_intel, df_churn = load_and_validate_inputs(
        intelligence_path=intelligence_path,
        churn_path=churn_path,
    )
    print(f"  -> Customer Intelligence: {len(df_intel):,} rows x {df_intel.shape[1]} cols")
    print(f"  -> Churn Predictions:     {len(df_churn):,} rows x {df_churn.shape[1]} cols")

    # 2. Join Datasets on customer_id
    print("\n[2/10] Executing controlled customer-level join on customer_id...")
    df_joined = join_intelligence_and_predictions(df_intel, df_churn)
    print(f"  -> Joined Customer Grain: {len(df_joined):,} rows (100% unique primary keys)")

    # 3. Calculate Normalized Scores
    print("\n[3/10] Calculating normalized risk, value, engagement, and friction scores...")
    df_scored = compute_all_scores(df_joined)
    print(f"  -> Risk Score:            Mean = {df_scored['risk_score'].mean():.4f}")
    print(f"  -> Value Score:           Mean = {df_scored['value_score'].mean():.4f}")
    print(f"  -> Engagement Score:      Mean = {df_scored['engagement_score'].mean():.4f}")
    print(f"  -> Friction Score:        Mean = {df_scored['friction_score'].mean():.4f}")

    # 4. Composite Priority Score (No min-max scaling)
    print("\n[4/10] Formulating composite priority score (0.50 Risk + 0.30 Value + 0.10 Eng + 0.10 Fric)...")
    print(f"  -> Composite Priority:    Mean = {df_scored['priority_score'].mean():.4f}, Min = {df_scored['priority_score'].min():.4f}, Max = {df_scored['priority_score'].max():.4f}")

    # 5. Assign Priority Tiers & Business Segments
    print("\n[5/10] Assigning priority tiers and 9-level precedence business segments...")
    df_segmented = apply_segmentation(df_scored)
    tier_counts = df_segmented["priority_tier"].value_counts()
    for tier_name, cnt in tier_counts.items():
        print(f"  -> {tier_name:<16}: {cnt:,} ({cnt/len(df_segmented)*100:.1f}%)")

    # 6. Assign Actions & Campaigns
    print("\n[6/10] Generating deterministic action recommendations and campaign mappings...")
    df_final = apply_recommendations(df_segmented)
    action_counts = df_final["recommended_action"].value_counts()
    for act_name, cnt in action_counts.items():
        print(f"  -> {act_name:<42}: {cnt:,} ({cnt/len(df_final)*100:.1f}%)")

    # 7. Export Primary Business Prioritization Dataset
    print("\n[7/10] Exporting final business prioritization dataset...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Ensure ordered columns
    cols_to_export = [c for c in PRIORITIZATION_COLUMNS if c in df_final.columns]
    df_export = df_final[cols_to_export]
    df_export.to_csv(output_path, index=False)
    print(f"  -> Exported:              {output_path} ({len(df_export):,} rows x {len(cols_to_export)} cols)")

    # 8. Generate Summary CSV Files
    print("\n[8/10] Generating 6 analytical summary tables...")
    summaries = generate_all_summaries(
        df=df_final,
        output_dir=DEFAULT_OUTPUT_DIR,
        summaries_dir=DEFAULT_SUMMARIES_DIR,
    )
    for filename, df_sum in summaries.items():
        print(f"  -> Summary [{filename}]: {len(df_sum):,} rows x {df_sum.shape[1]} cols")

    # 9. Render Visualizations
    print("\n[9/10] Rendering 7 publication-grade Matplotlib figures...")
    chart_paths = generate_all_visualizations(
        df=df_final,
        output_dir=DEFAULT_FIGURES_DIR,
    )
    for name, path in chart_paths.items():
        print(f"  -> Chart [{name}]: {path}")

    # 10. Compile Documentation Report
    print("\n[10/10] Compiling 17-section documentation report...")
    report_file = generate_business_prioritization_report(
        df=df_final,
        summaries=summaries,
        report_path=DEFAULT_REPORT_PATH,
    )
    print(f"  -> Compiled Report:       {report_file}")

    elapsed = time.time() - start_time
    print("\n================================================================================")
    print(f"PHASE 5 PART 2 COMPLETED SUCCESSFULLY IN {elapsed:.2f}s")
    print(f"Final Dataset: {output_path} | Customers: {len(df_export):,}")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_prioritization_pipeline())
