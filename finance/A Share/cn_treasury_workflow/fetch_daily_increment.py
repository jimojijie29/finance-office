#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国国债收益率数据 - 每日增量获取
==================================
每天自动获取一个月的数据，逐步积累近3年历史数据

使用方法:
    python fetch_daily_increment.py

功能:
    1. 读取现有数据，确定最后日期
    2. 获取下一个月的数据
    3. 合并保存
    4. 记录获取日志
"""

import pandas as pd
import tushare as ts
import time
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 设置输出编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 配置
CONFIG = {
    'data_file': 'cn_treasury_yields.csv',
    'log_file': 'fetch_log.txt',
    'ts_code': '1001.CB',
    'curve_type': '0',
    'page_size': 2000,
}

# 期限映射
TERM_MAPPING = {
    0.08: 'X1月', 0.10: 'X2月', 0.17: 'X3月', 0.25: 'X5月',
    0.50: 'X6月', 0.75: 'X9月', 1.00: 'X1年', 2.00: 'X2年',
    3.00: 'X3年', 5.00: 'X5年', 7.00: 'X7年', 10.00: 'X10年',
    15.00: 'X15年', 20.00: 'X20年', 30.00: 'X30年', 40.00: 'X40年',
}


def log(message):
    """打印并记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    
    # 写入日志文件
    with open(CONFIG['log_file'], 'a', encoding='utf-8') as f:
        f.write(log_msg + '\n')
    sys.stdout.flush()


def init_tushare():
    """初始化Tushare"""
    token = os.environ.get('TUSHARE_TOKEN')
    if not token:
        log("错误: 未设置 TUSHARE_TOKEN 环境变量")
        return None
    
    try:
        pro = ts.pro_api(token)
        return pro
    except Exception as e:
        log(f"初始化失败: {e}")
        return None


def get_existing_data():
    """读取现有数据"""
    if not os.path.exists(CONFIG['data_file']):
        return None, None
    
    try:
        df = pd.read_csv(CONFIG['data_file'])
        df['date'] = pd.to_datetime(df['date'])
        last_date = df['date'].max()
        return df, last_date
    except Exception as e:
        log(f"读取现有数据失败: {e}")
        return None, None


def get_next_month_range(last_date):
    """
    获取目标月份日期范围
    
    策略:
    1. 如果数据不足3年，获取历史月份（从3年前开始逐步获取到今天）
    2. 如果数据已接近今天，获取下个月
    """
    today = datetime.now()
    
    if last_date is None:
        # 从3年前开始
        start_date = today - timedelta(days=3*365)
        end_date = start_date + timedelta(days=30)
        return start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d')
    
    # 检查最早日期
    # 获取数据文件中的最早日期
    try:
        df = pd.read_csv(CONFIG['data_file'])
        df['date'] = pd.to_datetime(df['date'])
        earliest_date = df['date'].min()
        latest_date = df['date'].max()
    except:
        earliest_date = last_date
        latest_date = last_date
    
    # 目标：获取从最早日期前一个月到今天的所有数据
    target_start = today - timedelta(days=3*365)  # 3年前
    
    if earliest_date > target_start:
        # 还有历史数据需要获取，从最早日期往前推
        if earliest_date.month == 1:
            target_month_start = earliest_date.replace(year=earliest_date.year - 1, month=12, day=1)
        else:
            target_month_start = earliest_date.replace(month=earliest_date.month - 1, day=1)
        
        if target_month_start.month == 12:
            target_month_end = target_month_start.replace(year=target_month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            target_month_end = target_month_start.replace(month=target_month_start.month + 1, day=1) - timedelta(days=1)
        
        return target_month_start.strftime('%Y%m%d'), target_month_end.strftime('%Y%m%d')
    else:
        # 历史数据已完整，获取最新月份
        if latest_date.month == 12:
            next_month_start = latest_date.replace(year=latest_date.year + 1, month=1, day=1)
        else:
            next_month_start = latest_date.replace(month=latest_date.month + 1, day=1)
        
        if next_month_start > today:
            log(f"数据已是最新，下一个月 {next_month_start.strftime('%Y-%m')} 还未到")
            return None, None
        
        if next_month_start.month == 12:
            next_month_end = next_month_start.replace(year=next_month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            next_month_end = next_month_start.replace(month=next_month_start.month + 1, day=1) - timedelta(days=1)
        
        if next_month_end > today:
            next_month_end = today
        
        return next_month_start.strftime('%Y%m%d'), next_month_end.strftime('%Y%m%d')


def fetch_month_data(pro, start_date, end_date):
    """获取一个月的数据"""
    all_data = []
    page = 1
    
    log(f"获取数据: {start_date} 至 {end_date}")
    
    while True:
        try:
            df = pro.yc_cb(
                ts_code=CONFIG['ts_code'],
                curve_type=CONFIG['curve_type'],
                start_date=start_date,
                end_date=end_date,
                limit=CONFIG['page_size'],
                offset=(page-1) * CONFIG['page_size']
            )
            
            if df is None or len(df) == 0:
                break
            
            all_data.append(df)
            log(f"  第 {page} 页: {len(df)} 条")
            
            if len(df) < CONFIG['page_size']:
                break
            
            page += 1
            time.sleep(35)  # 遵守频率限制
            
        except Exception as e:
            error_msg = str(e)
            log(f"  错误: {error_msg[:80]}")
            if '频次' in error_msg:
                time.sleep(60)
            else:
                time.sleep(10)
    
    if len(all_data) == 0:
        return None
    
    return pd.concat(all_data, ignore_index=True)


def process_data(raw_df):
    """处理原始数据"""
    if raw_df is None or len(raw_df) == 0:
        return None
    
    # 转换
    raw_df['date'] = pd.to_datetime(raw_df['trade_date'], format='%Y%m%d')
    raw_df['curve_term'] = pd.to_numeric(raw_df['curve_term'], errors='coerce')
    raw_df['yield'] = pd.to_numeric(raw_df['yield'], errors='coerce')
    
    # 透视
    pivot_data = []
    for date, group in raw_df.groupby('date'):
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
    
    return df_result[['date'] + target_cols].sort_values('date')


def save_data(df):
    """保存数据"""
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    df.to_csv(CONFIG['data_file'], index=False, encoding='utf-8-sig')


def main():
    """主函数"""
    log("="*60)
    log("中国国债收益率数据 - 每日增量获取")
    log("="*60)
    
    # 初始化
    pro = init_tushare()
    if pro is None:
        return
    
    # 读取现有数据
    existing_df, last_date = get_existing_data()
    
    if existing_df is not None:
        log(f"现有数据: {len(existing_df)} 条")
        log(f"最后日期: {last_date.strftime('%Y-%m-%d')}")
    else:
        log("无现有数据，从头开始获取")
    
    # 获取下一个月的日期范围
    start_date, end_date = get_next_month_range(last_date)
    
    if start_date is None:
        log("无需获取数据")
        return
    
    log(f"目标月份: {start_date[:6]}")
    
    # 获取数据
    raw_data = fetch_month_data(pro, start_date, end_date)
    
    if raw_data is None or len(raw_data) == 0:
        log("未获取到数据")
        return
    
    log(f"原始记录: {len(raw_data)} 条")
    
    # 处理数据
    processed = process_data(raw_data)
    
    if processed is None or len(processed) == 0:
        log("数据处理失败")
        return
    
    log(f"处理后: {len(processed)} 个交易日")
    
    # 合并数据
    if existing_df is not None:
        combined = pd.concat([existing_df, processed], ignore_index=True)
        combined = combined.drop_duplicates(subset=['date'], keep='last')
        combined = combined.sort_values('date')
    else:
        combined = processed
    
    # 保存
    save_data(combined)
    
    log(f"数据已保存: {CONFIG['data_file']}")
    log(f"总记录数: {len(combined)}")
    log(f"日期范围: {combined['date'].min()} 至 {combined['date'].max()}")
    
    # 显示最新数据
    log("\n最新数据:")
    latest = combined.iloc[-1]
    for col in ['X1年', 'X2年', 'X3年', 'X5年', 'X7年', 'X10年', 'X20年', 'X30年']:
        if col in combined.columns and pd.notna(latest[col]):
            log(f"  {col.replace('X', '')}: {latest[col]:.2f}%")
    
    log("="*60)
    log("完成!")
    log("="*60)


if __name__ == "__main__":
    main()
