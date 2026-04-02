#!/usr/bin/env python3
"""
整合所有期限的中国国债收益率数据
==========================
查询并整合所有期限（1年、2年、3年、5年、7年、10年、20年、30年）的国债数据
"""

import pandas as pd
import sys
import os
import asyncio
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# 配置
MX_MACRO_SKILL_PATH = r'D:\OpenClawData\.openclaw\workspace\skills\mx-macro-data'
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = 'cn_treasury_yields.csv'

# 要查询的期限
MATURITIES = ['1年', '2年', '3年', '5年', '7年', '10年', '20年', '30年']


def log(message):
    """打印带时间戳的日志"""
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
    except UnicodeEncodeError:
        safe_message = message.encode('ascii', 'ignore').decode('ascii')
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {safe_message}")


async def fetch_single_maturity_async(maturity):
    """获取单个期限的数据"""
    log(f"Querying {maturity} maturity...")
    
    query = f"中国{maturity}期国债收益率日度数据，最近3年"
    
    try:
        if MX_MACRO_SKILL_PATH not in sys.path:
            sys.path.insert(0, MX_MACRO_SKILL_PATH)
        
        from scripts.get_data import query_mx_macro_data
        
        temp_dir = os.path.join(WORKING_DIR, 'temp_integrate', maturity)
        os.makedirs(temp_dir, exist_ok=True)
        
        os.environ['MX_MACRO_DATA_OUTPUT_DIR'] = temp_dir
        
        result = await query_mx_macro_data(query, output_dir=Path(temp_dir))
        
        if 'error' in result:
            log(f"  {maturity} query error: {result['error']}")
            return None
        
        if 'csv_paths' in result and len(result['csv_paths']) > 0:
            csv_file = result['csv_paths'][0]
            log(f"  [OK] {maturity} data retrieved")
            return {'maturity': maturity, 'file': csv_file}
        else:
            log(f"  [X] {maturity} no data")
            return None
            
    except Exception as e:
        log(f"  {maturity} query failed: {e}")
        return None


def process_maturity_data(file_info):
    """处理单个期限的数据文件"""
    csv_file = file_info['file']
    maturity = file_info['maturity']
    
    if not csv_file or not os.path.exists(csv_file):
        return None
    
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
        
        # 找出日期列
        date_cols = [col for col in df.columns if re.match(r'\d{4}-\d{2}(-\d{2})?', str(col))]
        
        if len(date_cols) == 0:
            return None
        
        # 转换为长格式
        meta_cols = [col for col in df.columns if col not in date_cols]
        df_long = df.melt(
            id_vars=meta_cols,
            value_vars=date_cols,
            var_name='date',
            value_name='yield'
        )
        
        # 解析日期
        def parse_date(date_str):
            try:
                if re.match(r'\d{4}-\d{2}$', str(date_str)):
                    from calendar import monthrange
                    year, month = int(date_str[:4]), int(date_str[5:7])
                    last_day = monthrange(year, month)[1]
                    return pd.Timestamp(year, month, last_day)
                else:
                    return pd.to_datetime(date_str)
            except:
                return pd.NaT
        
        df_long['date'] = df_long['date'].apply(parse_date)
        df_long = df_long[df_long['date'].notna()]
        
        # 清洗数据
        df_long = df_long[df_long['yield'].notna()]
        df_long = df_long[df_long['yield'] != '-']
        df_long = df_long[df_long['yield'] != '']
        df_long['yield'] = pd.to_numeric(df_long['yield'], errors='coerce')
        df_long = df_long[df_long['yield'].notna()]
        
        if len(df_long) == 0:
            return None
        
        df_long['maturity'] = maturity
        df_result = df_long[['date', 'maturity', 'yield']].copy()
        
        log(f"  {maturity}: {len(df_result)} records")
        return df_result
        
    except Exception as e:
        log(f"  Process {maturity} failed: {e}")
        return None


def merge_all_data(data_list):
    """合并所有期限的数据"""
    if len(data_list) == 0:
        return None
    
    # 合并所有数据
    combined = pd.concat(data_list, ignore_index=True)
    log(f"Combined data: {len(combined)} records")
    
    # 透视表
    df_pivot = combined.pivot_table(
        index='date',
        columns='maturity',
        values='yield',
        aggfunc='first'
    ).reset_index()
    
    # 重命名列
    column_mapping = {'date': 'date'}
    for maturity in MATURITIES:
        if maturity in df_pivot.columns:
            column_mapping[maturity] = f'X{maturity}'
    
    df_pivot = df_pivot.rename(columns=column_mapping)
    
    # 确保所有期限列都存在
    for maturity in MATURITIES:
        col_name = f'X{maturity}'
        if col_name not in df_pivot.columns:
            df_pivot[col_name] = float('nan')
    
    # 排序
    df_pivot = df_pivot.sort_values('date')
    
    # 只保留标准列
    std_columns = ['date'] + [f'X{m}' for m in MATURITIES]
    df_pivot = df_pivot[std_columns]
    
    return df_pivot


def merge_with_existing(new_df):
    """合并新数据与现有数据"""
    data_file = os.path.join(WORKING_DIR, DATA_FILE)
    
    if os.path.exists(data_file):
        existing_df = pd.read_csv(data_file)
        existing_df['date'] = pd.to_datetime(existing_df['date'])
        
        log(f"Existing data: {len(existing_df)} records")
        log(f"New data: {len(new_df)} records")
        
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
        combined_df = combined_df.sort_values('date')
        
        log(f"Merged data: {len(combined_df)} records")
        return combined_df
    else:
        log("No existing data, using new data")
        return new_df


def save_data(df):
    """保存数据"""
    data_file = os.path.join(WORKING_DIR, DATA_FILE)
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    df.to_csv(data_file, index=False, encoding='utf-8-sig')
    log(f"Data saved: {data_file}")
    log(f"Total records: {len(df)}")
    log(f"Date range: {df['date'].min()} to {df['date'].max()}")
    return data_file


def print_summary(df):
    """打印摘要"""
    print("\n" + "="*60)
    print("China Treasury Yield Summary")
    print("="*60)
    
    print(f"\nDate range: {df['date'].min()} to {df['date'].max()}")
    print(f"Total records: {len(df)}")
    
    print("\nLatest yields (%):")
    latest = df.iloc[-1]
    for maturity in MATURITIES:
        col = f'X{maturity}'
        if col in df.columns:
            value = latest[col]
            if pd.notna(value):
                print(f"  {maturity:>3}: {value:.2f}%")
    
    print("\n" + "="*60)


def cleanup_temp():
    """清理临时文件"""
    temp_dir = os.path.join(WORKING_DIR, 'temp_integrate')
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        log("Temp files cleaned")


async def main_async():
    """主函数（异步）"""
    print("="*60)
    print("China Treasury Yield Data Integration")
    print("="*60)
    
    try:
        # 查询所有期限
        log("Querying all maturities...")
        tasks = [fetch_single_maturity_async(m) for m in MATURITIES]
        results = await asyncio.gather(*tasks)
        
        valid_results = [r for r in results if r is not None]
        log(f"Successfully retrieved: {len(valid_results)}/{len(MATURITIES)} maturities")
        
        if len(valid_results) == 0:
            log("No data retrieved")
            return
        
        # 处理数据
        log("Processing data...")
        data_list = []
        for result in valid_results:
            df = process_maturity_data(result)
            if df is not None:
                data_list.append(df)
        
        if len(data_list) == 0:
            log("No valid data to process")
            return
        
        # 合并数据
        new_df = merge_all_data(data_list)
        if new_df is None:
            log("Failed to merge data")
            return
        
        # 与现有数据合并
        combined_df = merge_with_existing(new_df)
        
        # 保存数据
        save_data(combined_df)
        
        # 打印摘要
        print_summary(combined_df)
        
    finally:
        cleanup_temp()
    
    print("\n" + "="*60)
    print("Integration complete!")
    print("="*60)


def main():
    """主函数"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
