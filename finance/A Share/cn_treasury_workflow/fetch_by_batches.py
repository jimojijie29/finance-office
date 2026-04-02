import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

import pandas as pd
import tushare as ts
import time
from datetime import datetime

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

# 分批次获取数据
# 每批获取约6个月的数据
batches = [
    ('20230101', '20230630'),  # 2023上半年
    ('20230701', '20231231'),  # 2023下半年
    ('20240101', '20240630'),  # 2024上半年
    ('20240701', '20241231'),  # 2024下半年
    ('20250101', '20250630'),  # 2025上半年
    ('20250701', '20251231'),  # 2025下半年
]

all_processed_data = []

for start_date, end_date in batches:
    print(f'\n获取批次: {start_date} 至 {end_date}')
    
    all_data = []
    page = 1
    
    while True:
        try:
            print(f'  第 {page} 页...', end=' ')
            
            df = pro.yc_cb(
                ts_code='1001.CB',
                curve_type='0',
                start_date=start_date,
                end_date=end_date,
                limit=2000,
                offset=(page-1)*2000
            )
            
            if df is None or len(df) == 0:
                print('无数据')
                break
            
            all_data.append(df)
            print(f'{len(df)} 条')
            
            if len(df) < 2000:
                print('  完成')
                break
            
            page += 1
            time.sleep(35)  # 遵守频率限制
            
        except Exception as e:
            error_msg = str(e)
            if '频次' in error_msg:
                print('API限制，等待60秒...')
                time.sleep(60)
            else:
                print(f'错误: {error_msg[:50]}')
                time.sleep(10)
    
    if len(all_data) > 0:
        # 处理这批数据
        combined = pd.concat(all_data, ignore_index=True)
        print(f'  本批共 {len(combined)} 条原始记录')
        
        # 转换和处理
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
        
        df_batch = pd.DataFrame(pivot_data)
        all_processed_data.append(df_batch)
        print(f'  处理后: {len(df_batch)} 个交易日')
    
    # 批次间等待
    time.sleep(35)

# 合并所有批次
if len(all_processed_data) > 0:
    print('\n合并所有数据...')
    final_df = pd.concat(all_processed_data, ignore_index=True)
    
    # 确保所有列存在
    target_cols = ['X1年', 'X2年', 'X3年', 'X5年', 'X7年', 'X10年', 'X20年', 'X30年']
    for col in target_cols:
        if col not in final_df.columns:
            final_df[col] = float('nan')
    
    final_df = final_df[['date'] + target_cols].sort_values('date')
    
    # 保存
    final_df['date'] = final_df['date'].dt.strftime('%Y-%m-%d')
    final_df.to_csv('cn_treasury_yields.csv', index=False, encoding='utf-8-sig')
    
    print(f'\n数据已保存!')
    print(f'日期范围: {final_df["date"].min()} 至 {final_df["date"].max()}')
    print(f'总交易日数: {len(final_df)}')
    print('\n最新数据:')
    print(final_df.iloc[-1].to_string())
else:
    print('未获取到数据')
