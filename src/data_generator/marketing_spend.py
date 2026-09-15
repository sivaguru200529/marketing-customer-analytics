"""
Marketing spend generation module for Aura Retail.
Produces fact_marketing_spend covering 731 calendar days across the 3 paid
marketing channels (Paid Search, Paid Social, Affiliate), totaling exactly
2,193 records with realistic CPC, CTR, and Q4 holiday surges.
"""

from datetime import timedelta
import numpy as np
import pandas as pd
from src.data_generator.config import GeneratorConfig
from src.data_generator.channels import PAID_CHANNEL_IDS

PAID_CHANNEL_CONFIGS = {
    2: {  # Paid Search
        "name": "Paid Search",
        "campaigns": [
            "Search_Brand_Core",
            "Search_Generic_HighIntent",
            "Search_Competitor_Conquest",
            "Search_Holiday_Surge"
        ],
        "base_daily_spend": (550.0, 950.0),
        "ctr_range": (0.025, 0.045),      # High intent, higher CTR
        "cpc_range": (0.90, 1.85),        # Higher CPC for search
    },
    3: {  # Paid Social
        "name": "Paid Social",
        "campaigns": [
            "Meta_Advantage_Catalog_Ads",
            "TikTok_Creator_Lifestyle",
            "Instagram_Story_Retargeting",
            "Social_Cyber_Week_Special"
        ],
        "base_daily_spend": (700.0, 1300.0),
        "ctr_range": (0.012, 0.025),      # Lower CTR, massive reach
        "cpc_range": (0.50, 1.20),        # Moderate CPC
    },
    4: {  # Affiliate
        "name": "Affiliate",
        "campaigns": [
            "Affiliate_Creator_Network",
            "Editorial_Lifestyle_Reviews",
            "Partner_Syndication_Cashback"
        ],
        "base_daily_spend": (180.0, 420.0),
        "ctr_range": (0.018, 0.032),
        "cpc_range": (0.35, 0.75),        # Performance affiliate CPC
    }
}


def generate_marketing_spend(config: GeneratorConfig) -> pd.DataFrame:
    """
    Generates deterministic fact_marketing_spend DataFrame.
    
    Args:
        config: Generator configuration with seed and date bounds.
        
    Returns:
        pd.DataFrame: Table with marketing spend metrics for 731 days x 3 channels = 2,193 rows.
    """
    rng = np.random.default_rng(config.seed)
    total_days = config.total_calendar_days  # 731 days
    spend_records = []
    record_id = 1001

    for day_offset in range(total_days):
        current_date = config.start_date + timedelta(days=day_offset)
        
        # Day of week multiplier (higher spend on Sunday/Monday/Thursday)
        dow = current_date.weekday()
        dow_mult = 1.15 if dow in (0, 3, 6) else (0.90 if dow == 5 else 1.0)
        
        # Annual trend multiplier (gradual scale from 2024 to 2025: 1.0 -> 1.35)
        trend_mult = 1.0 + 0.35 * (day_offset / total_days)
        
        # Seasonal multiplier (Q4 holiday surge, July summer sale)
        month = current_date.month
        day = current_date.day
        if month == 11 and day >= 20:
            season_mult = 2.85  # Black Friday / Cyber Week
        elif month == 11 and day < 20:
            season_mult = 1.70  # Early holiday warm-up
        elif month == 12 and day <= 22:
            season_mult = 2.40  # Holiday shopping rush
        elif month == 12 and day > 22:
            season_mult = 1.20  # Post-holiday wind-down
        elif month == 7 and 10 <= day <= 20:
            season_mult = 1.45  # Mid-year / Summer Prime event
        elif month in (1, 2):
            season_mult = 0.85  # Post-holiday lull
        else:
            season_mult = 1.05

        for channel_id in PAID_CHANNEL_IDS:
            chan_cfg = PAID_CHANNEL_CONFIGS[channel_id]
            
            # Select appropriate campaign
            if month in (11, 12):
                campaign = [c for c in chan_cfg["campaigns"] if "Holiday" in c or "Cyber" in c or "Special" in c]
                campaign_name = campaign[0] if campaign else chan_cfg["campaigns"][0]
            else:
                non_holiday_camps = [c for c in chan_cfg["campaigns"] if "Holiday" not in c and "Cyber" not in c]
                campaign_name = non_holiday_camps[day_offset % len(non_holiday_camps)]

            # Calculate daily spend
            min_s, max_s = chan_cfg["base_daily_spend"]
            base_spend = rng.uniform(min_s, max_s)
            daily_spend = round(base_spend * dow_mult * trend_mult * season_mult, 2)
            
            # CPC and Clicks
            cpc_min, cpc_max = chan_cfg["cpc_range"]
            # Holiday CPC inflation
            cpc_inflation = 1.35 if (month in (11, 12)) else 1.0
            actual_cpc = rng.uniform(cpc_min, cpc_max) * cpc_inflation
            clicks = max(10, int(round(daily_spend / actual_cpc)))
            
            # CTR and Impressions
            ctr_min, ctr_max = chan_cfg["ctr_range"]
            actual_ctr = rng.uniform(ctr_min, ctr_max)
            impressions = max(clicks * 5, int(round(clicks / actual_ctr)))

            spend_records.append({
                "spend_id": record_id,
                "spend_date": current_date.isoformat(),
                "channel_id": channel_id,
                "campaign_name": campaign_name,
                "impressions": int(impressions),
                "clicks": int(clicks),
                "spend_usd": float(daily_spend)
            })
            record_id += 1

    df = pd.DataFrame(spend_records)
    return df
