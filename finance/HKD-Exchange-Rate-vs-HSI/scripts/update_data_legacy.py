#!/usr/bin/env python3
"""
HKD-Exchange-Rate-vs-HSI 数据增量更新脚本 - 修复版
处理不同格式的CSV文件

【历史版本】使用东方财富API获取数据
- USD/HKD: 使用 secid='119.USDHKD' (可能受网络代理影响)
- HSI: 使用 secid='100.HSI'

【状态】已弃用，保留用于参考和切换
【替代方案】update_data.py (当前使用 mx-macro-data skill)
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import sys
import os
import traceback

def get_last_date(filepath):
    """获取CSV文件的最后日期"""
    try:
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        # 标准化列名（转为小写）
        df.columns = df.columns.str.lower().str.replace('\ufeff', '')
        return pd.to_datetime(df['date']).max()
    except FileNotFoundError:
        return None

def fetch_data(secid, start_date, end_date):
    """从东方财富API获取数据"""
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": "0",
        "beg": start_date,
        "end": end_date,
        "lmt": "10000"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if data.get('rc') == 0 and data.get('data'):
            return data['data'].get('klines', [])
    except Exception as e:
        print(f"请求失败: {e}")
    
    return []

def parse_klines(klines):
    """解析K线数据为DataFrame"""
    if not klines:
        return pd.DataFrame()
    
    records = []
    for line in klines:
        parts = line.split(',')
        records.append({
            'Date': parts[0],
            'Open': float(parts[1]),
            'Close': float(parts[2]),
            'High': float(parts[3]),
            'Low': float(parts[4]),
            'Volume': float(parts[5]),
            'Amount': float(parts[6]),
            'Amplitude': float(parts[7]),
            'Pct_Change': float(parts[8]),
            'Change': float(parts[9]),
            'Turnover': float(parts[10])
        })
    
    return pd.DataFrame(records)

def update_csv(filepath, secid, name):
    """更新单个CSV文件"""
    print(f"\n{'='*50}")
    print(f"更新: {name}")
    print(f"{'='*50}")
    
    # 获取现有数据最后日期
    last_date = get_last_date(filepath)
    
    if last_date is None:
        print(f"文件不存在: {filepath}")
        return False
    
    print(f"现有数据最后日期: {last_date.strftime('%Y-%m-%d')}")
    
    # 计算更新范围
    today = datetime.now()
    start_date = (last_date + timedelta(days=1)).strftime('%Y%m%d')
    end_date = today.strftime('%Y%m%d')
    
    if start_date > end_date:
        print("数据已是最新，无需更新")
        return True
    
    print(f"获取范围: {start_date} 至 {end_date}")
    
    # 获取新数据
    klines = fetch_data(secid, start_date, end_date)
    
    if not klines:
        print("无新数据")
        return True
    
    print(f"获取到 {len(klines)} 条新数据")
    
    # 读取现有数据
    df_existing = pd.read_csv(filepath, encoding='utf-8-sig')
    # 标准化列名
    df_existing.columns = df_existing.columns.str.lower().str.replace('\ufeff', '')
    
    # 获取新数据
    df_new = parse_klines(klines)
    # 标准化新数据的列名
    df_new.columns = df_new.columns.str.lower()
    
    # 确保列一致（只保留共同列）
    common_cols = list(set(df_existing.columns) & set(df_new.columns))
    print(f"共同列: {common_cols}")
    
    df_existing = df_existing[common_cols]
    df_new = df_new[common_cols]
    
    # 合并（去重）
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset=['date'], keep='last')
    df_combined = df_combined.sort_values('date').reset_index(drop=True)
    
    # 保存（保持原始大小写格式）
    df_combined.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    print(f"更新完成: {len(df_existing)} -> {len(df_combined)} 条")
    print(f"时间范围: {df_combined['date'].min()} 至 {df_combined['date'].max()}")
    
    return True

def main():
    try:
        print("="*60)
        print("HKD-Exchange-Rate-vs-HSI 数据增量更新")
        print(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # 配置路径
        data_dir = 'HKD-Exchange-Rate-vs-HSI/data'
        
        # 更新USD/HKD
        update_csv(os.path.join(data_dir, 'HKD_USD_Exchange_Rate.csv'), '119.USDHKD', 'USD/HKD 汇率')
        
        # 更新HSI
        update_csv(os.path.join(data_dir, 'Hang_Seng_Index.csv'), '100.HSI', '恒生指数')
        
        print("\n" + "="*60)
        print("所有更新完成!")
        print("="*60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
