"""
Customer profiles generation module for Aura Retail.
Produces dim_customers with realistic demographic distributions,
growth in acquisition over 2024-2025, device preferences, and channel attribution.
"""

from datetime import timedelta
import numpy as np
import pandas as pd
from faker import Faker
from src.data_generator.config import GeneratorConfig

US_METROS = [
    ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"),
    ("Houston", "TX"), ("Phoenix", "AZ"), ("Philadelphia", "PA"),
    ("San Antonio", "TX"), ("San Diego", "CA"), ("Dallas", "TX"),
    ("Austin", "TX"), ("San Jose", "CA"), ("Seattle", "WA"),
    ("Denver", "CO"), ("Boston", "MA"), ("Atlanta", "GA"),
    ("Miami", "FL"), ("Nashville", "TN"), ("Minneapolis", "MN"),
    ("Charlotte", "NC"), ("Portland", "OR"), ("Salt Lake City", "UT"),
    ("Tampa", "FL"), ("San Francisco", "CA"), ("Raleigh", "NC")
]

# Channel allocation probabilities (sum = 1.0)
CHANNEL_PROBS = {
    1: 0.20,  # Organic Search
    2: 0.24,  # Paid Search
    3: 0.28,  # Paid Social
    4: 0.09,  # Affiliate
    5: 0.05,  # Email
    6: 0.14,  # Direct
}


def generate_customers(config: GeneratorConfig) -> pd.DataFrame:
    """
    Generates deterministic dim_customers DataFrame.
    
    Args:
        config: Generator configuration with seed, date bounds, and customer count.
        
    Returns:
        pd.DataFrame: Table with customer profiles.
    """
    rng = np.random.default_rng(config.seed)
    fake = Faker()
    fake.seed_instance(config.seed)
    Faker.seed(config.seed)

    n_customers = config.n_customers
    total_days = config.total_calendar_days  # 731 days

    # 1. Signup date weights: gradual brand growth + Q4 holiday acquisition spikes
    # Weight per day i in [0, total_days - 1]
    days_arr = np.arange(total_days)
    # Trend: 1.0 at start to 2.2 at end (linear growth)
    growth_trend = 1.0 + 1.2 * (days_arr / total_days)
    
    # Seasonality weights:
    day_dates = [config.start_date + timedelta(days=int(d)) for d in days_arr]
    seasonal_factors = []
    for d in day_dates:
        factor = 1.0
        # Holiday season boost (Nov 15 - Dec 31)
        if d.month == 11 and d.day >= 15:
            factor = 2.4
        elif d.month == 12:
            factor = 2.2
        # Summer promotion (July)
        elif d.month == 7:
            factor = 1.3
        # Spring refresh (March/April)
        elif d.month in (3, 4):
            factor = 1.15
        seasonal_factors.append(factor)
        
    weights = growth_trend * np.array(seasonal_factors)
    signup_day_probs = weights / weights.sum()

    # Draw signup days
    customer_signup_day_indices = rng.choice(total_days, size=n_customers, p=signup_day_probs)
    # Sort indices so customer IDs generally follow registration chronological order
    customer_signup_day_indices.sort()

    # 2. Acquisition channels
    channel_ids = list(CHANNEL_PROBS.keys())
    channel_weights = list(CHANNEL_PROBS.values())
    cust_channels = rng.choice(channel_ids, size=n_customers, p=channel_weights)

    # 3. Ages: Gamma/Normal centered around 34, bounded [18, 75]
    raw_ages = rng.normal(loc=34.0, scale=11.0, size=n_customers)
    ages = np.clip(np.round(raw_ages), 18, 75).astype(int)

    # 4. Genders: Female (52%), Male (42%), Non-binary (6%)
    genders = rng.choice(["Female", "Male", "Non-binary"], size=n_customers, p=[0.52, 0.42, 0.06])

    # 5. Device preference: Mobile (65%), Desktop (28%), Tablet (7%)
    device_prefs = rng.choice(["Mobile", "Desktop", "Tablet"], size=n_customers, p=[0.65, 0.28, 0.07])

    # 6. Geography (City, State)
    metro_indices = rng.choice(len(US_METROS), size=n_customers)

    customers = []
    email_set = set()

    for i in range(n_customers):
        cust_id = f"CUST_{i + 1:05d}"
        gender = genders[i]
        
        if gender == "Female":
            first_name = fake.first_name_female()
        elif gender == "Male":
            first_name = fake.first_name_male()
        else:
            first_name = fake.first_name_nonbinary()
            
        last_name = fake.last_name()
        
        # Ensure unique email
        clean_first = first_name.lower().replace(" ", "").replace("'", "")
        clean_last = last_name.lower().replace(" ", "").replace("'", "")
        email_candidate = f"{clean_first}.{clean_last}{i + 1}@example.com"
        email_set.add(email_candidate)

        signup_date = config.start_date + timedelta(days=int(customer_signup_day_indices[i]))
        city, state = US_METROS[metro_indices[i]]

        customers.append({
            "customer_id": cust_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email_candidate,
            "signup_date": signup_date.isoformat(),
            "acquisition_channel_id": int(cust_channels[i]),
            "age": int(ages[i]),
            "gender": gender,
            "city": city,
            "state": state,
            "device_preference": device_prefs[i]
        })

    df = pd.DataFrame(customers)
    return df
