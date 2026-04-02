#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国国债收益率数据获取工具 (Tushare版)
======================================
使用 Tushare yc_cb 接口获取中债国债收益率曲线数据

核心参数:
    - ts_code: '1001.CB' (国债收益率曲线专用代码)
    - curve_type: '0'=到期收益率, '1'=即期收益率
    - trade_date: 特定交易日 (YYYYMMDD)

使用方法:
    python fetch_cn_treasury_tushare.py

功能:
    1. 使用 Tushare yc_cb 接口获取国债收益率数据
    2. 支持按日期循环获取历史数据
    3. 获取各期限数据: 1年、2年、3年、5年、7年、10年、20年、30年
    4. 保存为CSV格式，便于后续分析
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

# ============ 配置 ============
CONFIG = {
    # 数据文件路径
    'data_file': 'cn_treasury_yields.csv',
    
    # 工作目录
    'working_dir': os.path.dirname(os.path.abspath(__file__)),
    
    # 国债收益率曲线代码
    'ts_code': '1001.CB',
    
    # 曲线类型: '0'=到期收益率, '1'=即期收益率
    'curve_type': '0',
    
    # Tushare配置
    'api_rate_limit': 2,    # 每分钟最多2次调用
    'page_size': 2000,      # 单次最大获取条数
    
    # 最大重试次数
    'max_retries': 3,
}

# 期限映射 (curve_term 值 -> 列名)
TERM_MAPPING = {
    0.08: 'X1月',      # 1个月
    0.10: 'X2月',      # 2个月
    0.17: 'X3月',      # 3个月
    0.25: 'X5月',      # 5个月
    0.50: 'X6月',      # 6个月
    0.75: 'X9月',      # 9个月
    1.00: 'X1年',      # 1年
    2.00: 'X2年',      # 2年
    3.00: 'X3年',      # 3年
    5.00: 'X5年',      # 5年
    7.00: 'X7年',      # 7年
    10.00: 'X10年',    # 10年
    15.00: 'X15年',    # 15年
    20.00: 'X20年',    # 20年
    30.00: 'X30年',    # 30年
    40.00: 'X40年',    # 40年
}


def log(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()


def get_tushare_token():
    """获取Tushare Token"""
    token = os.environ.get('TUSHARE_TOKEN')
    
    if not token:
        config_paths = [
            os.path.join(CONFIG['working_dir'], 'tushare_config.txt'),
            os.path.expanduser('~/.tushare/token'),
        ]
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                token = line
                                break
                        if token:
                            log(f"从配置文件读取Token")
                            break
                except Exception as e:
                    pass
    
    return token


def init_tushare():
    """初始化Tushare接口"""
    token = get_tushare_token()
    
    if not token:
        log("错误: 未找到Tushare Token")
        log("请设置环境变量 TUSHARE_TOKEN")
        return None
    
    try:
        pro = ts.pro_api(token)
        log("Tushare接口初始化成功")
        return pro
    except Exception as e:
        log(f"Tushare接口初始化失败: {e}")
        return None


def fetch_single_day(pro, trade_date, max_retries=3):
    """
    获取单日的收益率曲线数据
    
    参数:
        pro: Tushare pro 接口
        trade_date: 交易日 (YYYYMMDD)
        max_retries: 最大重试次数
    
    返回:
        DataFrame 或 None
    """
    for attempt in range(max_retries):
        try:
            df = pro.yc_cb(
                ts_code=CONFIG['ts_code'],
                curve_type=CONFIG['curve_type'],
                trade_date=trade_date,
                limit=CONFIG['page_size']
            )
            
            if df is not None and len(df) > 0:
                return df
            else:
                return None
                
        except Exception as e:
            error_msg = str(e)
            if "频次" in error_msg or "积分" in error_msg:
                log(f"  {trade_date}: API限制，等待后重试...")
                time.sleep(35)
            else:
                log(f"  {trade_date}: 错误 - {error_msg[:50]}")
                time.sleep(5)
    
    return None


def fetch_date_range(pro, start_date, end_date):
    """
    获取日期范围内的收益率数据
    
    参数:
        pro: Tushare pro 接口
        start_date: 开始日期 (datetime)
        end_date: 结束日期 (datetime)
    
    返回:
        DataFrame 包含所有日期的数据
    """
    all_data = []
    current_date = end_date
    
    log(f"开始获取数据: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    
    while current_date >= start_date:
        trade_date = current_date.strftime('%Y%m%d')
        
        # 跳过周末
        if current_date.weekday() >= 5:  # 5=周六, 6=周日
            current_date -= timedelta(days=1)
            continue
        
        log(f"获取 {trade_date} 数据...")
        df = fetch_single_day(pro, trade_date)
        
        if df is not None and len(df) > 0:
            all_data.append(df)
            log(f"  成功: {len(df)} 条记录")
        else:
            log(f"  无数据")
        
        # 遵守API频率限制
        time.sleep(35)
        
        # 往前推一天
        current_date -= timedelta(days=1)
    
    if len(all_data) == 0:
        return None
    
    # 合并所有数据
    combined = pd.concat(all_data, ignore_index=True)
    log(f"总共获取 {len(combined)} 条记录，跨越 {len(all_data)} 个交易日")
    
    return combined


def process_yield_data(df):
    """
    处理收益率曲线数据
    
    原始数据格式:
    - trade_date: 交易日期
    - ts_code: 曲线代码
    - curve_name: 曲线名称
    - curve_type: 曲线类型
    - curve_term: 期限(年)
    - yield: 收益率
    
    转换为标准格式:
    - date: 日期
    - X1年, X2年, X3年, X5年, X7年, X10年, X20年, X30年: 各期限收益率
    """
    if df is None or len(df) == 0:
        return None
    
    log("处理数据...")
    log(f"原始数据形状: {df.shape}")
    
    # 转换日期格式
    df['date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
    
    # 确保 curve_term 和 yield 是数值类型
    df['curve_term'] = pd.to_numeric(df['curve_term'], errors='coerce')
    df['yield'] = pd.to_numeric(df['yield'], errors='coerce')
    
    # 透视表: 行=日期, 列=期限
    pivot_data = []
    
    for date, group in df.groupby('date'):
        row = {'date': date}
        for _, r in group.iterrows():
            term = r['curve_term']
            yield_val = r['yield']
            if term in TERM_MAPPING and pd.notna(yield_val):
                col_name = TERM_MAPPING[term]
                row[col_name] = yield_val
        pivot_data.append(row)
    
    if len(pivot_data) == 0:
        log("警告: 没有有效数据")
        return None
    
    # 创建DataFrame
    df_result = pd.DataFrame(pivot_data)
    
    # 确保所有目标列都存在
    target_cols = ['X1年', 'X2年', 'X3年', 'X5年', 'X7年', 'X10年', 'X20年', 'X30年']
    for col in target_cols:
        if col not in df_result.columns:
            df_result[col] = float('nan')
    
    # 重新排列列顺序
    df_result = df_result[['date'] + target_cols].copy()
    
    # 按日期排序
    df_result = df_result.sort_values('date')
    
    log(f"处理后数据形状: {df_result.shape}")
    if len(df_result) > 0:
        log(f"日期范围: {df_result['date'].min().strftime('%Y-%m-%d')} 至 {df_result['date'].max().strftime('%Y-%m-%d')}")
    
    return df_result


def merge_with_existing(new_df):
    """合并新数据与现有数据"""
    data_file = os.path.join(CONFIG['working_dir'], CONFIG['data_file'])
    
    if os.path.exists(data_file):
        try:
            existing_df = pd.read_csv(data_file)
            existing_df['date'] = pd.to_datetime(existing_df['date'])
            
            log(f"现有数据: {len(existing_df)} 条")
            log(f"新数据: {len(new_df)} 条")
            
            # 合并数据
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            # 按日期去重，保留最新数据
            combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
            
            # 按日期排序
            combined_df = combined_df.sort_values('date')
            
            log(f"合并后数据: {len(combined_df)} 条")
            
            return combined_df
        except Exception as e:
            log(f"合并数据失败: {e}")
            return new_df
    else:
        log("无现有数据，使用新数据")
        return new_df


def save_data(df):
    """保存数据到CSV文件"""
    data_file = os.path.join(CONFIG['working_dir'], CONFIG['data_file'])
    
    # 确保日期格式统一
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    
    # 保存数据
    df.to_csv(data_file, index=False, encoding='utf-8-sig')
    
    log(f"数据已保存: {data_file}")
    log(f"总行数: {len(df)}")
    log(f"日期范围: {df['date'].min()} 至 {df['date'].max()}")
    
    return data_file


def print_summary(df):
    """打印数据摘要"""
    print("\n" + "="*60)
    print("中国国债收益率数据摘要")
    print("="*60)
    
    print(f"\n数据时间范围: {df['date'].min()} 至 {df['date'].max()}")
    print(f"总记录数: {len(df)}")
    
    print("\n最新收益率 (%):")
    latest = df.iloc[-1]
    maturity_cols = ['X1年', 'X2年', 'X3年', 'X5年', 'X7年', 'X10年', 'X20年', 'X30年']
    for col in maturity_cols:
        if col in df.columns:
            value = latest[col]
            if pd.notna(value):
                print(f"  {col.replace('X', ''):>4}: {value:.2f}%")
    
    print("\n数据完整性:")
    for col in maturity_cols:
        if col in df.columns:
            non_null = df[col].notna().sum()
            total = len(df)
            pct = non_null / total * 100 if total > 0 else 0
            print(f"  {col.replace('X', ''):>4}: {non_null}/{total} ({pct:.1f}%)")
    
    print("\n" + "="*60)


def main():
    """主函数"""
    print("="*60)
    print("中国国债收益率数据获取 (Tushare)")
    print(f"曲线代码: {CONFIG['ts_code']}")
    print(f"曲线类型: {'到期收益率' if CONFIG['curve_type'] == '0' else '即期收益率'}")
    print("="*60)
    
    # 初始化Tushare
    pro = init_tushare()
    if pro is None:
        return
    
    # 确定日期范围
    end_date = datetime.now()
    
    # 如果存在现有数据，从最后日期开始
    data_file = os.path.join(CONFIG['working_dir'], CONFIG['data_file'])
    if os.path.exists(data_file):
        try:
            existing_df = pd.read_csv(data_file)
            if len(existing_df) > 0:
                last_date = pd.to_datetime(existing_df['date'].max())
                start_date = last_date + timedelta(days=1)
                log(f"现有数据最后日期: {last_date.strftime('%Y-%m-%d')}")
            else:
                start_date = end_date - timedelta(days=30)  # 默认获取最近30天
        except Exception as e:
            log(f"读取现有数据失败: {e}")
            start_date = end_date - timedelta(days=30)
    else:
        # 首次运行，获取最近3个月的数据
        start_date = end_date - timedelta(days=90)
        log("首次运行，获取最近3个月数据")
    
    # 确保开始日期不晚于结束日期
    if start_date > end_date:
        log("数据已是最新，无需更新")
        return
    
    log(f"获取数据范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    
    try:
        # 获取数据
        raw_data = fetch_date_range(pro, start_date, end_date)
        
        if raw_data is None or len(raw_data) == 0:
            log("未获取到数据")
            return
        
        # 处理数据
        processed_data = process_yield_data(raw_data)
        
        if processed_data is None or len(processed_data) == 0:
            log("数据处理失败")
            return
        
        # 合并现有数据
        combined_data = merge_with_existing(processed_data)
        
        # 保存数据
        save_data(combined_data)
        
        # 打印摘要
        print_summary(combined_data)
        
    except Exception as e:
        log(f"执行过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("获取完成!")
    print("="*60)


if __name__ == "__main__":
    main()
