"""
Aura Retail Analytics - Phase 4 Part 1
Command-Line Entry Point for Python EDA & Data Quality Pipeline.

Usage:
    python -m src.eda.run_eda
"""

import os
import sys
import time
from typing import Dict, Optional
import pandas as pd

from src.eda.loader import load_all_analytics_datasets, get_dataset_profiles
from src.eda.quality import run_full_data_quality_audit, export_data_quality_reports
from src.eda.customer_eda import analyze_customer_metrics, plot_customer_visualizations, export_customer_summary
from src.eda.product_eda import analyze_product_metrics, plot_product_visualizations, export_product_summary
from src.eda.revenue_eda import analyze_revenue_metrics, plot_revenue_visualizations, export_revenue_summary
from src.eda.marketing_eda import analyze_marketing_metrics, plot_marketing_visualizations, export_marketing_summary
from src.eda.cohort_eda import analyze_cohort_metrics, plot_cohort_visualizations, export_cohort_summary
from src.eda.kpi_eda import analyze_business_kpis, export_business_kpi_summary
from src.eda.report import generate_eda_report_markdown


def get_workspace_dir() -> str:
    """Return workspace root directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, "..", ".."))


def run_eda_pipeline(
    data_dir: Optional[str] = None,
    output_base_dir: Optional[str] = None,
    report_path: Optional[str] = None,
    generate_charts: bool = True,
) -> Dict[str, str]:
    """
    Execute full end-to-end Phase 4 Part 1 EDA and Data Quality pipeline.

    Returns:
        Dict mapping artifact descriptions to their generated output filepaths.
    """
    start_time = time.time()
    workspace = get_workspace_dir()

    if data_dir is None:
        data_dir = os.path.join(workspace, "data", "03_analytics")
    if output_base_dir is None:
        output_base_dir = os.path.join(workspace, "data", "04_eda")
    if report_path is None:
        report_path = os.path.join(workspace, "docs", "eda_report.md")

    figures_dir = os.path.join(output_base_dir, "figures")
    summaries_dir = os.path.join(output_base_dir, "summaries")
    reports_dir = os.path.join(output_base_dir, "reports")

    os.makedirs(figures_dir, exist_ok=True)
    os.makedirs(summaries_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    # Support windows console utf-8
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 78)
    print("Aura Retail Analytics -- Phase 4 Part 1: Python EDA & Data Quality Pipeline")
    print("=" * 78)

    # 1. Ingestion & Profile
    print(f"\n[1/7] Ingesting Phase 3 Analytical Datasets from: {data_dir}")
    datasets = load_all_analytics_datasets(data_dir=data_dir)
    profiles = get_dataset_profiles(datasets)
    for _, row in profiles.iterrows():
        print(f"  [OK] Loaded {row['filename']:<28} | Rows: {row['rows']:>6,d} | Cols: {row['columns']:>2d} | Nulls: {row['total_null_cells']:>4d}")

    # 2. Data Quality Audits
    print(f"\n[2/7] Executing Exhaustive Data Quality Audits...")
    quality_results = run_full_data_quality_audit(datasets)
    export_data_quality_reports(quality_results, summaries_dir)
    export_data_quality_reports(quality_results, reports_dir)
    for _, q in quality_results["quality_summary"].iterrows():
        print(f"  [OK] [{q['audit_category']}] Status: {q['status']} (Evaluated: {q['evaluated_items']}, Passed: {q['passed_items']})")

    # 3. Customer EDA
    print(f"\n[3/7] Analyzing Customer Behavior & RFM Segmentation...")
    cust_metrics, cust_seg_df, cust_dist_df = analyze_customer_metrics(datasets["customer_analytics"])
    export_customer_summary(cust_metrics, cust_seg_df, summaries_dir)
    print(f"  [OK] 10,000 customers analyzed | Mean orders: {cust_metrics['mean_orders_per_customer']} | Median orders: {cust_metrics['median_orders_per_customer']}")
    print(f"  [OK] Mean delivered revenue: ${cust_metrics['mean_delivered_revenue_per_customer']:,.2f} | 8 RFM segments profiled")

    # 4. Product Catalog EDA
    print(f"\n[4/7] Analyzing Product Catalog & Margin Spreads...")
    prod_metrics, prod_cat_df, prod_sub_df, prod_top10 = analyze_product_metrics(datasets["product_analytics"])
    export_product_summary(prod_cat_df, summaries_dir)
    print(f"  [OK] 150 products across 5 categories | Units sold: {prod_metrics['total_units_sold']:,} | Blended Margin: {prod_metrics['blended_gross_margin_pct']:.2f}%")

    # 5. Monthly Revenue & Order Dynamics
    print(f"\n[5/7] Analyzing 24-Month Monthly Revenue Time Series...")
    rev_metrics, rev_df = analyze_revenue_metrics(datasets["monthly_revenue"])
    export_revenue_summary(rev_metrics, rev_df, summaries_dir)
    print(f"  [OK] 24 months ({rev_metrics['min_month']} to {rev_metrics['max_month']}) | Gross: ${rev_metrics['total_gross_billed_revenue']:,.2f} | Delivered: ${rev_metrics['total_delivered_revenue']:,.2f}")
    print(f"  [OK] Peak month: {rev_metrics['highest_revenue_month']} (${rev_metrics['highest_monthly_revenue']:,.2f})")

    # 6. Marketing Performance & Cohort Retention
    print(f"\n[6/7] Analyzing Marketing Performance & Cohort Retention...")
    mkt_metrics, mkt_comparison = analyze_marketing_metrics(datasets["marketing_performance"])
    export_marketing_summary(mkt_comparison, summaries_dir)
    print(f"  [OK] Marketing spend: ${mkt_metrics['total_marketing_spend_usd']:,.2f} | Blended CAC: ${mkt_metrics['blended_cac_usd']:.2f} | Blended ROAS: {mkt_metrics['blended_roas']:.2f}x")

    cohort_metrics, cohort_ret_curve, cohort_pivot = analyze_cohort_metrics(datasets["cohort_retention"])
    export_cohort_summary(cohort_ret_curve, cohort_pivot, summaries_dir)
    print(f"  [OK] 24 cohorts analyzed | M0 Retention: {cohort_metrics['m0_mean_retention_pct']:.2f}% | M12 Retention: {cohort_metrics['m12_mean_retention_pct']:.2f}%")

    # Business KPIs Scorecard
    kpi_raw, kpi_df = analyze_business_kpis(datasets["business_kpis"])
    export_business_kpi_summary(kpi_df, summaries_dir)
    print(f"  [OK] Executive KPI scorecard verified (37 core metrics across 6 operational pillars)")

    # Visualizations
    generated_figures = {}
    if generate_charts:
        print(f"\n[*] Generating Matplotlib Charts under: {figures_dir}")
        c_figs = plot_customer_visualizations(datasets["customer_analytics"], figures_dir)
        p_figs = plot_product_visualizations(datasets["product_analytics"], prod_cat_df, figures_dir)
        r_figs = plot_revenue_visualizations(datasets["monthly_revenue"], figures_dir)
        m_figs = plot_marketing_visualizations(datasets["marketing_performance"], figures_dir)
        h_figs = plot_cohort_visualizations(cohort_pivot, figures_dir)

        generated_figures.update(c_figs)
        generated_figures.update(p_figs)
        generated_figures.update(r_figs)
        generated_figures.update(m_figs)
        generated_figures.update(h_figs)
        for name, path in generated_figures.items():
            print(f"  [OK] Chart: {os.path.basename(path)}")

    # 7. Documentation Generation
    print(f"\n[7/7] Compiling Comprehensive EDA Markdown Report at: {report_path}")
    generate_eda_report_markdown(
        quality_results=quality_results,
        cust_metrics=cust_metrics,
        cust_seg_df=cust_seg_df,
        cust_dist_df=cust_dist_df,
        prod_metrics=prod_metrics,
        prod_cat_df=prod_cat_df,
        prod_top10=prod_top10,
        rev_metrics=rev_metrics,
        rev_df=rev_df,
        mkt_metrics=mkt_metrics,
        mkt_comparison=mkt_comparison,
        cohort_metrics=cohort_metrics,
        cohort_retention_curve=cohort_ret_curve,
        kpi_df=kpi_df,
        output_filepath=report_path,
    )
    print(f"  [OK] Generated: {os.path.relpath(report_path, workspace)}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 78)
    print(f"Phase 4 Part 1 EDA Execution Complete in {elapsed:.2f}s! All artifacts generated.")
    print("=" * 78 + "\n")

    return {
        "data_quality_report": os.path.join(summaries_dir, "data_quality_report.csv"),
        "customer_summary": os.path.join(summaries_dir, "customer_summary.csv"),
        "product_summary": os.path.join(summaries_dir, "product_summary.csv"),
        "revenue_summary": os.path.join(summaries_dir, "revenue_summary.csv"),
        "marketing_summary": os.path.join(summaries_dir, "marketing_summary.csv"),
        "cohort_summary": os.path.join(summaries_dir, "cohort_summary.csv"),
        "business_kpi_summary": os.path.join(summaries_dir, "business_kpi_summary.csv"),
        "eda_report_md": report_path,
    }


def main():
    """CLI execution entrypoint."""
    try:
        run_eda_pipeline()
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
