"""
Aura Retail Analytics - Phase 4 Part 1
Python Exploratory Data Analysis (EDA) & Data Quality Package.
"""

from src.eda.loader import (
    DATASET_FILENAMES,
    REQUIRED_COLUMNS,
    GRAIN_KEYS,
    get_default_data_dir,
    load_dataset,
    load_all_analytics_datasets,
    get_dataset_profiles,
)
from src.eda.quality import (
    audit_completeness,
    audit_uniqueness,
    audit_numeric_ranges,
    audit_temporal_continuity,
    run_full_data_quality_audit,
    export_data_quality_reports,
)
from src.eda.customer_eda import (
    analyze_customer_metrics,
    plot_customer_visualizations,
    export_customer_summary,
)
from src.eda.product_eda import (
    analyze_product_metrics,
    plot_product_visualizations,
    export_product_summary,
)
from src.eda.revenue_eda import (
    analyze_revenue_metrics,
    plot_revenue_visualizations,
    export_revenue_summary,
)
from src.eda.marketing_eda import (
    analyze_marketing_metrics,
    plot_marketing_visualizations,
    export_marketing_summary,
)
from src.eda.cohort_eda import (
    analyze_cohort_metrics,
    plot_cohort_visualizations,
    export_cohort_summary,
)
from src.eda.kpi_eda import (
    analyze_business_kpis,
    export_business_kpi_summary,
)
from src.eda.report import generate_eda_report_markdown

__all__ = [
    "DATASET_FILENAMES",
    "REQUIRED_COLUMNS",
    "GRAIN_KEYS",
    "get_default_data_dir",
    "load_dataset",
    "load_all_analytics_datasets",
    "get_dataset_profiles",
    "audit_completeness",
    "audit_uniqueness",
    "audit_numeric_ranges",
    "audit_temporal_continuity",
    "run_full_data_quality_audit",
    "export_data_quality_reports",
    "analyze_customer_metrics",
    "plot_customer_visualizations",
    "export_customer_summary",
    "analyze_product_metrics",
    "plot_product_visualizations",
    "export_product_summary",
    "analyze_revenue_metrics",
    "plot_revenue_visualizations",
    "export_revenue_summary",
    "analyze_marketing_metrics",
    "plot_marketing_visualizations",
    "export_marketing_summary",
    "analyze_cohort_metrics",
    "plot_cohort_visualizations",
    "export_cohort_summary",
    "analyze_business_kpis",
    "export_business_kpi_summary",
    "generate_eda_report_markdown",
]
