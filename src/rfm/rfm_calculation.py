"""
Aura Retail Analytics - Phase 4 Part 2
RFM Extraction, Metric Structuring, and Validation Module.
"""

import os
from typing import Optional
import numpy as np
import pandas as pd

from src.rfm.config import (
    DEFAULT_OUTPUT_DIR,
    COL_CUSTOMER_ID,
    COL_RECENCY,
    COL_FREQUENCY,
    COL_MONETARY,
    COL_GROSS_REVENUE,
    COL_TOTAL_ORDERS,
    COL_DELIVERED_AOV,
    COL_TOTAL_UNITS,
    COL_RETURNED_ORDERS,
    COL_CANCELLED_ORDERS,
    COL_P3_R_SCORE,
    COL_P3_F_SCORE,
    COL_P3_M_SCORE,
    COL_P3_SEGMENT,
)


def extract_rfm_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and structure the primary RFM metrics and contextual behavioral fields.

    Parameters:
        df: Ingested customer analytics DataFrame.

    Returns:
        pd.DataFrame sorted deterministically by customer_id with validated RFM fields.
    """
    rfm_df = pd.DataFrame()
    rfm_df["customer_id"] = df[COL_CUSTOMER_ID]
    rfm_df["recency"] = df[COL_RECENCY].astype(int)
    rfm_df["frequency"] = df[COL_FREQUENCY].astype(int)
    rfm_df["monetary"] = df[COL_MONETARY].astype(float).round(2)

    # Contextual behavioral attributes
    rfm_df["total_orders"] = df[COL_TOTAL_ORDERS].astype(int)
    rfm_df["gross_revenue"] = df[COL_GROSS_REVENUE].astype(float).round(2)
    rfm_df["total_units"] = df[COL_TOTAL_UNITS].astype(int)
    rfm_df["delivered_aov"] = df[COL_DELIVERED_AOV].astype(float).round(2)
    rfm_df["returned_orders"] = df[COL_RETURNED_ORDERS].astype(int)
    rfm_df["cancelled_orders"] = df[COL_CANCELLED_ORDERS].astype(int)

    # Phase 3 Reference Columns
    rfm_df["p3_r_score"] = df[COL_P3_R_SCORE].astype(int)
    rfm_df["p3_f_score"] = df[COL_P3_F_SCORE].astype(int)
    rfm_df["p3_m_score"] = df[COL_P3_M_SCORE].astype(int)
    rfm_df["p3_rfm_segment"] = df[COL_P3_SEGMENT].astype(str)

    # Deterministic sorting
    rfm_df = rfm_df.sort_values("customer_id").reset_index(drop=True)

    # Sanity checks
    if (rfm_df["recency"] < 0).any():
        raise ValueError("Detected negative recency values in customer RFM extraction.")
    if (rfm_df["frequency"] < 0).any():
        raise ValueError("Detected negative frequency values in customer RFM extraction.")
    if (rfm_df["monetary"] < 0).any():
        raise ValueError("Detected negative monetary values in customer RFM extraction.")

    # Check finite
    for col in ["recency", "frequency", "monetary"]:
        if not np.isfinite(rfm_df[col]).all():
            raise ValueError(f"Non-finite values detected in RFM column '{col}'.")

    return rfm_df


def export_customer_rfm(rfm_df: pd.DataFrame, output_dir: Optional[str] = None) -> str:
    """
    Save the customer RFM base dataset to data/04_rfm/customer_rfm.csv.
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "customer_rfm.csv")

    # Export sorted deterministically
    rfm_df.sort_values("customer_id").to_csv(out_path, index=False)
    return out_path
