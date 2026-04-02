#!/usr/bin/env python3
"""
HKD-Exchange-Rate-vs-HSI 数据更新脚本 - 使用 web_fetch 工具
通过 HTTP 请求获取 USD/HKD 汇率和恒生指数数据
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
import subprocess
import sys

# 配置路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')

def log(message):
    """打印带时间戳的日志"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def get_last_date(filepath):
    """获取CSV文件的最后日期"""
    try:
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        df.columns = df.columns.str.lower().str.replace('\ufeff', '')
        return pd.to_datetime(df['date']).max()
    except FileNotFoundError:
        return None

def fetch_hsi_data(start_date, end_date):
    """使用 web_fetch 获取恒生指数数据"""
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=100.HSI&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=0&beg={start_date}&end={end_date}&lmt=10000"
    
    try:
        # 使用 web_fetch 工具
        result = subprocess.run(
            ['openclaw', 'web-fetch', url],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            log(f"web_fetch 失败: {result.stderr}")
            return []
        
        # 解析 JSON 响应
        data = json.loads(result.stdout)
        
        if data.get('rc') == 0 and data.get('data') and data['data'].get('klines'):
            return data['data']['klines']
        else:
            log(f"无数据返回: {data}")
            return []
            
    except Exception as e:
        log(f"获取数据失败: {e}")
        return []

def parse_klines(klines):
    """解析K线数据为DataFrame"""
    if not klines:
        return pd.DataFrame()
    
    records = []
    for line in klines:
        parts = line.split(',')
        records.append({
            'date': parts[0],
            'open': float(parts[1]),
            'close': float(parts[2]),
            'high': float(parts[3]),
            'low': float(parts[4]),
            'volume': float(parts[5]),
        })
    
    return pd.DataFrame(records)

def update_hsi():
    """更新恒生指数数据"""
    log("="*60)
    log("更新恒生指数数据")
    log("="*60)
    
    filepath = os.path.join(DATA_DIR, 'Hang_Seng_Index.csv')
    
    # 获取现有数据最后日期
    last_date = get_last_date(filepath)
    
    if last_date is None:
        log(f"文件不存在: {filepath}")
        log("请使用初始下载脚本获取完整历史数据")
        return False
    
    log(f"现有数据最后日期: {last_date.strftime('%Y-%m-%d')}")
    
    # 计算更新范围
    today = datetime.now()
    start_date = (last_date + timedelta(days=1)).strftime('%Y%m%d')
    end_date = today.strftime('%Y%m%d')
    
    if start_date > end_date:
        log("数据已是最新，无需更新")
        return True
    
    log(f"获取范围: {start_date} 至 {end_date}")
    
    # 获取新数据
    klines = fetch_hsi_data(start_date, end_date)
    
    if not klines:
        log("无新数据")
        return True
    
    log(f"获取到 {len(klines)} 条新数据")
    
    # 读取现有数据
    df_existing = pd.read_csv(filepath, encoding='utf-8-sig')
    df_existing.columns = df_existing.columns.str.lower().str.replace('\ufeff', '')
    df_new = parse_klines(klines)
    
    # 合并（去重）
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset=['date'], keep='last')
    df_combined = df_combined.sort_values('date').reset_index(drop=True)
    
    # 保存
    df_combined.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    log(f"更新完成: {len(df_existing)} → {len(df_combined)} 条")
    log(f"时间范围: {df_combined['date'].min()} 至 {df_combined['date'].max()}")
    
    return True

def main():
    """主函数"""
    log("="*60)
    log("HKD-Exchange-Rate-vs-HSI 数据增量更新 (web_fetch 版本)")
    log(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("="*60)
    
    # 更新恒生指数
    update_hsi()
    
    log("\n" + "="*60)
    log("所有更新完成!")
    log("="*60)

if __name__ == '__main__':
    main()
