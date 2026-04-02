#!/usr/bin/env python3
"""
使用 Tushare 获取中国国债收益率数据
==========================
获取中债国债收益率曲线数据

Tushare 接口: yc_cb - 债券收益率曲线
"""

import pandas as pd
import sys
import os
from datetime import datetime, timedelta

# 配置
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = 'cn_treasury_yields.csv'

# 要获取的期限
MATURITIES = ['1年', '2年', '3年', '5年', '7年', '10年', '20年', '30年']

# Tushare 期限代码映射
TUSHARE_MATURITY_MAP = {
    '1年': '1Y',
    '2年': '2Y',
    '3年': '3Y',
    '5年': '5Y',
    '7年': '7Y',
    '10年': '10Y',
    '20年': '20Y',
    '30年': '30Y',
}


def log(message):
    """打印带时间戳的日志"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")


def get_tushare_pro():
    """获取 Tushare Pro API"""
    try:
        import tushare as ts
        
        # 尝试从环境变量或配置文件获取 token
        token = os.environ.get('TUSHARE_TOKEN', '')
        
        if not token:
            # 尝试从文件读取
            token_file = os.path.expanduser('~/.tushare/token.txt')
            if os.path.exists(token_file):
                with open(token_file, 'r') as f:
                    token = f.read().strip()
        
        if not token:
            log("Tushare token not found. Please set TUSHARE_TOKEN environment variable.")
            return None
        
        pro = ts.pro_api(token)
        return pro
        
    except ImportError:
        log("tushare not installed. Please install: pip install tushare")
        return None
    except Exception as e:
        log(f"Error initializing Tushare: {e}")
        return None


def fetch_yc_cb_data(pro, start_date, end_date):
    """使用 yc_cb 接口获取债券收益率曲线数据"""
    log(f"Fetching yield curve data from {start_date} to {end_date}")
    
    try:
        # 中债国债收益率曲线代码
        # 曲线类型: 国债
        # 曲线代码: 1001 (中债国债收益率曲线)
        
        all_data = []
        
        # 分批获取数据（每次最多获取一段时间）
        current_date = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
        
        while current_date <= end:
            date_str = current_date.strftime('%Y%m%d')
            log(f"  Fetching data for {date_str}")
            
            try:
                # 获取当天的收益率曲线数据
                df = pro.yc_cb(trade_date=date_str, curve_type='0', curve_name='中债国债收益率曲线')
                
                if df is not None and len(df) > 0:
                    log(f"    Got {len(df)} records")
                    df['trade_date'] = date_str
                    all_data.append(df)
                else:
                    log(f"    No data for {date_str}")
                    
            except Exception as e:
                log(f"    Error fetching {date_str}: {e}")
            
            # 下一天
            current_date += timedelta(days=1)
        
        if len(all_data) == 0:
            log("No data retrieved")
            return None
        
        # 合并所有数据
        combined = pd.concat(all_data, ignore_index=True)
        log(f"Total records: {len(combined)}")
        
        return combined
        
    except Exception as e:
        log(f"Error fetching data: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_yc_cb_data(df):
    """处理 yc_cb 返回的数据"""
    log("Processing data...")
    
    try:
        # 查看数据结构
        log(f"Columns: {list(df.columns)}")
        log(f"Sample data:")
        print(df.head())
        
        # yc_cb 返回的数据通常包含:
        # - trade_date: 交易日期
        # - curve_name: 曲线名称
        # - curve_type: 曲线类型
        # - term: 期限 (如 '1Y', '2Y', '3Y', '5Y', '7Y', '10Y', '20Y', '30Y')
        # - yield: 收益率
        
        # 筛选需要的期限
        df_filtered = df[df['term'].isin(TUSHARE_MATURITY_MAP.values())].copy()
        
        # 转换日期格式
        df_filtered['date'] = pd.to_datetime(df_filtered['trade_date'], format='%Y%m%d')
        
        # 转换期限为中文
        reverse_map = {v: k for k, v in TUSHARE_MATURITY_MAP.items()}
        df_filtered['maturity'] = df_filtered['term'].map(reverse_map)
        
        # 选择需要的列
        df_result = df_filtered[['date', 'maturity', 'yield']].copy()
        
        # 转换收益率为数值
        df_result['yield'] = pd.to_numeric(df_result['yield'], errors='coerce')
        df_result = df_result[df_result['yield'].notna()]
        
        log(f"Processed data: {len(df_result)} records")
        
        return df_result
        
    except Exception as e:
        log(f"Error processing data: {e}")
        import traceback
        traceback.print_exc()
        return None


def pivot_data(df):
    """透视数据为宽格式"""
    log("Pivoting data...")
    
    try:
        # 透视表
        df_pivot = df.pivot_table(
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
        
        log(f"Pivoted data: {df_pivot.shape}")
        
        return df_pivot
        
    except Exception as e:
        log(f"Error pivoting data: {e}")
        import traceback
        traceback.print_exc()
        return None


def merge_with_existing(new_df):
    """合并新数据与现有数据"""
    data_file = os.path.join(WORKING_DIR, DATA_FILE)
    
    if os.path.exists(data_file):
        existing_df = pd.read_csv(data_file)
        existing_df['date'] = pd.to_datetime(existing_df['date'])
        
        log(f"Existing data: {len(existing_df)} records")
        log(f"New data: {len(new_df)} records")
        
        # 合并数据
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # 按日期去重，保留最新数据
        combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
        
        # 排序
        combined_df = combined_df.sort_values('date')
        
        log(f"Merged data: {len(combined_df)} records")
        
        return combined_df
    else:
        log("No existing data, using new data")
        return new_df


def save_data(df):
    """保存数据"""
    data_file = os.path.join(WORKING_DIR, DATA_FILE)
    
    # 格式化日期
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    
    # 保存
    df.to_csv(data_file, index=False, encoding='utf-8-sig')
    
    log(f"Data saved: {data_file}")
    log(f"Total records: {len(df)}")
    log(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    return data_file


def print_summary(df):
    """打印摘要"""
    print("\n" + "="*60)
    print("China Treasury Yield Summary (Tushare)")
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


def main():
    """主函数"""
    print("="*60)
    print("China Treasury Yield Data (Tushare)")
    print("="*60)
    
    # 获取 Tushare API
    pro = get_tushare_pro()
    if pro is None:
        log("Failed to initialize Tushare API")
        return
    
    # 确定日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*3)  # 最近3年
    
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    
    log(f"Date range: {start_str} to {end_str}")
    
    # 获取数据
    raw_data = fetch_yc_cb_data(pro, start_str, end_str)
    
    if raw_data is None or len(raw_data) == 0:
        log("No data retrieved")
        return
    
    # 处理数据
    processed_data = process_yc_cb_data(raw_data)
    
    if processed_data is None or len(processed_data) == 0:
        log("Failed to process data")
        return
    
    # 透视数据
    pivoted_data = pivot_data(processed_data)
    
    if pivoted_data is None:
        log("Failed to pivot data")
        return
    
    # 合并现有数据
    combined_data = merge_with_existing(pivoted_data)
    
    # 保存数据
    save_data(combined_data)
    
    # 打印摘要
    print_summary(combined_data)
    
    print("\n" + "="*60)
    print("Complete!")
    print("="*60)


if __name__ == "__main__":
    main()
