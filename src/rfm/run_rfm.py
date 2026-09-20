"""
Aura Retail Analytics - Phase 4 Part 2
Command-Line Entry Point for RFM Analysis and Customer Segmentation Pipeline.

Usage:
    python -m src.rfm.run_rfm
"""

import os
import sys
import time
from typing import Dict, Optional
import pandas as pd

from src.rfm.config import (
    DEFAULT_INPUT_CSV,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_FIGURES_DIR,
    DEFAULT_REPORT_PATH,
    get_workspace_dir,
)
from src.rfm.loader import load_customer_data
from src.rfm.rfm_calculation import extract_rfm_dataset, export_customer_rfm
from src.rfm.rfm_scoring import compute_rfm_scores
from src.rfm.parity import evaluate_rfm_parity, export_rfm_parity_report
from src.rfm.segmentation import apply_rfm_segmentation, export_customer_rfm_segments
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


def run_rfm_pipeline(
    input_csv: Optional[str] = None,
    output_dir: Optional[str] = None,
    figures_dir: Optional[str] = None,
    report_path: Optional[str] = None,
    generate_charts: bool = True,
) -> Dict[str, str]:
    """
    Execute full end-to-end Phase 4 Part 2 RFM Analysis & Customer Segmentation pipeline.

    Returns:
        Dict mapping artifact names to their generated output filepaths.
    """
    start_time = time.time()
    workspace = get_workspace_dir()

    if input_csv is None:
        input_csv = DEFAULT_INPUT_CSV
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    if figures_dir is None:
        figures_dir = DEFAULT_FIGURES_DIR
    if report_path is None:
        report_path = DEFAULT_REPORT_PATH

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 78)
    print("Aura Retail Analytics -- Phase 4 Part 2: RFM Analysis & Customer Segmentation")
    print("=" * 78)

    # 1. Ingestion & Validation
    print(f"\n[1/9] Ingesting Customer Analytics Dataset: {input_csv}")
    cust_df = load_customer_data(input_csv)
    print(f"  [OK] Ingested {len(cust_df):,d} customer records across {len(cust_df.columns)} columns.")

    # 2. RFM Metric Extraction
    print(f"\n[2/9] Extracting and Validating Core RFM Dimensions...")
    rfm_df = extract_rfm_dataset(cust_df)
    export_customer_rfm(rfm_df, output_dir)
    print(f"  [OK] Extracted Recency, Frequency, and Monetary metrics for {len(rfm_df):,d} customers.")

    # 3. RFM Scoring
    print(f"\n[3/9] Calculating Tie-Safe RFM Quantile Scores (1 to 5)...")
    scored_df = compute_rfm_scores(rfm_df)
    print(f"  [OK] Assigned rfm_recency_score, rfm_frequency_score, rfm_monetary_score, and composite representations.")

    # 4. Deterministic Segmentation (Authoritative Ordered Decision Tree)
    print(f"\n[4/9] Applying Authoritative Phase 3 Ordered Segmentation Decision Tree...")
    # Apply using Phase 3 authoritative scores to preserve established baseline
    seg_df = apply_rfm_segmentation(
        scored_df,
        r_col="p3_r_score",
        f_col="p3_f_score",
        m_col="p3_m_score",
        output_col="rfm_segment"
    )
    export_customer_rfm_segments(seg_df, output_dir)
    print(f"  [OK] Assigned 8 mutually exclusive RFM segments to 100% of customers.")

    # 5. Phase 3 ↔ Python Parity Evaluation
    print(f"\n[5/9] Evaluating Empirical Phase 3 vs Python RFM Parity...")
    # Evaluate Python segment assignment as well
    py_seg_df = apply_rfm_segmentation(
        scored_df,
        r_col="rfm_recency_score",
        f_col="rfm_frequency_score",
        m_col="rfm_monetary_score",
        output_col="rfm_segment"
    )
    eval_parity_df = scored_df.copy()
    eval_parity_df["rfm_segment"] = py_seg_df["rfm_segment"]
    audit_df, parity_metrics, parity_summary_df = evaluate_rfm_parity(eval_parity_df)
    export_rfm_parity_report(parity_summary_df, output_dir)
    print(f"  [OK] R-score parity: {parity_metrics['r_parity_pct']:.1f}% | M-score parity: {parity_metrics['m_parity_pct']:.1f}% | F-score parity: {parity_metrics['f_parity_pct']:.1f}%")
    print(f"  [OK] Parity summary saved to data/04_rfm/rfm_parity_report.csv.")

    # 6. K-Means Preprocessing & K Evaluation
    print(f"\n[6/9] Preprocessing Features & Evaluating K-Means (K=2 to 8)...")
    X_scaled, X_df, scaler = validate_and_preprocess_features(seg_df)
    eval_df = evaluate_kmeans_clusters(X_scaled)
    selected_k, k_rationale = select_optimal_k(eval_df)
    print(f"  [OK] Evaluated K=2 through 8. Selected: K={selected_k} ({k_rationale})")

    # 7. Final K-Means Model & Cluster Profiling
    print(f"\n[7/9] Training Final K-Means (K={selected_k}) & Generating Behavioral Profiles...")
    clusters_df, km_model = fit_final_kmeans(X_scaled, seg_df, selected_k)
    export_clustering_outputs(eval_df, clusters_df, output_dir)

    seg_summary_df = profile_rfm_segments(clusters_df)
    clus_summary_df = profile_kmeans_clusters(clusters_df)
    comp_df = compare_rfm_and_clusters(clusters_df)
    export_profiling_outputs(seg_summary_df, clus_summary_df, comp_df, output_dir)
    print(f"  [OK] Generated rfm_segment_summary.csv, cluster_profile.csv, and rfm_cluster_comparison.csv.")

    # 8. Visualizations
    generated_figures = {}
    if generate_charts:
        print(f"\n[8/9] Generating 12 Publication-Grade Matplotlib Charts under: {figures_dir}")
        generated_figures = generate_all_visualizations(clusters_df, eval_df, selected_k, figures_dir)
        for name, path in generated_figures.items():
            print(f"  [OK] Figure: {os.path.basename(path)}")

    # 9. Quality Validation & Report Generation
    print(f"\n[9/9] Running Mathematical Invariants Validation & Compiling Report...")
    quality_df = run_rfm_quality_validation(
        customer_df=cust_df,
        rfm_df=rfm_df,
        scored_df=seg_df,
        clusters_df=clusters_df,
        eval_df=eval_df,
        seg_summary_df=seg_summary_df,
        parity_summary_df=parity_summary_df,
        selected_k=selected_k,
        X_scaled=X_scaled,
    )
    export_rfm_quality_report(quality_df, output_dir)
    for _, q in quality_df.iterrows():
        print(f"  [OK] [{q['check_name']}]: {q['status']} ({q['details']})")

    generate_rfm_segmentation_report(
        eval_df=eval_df,
        selected_k=selected_k,
        k_rationale=k_rationale,
        seg_summary_df=seg_summary_df,
        clus_summary_df=clus_summary_df,
        comp_df=comp_df,
        parity_summary_df=parity_summary_df,
        quality_df=quality_df,
        metrics=parity_metrics,
        output_filepath=report_path,
    )
    print(f"  [OK] Documentation report compiled at: {os.path.relpath(report_path, workspace)}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 78)
    print(f"Phase 4 Part 2 RFM Pipeline Complete in {elapsed:.2f}s! All artifacts generated.")
    print("=" * 78 + "\n")

    return {
        "customer_rfm": os.path.join(output_dir, "customer_rfm.csv"),
        "customer_rfm_segments": os.path.join(output_dir, "customer_rfm_segments.csv"),
        "customer_clusters": os.path.join(output_dir, "customer_clusters.csv"),
        "rfm_segment_summary": os.path.join(output_dir, "rfm_segment_summary.csv"),
        "cluster_evaluation": os.path.join(output_dir, "cluster_evaluation.csv"),
        "cluster_profile": os.path.join(output_dir, "cluster_profile.csv"),
        "rfm_cluster_comparison": os.path.join(output_dir, "rfm_cluster_comparison.csv"),
        "rfm_quality_report": os.path.join(output_dir, "rfm_quality_report.csv"),
        "rfm_parity_report": os.path.join(output_dir, "rfm_parity_report.csv"),
        "rfm_segmentation_report_md": report_path,
    }


def main():
    """CLI execution entrypoint."""
    try:
        run_rfm_pipeline()
    except Exception as e:
        print(f"\n[ERROR] RFM Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
