#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国国债收益率数据 - 手动获取指定月份
======================================
手动指定获取某个月份的数据

使用方法:
    python fetch_manual.py [年月]
    
    示例:
    python fetch_manual.py 202301    # 获取2023年1月
    python fetch_manual.py 202305    # 获取2023年5月
    python fetch_manual.py all       # 获取所有缺失月份（从2023-01到2026-03）
"""

import pandas as pd
import tushare as ts
import time
import os
import sys
from datetime import datetime, timedelta

# 设置输出编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 配置
CONFIG = {
    'data_file': 'cn_treasury_yields.csv',
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
    """打印日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")
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


def fetch_month_data(pro, year, month):
    """获取指定月份的数据"""
    # 计算月份的起止日期
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # 不能超过今天
    today = datetime.now()
    if end_date > today:
        end_date = today
    
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    
    log(f"获取 {year}年{month}月 数据: {start_str} 至 {end_str}")
    
    all_data = []
    page = 1
    
    while True:
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
    
    raw_df['date'] = pd.to_datetime(raw_df['trade_date'], format='%Y%m%d')
    raw_df['curve_term'] = pd.to_numeric(raw_df['curve_term'], errors='coerce')
    raw_df['yield'] = pd.to_numeric(raw_df['yield'], errors='coerce')
    
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
    
    target_cols = ['X1年', 'X2年', 'X3年', 'X5年', 'X7年', 'X10年', 'X20年', 'X30年']
    for col in target_cols:
        if col not in df_result.columns:
            df_result[col] = float('nan')
    
    return df_result[['date'] + target_cols].sort_values('date')


def get_existing_months():
    """获取已有数据的月份列表"""
    if not os.path.exists(CONFIG['data_file']):
        return set()
    
    try:
        df = pd.read_csv(CONFIG['data_file'])
        df['date'] = pd.to_datetime(df['date'])
        months = set(df['date'].dt.strftime('%Y%m').unique())
        return months
    except:
        return set()


def get_missing_months():
    """获取缺失的月份列表"""
    existing = get_existing_months()
    
    # 从2023-01到2026-03
    missing = []
    for year in range(2023, 2027):
        for month in range(1, 13):
            if year == 2026 and month > 3:
                break
            ym = f"{year}{month:02d}"
            if ym not in existing:
                missing.append((year, month))
    
    return missing


def main():
    """主函数"""
    print("="*60)
    print("中国国债收益率数据 - 手动获取")
    print("="*60)
    
    # 解析参数
    if len(sys.argv) < 2:
        print("\n使用方法:")
        print("  python fetch_manual.py [年月]")
        print("  python fetch_manual.py all")
        print("\n示例:")
        print("  python fetch_manual.py 202301")
        print("  python fetch_manual.py all")
        return
    
    arg = sys.argv[1]
    
    # 初始化
    pro = init_tushare()
    if pro is None:
        return
    
    if arg.lower() == 'all':
        # 获取所有缺失月份
        missing = get_missing_months()
        log(f"发现 {len(missing)} 个缺失月份")
        
        for year, month in missing:
            log(f"\n{'='*60}")
            log(f"获取 {year}年{month}月")
            
            raw_data = fetch_month_data(pro, year, month)
            
            if raw_data is not None and len(raw_data) > 0:
                processed = process_data(raw_data)
                
                if processed is not None and len(processed) > 0:
                    # 读取现有数据
                    if os.path.exists(CONFIG['data_file']):
                        existing = pd.read_csv(CONFIG['data_file'])
                        existing['date'] = pd.to_datetime(existing['date'])
                    else:
                        existing = None
                    
                    # 合并
                    if existing is not None:
                        combined = pd.concat([existing, processed], ignore_index=True)
                        combined = combined.drop_duplicates(subset=['date'], keep='last')
                        combined = combined.sort_values('date')
                    else:
                        combined = processed
                    
                    # 保存
                    combined['date'] = combined['date'].dt.strftime('%Y-%m-%d')
                    combined.to_csv(CONFIG['data_file'], index=False, encoding='utf-8-sig')
                    
                    log(f"已保存 {len(processed)} 个交易日")
                    log(f"总计 {len(combined)} 个交易日")
            else:
                log("无数据")
            
            time.sleep(35)  # 批次间等待
    else:
        # 获取指定月份
        year = int(arg[:4])
        month = int(arg[4:6])
        
        log(f"获取 {year}年{month}月 数据")
        
        raw_data = fetch_month_data(pro, year, month)
        
        if raw_data is not None and len(raw_data) > 0:
            processed = process_data(raw_data)
            
            if processed is not None and len(processed) > 0:
                # 读取现有数据
                if os.path.exists(CONFIG['data_file']):
                    existing = pd.read_csv(CONFIG['data_file'])
                    existing['date'] = pd.to_datetime(existing['date'])
                else:
                    existing = None
                
                # 合并
                if existing is not None:
                    combined = pd.concat([existing, processed], ignore_index=True)
                    combined = combined.drop_duplicates(subset=['date'], keep='last')
                    combined = combined.sort_values('date')
                else:
                    combined = processed
                
                # 保存
                combined['date'] = combined['date'].dt.strftime('%Y-%m-%d')
                combined.to_csv(CONFIG['data_file'], index=False, encoding='utf-8-sig')
                
                log(f"\n已保存 {len(processed)} 个交易日")
                log(f"总计 {len(combined)} 个交易日")
                log(f"日期范围: {combined['date'].min()} 至 {combined['date'].max()}")
        else:
            log("无数据")
    
    log("\n" + "="*60)
    log("完成!")
    log("="*60)


if __name__ == "__main__":
    main()
