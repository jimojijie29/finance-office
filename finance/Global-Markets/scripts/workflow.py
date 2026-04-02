#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Global-Markets 外盘数据获取工作流

功能:
    1. 获取美国三大指数数据 (标普500、道琼斯、纳斯达克)
    2. 获取外盘黄金/白银数据 (XAU、XAG)
    3. 保存为CSV格式
    4. 生成数据摘要

使用方法:
    python workflow.py
"""

import akshare as ak
import pandas as pd
from datetime import datetime
import os

# 配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')

# 数据配置
CONFIG = {
    'indices': {
        'SP500': {'name': 'S&P 500', 'symbol': '.INX', 'file': 'SP500_History.csv'},
        'DJI': {'name': 'Dow Jones', 'symbol': '.DJI', 'file': 'DJI_History.csv'},
        'NASDAQ': {'name': 'NASDAQ', 'symbol': '.IXIC', 'file': 'NASDAQ_History.csv'}
    },
    'commodities': {
        'XAU': {'name': 'Gold', 'symbol': 'XAU', 'file': 'XAU_Gold_History.csv'},
        'XAG': {'name': 'Silver', 'symbol': 'XAG', 'file': 'XAG_Silver_History.csv'}
    }
}


def log(msg):
    """打印日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}")


def fetch_index_data(symbol, name):
    """获取美股指数数据"""
    log(f"获取 {name} ({symbol})...")
    try:
        df = ak.index_us_stock_sina(symbol=symbol)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df[['open', 'high', 'low', 'close', 'volume']]
        log(f"  [OK] {len(df)} 条记录 | 最新: {df['close'].iloc[-1]:.2f}")
        return df
    except Exception as e:
        log(f"  [ERROR] {e}")
        return None


def fetch_commodity_data(symbol, name):
    """获取商品数据"""
    log(f"获取 {name} ({symbol})...")
    try:
        df = ak.futures_foreign_hist(symbol=symbol)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['volume'] = pd.to_numeric(df.get('volume', 0), errors='coerce')
        
        df = df[['open', 'high', 'low', 'close', 'volume']]
        log(f"  [OK] {len(df)} 条记录 | 最新: {df['close'].iloc[-1]:.2f}")
        return df
    except Exception as e:
        log(f"  [ERROR] {e}")
        return None


def save_to_csv(df, filename):
    """保存为CSV"""
    filepath = os.path.join(DATA_DIR, filename)
    try:
        df.to_csv(filepath, encoding='utf-8-sig')
        log(f"  [OK] 已保存: {filename}")
        return True
    except Exception as e:
        log(f"  [ERROR] 保存失败: {e}")
        return False


def generate_summary():
    """生成数据摘要"""
    summary = []
    
    # 指数摘要
    for key, info in CONFIG['indices'].items():
        filepath = os.path.join(DATA_DIR, info['file'])
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            summary.append({
                'Type': 'Index',
                'Name': info['name'],
                'Symbol': info['symbol'],
                'Records': len(df),
                'Start': df['date'].iloc[0],
                'End': df['date'].iloc[-1],
                'Latest': df['close'].iloc[-1]
            })
    
    # 商品摘要
    for key, info in CONFIG['commodities'].items():
        filepath = os.path.join(DATA_DIR, info['file'])
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            summary.append({
                'Type': 'Commodity',
                'Name': info['name'],
                'Symbol': info['symbol'],
                'Records': len(df),
                'Start': df['date'].iloc[0],
                'End': df['date'].iloc[-1],
                'Latest': df['close'].iloc[-1]
            })
    
    summary_df = pd.DataFrame(summary)
    summary_file = os.path.join(DATA_DIR, 'DATA_SUMMARY.csv')
    summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
    log(f"[OK] 数据摘要已保存: DATA_SUMMARY.csv")
    return summary_df


def main():
    """主函数"""
    log("="*60)
    log("Global-Markets 数据获取工作流")
    log("="*60)
    
    # 获取美股指数
    log("")
    log("【美股指数】")
    for key, info in CONFIG['indices'].items():
        df = fetch_index_data(info['symbol'], info['name'])
        if df is not None:
            save_to_csv(df, info['file'])
    
    # 获取商品数据
    log("")
    log("【黄金/白银】")
    for key, info in CONFIG['commodities'].items():
        df = fetch_commodity_data(info['symbol'], info['name'])
        if df is not None:
            save_to_csv(df, info['file'])
    
    # 生成摘要
    log("")
    log("【生成数据摘要】")
    summary = generate_summary()
    
    log("")
    log("="*60)
    log("工作流完成")
    log("="*60)
    
    # 打印摘要
    print("\n数据摘要:")
    print(summary.to_string(index=False))


if __name__ == '__main__':
    main()
