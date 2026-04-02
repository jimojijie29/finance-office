import akshare as ak
import pandas as pd
from datetime import datetime
import os

# 保存路径
script_dir = os.path.dirname(os.path.abspath(__file__))
save_dir = os.path.join(script_dir, '..', 'data')
os.makedirs(save_dir, exist_ok=True)

print("=" * 60)
print("Getting USD/HKD Exchange Rate Data")
print("=" * 60)

# 获取外汇数据
try:
    # 使用 fx_spot_quote 获取外汇数据
    fx_data = ak.fx_spot_quote()
    print("Available FX symbols:")
    print(fx_data.head(20))
except Exception as e:
    print(f"fx_spot_quote failed: {e}")

# 尝试获取历史外汇数据
try:
    # 使用 currency_history 接口
    print("\nTrying currency_history...")
    hkd_data = ak.currency_history(symbol="USDHKD", period="每日")
    print(f"Got {len(hkd_data)} USD/HKD records")
    print(f"Date range: {hkd_data['日期'].min()} to {hkd_data['日期'].max()}")
    print(hkd_data.head())
    
    hkd_file = os.path.join(save_dir, "HKD_USD_Exchange_Rate.csv")
    hkd_data.to_csv(hkd_file, index=False, encoding='utf-8-sig')
    print(f"\nSaved to: {hkd_file}")
except Exception as e:
    print(f"currency_history failed: {e}")

print("\n" + "=" * 60)
print("Getting Hang Seng Index Data")
print("=" * 60)

# 获取恒生指数
try:
    # 使用 index_stock_hk 获取港股指数
    print("\nTrying index_stock_hk...")
    hsi_data = ak.index_stock_hk(symbol="HSI")
    print(f"Got {len(hsi_data)} HSI records")
    print(hsi_data.head())
except Exception as e:
    print(f"index_stock_hk failed: {e}")

try:
    # 使用 stock_hk_index_daily_sina
    print("\nTrying stock_hk_index_daily_sina...")
    hsi_data = ak.stock_hk_index_daily_sina(symbol="HSI")
    print(f"Got {len(hsi_data)} HSI records")
    print(f"Date range: {hsi_data['date'].min()} to {hsi_data['date'].max()}")
    print(hsi_data.head())
    
    hsi_file = os.path.join(save_dir, "Hang_Seng_Index.csv")
    hsi_data.to_csv(hsi_file, index=False, encoding='utf-8-sig')
    print(f"\nSaved to: {hsi_file}")
except Exception as e:
    print(f"stock_hk_index_daily_sina failed: {e}")

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)
