"""
Automated unit and integration test suite for Aura Retail Synthetic Data Generator.
Verifies reproducibility, catalog integrity, demographic distributions,
referential integrity, order item mathematics, marketing seasonality,
web session linkage, and validator exception handling.
"""

from datetime import date
import pytest
import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal

from src.data_generator.config import GeneratorConfig, get_sample_config
from src.data_generator.channels import generate_channels, PAID_CHANNEL_IDS
from src.data_generator.products import generate_products
from src.data_generator.customers import generate_customers
from src.data_generator.marketing_spend import generate_marketing_spend
from src.data_generator.orders import generate_orders_and_items
from src.data_generator.web_sessions import generate_web_sessions
from src.data_generator.validators import DatasetValidator, ValidationError


@pytest.fixture
def sample_config(tmp_path):
    """Provides a small, fast sample configuration for testing."""
    return GeneratorConfig(
        seed=42,
        start_date=date(2024, 1, 1),
        end_date=date(2025, 12, 31),
        n_customers=200,
        n_products=40,
        n_orders=600,
        n_sessions=1500,
        min_order_items=1400,
        output_dir=tmp_path,
        is_sample=True
    )


@pytest.fixture
def sample_dataset(sample_config):
    """Generates a complete validated dataset using sample_config."""
    channels_df = generate_channels()
    products_df = generate_products(sample_config)
    customers_df = generate_customers(sample_config)
    marketing_df = generate_marketing_spend(sample_config)
    orders_df, items_df = generate_orders_and_items(customers_df, products_df, sample_config)
    sessions_df = generate_web_sessions(customers_df, orders_df, sample_config)

    tables = {
        "channels": channels_df,
        "customers": customers_df,
        "products": products_df,
        "orders": orders_df,
        "order_items": items_df,
        "web_sessions": sessions_df,
        "marketing_spend": marketing_df
    }
    return tables


def test_reproducibility(tmp_path):
    """
    Requirement 2: Verifies that running generation twice with seed=42
    produces identical DataFrames across all entities.
    """
    config1 = GeneratorConfig(
        seed=42,
        start_date=date(2024, 1, 1),
        end_date=date(2025, 12, 31),
        n_customers=100,
        n_products=25,
        n_orders=250,
        n_sessions=600,
        min_order_items=550,
        output_dir=tmp_path / "run1",
        is_sample=True
    )
    config2 = GeneratorConfig(
        seed=42,
        start_date=date(2024, 1, 1),
        end_date=date(2025, 12, 31),
        n_customers=100,
        n_products=25,
        n_orders=250,
        n_sessions=600,
        min_order_items=550,
        output_dir=tmp_path / "run2",
        is_sample=True
    )

    # Run 1
    p1 = generate_products(config1)
    c1 = generate_customers(config1)
    m1 = generate_marketing_spend(config1)
    o1, i1 = generate_orders_and_items(c1, p1, config1)
    s1 = generate_web_sessions(c1, o1, config1)

    # Run 2
    p2 = generate_products(config2)
    c2 = generate_customers(config2)
    m2 = generate_marketing_spend(config2)
    o2, i2 = generate_orders_and_items(c2, p2, config2)
    s2 = generate_web_sessions(c2, o2, config2)

    assert_frame_equal(p1, p2)
    assert_frame_equal(c1, c2)
    assert_frame_equal(m1, m2)
    assert_frame_equal(o1, o2)
    assert_frame_equal(i1, i2)
    assert_frame_equal(s1, s2)


def test_product_catalog_integrity(sample_dataset):
    """Verifies product pricing, category margins, and ID uniqueness."""
    products = sample_dataset["products"]
    assert len(products) > 0
    assert products["product_id"].is_unique
    assert (products["cost_price"] > 0).all()
    assert (products["retail_price"] >= products["cost_price"]).all()

    # Check that gross margin is strictly positive
    margins = (products["retail_price"] - products["cost_price"]) / products["retail_price"]
    assert (margins >= 0.30).all()
    assert (margins <= 0.85).all()

    # Verify categories present
    expected_categories = {"Apparel", "Home Goods", "Beauty & Wellness", "Accessories", "Electronics & Audio"}
    assert set(products["category"].unique()).issubset(expected_categories)


def test_customer_distributions(sample_dataset, sample_config):
    """Verifies customer age ranges, signup date limits, and channel assignment."""
    customers = sample_dataset["customers"]
    assert len(customers) == sample_config.n_customers
    assert customers["customer_id"].is_unique
    assert customers["email"].is_unique

    # Age bounds
    assert (customers["age"] >= 18).all()
    assert (customers["age"] <= 75).all()

    # Signup dates within 2024-01-01 to 2025-12-31
    assert (customers["signup_date"] >= "2024-01-01").all()
    assert (customers["signup_date"] <= "2025-12-31").all()

    # 6 channels referenced
    assert set(customers["acquisition_channel_id"].unique()).issubset({1, 2, 3, 4, 5, 6})


def test_order_chronology_and_fks(sample_dataset, sample_config):
    """Verifies foreign keys and that order dates are strictly >= signup dates."""
    customers = sample_dataset["customers"]
    orders = sample_dataset["orders"]

    assert len(orders) == sample_config.n_orders
    assert orders["order_id"].is_unique

    # Foreign key check
    valid_cust_ids = set(customers["customer_id"])
    assert set(orders["customer_id"]).issubset(valid_cust_ids)

    # Date chronology check
    signup_map = dict(zip(customers["customer_id"], customers["signup_date"]))
    order_dates = orders["order_date"].str[:10]
    cust_signups = orders["customer_id"].map(signup_map)
    assert (order_dates >= cust_signups).all()
    assert (order_dates >= "2024-01-01").all()
    assert (order_dates <= "2025-12-31").all()


def test_order_item_math(sample_dataset):
    """Verifies line_total = quantity * unit_price and order total consistency."""
    orders = sample_dataset["orders"]
    items = sample_dataset["order_items"]

    assert items["order_item_id"].is_unique
    assert (items["quantity"] >= 1).all()
    assert (items["quantity"] <= 10).all()
    assert (items["unit_price"] > 0).all()

    # Math: line_total == quantity * unit_price
    expected_line_totals = (items["quantity"] * items["unit_price"]).round(2)
    diff = (items["line_total"] - expected_line_totals).abs()
    assert (diff <= 0.01).all()

    # Order header total consistency
    items_sum = items.groupby("order_id")["line_total"].sum().round(2)
    orders_indexed = orders.set_index("order_id")
    expected_totals = (items_sum + orders_indexed["shipping_cost"] - orders_indexed["discount_amount"]).round(2)
    expected_totals = expected_totals.clip(lower=0.0)

    total_diff = (orders_indexed["total_order_amount"] - expected_totals).abs()
    assert (total_diff <= 0.01).all()


def test_customer_order_distribution(sample_config):
    """
    Requirement 4: Verifies repeat purchase behavior and rebalancing logic.
    - ~60% single purchase
    - ~22% 2-3 orders
    - ~12% 4-6 orders
    - ~6% 7-15+ orders
    - Exactly hits target order count.
    """
    customers = generate_customers(sample_config)
    products = generate_products(sample_config)
    orders, _ = generate_orders_and_items(customers, products, sample_config)

    assert len(orders) == sample_config.n_orders
    order_counts_per_cust = orders["customer_id"].value_counts()
    
    single_orders = (order_counts_per_cust == 1).sum()
    pct_single = single_orders / len(customers)
    
    # Check that single buyers are approximately ~55-65%
    assert 0.50 <= pct_single <= 0.70
    
    # Check that repeat buyers exist in all tiers
    repeat_2_3 = ((order_counts_per_cust >= 2) & (order_counts_per_cust <= 3)).sum()
    repeat_4_6 = ((order_counts_per_cust >= 4) & (order_counts_per_cust <= 6)).sum()
    vip_7_plus = (order_counts_per_cust >= 7).sum()

    assert repeat_2_3 > 0
    assert repeat_4_6 > 0
    assert vip_7_plus > 0


def test_marketing_spend_seasonality(sample_dataset, sample_config):
    """
    Requirement 5: Verifies 731 days x 3 paid channels = 2,193 rows.
    Only channels 2, 3, 4 are present. Q4 holiday spend > Q1 spend.
    """
    spend = sample_dataset["marketing_spend"]
    total_expected_rows = sample_config.total_calendar_days * 3  # 731 * 3 = 2,193
    assert len(spend) == total_expected_rows
    assert spend["spend_id"].is_unique

    # Channels strictly in PAID_CHANNEL_IDS [2, 3, 4]
    assert set(spend["channel_id"].unique()) == set(PAID_CHANNEL_IDS)

    # Sanity of metrics
    assert (spend["spend_usd"] > 0).all()
    assert (spend["impressions"] > 0).all()
    assert (spend["clicks"] > 0).all()
    assert (spend["clicks"] <= spend["impressions"]).all()

    # Seasonality check: Nov/Dec average spend should exceed Jan/Feb average spend
    spend["month"] = pd.to_datetime(spend["spend_date"]).dt.month
    q4_spend = spend[spend["month"].isin([11, 12])]["spend_usd"].mean()
    q1_spend = spend[spend["month"].isin([1, 2])]["spend_usd"].mean()
    assert q4_spend > 1.5 * q1_spend


def test_web_sessions_linkage(sample_dataset, sample_config):
    """Verifies web sessions foreign keys, date consistency, and cart abandonment."""
    sessions = sample_dataset["web_sessions"]
    customers = sample_dataset["customers"]

    assert len(sessions) == sample_config.n_sessions
    assert sessions["session_id"].is_unique
    assert set(sessions["customer_id"]).issubset(set(customers["customer_id"]))

    # Signup <= session date
    signup_map = dict(zip(customers["customer_id"], customers["signup_date"]))
    cust_signups = sessions["customer_id"].map(signup_map)
    assert (sessions["session_date"] >= cust_signups).all()

    # Engagement metrics
    assert (sessions["page_views"] >= 1).all()
    assert (sessions["time_spent_seconds"] >= 0).all()
    assert (sessions["support_tickets"] >= 0).all()
    assert sessions["cart_abandoned"].isin([True, False]).all()


def test_validator_failure_cases(sample_dataset, sample_config):
    """Requirement 7: Verifies that DatasetValidator detects intentional errors."""
    validator = DatasetValidator(sample_config)
    
    # 1. Baseline should pass
    assert validator.validate_all(sample_dataset) is True

    # 2. Test duplicate primary key injection
    corrupted_tables = {k: v.copy() for k, v in sample_dataset.items()}
    corrupted_tables["customers"].loc[1, "customer_id"] = corrupted_tables["customers"].loc[0, "customer_id"]
    with pytest.raises(ValidationError) as excinfo:
        validator.validate_all(corrupted_tables)
    assert "duplicate primary key" in str(excinfo.value)

    # 3. Test orphan foreign key injection
    corrupted_tables = {k: v.copy() for k, v in sample_dataset.items()}
    corrupted_tables["orders"].loc[0, "customer_id"] = "CUST_NON_EXISTENT"
    with pytest.raises(ValidationError) as excinfo:
        validator.validate_all(corrupted_tables)
    assert "orphan customer_id" in str(excinfo.value)

    # 4. Test negative price injection
    corrupted_tables = {k: v.copy() for k, v in sample_dataset.items()}
    corrupted_tables["products"].loc[0, "cost_price"] = -10.00
    with pytest.raises(ValidationError) as excinfo:
        validator.validate_all(corrupted_tables)
    assert "products.cost_price contains non-positive values" in str(excinfo.value)

    # 5. Test chronology violation injection (order before signup)
    corrupted_tables = {k: v.copy() for k, v in sample_dataset.items()}
    corrupted_tables["orders"].loc[0, "order_date"] = "2023-12-01 10:00:00"
    with pytest.raises(ValidationError) as excinfo:
        validator.validate_all(corrupted_tables)
    assert "outside" in str(excinfo.value) or "order_date < customer signup_date" in str(excinfo.value)

    # 6. Test invalid marketing channel injection (channel 1 in spend)
    corrupted_tables = {k: v.copy() for k, v in sample_dataset.items()}
    corrupted_tables["marketing_spend"].loc[0, "channel_id"] = 1  # Organic Search (non-paid)
    with pytest.raises(ValidationError) as excinfo:
        validator.validate_all(corrupted_tables)
    assert "non-paid channel_id" in str(excinfo.value)
