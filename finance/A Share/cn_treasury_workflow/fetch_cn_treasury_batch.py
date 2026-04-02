#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国国债收益率数据获取工具 - 批量版
====================================
使用 Tushare yc_cb 接口批量获取中债国债收益率曲线数据

特点:
    - 使用 start_date/end_date 批量获取，无需按天循环
    - 支持分页获取大量数据
    - 自动处理数据透视转换

使用方法:
    python fetch_cn_treasury_batch.py [年份]
    
    示例:
    python fetch_cn_treasury_batch.py        # 获取近3年
    python fetch_cn_treasury_batch.py 2023   # 获取2023年全年
"""

import pandas as pd
import tushare as ts
import time
import os
import sys
from datetime import datetime, timedelta

# 设置输出编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# ============ 配置 ============
CONFIG = {
    'ts_code': '1001.CB',      # 国债收益率曲线代码
    'curve_type': '0',          # 到期收益率
    'page_size': 2000,          # 单次最大条数
    'data_file': 'cn_treasury_yields.csv',
}

# 期限映射 (curve_term -> 列名)
TERM_MAPPING = {
    0.08: 'X1月', 0.10: 'X2月', 0.17: 'X3月', 0.25: 'X5月',
    0.50: 'X6月', 0.75: 'X9月', 1.00: 'X1年', 2.00: 'X2年',
    3.00: 'X3年', 5.00: 'X5年', 7.00: 'X7年', 10.00: 'X10年',
    15.00: 'X15年', 20.00: 'X20年', 30.00: 'X30年', 40.00: 'X40年',
}


def log(message):
    """打印日志"""
    timestamp = datetime.now().strftime('%H:%M:%S')
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
        log("Tushare初始化成功")
        return pro
    except Exception as e:
        log(f"初始化失败: {e}")
        return None


def fetch_data_batch(pro, start_date, end_date):
    """
    批量获取数据
    
    参数:
        pro: Tushare pro接口
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
    
    返回:
        DataFrame 或 None
    """
    all_data = []
    page = 1
    
    log(f"开始获取数据: {start_date} 至 {end_date}")
    
    while True:
        try:
            log(f"获取第 {page} 页...")
            
            df = pro.yc_cb(
                ts_code=CONFIG['ts_code'],
                curve_type=CONFIG['curve_type'],
                start_date=start_date,
                end_date=end_date,
                limit=CONFIG['page_size'],
                offset=(page-1) * CONFIG['page_size']
            )
            
            if df is None or len(df) == 0:
                log(f"第 {page} 页无数据")
                break
            
            all_data.append(df)
            log(f"第 {page} 页: {len(df)} 条")
            
            # 如果不足page_size，说明已获取全部
            if len(df) < CONFIG['page_size']:
                log("数据获取完成")
                break
            
            page += 1
            
            # 遵守频率限制 (每分钟2次)
            log("等待35秒...")
            time.sleep(35)
            
        except Exception as e:
            error_msg = str(e)
            log(f"错误: {error_msg[:80]}")
            
            if '频次' in error_msg or '积分' in error_msg:
                log("API限制，等待60秒...")
                time.sleep(60)
            else:
                time.sleep(10)
            
            # 连续错误3次则退出
            if page > 3 and len(all_data) == 0:
                log("多次失败，退出")
                break
    
    if len(all_data) == 0:
        return None
    
    combined = pd.concat(all_data, ignore_index=True)
    log(f"总共获取 {len(combined)} 条记录")
    return combined


def process_data(df):
    """处理原始数据"""
    if df is None or len(df) == 0:
        return None
    
    log("处理数据...")
    
    # 转换日期
    df['date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
    
    # 转换数值
    df['curve_term'] = pd.to_numeric(df['curve_term'], errors='coerce')
    df['yield'] = pd.to_numeric(df['yield'], errors='coerce')
    
    # 透视转换
    pivot_data = []
    for date, group in df.groupby('date'):
        row = {'date': date}
        for _, r in group.iterrows():
            term = r['curve_term']
            yield_val = r['yield']
            if term in TERM_MAPPING and pd.notna(yield_val):
                row[TERM_MAPPING[term]] = yield_val
        pivot_data.append(row)
    
    df_result = pd.DataFrame(pivot_data)
    
    # 确保所有目标列存在
    target_cols = ['X1年', 'X2年', 'X3年', 'X5年', 'X7年', 'X10年', 'X20年', 'X30年']
    for col in target_cols:
        if col not in df_result.columns:
            df_result[col] = float('nan')
    
    df_result = df_result[['date'] + target_cols].sort_values('date')
    
    log(f"处理后: {len(df_result)} 个交易日")
    return df_result


def save_data(df):
    """保存数据"""
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    df.to_csv(CONFIG['data_file'], index=False, encoding='utf-8-sig')
    log(f"数据已保存: {CONFIG['data_file']}")
    log(f"日期范围: {df['date'].min()} 至 {df['date'].max()}")


def print_summary(df):
    """打印摘要"""
    print("\n" + "="*60)
    print("数据摘要")
    print("="*60)
    print(f"交易日数: {len(df)}")
    print(f"日期范围: {df['date'].min()} 至 {df['date'].max()}")
    
    print("\n最新收益率 (%):")
    latest = df.iloc[-1]
    for col in ['X1年', 'X2年', 'X3年', 'X5年', 'X7年', 'X10年', 'X20年', 'X30年']:
        if col in df.columns and pd.notna(latest[col]):
            print(f"  {col.replace('X', ''):>4}: {latest[col]:.2f}%")
    
    print("="*60)


def main():
    """主函数"""
    print("="*60)
    print("中国国债收益率数据获取 (批量版)")
    print("="*60)
    
    # 解析参数
    if len(sys.argv) > 1:
        year = sys.argv[1]
        start_date = f"{year}0101"
        end_date = f"{year}1231"
    else:
        # 默认获取近3年
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3*365)
        start_date = start_date.strftime('%Y%m%d')
        end_date = end_date.strftime('%Y%m%d')
    
    log(f"数据范围: {start_date} 至 {end_date}")
    
    # 初始化
    pro = init_tushare()
    if pro is None:
        return
    
    # 获取数据
    raw_data = fetch_data_batch(pro, start_date, end_date)
    if raw_data is None:
        log("未获取到数据")
        return
    
    # 处理数据
    processed = process_data(raw_data)
    if processed is None:
        log("数据处理失败")
        return
    
    # 保存
    save_data(processed)
    
    # 打印摘要
    print_summary(processed)
    
    log("完成!")


if __name__ == "__main__":
    main()
