"""
Aura Retail Analytics - Phase 4 Part 2
Deterministic Rule-Based RFM Customer Segmentation Module.

Implements the authoritative ordered decision tree discovered from Phase 3 SQL
(002_customer_analytics.sql), ensuring mutually exclusive and collectively exhaustive
segment assignment for all customers.
"""

import os
from typing import Optional
import pandas as pd

from src.rfm.config import DEFAULT_OUTPUT_DIR, SEGMENT_PRIORITY_ORDER


def assign_rfm_segment(r: int, f: int, m: int) -> str:
    """
    Assign a single RFM segment to a customer based on the authoritative Phase 3
    ordered decision tree.

    Priority Order:
        1. Champions:           R >= 4 AND F >= 4 AND M >= 4
        2. Loyal Customers:     R >= 3 AND F >= 3 AND M >= 3
        3. Recent Inquirers:    R >= 4 AND F <= 2
        4. Promising:           R >= 3 AND F <= 2 AND M >= 3
        5. At Risk High Value:  R <= 2 AND F >= 3 AND M >= 3
        6. Need Attention:      R <= 2 AND F >= 2
        7. Lost / Dormant:      R == 1 AND F == 1
        8. Potential / Developing: All remaining (catch-all)
    """
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    elif r >= 3 and f >= 3 and m >= 3:
        return "Loyal Customers"
    elif r >= 4 and f <= 2:
        return "Recent Inquirers"
    elif r >= 3 and f <= 2 and m >= 3:
        return "Promising"
    elif r <= 2 and f >= 3 and m >= 3:
        return "At Risk High Value"
    elif r <= 2 and f >= 2:
        return "Need Attention"
    elif r == 1 and f == 1:
        return "Lost / Dormant"
    else:
        return "Potential / Developing"


def apply_rfm_segmentation(
    df: pd.DataFrame,
    r_col: str = "rfm_recency_score",
    f_col: str = "rfm_frequency_score",
    m_col: str = "rfm_monetary_score",
    output_col: str = "rfm_segment"
) -> pd.DataFrame:
    """
    Apply the deterministic segmentation decision tree across all rows.

    Parameters:
        df: Input DataFrame containing R, F, and M score columns.
        r_col: Column name for Recency score.
        f_col: Column name for Frequency score.
        m_col: Column name for Monetary score.
        output_col: Name of the resulting segment column.

    Returns:
        pd.DataFrame with output_col populated.
    """
    res = df.copy()
    res[output_col] = [
        assign_rfm_segment(r, f, m)
        for r, f, m in zip(res[r_col], res[f_col], res[m_col])
    ]

    # Invariants validation
    if res[output_col].isnull().any():
        raise ValueError(f"Segment assignment failed: found null values in '{output_col}'.")

    invalid_names = set(res[output_col]) - set(SEGMENT_PRIORITY_ORDER)
    if invalid_names:
        raise ValueError(f"Unexpected segment names encountered: {invalid_names}")

    return res


def export_customer_rfm_segments(
    df: pd.DataFrame,
    output_dir: Optional[str] = None
) -> str:
    """
    Export customer RFM segments table to data/04_rfm/customer_rfm_segments.csv.
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "customer_rfm_segments.csv")

    cols_to_export = [
        "customer_id",
        "recency",
        "frequency",
        "monetary",
        "rfm_recency_score",
        "rfm_frequency_score",
        "rfm_monetary_score",
        "rfm_total_score",
        "rfm_score",
        "rfm_segment",
    ]

    # Include supporting context if present
    for extra in ["gross_revenue", "total_orders", "total_units", "delivered_aov", "returned_orders", "cancelled_orders"]:
        if extra in df.columns:
            cols_to_export.append(extra)

    df_export = df[cols_to_export].sort_values("customer_id").reset_index(drop=True)
    df_export.to_csv(out_path, index=False)
    return out_path
