import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

import pandas as pd
import tushare as ts
from datetime import datetime, timedelta
import time

# 初始化Tushare
token = os.environ.get('TUSHARE_TOKEN')
pro = ts.pro_api(token)

# 期限映射
TERM_MAPPING = {
    0.08: 'X1月', 0.10: 'X2月', 0.17: 'X3月', 0.25: 'X5月',
    0.50: 'X6月', 0.75: 'X9月', 1.00: 'X1年', 2.00: 'X2年',
    3.00: 'X3年', 5.00: 'X5年', 7.00: 'X7年', 10.00: 'X10年',
    15.00: 'X15年', 20.00: 'X20年', 30.00: 'X30年', 40.00: 'X40年',
}

# 获取最近10个工作日的数据
all_data = []
dates_to_fetch = []

end_date = datetime.now()
for i in range(1, 20):
    d = end_date - timedelta(days=i)
    if d.weekday() < 5:  # 工作日
        dates_to_fetch.append(d.strftime('%Y%m%d'))
    if len(dates_to_fetch) >= 10:
        break

print(f'将获取 {len(dates_to_fetch)} 个交易日的数据')

for trade_date in dates_to_fetch:
    try:
        df = pro.yc_cb(ts_code='1001.CB', curve_type='0', trade_date=trade_date, limit=2000)
        if df is not None and len(df) > 0:
            all_data.append(df)
            print(f'{trade_date}: {len(df)} 条')
        else:
            print(f'{trade_date}: 无数据')
        time.sleep(35)
    except Exception as e:
        print(f'{trade_date}: 错误 - {str(e)[:60]}')
        time.sleep(35)

print(f'\n总共获取 {len(all_data)} 个交易日')

if len(all_data) > 0:
    # 合并数据
    combined = pd.concat(all_data, ignore_index=True)
    print(f'总记录数: {len(combined)}')
    
    # 处理数据
    combined['date'] = pd.to_datetime(combined['trade_date'], format='%Y%m%d')
    combined['curve_term'] = pd.to_numeric(combined['curve_term'], errors='coerce')
    combined['yield'] = pd.to_numeric(combined['yield'], errors='coerce')
    
    # 透视
    pivot_data = []
    for date, group in combined.groupby('date'):
        row = {'date': date}
        for _, r in group.iterrows():
            term = r['curve_term']
            yield_val = r['yield']
            if term in TERM_MAPPING and pd.notna(yield_val):
                row[TERM_MAPPING[term]] = yield_val
        pivot_data.append(row)
    
    df_result = pd.DataFrame(pivot_data)
    
    # 确保所有列存在
    target_cols = ['X1年', 'X2年', 'X3年', 'X5年', 'X7年', 'X10年', 'X20年', 'X30年']
    for col in target_cols:
        if col not in df_result.columns:
            df_result[col] = float('nan')
    
    df_result = df_result[['date'] + target_cols].sort_values('date')
    
    # 保存
    df_result['date'] = df_result['date'].dt.strftime('%Y-%m-%d')
    df_result.to_csv('cn_treasury_yields.csv', index=False, encoding='utf-8-sig')
    
    print('\n数据已保存到 cn_treasury_yields.csv')
    print(f'日期范围: {df_result["date"].min()} 至 {df_result["date"].max()}')
    print(f'总记录数: {len(df_result)}')
    print('\n最新数据:')
    print(df_result.iloc[-1].to_string())
else:
    print('未获取到数据')
