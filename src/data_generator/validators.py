"""
Validation suite for Aura Retail synthetic data generation.
Executes rigorous integrity checks on all entities before data export:
row counts, primary/foreign key constraints, date chronology,
pricing and mathematics consistency, and non-negative constraints.
"""

from datetime import date
from typing import Dict, List
import pandas as pd
from src.data_generator.config import GeneratorConfig
from src.data_generator.channels import PAID_CHANNEL_IDS


class ValidationError(Exception):
    """Raised when synthetic dataset fails validation checks."""
    pass


class DatasetValidator:
    """Validator that audits all generated tables against business and relational rules."""

    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.errors: List[str] = []

    def validate_all(self, tables: Dict[str, pd.DataFrame]) -> bool:
        """
        Runs comprehensive validation across all generated tables.
        
        Args:
            tables: Dictionary mapping table name to DataFrame.
            
        Returns:
            bool: True if validation passed.
            
        Raises:
            ValidationError: If one or more validation checks fail.
        """
        self.errors.clear()

        self._check_row_counts(tables)
        self._check_primary_keys(tables)
        self._check_foreign_keys(tables)
        self._check_null_constraints(tables)
        self._check_dates_and_chronology(tables)
        self._check_monetary_and_quantities(tables)
        self._check_marketing_spend_integrity(tables)
        self._check_web_sessions_integrity(tables)

        if self.errors:
            error_report = "\n - ".join(self.errors)
            raise ValidationError(f"Synthetic dataset validation failed with {len(self.errors)} error(s):\n - {error_report}")

        return True

    def _check_row_counts(self, tables: Dict[str, pd.DataFrame]):
        """Validates that table row counts meet configured expectations."""
        # Channels
        n_chan = len(tables["channels"])
        if n_chan != 6:
            self.errors.append(f"dim_channels must have 6 rows, found {n_chan}")

        # Customers
        n_cust = len(tables["customers"])
        if n_cust != self.config.n_customers:
            self.errors.append(f"dim_customers expected {self.config.n_customers} rows, found {n_cust}")

        # Products
        n_prod = len(tables["products"])
        if n_prod != self.config.n_products:
            self.errors.append(f"dim_products expected {self.config.n_products} rows, found {n_prod}")

        # Orders
        n_ord = len(tables["orders"])
        if n_ord != self.config.n_orders:
            self.errors.append(f"fact_orders expected {self.config.n_orders} rows, found {n_ord}")

        # Order items
        n_items = len(tables["order_items"])
        if n_items < self.config.min_order_items:
            self.errors.append(f"fact_order_items minimum is {self.config.min_order_items}, found {n_items}")

        # Web sessions
        n_sess = len(tables["web_sessions"])
        if n_sess != self.config.n_sessions:
            self.errors.append(f"fact_web_sessions expected {self.config.n_sessions} rows, found {n_sess}")

        # Marketing spend
        expected_spend_rows = self.config.total_calendar_days * len(PAID_CHANNEL_IDS)
        n_spend = len(tables["marketing_spend"])
        if n_spend != expected_spend_rows:
            self.errors.append(f"fact_marketing_spend expected {expected_spend_rows} rows (731 days x 3 paid channels), found {n_spend}")

    def _check_primary_keys(self, tables: Dict[str, pd.DataFrame]):
        """Ensures all primary keys are completely unique and non-null."""
        pk_map = {
            "channels": "channel_id",
            "customers": "customer_id",
            "products": "product_id",
            "orders": "order_id",
            "order_items": "order_item_id",
            "web_sessions": "session_id",
            "marketing_spend": "spend_id"
        }

        for table_name, pk_col in pk_map.items():
            if table_name in tables:
                df = tables[table_name]
                if df[pk_col].isnull().any():
                    self.errors.append(f"{table_name}.{pk_col} contains null values in primary key")
                if df[pk_col].duplicated().any():
                    dup_count = df[pk_col].duplicated().sum()
                    self.errors.append(f"{table_name}.{pk_col} contains {dup_count} duplicate primary key values")

    def _check_foreign_keys(self, tables: Dict[str, pd.DataFrame]):
        """Verifies referential integrity across all relationships."""
        cust_ids = set(tables["customers"]["customer_id"])
        prod_ids = set(tables["products"]["product_id"])
        order_ids = set(tables["orders"]["order_id"])
        chan_ids = set(tables["channels"]["channel_id"])

        # customers.acquisition_channel_id -> channels.channel_id
        orphan_cust_chan = tables["customers"][~tables["customers"]["acquisition_channel_id"].isin(chan_ids)]
        if not orphan_cust_chan.empty:
            self.errors.append(f"customers contains {len(orphan_cust_chan)} invalid acquisition_channel_id references")

        # orders.customer_id -> customers.customer_id
        orphan_orders = tables["orders"][~tables["orders"]["customer_id"].isin(cust_ids)]
        if not orphan_orders.empty:
            self.errors.append(f"orders contains {len(orphan_orders)} orphan customer_id references")

        # order_items.order_id -> orders.order_id
        orphan_items_order = tables["order_items"][~tables["order_items"]["order_id"].isin(order_ids)]
        if not orphan_items_order.empty:
            self.errors.append(f"order_items contains {len(orphan_items_order)} orphan order_id references")

        # order_items.product_id -> products.product_id
        orphan_items_prod = tables["order_items"][~tables["order_items"]["product_id"].isin(prod_ids)]
        if not orphan_items_prod.empty:
            self.errors.append(f"order_items contains {len(orphan_items_prod)} orphan product_id references")

        # web_sessions.customer_id -> customers.customer_id
        orphan_sessions = tables["web_sessions"][~tables["web_sessions"]["customer_id"].isin(cust_ids)]
        if not orphan_sessions.empty:
            self.errors.append(f"web_sessions contains {len(orphan_sessions)} orphan customer_id references")

        # marketing_spend.channel_id -> strictly in PAID_CHANNEL_IDS
        paid_chan_set = set(PAID_CHANNEL_IDS)
        invalid_spend_chan = tables["marketing_spend"][~tables["marketing_spend"]["channel_id"].isin(paid_chan_set)]
        if not invalid_spend_chan.empty:
            self.errors.append(f"marketing_spend contains {len(invalid_spend_chan)} records with non-paid channel_id")

    def _check_null_constraints(self, tables: Dict[str, pd.DataFrame]):
        """Verifies that mandatory columns do not contain nulls."""
        mandatory_cols = {
            "channels": ["channel_id", "channel_name", "channel_type"],
            "customers": ["customer_id", "first_name", "last_name", "email", "signup_date", "acquisition_channel_id", "age", "city", "state", "device_preference"],
            "products": ["product_id", "product_name", "category", "sub_category", "cost_price", "retail_price"],
            "orders": ["order_id", "customer_id", "order_date", "order_status", "payment_method", "shipping_cost", "discount_amount", "total_order_amount"],
            "order_items": ["order_item_id", "order_id", "product_id", "quantity", "unit_price", "line_total"],
            "web_sessions": ["session_id", "customer_id", "session_date", "page_views", "time_spent_seconds", "cart_abandoned", "support_tickets"],
            "marketing_spend": ["spend_id", "spend_date", "channel_id", "campaign_name", "impressions", "clicks", "spend_usd"]
        }

        for table_name, cols in mandatory_cols.items():
            if table_name in tables:
                df = tables[table_name]
                for col in cols:
                    if col in df.columns and df[col].isnull().any():
                        null_cnt = df[col].isnull().sum()
                        self.errors.append(f"{table_name}.{col} contains {null_cnt} unexpected null values")

    def _check_dates_and_chronology(self, tables: Dict[str, pd.DataFrame]):
        """Checks observation boundaries and chronological sequence."""
        start_str = self.config.start_date.isoformat()
        end_str = self.config.end_date.isoformat()

        # Customer signup date range
        cust_df = tables["customers"]
        if (cust_df["signup_date"] < start_str).any() or (cust_df["signup_date"] > end_str).any():
            self.errors.append(f"customers.signup_date contains values outside [{start_str}, {end_str}]")

        # Marketing spend date range
        spend_df = tables["marketing_spend"]
        if (spend_df["spend_date"] < start_str).any() or (spend_df["spend_date"] > end_str).any():
            self.errors.append(f"marketing_spend.spend_date contains values outside [{start_str}, {end_str}]")

        # Web session date range
        sess_df = tables["web_sessions"]
        if (sess_df["session_date"] < start_str).any() or (sess_df["session_date"] > end_str).any():
            self.errors.append(f"web_sessions.session_date contains values outside [{start_str}, {end_str}]")

        # Orders date range
        ord_df = tables["orders"]
        ord_dates = ord_df["order_date"].str[:10]
        if (ord_dates < start_str).any() or (ord_dates > end_str).any():
            self.errors.append(f"orders.order_date contains dates outside [{start_str}, {end_str}]")

        # Customer signup <= order_date
        cust_signup_map = dict(zip(cust_df["customer_id"], cust_df["signup_date"]))
        ord_cust_signups = ord_df["customer_id"].map(cust_signup_map)
        invalid_order_chron = ord_df[ord_dates < ord_cust_signups]
        if not invalid_order_chron.empty:
            self.errors.append(f"Found {len(invalid_order_chron)} orders where order_date < customer signup_date")

        # Customer signup <= session_date
        sess_cust_signups = sess_df["customer_id"].map(cust_signup_map)
        invalid_sess_chron = sess_df[sess_df["session_date"] < sess_cust_signups]
        if not invalid_sess_chron.empty:
            self.errors.append(f"Found {len(invalid_sess_chron)} web sessions where session_date < customer signup_date")

    def _check_monetary_and_quantities(self, tables: Dict[str, pd.DataFrame]):
        """Checks pricing rules, quantity constraints, line totals, and order totals."""
        prod_df = tables["products"]
        # Retail price >= cost price > 0
        if (prod_df["cost_price"] <= 0).any():
            self.errors.append("products.cost_price contains non-positive values")
        if (prod_df["retail_price"] < prod_df["cost_price"]).any():
            self.errors.append("products contains items where retail_price < cost_price")

        # Order items quantity 1 to 10
        items_df = tables["order_items"]
        if (items_df["quantity"] < 1).any() or (items_df["quantity"] > 10).any():
            self.errors.append("order_items.quantity contains values outside [1, 10]")
        if (items_df["unit_price"] <= 0).any():
            self.errors.append("order_items.unit_price contains non-positive values")

        # line_total = quantity * unit_price
        expected_line_total = (items_df["quantity"] * items_df["unit_price"]).round(2)
        diff = (items_df["line_total"] - expected_line_total).abs()
        if (diff > 0.01).any():
            self.errors.append(f"order_items contains {(diff > 0.01).sum()} rows with line_total mismatch")

        # Orders financial consistency
        ord_df = tables["orders"]
        if (ord_df["total_order_amount"] < 0).any():
            self.errors.append("orders.total_order_amount contains negative values")
        if (ord_df["shipping_cost"] < 0).any():
            self.errors.append("orders.shipping_cost contains negative values")
        if (ord_df["discount_amount"] < 0).any():
            self.errors.append("orders.discount_amount contains negative values")

        # Sum of items + shipping - discount == total_order_amount
        items_by_order = items_df.groupby("order_id")["line_total"].sum().round(2)
        ord_df_calc = ord_df.set_index("order_id")
        expected_totals = (items_by_order + ord_df_calc["shipping_cost"] - ord_df_calc["discount_amount"]).round(2)
        expected_totals = expected_totals.clip(lower=0.0)

        total_diff = (ord_df_calc["total_order_amount"] - expected_totals).abs()
        mismatches = total_diff[total_diff > 0.01]
        if not mismatches.empty:
            self.errors.append(f"orders contains {len(mismatches)} rows where total_order_amount does not match line items + shipping - discount")

    def _check_marketing_spend_integrity(self, tables: Dict[str, pd.DataFrame]):
        """Checks marketing spend non-negativity and ratio sanity."""
        spend_df = tables["marketing_spend"]
        if (spend_df["spend_usd"] < 0).any():
            self.errors.append("marketing_spend.spend_usd contains negative values")
        if (spend_df["impressions"] < 0).any():
            self.errors.append("marketing_spend.impressions contains negative values")
        if (spend_df["clicks"] < 0).any():
            self.errors.append("marketing_spend.clicks contains negative values")
        if (spend_df["clicks"] > spend_df["impressions"]).any():
            self.errors.append("marketing_spend contains records where clicks > impressions")

    def _check_web_sessions_integrity(self, tables: Dict[str, pd.DataFrame]):
        """Checks web sessions metrics."""
        sess_df = tables["web_sessions"]
        if (sess_df["page_views"] < 1).any():
            self.errors.append("web_sessions.page_views contains values < 1")
        if (sess_df["time_spent_seconds"] < 0).any():
            self.errors.append("web_sessions.time_spent_seconds contains negative values")
        if (sess_df["support_tickets"] < 0).any():
            self.errors.append("web_sessions.support_tickets contains negative values")
