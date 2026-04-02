#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch CN Treasury Yield Data (Last 3 Years)
Using Tushare yc_cb API
"""

import os
import tushare as ts
from datetime import datetime, timedelta
import pandas as pd

# Get token from environment
token = os.getenv('TUSHARE_TOKEN') or ts.get_token()

if not token:
    raise ValueError("TUSHARE_TOKEN not found. Set env var or use ts.set_token()")

# Initialize pro API
pro = ts.pro_api(token)

# Date range: last 3 years
end_date = datetime.now().strftime('%Y%m%d')
start_date = (datetime.now() - timedelta(days=3*365)).strftime('%Y%m%d')

print(f"Fetching data: {start_date} to {end_date}")
print("Trying to fetch all curve data...")

try:
    df = pro.yc_cb(
        start_date=start_date,
        end_date=end_date,
        limit=2000
    )
    if df.empty:
        print("No data retrieved")
    else:
        print(f"Retrieved {len(df)} records")
        print("Curve types:", df['curve_type'].unique())
        print("Terms available:", df['curve_term'].unique())

        # Pivot: terms as columns
        pivot_df = df.pivot_table(
            index='trade_date',
            columns='curve_term',
            values='yield'
        )

        # Flatten column names
        pivot_df.columns = [f'term_{col}' for col in pivot_df.columns]
        pivot_df = pivot_df.reset_index(inplace=True)
        pivot_df.index.name = 'trade_date'

        # Save to CSV
        output_file = 'cn_treasury_yield.csv'
        pivot_df.to_csv(output_file, index=True, encoding='utf-8-sig')
        print(f"\nData saved to: {output_file}")
        print(f"Total records: {len(pivot_df)}")

except Exception as e:
    print(f"Error: {e}")
