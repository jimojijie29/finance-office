import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

import pandas as pd
import tushare as ts
import time
from datetime import datetime, timedelta

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

# 读取现有数据
try:
    existing_df = pd.read_csv('cn_treasury_yields.csv')
    existing_df['date'] = pd.to_datetime(existing_df['date'])
    last_date = existing_df['date'].max()
    print(f'现有数据最后日期: {last_date.strftime("%Y-%m-%d")}')
    print(f'现有记录数: {len(existing_df)}')
except:
    existing_df = None
    last_date = None
    print('无现有数据')

# 获取近3年数据，但只获取每月1日的数据（减少API调用）
end_date = datetime.now()
start_date = end_date - timedelta(days=3*365)

# 生成每月1日的日期列表
monthly_dates = []
current = start_date
while current <= end_date:
    monthly_dates.append(current.strftime('%Y%m%d'))
    # 下个月
    if current.month == 12:
        current = current.replace(year=current.year+1, month=1)
    else:
        current = current.replace(month=current.month+1)

print(f'\n计划获取 {len(monthly_dates)} 个月的数据（每月1日）')

# 获取数据
all_data = []
for i, trade_date in enumerate(monthly_dates):
    try:
        df = pro.yc_cb(ts_code='1001.CB', curve_type='0', trade_date=trade_date, limit=2000)
        if df is not None and len(df) > 0:
            all_data.append(df)
            print(f'{i+1}/{len(monthly_dates)} {trade_date}: {len(df)} 条')
        else:
            print(f'{i+1}/{len(monthly_dates)} {trade_date}: 无数据')
        time.sleep(35)  # 遵守频率限制
    except Exception as e:
        print(f'{i+1}/{len(monthly_dates)} {trade_date}: 错误 - {str(e)[:50]}')
        time.sleep(35)

print(f'\n成功获取 {len(all_data)} 个月的数据')

if len(all_data) > 0:
    # 处理数据
    combined = pd.concat(all_data, ignore_index=True)
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
    
    df_new = pd.DataFrame(pivot_data)
    
    # 确保所有列存在
    target_cols = ['X1年', 'X2年', 'X3年', 'X5年', 'X7年', 'X10年', 'X20年', 'X30年']
    for col in target_cols:
        if col not in df_new.columns:
            df_new[col] = float('nan')
    
    df_new = df_new[['date'] + target_cols].sort_values('date')
    
    # 合并现有数据
    if existing_df is not None:
        combined_df = pd.concat([existing_df, df_new], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
        combined_df = combined_df.sort_values('date')
        print(f'\n合并后: {len(combined_df)} 个交易日')
    else:
        combined_df = df_new
    
    # 保存
    combined_df['date'] = combined_df['date'].dt.strftime('%Y-%m-%d')
    combined_df.to_csv('cn_treasury_yields.csv', index=False, encoding='utf-8-sig')
    
    print(f'\n数据已保存!')
    print(f'日期范围: {combined_df["date"].min()} 至 {combined_df["date"].max()}')
    print(f'总交易日数: {len(combined_df)}')
else:
    print('未获取到数据')
