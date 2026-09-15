"""
Orders and Order Items generation module for Aura Retail.
Produces fact_orders and fact_order_items with realistic customer repeat buying,
basket sizes (2.4-2.5 items/order, >= 120,000 items), order statuses,
discounts, shipping fees, and mathematical integrity.
"""

from datetime import datetime, date, timedelta
from typing import Tuple, List, Dict
import numpy as np
import pandas as pd
from src.data_generator.config import GeneratorConfig

# Payment method probabilities
PAYMENT_METHODS = ["Credit Card", "PayPal", "Apple Pay", "Klarna / BNPL"]
PAYMENT_PROBS = [0.50, 0.25, 0.15, 0.10]

# Order status probabilities
ORDER_STATUSES = ["Delivered", "Returned", "Cancelled"]
STATUS_PROBS = [0.86, 0.10, 0.04]


def _assign_customer_order_counts(
    n_customers: int,
    target_orders: int,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Assigns order counts to customers following the target behavioral distribution:
    - ~60% single-purchase (1 order)
    - ~22% casual repeat (2-3 orders)
    - ~12% frequent repeat (4-6 orders)
    - ~6% VIP champions (7-15+ orders)
    
    Rebalances repeat customer counts so total orders strictly equals target_orders.
    """
    # Behavioral segment target counts
    n_tier1 = int(round(0.60 * n_customers))
    n_tier2 = int(round(0.22 * n_customers))
    n_tier3 = int(round(0.12 * n_customers))
    n_tier4 = n_customers - (n_tier1 + n_tier2 + n_tier3)

    # Initial order count assignments
    counts = np.zeros(n_customers, dtype=int)
    
    # Tier 1: Single purchase (exactly 1)
    counts[:n_tier1] = 1
    
    # Tier 2: Casual repeat (2-3 orders initial)
    counts[n_tier1:n_tier1 + n_tier2] = rng.integers(2, 4, size=n_tier2)
    
    # Tier 3: Frequent repeat (4-6 orders initial)
    counts[n_tier1 + n_tier2:n_tier1 + n_tier2 + n_tier3] = rng.integers(4, 7, size=n_tier3)
    
    # Tier 4: VIP / Champions (7-15 orders initial)
    counts[n_tier1 + n_tier2 + n_tier3:] = rng.integers(7, 16, size=n_tier4)

    # Rebalance: We preserve Tier 1 at 1 order to maintain the ~60% single-buyer base.
    # We distribute the deficit across Tier 2, 3, and 4 proportionally.
    current_total = int(counts.sum())
    deficit = target_orders - current_total

    if deficit > 0:
        # Weights for repeat tiers: Tier 2 weight 1, Tier 3 weight 2.5, Tier 4 weight 5
        repeat_indices = np.arange(n_tier1, n_customers)
        tier_weights = np.zeros(len(repeat_indices), dtype=float)
        tier_weights[:n_tier2] = 1.0
        tier_weights[n_tier2:n_tier2 + n_tier3] = 2.5
        tier_weights[n_tier2 + n_tier3:] = 5.5
        tier_weights /= tier_weights.sum()

        additions = rng.multinomial(deficit, tier_weights)
        counts[n_tier1:] += additions
    elif deficit < 0:
        # If surplus, reduce from highest tiers without dropping below minimum tier thresholds
        surplus = -deficit
        repeat_indices = np.arange(n_tier1, n_customers)
        for _ in range(surplus):
            # Pick from tier 4 or 3 where count > threshold
            eligible = np.where(counts > 2)[0]
            if len(eligible) > 0:
                idx = rng.choice(eligible)
                counts[idx] -= 1

    # Shuffle customer counts so customer ID does not strictly determine tier
    rng.shuffle(counts)
    return counts


def generate_orders_and_items(
    customers_df: pd.DataFrame,
    products_df: pd.DataFrame,
    config: GeneratorConfig
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates deterministic fact_orders and fact_order_items DataFrames.
    
    Args:
        customers_df: Generated dim_customers table.
        products_df: Generated dim_products table.
        config: GeneratorConfig instance.
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (orders_df, order_items_df)
    """
    rng = np.random.default_rng(config.seed)
    n_customers = len(customers_df)
    target_orders = config.n_orders

    # Assign order counts per customer
    order_counts = _assign_customer_order_counts(n_customers, target_orders, rng)

    # Prepare product lookup
    prod_ids = products_df["product_id"].values
    prod_prices = dict(zip(products_df["product_id"], products_df["retail_price"]))
    n_unique_prods = len(prod_ids)

    # Convert customer signups to datetime.date
    customer_records = customers_df[["customer_id", "signup_date"]].to_dict(orient="records")
    
    orders = []
    order_items = []
    
    order_id_counter = 1
    item_id_counter = 1

    # Line item distribution probabilities (1 to 6 items per order)
    # Expected value: 1*0.28 + 2*0.28 + 3*0.20 + 4*0.13 + 5*0.07 + 6*0.04 = 2.47 items/order
    item_count_choices = np.array([1, 2, 3, 4, 5, 6])
    item_count_probs = np.array([0.28, 0.28, 0.20, 0.13, 0.07, 0.04])

    for i in range(n_customers):
        k = int(order_counts[i])
        if k <= 0:
            continue
            
        cust_id = customer_records[i]["customer_id"]
        signup_dt = date.fromisoformat(customer_records[i]["signup_date"])
        
        # Max available days from signup to window end (2025-12-31)
        max_days = (config.end_date - signup_dt).days
        if max_days < 0:
            max_days = 0

        # Determine order dates for this customer
        if k == 1:
            # First order occurs within 0 to min(14, max_days) days from signup
            offset = 0 if max_days == 0 else rng.integers(0, min(14, max_days) + 1)
            order_days = [offset]
        else:
            # Customer lifespan in days: some churn early (dormant), some stay active
            # 40% of repeat customers churn after 60-240 days; 60% stay active across tenure
            is_churner = (rng.random() < 0.40)
            if is_churner and max_days > 120:
                active_window = rng.integers(60, min(240, max_days))
            else:
                active_window = max_days

            # Draw k non-decreasing day offsets
            if active_window <= 0:
                raw_offsets = np.zeros(k, dtype=int)
            else:
                raw_offsets = rng.integers(0, active_window + 1, size=k)
                raw_offsets.sort()
            order_days = list(raw_offsets)

        for day_offset in order_days:
            ord_date = signup_dt + timedelta(days=int(day_offset))
            # Random time of day: 08:00 to 22:59
            hour = rng.integers(8, 23)
            minute = rng.integers(0, 60)
            second = rng.integers(0, 60)
            order_timestamp = datetime(ord_date.year, ord_date.month, ord_date.day, hour, minute, second)

            # Order attributes
            ord_id = f"ORD_{order_id_counter:05d}"
            status = rng.choice(ORDER_STATUSES, p=STATUS_PROBS)
            payment = rng.choice(PAYMENT_METHODS, p=PAYMENT_PROBS)

            # Draw number of line items
            n_items = int(rng.choice(item_count_choices, p=item_count_probs))
            # Select distinct products for this order
            chosen_prods = rng.choice(prod_ids, size=min(n_items, n_unique_prods), replace=False)

            order_line_totals = []
            for prod_id in chosen_prods:
                # Quantity: 1 to 10 (heavily weighted towards 1-2)
                # 1 (72%), 2 (18%), 3 (5%), 4 (3%), 5-10 (2%)
                q_rand = rng.random()
                if q_rand < 0.72:
                    qty = 1
                elif q_rand < 0.90:
                    qty = 2
                elif q_rand < 0.95:
                    qty = 3
                elif q_rand < 0.98:
                    qty = 4
                else:
                    qty = int(rng.integers(5, 11))

                u_price = float(prod_prices[prod_id])
                l_total = round(qty * u_price, 2)
                order_line_totals.append(l_total)

                order_items.append({
                    "order_item_id": item_id_counter,
                    "order_id": ord_id,
                    "product_id": prod_id,
                    "quantity": qty,
                    "unit_price": u_price,
                    "line_total": l_total
                })
                item_id_counter += 1

            # Order financial aggregates
            subtotal = sum(order_line_totals)
            
            # Shipping: Free above $75 in 90% cases, otherwise $5.99 or $8.99
            if subtotal >= 75.0:
                shipping = 0.00 if (rng.random() < 0.90) else 4.99
            else:
                shipping = 5.99 if (rng.random() < 0.75) else 8.99

            # Discount: 55% no discount, 30% percentage discount (10-20%), 15% fixed discount ($10-$25)
            disc_rand = rng.random()
            if disc_rand < 0.55:
                discount = 0.00
            elif disc_rand < 0.85:
                pct = rng.choice([0.10, 0.15, 0.20])
                discount = round(subtotal * pct, 2)
            else:
                fixed_d = float(rng.choice([10.0, 15.0, 20.0, 25.0]))
                discount = min(fixed_d, round(subtotal * 0.40, 2))

            total_amount = round(max(0.00, subtotal + shipping - discount), 2)

            orders.append({
                "order_id": ord_id,
                "customer_id": cust_id,
                "order_date": order_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "order_status": status,
                "payment_method": payment,
                "shipping_cost": float(shipping),
                "discount_amount": float(discount),
                "total_order_amount": float(total_amount)
            })
            order_id_counter += 1

    orders_df = pd.DataFrame(orders)
    # Sort orders chronologically by order_date
    orders_df = orders_df.sort_values(by="order_date").reset_index(drop=True)
    # Re-assign sequential order_id in strict chronological order
    old_to_new_order_ids = {}
    for idx, row in orders_df.iterrows():
        new_id = f"ORD_{idx + 1:05d}"
        old_to_new_order_ids[row["order_id"]] = new_id
    orders_df["order_id"] = [old_to_new_order_ids[oid] for oid in orders_df["order_id"]]

    # Remap order_id in order_items
    items_df = pd.DataFrame(order_items)
    items_df["order_id"] = items_df["order_id"].map(old_to_new_order_ids)
    
    # Sort order items by order_id and re-index order_item_id sequentially
    items_df = items_df.sort_values(by=["order_id"]).reset_index(drop=True)
    items_df["order_item_id"] = np.arange(1, len(items_df) + 1)

    return orders_df, items_df
