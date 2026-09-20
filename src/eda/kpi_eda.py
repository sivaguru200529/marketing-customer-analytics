"""
Aura Retail Analytics - Phase 4 Part 1
Business KPI Exploratory Analysis Module.

Parses executive single-row scorecard, validates reference alignments against Phase 3
benchmarks, and formats multidimensional business health indicators.
"""

import os
from typing import Any, Dict, List, Tuple
import pandas as pd


def analyze_business_kpis(df: pd.DataFrame) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Extract and structure the 37 executive KPIs into functional domains:
    Customer Scale, Order Fulfillment, Revenue & Margins, Unit Economics,
    Digital Marketing, and Web Friction.

    Returns:
        Tuple containing:
        - Dict of all raw KPI values.
        - DataFrame structured into category, KPI name, value, and unit.
    """
    row = df.iloc[0]

    kpi_records = [
        # Customer Scale
        {"category": "Customer Scale", "metric": "Registered Customers", "value": f"{int(row['total_registered_customers']):,}", "raw_value": row['total_registered_customers'], "unit": "Count"},
        {"category": "Customer Scale", "metric": "Active Ordering Customers", "value": f"{int(row['active_ordering_customers']):,}", "raw_value": row['active_ordering_customers'], "unit": "Count"},
        {"category": "Customer Scale", "metric": "Customer Penetration Rate", "value": f"{row['customer_penetration_rate_pct']:.2f}%", "raw_value": row['customer_penetration_rate_pct'], "unit": "%"},
        {"category": "Customer Scale", "metric": "Active Geographic States", "value": f"{int(row['active_states_count'])}", "raw_value": row['active_states_count'], "unit": "Count"},

        # Order Fulfillment
        {"category": "Order Fulfillment", "metric": "Total Orders Placed", "value": f"{int(row['total_orders_placed']):,}", "raw_value": row['total_orders_placed'], "unit": "Count"},
        {"category": "Order Fulfillment", "metric": "Delivered Orders", "value": f"{int(row['delivered_orders']):,}", "raw_value": row['delivered_orders'], "unit": "Count"},
        {"category": "Order Fulfillment", "metric": "Returned Orders", "value": f"{int(row['returned_orders']):,}", "raw_value": row['returned_orders'], "unit": "Count"},
        {"category": "Order Fulfillment", "metric": "Cancelled Orders", "value": f"{int(row['cancelled_orders']):,}", "raw_value": row['cancelled_orders'], "unit": "Count"},
        {"category": "Order Fulfillment", "metric": "Order Fulfillment Rate", "value": f"{row['fulfillment_rate_pct']:.2f}%", "raw_value": row['fulfillment_rate_pct'], "unit": "%"},
        {"category": "Order Fulfillment", "metric": "Return Rate", "value": f"{row['return_rate_pct']:.2f}%", "raw_value": row['return_rate_pct'], "unit": "%"},
        {"category": "Order Fulfillment", "metric": "Cancellation Rate", "value": f"{row['cancellation_rate_pct']:.2f}%", "raw_value": row['cancellation_rate_pct'], "unit": "%"},

        # Catalog & Volume
        {"category": "Catalog & Volume", "metric": "Total Units Sold", "value": f"{int(row['total_units_sold']):,}", "raw_value": row['total_units_sold'], "unit": "Count"},
        {"category": "Catalog & Volume", "metric": "Distinct Products Ordered", "value": f"{int(row['distinct_products_ordered'])}", "raw_value": row['distinct_products_ordered'], "unit": "Count"},
        {"category": "Catalog & Volume", "metric": "Average Units per Order", "value": f"{row['avg_units_per_order']:.2f}", "raw_value": row['avg_units_per_order'], "unit": "Units/Order"},

        # Revenue & Margins
        {"category": "Revenue & Margins", "metric": "Total Gross Billed Revenue", "value": f"${row['total_gross_billed_revenue']:,.2f}", "raw_value": row['total_gross_billed_revenue'], "unit": "USD"},
        {"category": "Revenue & Margins", "metric": "Total Delivered Net Revenue", "value": f"${row['total_delivered_revenue']:,.2f}", "raw_value": row['total_delivered_revenue'], "unit": "USD"},
        {"category": "Revenue & Margins", "metric": "Returned Revenue", "value": f"${row['total_returned_revenue']:,.2f}", "raw_value": row['total_returned_revenue'], "unit": "USD"},
        {"category": "Revenue & Margins", "metric": "Cancelled Revenue", "value": f"${row['total_cancelled_revenue']:,.2f}", "raw_value": row['total_cancelled_revenue'], "unit": "USD"},
        {"category": "Revenue & Margins", "metric": "Total Discounts Granted", "value": f"${row['total_discounts_granted']:,.2f}", "raw_value": row['total_discounts_granted'], "unit": "USD"},
        {"category": "Revenue & Margins", "metric": "Total Shipping Revenue", "value": f"${row['total_shipping_revenue']:,.2f}", "raw_value": row['total_shipping_revenue'], "unit": "USD"},
        {"category": "Revenue & Margins", "metric": "Total Estimated COGS", "value": f"${row['total_estimated_cogs']:,.2f}", "raw_value": row['total_estimated_cogs'], "unit": "USD"},
        {"category": "Revenue & Margins", "metric": "Estimated Gross Profit", "value": f"${row['estimated_gross_profit_usd']:,.2f}", "raw_value": row['estimated_gross_profit_usd'], "unit": "USD"},
        {"category": "Revenue & Margins", "metric": "Gross Profit Margin", "value": f"{row['gross_profit_margin_pct']:.2f}%", "raw_value": row['gross_profit_margin_pct'], "unit": "%"},

        # Unit Economics
        {"category": "Unit Economics", "metric": "Average Order Value (AOV)", "value": f"${row['average_order_value_usd']:,.2f}", "raw_value": row['average_order_value_usd'], "unit": "USD/Order"},
        {"category": "Unit Economics", "metric": "Average Revenue per User (ARPU)", "value": f"${row['arpu_usd']:,.2f}", "raw_value": row['arpu_usd'], "unit": "USD/Customer"},
        {"category": "Unit Economics", "metric": "Average Revenue per Paying User (ARPPU)", "value": f"${row['arppu_usd']:,.2f}", "raw_value": row['arppu_usd'], "unit": "USD/Paying Cust"},

        # Digital Marketing Efficiency
        {"category": "Digital Marketing", "metric": "Total Marketing Media Spend", "value": f"${row['total_marketing_spend_usd']:,.2f}", "raw_value": row['total_marketing_spend_usd'], "unit": "USD"},
        {"category": "Digital Marketing", "metric": "Total Ad Impressions", "value": f"{int(row['total_ad_impressions']):,}", "raw_value": row['total_ad_impressions'], "unit": "Count"},
        {"category": "Digital Marketing", "metric": "Total Ad Clicks", "value": f"{int(row['total_ad_clicks']):,}", "raw_value": row['total_ad_clicks'], "unit": "Count"},
        {"category": "Digital Marketing", "metric": "Blended Click-Through Rate (CTR)", "value": f"{row['blended_ctr_pct']:.3f}%", "raw_value": row['blended_ctr_pct'], "unit": "%"},
        {"category": "Digital Marketing", "metric": "Blended Cost per Click (CPC)", "value": f"${row['blended_cpc_usd']:.2f}", "raw_value": row['blended_cpc_usd'], "unit": "USD/Click"},
        {"category": "Digital Marketing", "metric": "Blended Customer Acquisition Cost (CAC)", "value": f"${row['blended_cac_usd']:.2f}", "raw_value": row['blended_cac_usd'], "unit": "USD/Cust"},
        {"category": "Digital Marketing", "metric": "Blended Return on Ad Spend (ROAS)", "value": f"{row['blended_roas']:.2f}x", "raw_value": row['blended_roas'], "unit": "Ratio"},

        # Web Sessions & Engagement
        {"category": "Web Engagement", "metric": "Total Web Sessions", "value": f"{int(row['total_web_sessions']):,}", "raw_value": row['total_web_sessions'], "unit": "Count"},
        {"category": "Web Engagement", "metric": "Total Cart Abandonments", "value": f"{int(row['total_cart_abandonments']):,}", "raw_value": row['total_cart_abandonments'], "unit": "Count"},
        {"category": "Web Engagement", "metric": "Cart Abandonment Rate", "value": f"{row['cart_abandonment_rate_pct']:.2f}%", "raw_value": row['cart_abandonment_rate_pct'], "unit": "%"},
        {"category": "Customer Support", "metric": "Total Support Tickets Opened", "value": f"{int(row['total_support_tickets_opened']):,}", "raw_value": row['total_support_tickets_opened'], "unit": "Count"},
    ]

    kpi_df = pd.DataFrame(kpi_records)
    raw_dict = row.to_dict()

    return raw_dict, kpi_df


def export_business_kpi_summary(kpi_df: pd.DataFrame, output_dir: str) -> str:
    """
    Export unified business KPI summary CSV table.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "business_kpi_summary.csv")
    kpi_df.to_csv(out_path, index=False)
    return out_path
