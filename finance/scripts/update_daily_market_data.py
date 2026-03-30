#!/usr/bin/env python3
"""
A股两市行情数据每日更新脚本
用法: python update_daily_market_data.py [--date YYYYMMDD]

功能:
1. 获取上证指数和深证成指日线数据
2. 获取融资融券交易汇总数据
3. 生成综合市场数据文件
4. 自动合并新旧数据，去重并排序
5. 生成Plotly交互式可视化图表
"""

import requests
import pandas as pd
import os
import argparse
import sys
from datetime import datetime, timedelta

# 添加任务日志支持
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
try:
    from task_logger import log_task_status
    TASK_LOGGER_AVAILABLE = True
except ImportError:
    TASK_LOGGER_AVAILABLE = False
    print("Warning: task_logger not available")

# Tushare API Token
token = os.getenv('TUSHARE_TOKEN') or '242e48c14fbf0c72ffd3'

# 数据文件路径
DATA_DIR = 'finance/tushare'
SH_INDEX_FILE = os.path.join(DATA_DIR, 'index_sh_000001_daily.csv')
SZ_INDEX_FILE = os.path.join(DATA_DIR, 'index_sz_399001_daily.csv')
MARGIN_FILE = os.path.join(DATA_DIR, 'margin_trading_sse_szse.csv')
COMBINED_FILE = os.path.join(DATA_DIR, 'market_combined_data.csv')
COMBINED_TEMP_FILE = os.path.join(DATA_DIR, 'market_combined_data_temp.csv')

def fetch_index_daily(ts_code, start_date, end_date):
    """获取指数日线数据"""
    url = "https://api.tushare.pro"
    headers = {'Content-Type': 'application/json'}
    
    data = {
        'api_name': 'index_daily',
        'token': token,
        'params': {
            'ts_code': ts_code,
            'start_date': start_date,
            'end_date': end_date
        },
        'fields': ''
    }
    
    response = requests.post(url, json=data, headers=headers, timeout=60)
    result = response.json()
    
    if result.get('code') == 0 and result.get('data'):
        fields = result['data']['fields']
        items = result['data']['items']
        df = pd.DataFrame(items, columns=fields)
        return df
    else:
        print(f"  Error: {result.get('msg', 'Unknown error')}")
        return pd.DataFrame()

def fetch_margin_data(exchange, start_date, end_date):
    """获取融资融券数据"""
    url = "https://api.tushare.pro"
    headers = {'Content-Type': 'application/json'}
    
    data = {
        'api_name': 'margin',
        'token': token,
        'params': {
            'exchange': exchange,
            'start_date': start_date,
            'end_date': end_date
        },
        'fields': ''
    }
    
    response = requests.post(url, json=data, headers=headers, timeout=60)
    result = response.json()
    
    if result.get('code') == 0 and result.get('data'):
        fields = result['data']['fields']
        items = result['data']['items']
        df = pd.DataFrame(items, columns=fields)
        return df
    else:
        print(f"  Error: {result.get('msg', 'Unknown error')}")
        return pd.DataFrame()

def update_index_data(file_path, ts_code, start_date, end_date):
    """更新指数数据"""
    print(f"\nUpdating {ts_code}...")
    
    # 读取现有数据
    if os.path.exists(file_path):
        df_existing = pd.read_csv(file_path)
        df_existing['trade_date'] = df_existing['trade_date'].astype(str)
        print(f"  Existing: {len(df_existing)} records")
    else:
        df_existing = pd.DataFrame()
        print(f"  No existing file, creating new...")
    
    # 获取新数据
    df_new = fetch_index_daily(ts_code, start_date, end_date)
    
    if len(df_new) > 0:
        df_new['trade_date'] = df_new['trade_date'].astype(str)
        print(f"  New data: {len(df_new)} records")
        
        # 合并数据
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=['trade_date'])
        df_combined = df_combined.sort_values('trade_date', ascending=False, key=lambda x: x.astype(str))
        
        # 保存
        os.makedirs(DATA_DIR, exist_ok=True)
        df_combined.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"  Saved: {len(df_combined)} records")
        print(f"  Date range: {df_combined['trade_date'].min()} to {df_combined['trade_date'].max()}")
        return df_combined
    else:
        print(f"  No new data")
        return df_existing

def update_margin_data(start_date, end_date):
    """更新融资融券数据"""
    print(f"\nUpdating margin trading data...")
    
    # 读取现有数据
    if os.path.exists(MARGIN_FILE):
        df_existing = pd.read_csv(MARGIN_FILE)
        df_existing['trade_date'] = df_existing['trade_date'].astype(str)
        print(f"  Existing: {len(df_existing)} records")
    else:
        df_existing = pd.DataFrame()
        print(f"  No existing file, creating new...")
    
    # 获取沪市和深市数据
    df_sse = fetch_margin_data('SSE', start_date, end_date)
    df_szse = fetch_margin_data('SZSE', start_date, end_date)
    
    df_new = pd.concat([df_sse, df_szse], ignore_index=True)
    
    if len(df_new) > 0:
        df_new['trade_date'] = df_new['trade_date'].astype(str)
        # 只保留SSE和SZSE数据
        df_new = df_new[df_new['exchange_id'].isin(['SSE', 'SZSE'])].copy()
        print(f"  New data: {len(df_new)} records")
        
        # 合并数据
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=['trade_date', 'exchange_id'])
        df_combined = df_combined.sort_values(['trade_date', 'exchange_id'], ascending=[False, True])
        
        # 保存
        os.makedirs(DATA_DIR, exist_ok=True)
        df_combined.to_csv(MARGIN_FILE, index=False, encoding='utf-8-sig')
        print(f"  Saved: {len(df_combined)} records")
        if len(df_combined) > 0:
            print(f"  Date range: {df_combined['trade_date'].min()} to {df_combined['trade_date'].max()}")
        return df_combined
    else:
        print(f"  No new data")
        return df_existing

def generate_combined_data():
    """生成综合市场数据"""
    print(f"\nGenerating combined market data...")
    
    # 读取数据
    df_sh = pd.read_csv(SH_INDEX_FILE)
    df_sz = pd.read_csv(SZ_INDEX_FILE)
    df_margin = pd.read_csv(MARGIN_FILE)
    
    # 确保日期列为字符串
    df_sh['trade_date'] = df_sh['trade_date'].astype(str)
    df_sz['trade_date'] = df_sz['trade_date'].astype(str)
    df_margin['trade_date'] = df_margin['trade_date'].astype(str)
    
    # 合并指数数据
    df_sh_sel = df_sh[['trade_date', 'close', 'amount']].copy()
    df_sh_sel.columns = ['trade_date', 'sh_close', 'sh_amount']
    
    df_sz_sel = df_sz[['trade_date', 'close', 'amount']].copy()
    df_sz_sel.columns = ['trade_date', 'sz_close', 'sz_amount']
    
    df_index = pd.merge(df_sh_sel, df_sz_sel, on='trade_date', how='outer')
    df_index['avg_close'] = (df_index['sh_close'] + df_index['sz_close']) / 2
    df_index['total_turnover'] = (df_index['sh_amount'].fillna(0) + df_index['sz_amount'].fillna(0)) / 100000
    
    # 计算融资余额
    margin_grouped = df_margin.groupby('trade_date').agg({
        'rzye': 'sum',
        'rqye': 'sum',
        'rzrqye': 'sum'
    }).reset_index()
    margin_grouped.columns = ['trade_date', 'margin_balance', 'short_balance', 'total_margin_balance']
    
    # 转换为亿元
    margin_grouped['margin_balance'] = margin_grouped['margin_balance'] / 100000000
    margin_grouped['short_balance'] = margin_grouped['short_balance'] / 100000000
    margin_grouped['total_margin_balance'] = margin_grouped['total_margin_balance'] / 100000000
    
    # 合并所有数据
    df_combined = pd.merge(df_index, margin_grouped, on='trade_date', how='outer')
    df_combined = df_combined.sort_values('trade_date', ascending=False, key=lambda x: x.astype(str))
    
    # 选择需要的列
    df_result = df_combined[['trade_date', 'sh_close', 'sz_close', 'avg_close',
                             'total_turnover', 'margin_balance', 'short_balance', 'total_margin_balance']].copy()
    
    # 保存到临时文件，然后重命名
    df_result.to_csv(COMBINED_TEMP_FILE, index=False, encoding='utf-8-sig')
    if os.path.exists(COMBINED_FILE):
        os.remove(COMBINED_FILE)
    os.rename(COMBINED_TEMP_FILE, COMBINED_FILE)
    print(f"  Saved: {len(df_result)} records")
    print(f"  Date range: {df_result['trade_date'].min()} to {df_result['trade_date'].max()}")
    
    return df_result

def main():
    # 记录任务开始
    if TASK_LOGGER_AVAILABLE:
        log_task_status(
            task_id="a-stock-market-update",
            name="A股两市行情数据每日更新",
            schedule="09:30",
            status="running"
        )
    
    parser = argparse.ArgumentParser(description='Update A-share market data daily')
    parser.add_argument('--date', type=str, help='Target date (YYYYMMDD), default is today')
    args = parser.parse_args()
    
    try:
        # 确定日期范围
        if args.date:
            end_date = args.date
            start_date = args.date
        else:
            today = datetime.now()
            end_date = today.strftime('%Y%m%d')
            # 获取最近7天的数据（以防遗漏）
            start_date = (today - timedelta(days=7)).strftime('%Y%m%d')
        
        print("=" * 60)
        print("A-Share Market Data Daily Update")
        print("=" * 60)
        print(f"Date range: {start_date} to {end_date}")
        print(f"Data directory: {DATA_DIR}")
        
        # 更新指数数据
        df_sh = update_index_data(SH_INDEX_FILE, '000001.SH', start_date, end_date)
        df_sz = update_index_data(SZ_INDEX_FILE, '399001.SZ', start_date, end_date)
        
        # 更新融资融券数据
        df_margin = update_margin_data(start_date, end_date)
        
        # 生成综合数据
        df_combined = generate_combined_data()
        
        # 显示最新数据
        print("\n" + "=" * 60)
        print("Latest Data Summary")
        print("=" * 60)
        
        latest = df_combined.iloc[0]
        print(f"Date: {latest['trade_date']}")
        print(f"  Shanghai Close: {latest['sh_close']:.2f}")
        print(f"  Shenzhen Close: {latest['sz_close']:.2f}")
        print(f"  Average Close: {latest['avg_close']:.2f}")
        print(f"  Total Turnover: {latest['total_turnover']:.2f} billion CNY")
        print(f"  Margin Balance: {latest['margin_balance']:.2f} billion CNY")
        print(f"  Short Balance: {latest['short_balance']:.2f} billion CNY")
        print(f"  Total Margin Balance: {latest['total_margin_balance']:.2f} billion CNY")
        
        # 生成可视化图表
        print("\n" + "=" * 60)
        print("Generating Visualization Charts")
        print("=" * 60)
        import subprocess
        
        r_script_path = os.path.join(os.path.dirname(__file__), 'visualize_market_data_plotly_dual.R')
        try:
            result = subprocess.run(
                ['Rscript', r_script_path],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            if result.stderr:
                print("R script warnings:", result.stderr)
        except subprocess.CalledProcessError as e:
            print(f"Error running R visualization script: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}
            raise  # 重新抛出异常以便记录失败状态
        except FileNotFoundError:
            print("Warning: Rscript not found. Please ensure R is installed and in PATH.")
        
        print("\n" + "=" * 60)
        print("Update Complete!")
        print("=" * 60)
        
        # 记录任务成功
        if TASK_LOGGER_AVAILABLE:
            log_task_status(
                task_id="a-stock-market-update",
                status="success",
                output_file="finance/tushare/market_combined_data.csv"
            )
        
    except Exception as e:
        # 记录任务失败
        if TASK_LOGGER_AVAILABLE:
            log_task_status(
                task_id="a-stock-market-update",
                status="failed",
                error=str(e)
            )
        print(f"\nError: {e}")
        raise

if __name__ == '__main__':
    main()
