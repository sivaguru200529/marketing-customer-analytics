"""
Marketing and acquisition channels definition module.
Generates dim_channels containing 6 acquisition channels, distinguishing
paid channels (Paid Search, Paid Social, Affiliate) from organic/owned channels.
"""

import pandas as pd

CHANNELS_DATA = [
    {"channel_id": 1, "channel_name": "Organic Search", "channel_type": "Organic"},
    {"channel_id": 2, "channel_name": "Paid Search", "channel_type": "Paid"},
    {"channel_id": 3, "channel_name": "Paid Social", "channel_type": "Paid"},
    {"channel_id": 4, "channel_name": "Affiliate", "channel_type": "Referral"},
    {"channel_id": 5, "channel_name": "Email", "channel_type": "Owned"},
    {"channel_id": 6, "channel_name": "Direct", "channel_type": "Organic"},
]

PAID_CHANNEL_IDS = [2, 3, 4]


def generate_channels() -> pd.DataFrame:
    """
    Generates the reference DataFrame for dim_channels.
    
    Returns:
        pd.DataFrame: Table with columns [channel_id, channel_name, channel_type].
    """
    df = pd.DataFrame(CHANNELS_DATA)
    return df
