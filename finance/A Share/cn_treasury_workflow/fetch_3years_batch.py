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

# 获取近3年的数据
end_date = datetime.now()
start_date = end_date - timedelta(days=3*365)

start_date_str = start_date.strftime('%Y%m%d')
end_date_str = end_date.strftime('%Y%m%d')

print(f'开始获取近3年数据: {start_date_str} 至 {end_date_str}')
print('使用 start_date 和 end_date 参数批量获取...')
print()

all_data = []
page = 1

while True:
    try:
        print(f'获取第 {page} 页数据...')
        
        df = pro.yc_cb(
            ts_code='1001.CB',
            curve_type='0',
            start_date=start_date_str,
            end_date=end_date_str,
            limit=2000,
            offset=(page-1)*2000
        )
        
        if df is None or len(df) == 0:
            print(f'第 {page} 页无数据，结束获取')
            break
        
        all_data.append(df)
        print(f'第 {page} 页成功: {len(df)} 条')
        
        # 如果不足2000条，说明已获取全部
        if len(df) < 2000:
            print('数据获取完成')
            break
        
        page += 1
        
        # 遵守频率限制
        print('等待35秒以遵守API频率限制...')
        time.sleep(35)
        
    except Exception as e:
        error_msg = str(e)
        print(f'错误: {error_msg[:100]}')
        if '频次' in error_msg or '积分' in error_msg:
            print('API限制，等待60秒...')
            time.sleep(60)
        else:
            time.sleep(10)

print(f'\n总共获取 {len(all_data)} 页数据')

if len(all_data) > 0:
    # 合并数据
    combined = pd.concat(all_data, ignore_index=True)
    print(f'总记录数: {len(combined)}')
    print(f'数据日期范围: {combined["trade_date"].min()} 至 {combined["trade_date"].max()}')
    
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
    print(f'总记录数: {len(df_result)} 个交易日')
    print('\n最新数据:')
    print(df_result.iloc[-1].to_string())
    print('\n最早数据:')
    print(df_result.iloc[0].to_string())
else:
    print('未获取到数据')
