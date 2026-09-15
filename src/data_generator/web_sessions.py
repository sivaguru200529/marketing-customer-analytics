"""
Web sessions generation module for Aura Retail.
Produces fact_web_sessions representing digital touchpoints,
linking order conversions to browsing activity, cart abandonments,
session durations, page views, and customer service support tickets.
"""

from datetime import date, timedelta
import numpy as np
import pandas as pd
from src.data_generator.config import GeneratorConfig


def generate_web_sessions(
    customers_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    config: GeneratorConfig
) -> pd.DataFrame:
    """
    Generates deterministic fact_web_sessions DataFrame.
    
    Args:
        customers_df: Generated dim_customers table.
        orders_df: Generated fact_orders table.
        config: GeneratorConfig instance.
        
    Returns:
        pd.DataFrame: Table with web browsing touchpoints.
    """
    rng = np.random.default_rng(config.seed)
    n_total_sessions = config.n_sessions

    sessions = []
    session_id_counter = 1

    # 1. Generate purchasing sessions matching each order
    # Extract order metadata: customer_id, order_date (date part), order_status
    orders_df_temp = orders_df.copy()
    orders_df_temp["ord_date_only"] = pd.to_datetime(orders_df_temp["order_date"]).dt.date

    for _, row in orders_df_temp.iterrows():
        cust_id = row["customer_id"]
        sess_dt = row["ord_date_only"]
        status = row["order_status"]

        # Purchasing session engagement
        p_views = int(rng.integers(5, 23))
        time_spent = int(rng.integers(180, 960))
        cart_abandon = False

        # Support ticket correlation
        if status == "Returned":
            tickets = 1 if (rng.random() < 0.28) else 0
        elif status == "Cancelled":
            tickets = 1 if (rng.random() < 0.38) else 0
        else:
            tickets = 1 if (rng.random() < 0.03) else 0

        sessions.append({
            "session_id": f"SESS_{session_id_counter:06d}",
            "customer_id": cust_id,
            "session_date": sess_dt.isoformat(),
            "page_views": p_views,
            "time_spent_seconds": time_spent,
            "cart_abandoned": cart_abandon,
            "support_tickets": tickets
        })
        session_id_counter += 1

    # 2. Generate non-purchasing browsing sessions
    remaining_sessions = n_total_sessions - len(sessions)
    if remaining_sessions > 0:
        cust_lookup = customers_df[["customer_id", "signup_date"]].to_dict(orient="records")
        n_custs = len(cust_lookup)

        # Distribute remaining sessions across customers
        # Active customers (higher activity) get more sessions
        cust_indices = rng.integers(0, n_custs, size=remaining_sessions)

        for c_idx in cust_indices:
            cust = cust_lookup[c_idx]
            cust_id = cust["customer_id"]
            signup_dt = date.fromisoformat(cust["signup_date"])

            max_days = (config.end_date - signup_dt).days
            if max_days <= 0:
                day_offset = 0
            else:
                day_offset = int(rng.integers(0, max_days + 1))

            sess_dt = signup_dt + timedelta(days=day_offset)

            # Cart abandonment behavior: ~28% abandoned carts
            is_abandoned = bool(rng.random() < 0.28)

            if is_abandoned:
                p_views = int(rng.integers(3, 14))
                time_spent = int(rng.integers(75, 480))
            else:
                # Casual bounce / product research
                p_views = int(rng.choice([1, 2, 3, 4, 6], p=[0.35, 0.28, 0.18, 0.12, 0.07]))
                time_spent = int(rng.integers(15, 240))

            # General support inquiries
            tickets = 1 if (rng.random() < 0.02) else 0

            sessions.append({
                "session_id": f"SESS_{session_id_counter:06d}",
                "customer_id": cust_id,
                "session_date": sess_dt.isoformat(),
                "page_views": p_views,
                "time_spent_seconds": time_spent,
                "cart_abandoned": is_abandoned,
                "support_tickets": tickets
            })
            session_id_counter += 1

    df = pd.DataFrame(sessions)
    # Sort chronologically by session_date
    df = df.sort_values(by=["session_date", "customer_id"]).reset_index(drop=True)
    # Re-assign clean sequential session_ids
    df["session_id"] = [f"SESS_{i + 1:06d}" for i in range(len(df))]

    return df
