"""
Aura Retail Analytics - Phase 4 Part 3
CLI Pipeline Entry Point for Customer Intelligence Dataset & Analytical Outputs.

Usage:
    python -m src.customer_intelligence.run_customer_intelligence
"""

import sys
import time
from src.customer_intelligence.config import (
    DEFAULT_CUSTOMER_ANALYTICS_CSV,
    DEFAULT_CUSTOMER_CLUSTERS_CSV,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPORT_PATH,
)
from src.customer_intelligence.intelligence_dataset import build_customer_intelligence_dataset
from src.customer_intelligence.loader import load_and_validate_inputs
from src.customer_intelligence.report import generate_customer_intelligence_report
from src.customer_intelligence.summaries import generate_all_summaries
from src.customer_intelligence.validation import run_customer_intelligence_quality_checks


def run_pipeline() -> int:
    """Execute the end-to-end Customer Intelligence pipeline."""
    start_time = time.time()
    print("================================================================================")
    print("AURA RETAIL ANALYTICS — PHASE 4 PART 3: CUSTOMER INTELLIGENCE PIPELINE")
    print("================================================================================")

    # 1. Load Inputs
    print("\n[1/5] Loading and validating upstream inputs...")
    df_analytics, df_clusters = load_and_validate_inputs(
        analytics_path=DEFAULT_CUSTOMER_ANALYTICS_CSV,
        clusters_path=DEFAULT_CUSTOMER_CLUSTERS_CSV,
    )
    print(f"  -> Ingested Customer Analytics: {df_analytics.shape[0]:,} rows x {df_analytics.shape[1]} cols")
    print(f"  -> Ingested Customer Clusters:  {df_clusters.shape[0]:,} rows x {df_clusters.shape[1]} cols")

    # 2. Build Customer Intelligence Dataset
    print("\n[2/5] Building unified Customer Intelligence dataset & engineering features...")
    df_intel = build_customer_intelligence_dataset(df_analytics, df_clusters)
    print(f"  -> Assembled Dataset: {df_intel.shape[0]:,} rows x {df_intel.shape[1]} cols")
    print(f"  -> Exported to: {DEFAULT_OUTPUT_DIR}/customer_intelligence.csv")

    # 3. Generate Analytical Summaries
    print("\n[3/5] Generating supporting analytical summaries & cross-tabulations...")
    summaries = generate_all_summaries(df_intel, output_dir=DEFAULT_OUTPUT_DIR)
    for name, df_sum in summaries.items():
        print(f"  -> Generated {name}.csv ({df_sum.shape[0]} rows x {df_sum.shape[1]} cols)")

    # 4. Data Quality & Invariants Validation
    print("\n[4/5] Executing 18 rigorous data quality & mathematical invariant checks...")
    all_passed, df_quality = run_customer_intelligence_quality_checks(df_intel)
    passed_count = int((df_quality["status"] == "PASSED").sum())
    total_count = len(df_quality)
    print(f"  -> Quality Invariant Results: {passed_count}/{total_count} PASSED")
    if not all_passed:
        failed = df_quality[df_quality["status"] != "PASSED"]
        for _, row in failed.iterrows():
            print(f"     [FAILED] {row['check_name']}: {row['details']}")
        return 1

    # 5. Documentation Report Generation
    print("\n[5/5] Compiling comprehensive customer intelligence documentation report...")
    generate_customer_intelligence_report(
        df_intel=df_intel,
        summaries=summaries,
        df_quality=df_quality,
        report_path=DEFAULT_REPORT_PATH,
    )
    print(f"  -> Generated: {DEFAULT_REPORT_PATH}")

    elapsed = time.time() - start_time
    print("\n================================================================================")
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f}s — ALL INVARIANTS VERIFIED")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_pipeline())
