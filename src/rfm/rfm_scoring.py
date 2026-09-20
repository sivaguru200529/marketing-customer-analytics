"""
Aura Retail Analytics - Phase 4 Part 2
Tie-Safe RFM Quantile Scoring Module.

Calculates deterministic 1-to-5 integer scores for Recency, Frequency, and Monetary
dimensions, composite total scores (3 to 15), and 3-character string representations.
"""

import pandas as pd
import numpy as np


def calculate_recency_score(recency_series: pd.Series) -> pd.Series:
    """
    Calculate 1-to-5 Recency score using rank-based quintiles.
    Inverted: Lowest recency days (most recent purchase) receives score 5;
              Highest recency days (purchased longest ago) receives score 1.
    """
    # Ranking descending so that smallest recency_days gets highest rank (maps to 5)
    ranks = recency_series.rank(method="first", ascending=False)
    scores = pd.qcut(ranks, q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    return scores


def calculate_frequency_score(freq_series: pd.Series) -> pd.Series:
    """
    Calculate 1-to-5 Frequency score using rank-based quintiles.
    Highest order frequency receives score 5; lowest receives score 1.
    """
    ranks = freq_series.rank(method="first", ascending=True)
    scores = pd.qcut(ranks, q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    return scores


def calculate_monetary_score(monetary_series: pd.Series) -> pd.Series:
    """
    Calculate 1-to-5 Monetary score using rank-based quintiles.
    Highest monetary revenue receives score 5; lowest receives score 1.
    """
    ranks = monetary_series.rank(method="first", ascending=True)
    scores = pd.qcut(ranks, q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    return scores


def compute_rfm_scores(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Attach standalone Python RFM scores and composite representations to the RFM DataFrame.

    Parameters:
        rfm_df: DataFrame containing 'recency', 'frequency', and 'monetary' columns.

    Returns:
        pd.DataFrame with added score columns:
        - rfm_recency_score (1 to 5)
        - rfm_frequency_score (1 to 5)
        - rfm_monetary_score (1 to 5)
        - rfm_total_score (3 to 15)
        - rfm_score (str, e.g. '555')
    """
    df = rfm_df.copy()

    df["rfm_recency_score"] = calculate_recency_score(df["recency"])
    df["rfm_frequency_score"] = calculate_frequency_score(df["frequency"])
    df["rfm_monetary_score"] = calculate_monetary_score(df["monetary"])

    # Total Score: integer sum in [3, 15]
    df["rfm_total_score"] = (
        df["rfm_recency_score"] + df["rfm_frequency_score"] + df["rfm_monetary_score"]
    ).astype(int)

    # Human-readable 3-character representation (categorical, not continuous numeric)
    df["rfm_score"] = (
        df["rfm_recency_score"].astype(str)
        + df["rfm_frequency_score"].astype(str)
        + df["rfm_monetary_score"].astype(str)
    )

    # Sanity validations
    for col in ["rfm_recency_score", "rfm_frequency_score", "rfm_monetary_score"]:
        if not df[col].isin([1, 2, 3, 4, 5]).all():
            raise ValueError(f"Score column '{col}' contains values outside [1, 5].")

    if not df["rfm_total_score"].between(3, 15).all():
        raise ValueError("Composite 'rfm_total_score' contains values outside [3, 15].")

    if not (df["rfm_score"].str.len() == 3).all():
        raise ValueError("Readable 'rfm_score' string representations must be exactly 3 characters.")

    return df
