#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国国债收益率数据 - 修复版
==============================
修复数据获取逻辑，确保保留所有交易日数据

使用方法:
    python fetch_fixed.py [年月]
    python fetch_fixed.py all
"""

import pandas as pd
import tushare as ts
import time
import os
import sys
from datetime import datetime, timedelta

os.environ['PYTHONIOENCODING'] = 'utf-8'

CONFIG = {
    'data_file': 'cn_treasury_yields.csv',
    'ts_code': '1001.CB',
    'curve_type': '0',
    'page_size': 2000,
}

TERM_MAPPING = {
    0.08: 'X1月', 0.10: 'X2月', 0.17: 'X3月', 0.25: 'X5月',
    0.50: 'X6月', 0.75: 'X9月', 1.00: 'X1年', 2.00: 'X2年',
    3.00: 'X3年', 5.00: 'X5年', 7.00: 'X7年', 10.00: 'X10年',
    15.00: 'X15年', 20.00: 'X20年', 30.00: 'X30年', 40.00: 'X40年',
}

TARGET_COLS = ['X1年', 'X2年', 'X3年', 'X5年', 'X7年', 'X10年', 'X20年', 'X30年']


def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()


def init_tushare():
    token = os.environ.get('TUSHARE_TOKEN')
    if not token:
        log("错误: 未设置 TUSHARE_TOKEN")
        return None
    try:
        return ts.pro_api(token)
    except Exception as e:
        log(f"初始化失败: {e}")
        return None


def fetch_month_data(pro, year, month):
    """获取指定月份的所有原始数据"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    today = datetime.now()
    if end_date > today:
        end_date = today
    
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    
    log(f"获取 {year}年{month}月: {start_str} 至 {end_str}")
    
    all_data = []
    page = 1
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            df = pro.yc_cb(
                ts_code=CONFIG['ts_code'],
                curve_type=CONFIG['curve_type'],
                start_date=start_str,
                end_date=end_str,
                limit=CONFIG['page_size'],
                offset=(page-1) * CONFIG['page_size']
            )
            
            if df is None or len(df) == 0:
                break
            
            all_data.append(df)
            log(f"  第{page}页: {len(df)}条")
            
            if len(df) < CONFIG['page_size']:
                break
            
            page += 1
            retry_count = 0  # 重置重试计数
            time.sleep(35)  # 遵守频率限制
            
        except Exception as e:
            error_msg = str(e)
            if '频次' in error_msg:
                log(f"  频次限制，等待60秒...")
                time.sleep(60)
            else:
                log(f"  错误: {error_msg[:60]}")
                retry_count += 1
                time.sleep(10)
    
    if len(all_data) == 0:
        return None
    
    combined = pd.concat(all_data, ignore_index=True)
    log(f"  原始数据总计: {len(combined)}条")
    return combined


def process_data(raw_df):
    """处理原始数据，保留所有交易日"""
    if raw_df is None or len(raw_df) == 0:
        return None
    
    # 转换数据类型
    raw_df['date'] = pd.to_datetime(raw_df['trade_date'], format='%Y%m%d')
    raw_df['curve_term'] = pd.to_numeric(raw_df['curve_term'], errors='coerce')
    raw_df['yield'] = pd.to_numeric(raw_df['yield'], errors='coerce')
    
    # 按日期透视
    pivot_data = []
    for date, group in raw_df.groupby('date'):
        row = {'date': date}
        for _, r in group.iterrows():
            term = r['curve_term']
            yield_val = r['yield']
            if term in TERM_MAPPING and pd.notna(yield_val):
                col_name = TERM_MAPPING[term]
                row[col_name] = yield_val
        pivot_data.append(row)
    
    df_result = pd.DataFrame(pivot_data)
    
    # 确保所有目标列都存在
    for col in TARGET_COLS:
        if col not in df_result.columns:
            df_result[col] = float('nan')
    
    # 只保留目标列
    df_result = df_result[['date'] + TARGET_COLS]
    df_result = df_result.sort_values('date')
    
    log(f"  处理后: {len(df_result)}个交易日")
    
    # 显示样本
    if len(df_result) > 0:
        log(f"  样本: {df_result.iloc[0]['date'].strftime('%Y-%m-%d')}")
    
    return df_result


def save_data(new_df):
    """合并并保存数据"""
    if os.path.exists(CONFIG['data_file']):
        existing = pd.read_csv(CONFIG['data_file'])
        existing['date'] = pd.to_datetime(existing['date'])
        
        # 合并
        combined = pd.concat([existing, new_df], ignore_index=True)
        # 去重（保留最新的）
        combined = combined.drop_duplicates(subset=['date'], keep='last')
        combined = combined.sort_values('date')
    else:
        combined = new_df
    
    # 保存
    combined['date'] = combined['date'].dt.strftime('%Y-%m-%d')
    combined.to_csv(CONFIG['data_file'], index=False, encoding='utf-8-sig')
    
    return combined


def get_missing_months():
    """获取缺失的月份列表"""
    if not os.path.exists(CONFIG['data_file']):
        # 从2023-01到2026-03
        missing = []
        for year in range(2023, 2027):
            for month in range(1, 13):
                if year == 2026 and month > 3:
                    break
                missing.append((year, month))
        return missing
    
    df = pd.read_csv(CONFIG['data_file'])
    df['date'] = pd.to_datetime(df['date'])
    existing_months = set(df['date'].dt.strftime('%Y%m').unique())
    
    missing = []
    for year in range(2023, 2027):
        for month in range(1, 13):
            if year == 2026 and month > 3:
                break
            ym = f"{year}{month:02d}"
            if ym not in existing_months:
                missing.append((year, month))
    
    return missing


def main():
    print("="*60)
    print("中国国债收益率数据 - 修复版")
    print("="*60)
    
    if len(sys.argv) < 2:
        print("\n使用方法:")
        print("  python fetch_fixed.py [年月]  # 如 202301")
        print("  python fetch_fixed.py all     # 获取所有缺失月份")
        return
    
    arg = sys.argv[1]
    
    pro = init_tushare()
    if pro is None:
        return
    
    if arg.lower() == 'all':
        missing = get_missing_months()
        log(f"缺失 {len(missing)} 个月份")
        
        for year, month in missing:
            log(f"\n{'='*40}")
            raw_data = fetch_month_data(pro, year, month)
            
            if raw_data is not None:
                processed = process_data(raw_data)
                if processed is not None and len(processed) > 0:
                    combined = save_data(processed)
                    log(f"已保存，总计 {len(combined)} 个交易日")
            
            time.sleep(35)  # 月份间等待
    else:
        year = int(arg[:4])
        month = int(arg[4:6])
        
        raw_data = fetch_month_data(pro, year, month)
        
        if raw_data is not None:
            processed = process_data(raw_data)
            if processed is not None and len(processed) > 0:
                combined = save_data(processed)
                log(f"\n总计 {len(combined)} 个交易日")
                log(f"日期范围: {combined['date'].min()} 至 {combined['date'].max()}")
    
    log("\n" + "="*60)
    log("完成!")
    log("="*60)


if __name__ == "__main__":
    main()
