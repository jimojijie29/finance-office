#!/usr/bin/env python3
"""
使用 Tushare 获取中国国债收益率数据（替代方案）
==========================
由于 yc_cb 接口需要积分权限，使用其他可用接口获取国债相关数据
"""

import pandas as pd
import tushare as ts
from datetime import datetime, timedelta
import os

# 配置
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = 'cn_treasury_yields_tushare.csv'

# 国债收益率指数代码（中债指数）
TREASURY_INDICES = {
    '1年': '000013.SH',  # 中债1年期国债到期收益率
    '3年': '000014.SH',  # 中债3年期国债到期收益率
    '5年': '000015.SH',  # 中债5年期国债到期收益率
    '7年': '000016.SH',  # 中债7年期国债到期收益率
    '10年': '000012.SH', # 中债10年期国债到期收益率
}


def log(message):
    """打印带时间戳的日志"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")


def fetch_treasury_yield(pro, ts_code, maturity, start_date, end_date):
    """获取国债收益率指数数据"""
    log(f"Fetching {maturity} yield data ({ts_code})...")
    
    try:
        # 获取指数日线数据
        df = pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if df is None or len(df) == 0:
            log(f"  No data for {maturity}")
            return None
        
        log(f"  Got {len(df)} records")
        
        # 处理数据
        df = df[['trade_date', 'close']].copy()
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        df['maturity'] = maturity
        df['yield'] = df['close']  # 收盘价作为收益率
        
        return df[['trade_date', 'maturity', 'yield']]
        
    except Exception as e:
        log(f"  Error fetching {maturity}: {e}")
        return None


def main():
    """主函数"""
    print("="*60)
    print("China Treasury Yield Data (Tushare Alternative)")
    print("="*60)
    
    # 初始化 Tushare
    pro = ts.pro_api()
    log("Tushare API initialized")
    
    # 日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*3)  # 最近3年
    
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    
    log(f"Date range: {start_str} to {end_str}")
    
    # 获取各期限数据
    all_data = []
    for maturity, ts_code in TREASURY_INDICES.items():
        df = fetch_treasury_yield(pro, ts_code, maturity, start_str, end_str)
        if df is not None:
            all_data.append(df)
    
    if len(all_data) == 0:
        log("No data retrieved")
        return
    
    # 合并数据
    combined = pd.concat(all_data, ignore_index=True)
    log(f"Combined data: {len(combined)} records")
    
    # 透视表
    df_pivot = combined.pivot_table(
        index='trade_date',
        columns='maturity',
        values='yield',
        aggfunc='first'
    ).reset_index()
    
    # 重命名列
    df_pivot = df_pivot.rename(columns={'trade_date': 'date'})
    column_mapping = {}
    for maturity in TREASURY_INDICES.keys():
        if maturity in df_pivot.columns:
            column_mapping[maturity] = f'X{maturity}'
    df_pivot = df_pivot.rename(columns=column_mapping)
    
    # 确保所有期限列都存在
    for maturity in TREASURY_INDICES.keys():
        col_name = f'X{maturity}'
        if col_name not in df_pivot.columns:
            df_pivot[col_name] = float('nan')
    
    # 排序
    df_pivot = df_pivot.sort_values('date')
    
    # 格式化日期
    df_pivot['date'] = df_pivot['date'].dt.strftime('%Y-%m-%d')
    
    # 保存数据
    data_file = os.path.join(WORKING_DIR, DATA_FILE)
    df_pivot.to_csv(data_file, index=False, encoding='utf-8-sig')
    
    log(f"Data saved: {data_file}")
    log(f"Total records: {len(df_pivot)}")
    log(f"Date range: {df_pivot['date'].min()} to {df_pivot['date'].max()}")
    
    # 打印摘要
    print("\n" + "="*60)
    print("China Treasury Yield Summary (Tushare)")
    print("="*60)
    
    print(f"\nDate range: {df_pivot['date'].min()} to {df_pivot['date'].max()}")
    print(f"Total records: {len(df_pivot)}")
    
    print("\nLatest yields:")
    latest = df_pivot.iloc[-1]
    for maturity in TREASURY_INDICES.keys():
        col = f'X{maturity}'
        if col in df_pivot.columns:
            value = latest[col]
            if pd.notna(value):
                print(f"  {maturity:>3}: {value:.3f}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
