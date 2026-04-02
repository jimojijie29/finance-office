#!/usr/bin/env python3
"""
中国国债收益率数据更新工作流
==========================
自动获取中国各期限国债收益率历史数据并保存为CSV

使用方法:
    python update_cn_treasury_data.py

功能:
    1. 从 mx-macro-data 获取最新中国国债收益率数据
    2. 处理并合并到现有数据文件
    3. 支持全期限数据: 1年、2年、3年、5年、7年、10年、20年、30年
"""

import pandas as pd
import subprocess
import sys
import os
import asyncio
import re
from datetime import datetime, timedelta
from pathlib import Path

# ============ 配置 ============
CONFIG = {
    # 数据文件路径
    'data_file': 'cn_treasury_yields.csv',
    
    # mx-macro-data 技能路径
    'mx_macro_skill_path': r'D:\OpenClawData\.openclaw\workspace\skills\mx-macro-data',
    
    # 工作目录
    'working_dir': os.path.dirname(os.path.abspath(__file__)),
    
    # 数据期限列表（中国国债主要期限）
    'maturities': ['1年', '2年', '3年', '5年', '7年', '10年', '20年', '30年'],
}


def log(message):
    """打印带时间戳的日志"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")


def get_working_dir():
    """获取工作目录"""
    return CONFIG['working_dir']


def get_date_range():
    """确定需要获取数据的日期范围"""
    working_dir = get_working_dir()
    data_file = os.path.join(working_dir, CONFIG['data_file'])
    
    if os.path.exists(data_file):
        # 读取现有数据，获取最后日期
        df = pd.read_csv(data_file)
        last_date = pd.to_datetime(df['date'].max())
        start_date = last_date + timedelta(days=1)
        log(f"现有数据最后日期: {last_date.strftime('%Y-%m-%d')}")
    else:
        # 如果没有现有数据，从2020年开始
        start_date = datetime(2020, 1, 1)
        log("未找到现有数据，将从2020-01-01开始获取")
    
    # 结束日期为今天
    end_date = datetime.now()
    
    return start_date, end_date


async def fetch_single_maturity_async(maturity, start_date, end_date):
    """获取单个期限的数据"""
    log(f"获取 {maturity}期 数据...")
    
    # 构建查询 - 限制在3年内以符合系统限制
    query = f"中国{maturity}期国债收益率日度数据，从{start_date.strftime('%Y年%m月')}到{end_date.strftime('%Y年%m月')}"
    
    try:
        # 添加 mx-macro-data 路径
        mx_macro_path = CONFIG['mx_macro_skill_path']
        if mx_macro_path not in sys.path:
            sys.path.insert(0, mx_macro_path)
        
        # 导入 mx-macro-data 模块
        from scripts.get_data import query_mx_macro_data
        
        # 创建临时输出目录
        temp_dir = os.path.join(get_working_dir(), 'temp_data', maturity)
        os.makedirs(temp_dir, exist_ok=True)
        
        # 设置环境变量
        os.environ['MX_MACRO_DATA_OUTPUT_DIR'] = temp_dir
        
        # 调用查询函数
        result = await query_mx_macro_data(query, output_dir=Path(temp_dir))
        
        if 'error' in result:
            log(f"  获取 {maturity}期 数据出错: {result['error']}")
            return None
        
        if 'csv_paths' in result and len(result['csv_paths']) > 0:
            # 优先使用日度数据
            daily_files = [p for p in result['csv_paths'] if 'daily' in p.lower()]
            if daily_files:
                csv_file = daily_files[0]
            else:
                csv_file = result['csv_paths'][0]
            log(f"  获取到 {maturity}期 数据文件: {csv_file}")
            return {'maturity': maturity, 'file': csv_file}
        else:
            log(f"  未获取到 {maturity}期 数据文件")
            return None
            
    except Exception as e:
        log(f"  获取 {maturity}期 数据失败: {e}")
        return None


async def fetch_all_data_async(start_date, end_date):
    """获取所有期限的数据"""
    log(f"获取数据: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    
    tasks = []
    for maturity in CONFIG['maturities']:
        tasks.append(fetch_single_maturity_async(maturity, start_date, end_date))
    
    results = await asyncio.gather(*tasks)
    
    # 过滤掉 None 结果
    return [r for r in results if r is not None]


def fetch_new_data(start_date, end_date):
    """同步包装异步函数"""
    return asyncio.run(fetch_all_data_async(start_date, end_date))


def process_single_file(file_info):
    """处理单个数据文件"""
    csv_file = file_info['file']
    maturity = file_info['maturity']
    
    if not csv_file or not os.path.exists(csv_file):
        log(f"  数据文件不存在: {csv_file}")
        return None
    
    try:
        # 读取数据
        df = pd.read_csv(csv_file, encoding='utf-8')
        
        if len(df) == 0:
            log(f"  {maturity}期 数据为空")
            return None
        
        # 找出日期列（格式为 YYYY-MM-DD 或 YYYY-MM）
        date_cols = [col for col in df.columns if re.match(r'\d{4}-\d{2}(-\d{2})?', str(col))]
        
        if len(date_cols) == 0:
            log(f"  {maturity}期 未找到日期列")
            return None
        
        # 转换为长格式
        meta_cols = [col for col in df.columns if col not in date_cols]
        df_long = df.melt(
            id_vars=meta_cols,
            value_vars=date_cols,
            var_name='date',
            value_name='yield'
        )
        
        # 转换日期 - 处理 YYYY-MM 格式
        def parse_date(date_str):
            try:
                if re.match(r'\d{4}-\d{2}$', str(date_str)):
                    # 月度数据，取月末
                    from calendar import monthrange
                    year, month = int(date_str[:4]), int(date_str[5:7])
                    last_day = monthrange(year, month)[1]
                    return pd.Timestamp(year, month, last_day)
                else:
                    return pd.to_datetime(date_str)
            except:
                return pd.NaT
        
        df_long['date'] = df_long['date'].apply(parse_date)
        
        # 过滤掉空值
        df_long = df_long[df_long['date'].notna()]
        df_long = df_long[df_long['yield'].notna()]
        df_long = df_long[df_long['yield'] != '-']
        df_long = df_long[df_long['yield'] != '']
        
        # 转换收益率为数值
        df_long['yield'] = pd.to_numeric(df_long['yield'], errors='coerce')
        df_long = df_long[df_long['yield'].notna()]
        
        if len(df_long) == 0:
            log(f"  {maturity}期 无有效数据")
            return None
        
        # 添加期限列
        df_long['maturity'] = maturity
        
        # 只保留需要的列
        df_result = df_long[['date', 'maturity', 'yield']].copy()
        
        log(f"  {maturity}期 处理完成: {len(df_result)} 条记录")
        
        return df_result
        
    except Exception as e:
        log(f"  处理 {maturity}期 数据失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_data(file_list):
    """处理所有数据文件"""
    log("处理数据...")
    
    all_data = []
    for file_info in file_list:
        df = process_single_file(file_info)
        if df is not None and len(df) > 0:
            all_data.append(df)
    
    if len(all_data) == 0:
        log("无有效数据")
        return None
    
    # 合并所有数据
    combined = pd.concat(all_data, ignore_index=True)
    log(f"合并后数据: {len(combined)} 条")
    
    # 透视表：行=日期，列=期限
    df_pivot = combined.pivot_table(
        index='date',
        columns='maturity',
        values='yield',
        aggfunc='first'
    ).reset_index()
    
    # 重命名列为标准格式
    column_mapping = {'date': 'date'}
    for maturity in CONFIG['maturities']:
        if maturity in df_pivot.columns:
            column_mapping[maturity] = f'X{maturity}'
    
    df_pivot = df_pivot.rename(columns=column_mapping)
    
    # 确保所有期限列都存在（缺失的填NaN）
    for maturity in CONFIG['maturities']:
        col_name = f'X{maturity}'
        if col_name not in df_pivot.columns:
            df_pivot[col_name] = float('nan')
    
    # 按日期排序
    df_pivot = df_pivot.sort_values('date')
    
    # 只保留标准列
    std_columns = ['date'] + [f'X{m}' for m in CONFIG['maturities']]
    df_pivot = df_pivot[std_columns]
    
    log(f"处理后数据形状: {df_pivot.shape}")
    log(f"处理后列: {list(df_pivot.columns)}")
    log(f"日期范围: {df_pivot['date'].min()} 至 {df_pivot['date'].max()}")
    
    return df_pivot


def merge_with_existing(new_df):
    """合并新数据与现有数据"""
    working_dir = get_working_dir()
    data_file = os.path.join(working_dir, CONFIG['data_file'])
    
    if os.path.exists(data_file):
        # 读取现有数据
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
    else:
        log("无现有数据，使用新数据")
        return new_df


def validate_data(df):
    """验证数据质量"""
    log("验证数据质量...")
    
    # 检查日期范围
    date_range = df['date'].max() - df['date'].min()
    log(f"数据时间跨度: {date_range.days} 天")
    
    # 检查10年期收益率范围（作为参考）
    if 'X10年' in df.columns:
        yield_10y = df['X10年'].dropna()
        if len(yield_10y) > 0:
            log(f"10年期收益率范围: {yield_10y.min():.2f}% - {yield_10y.max():.2f}%")
            
            # 合理性检查（中国国债通常在1%-5%之间）
            if yield_10y.min() < 0.5 or yield_10y.max() > 6:
                log("警告: 10年期收益率数据可能异常，请检查")
    
    # 检查缺失值
    missing_counts = df.isnull().sum()
    if missing_counts.sum() > 0:
        log(f"缺失值统计:\n{missing_counts[missing_counts > 0]}")
    else:
        log("数据完整性检查通过")
    
    return True


def save_data(df):
    """保存数据到CSV文件"""
    working_dir = get_working_dir()
    data_file = os.path.join(working_dir, CONFIG['data_file'])
    
    # 确保日期格式统一
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    
    # 保存数据
    df.to_csv(data_file, index=False, encoding='utf-8-sig')
    
    log(f"数据已保存: {data_file}")
    log(f"总行数: {len(df)}")
    log(f"日期范围: {df['date'].min()} 至 {df['date'].max()}")
    log(f"数据列: {', '.join(df.columns.tolist())}")
    
    return data_file


def cleanup_temp():
    """清理临时文件"""
    temp_dir = os.path.join(get_working_dir(), 'temp_data')
    if os.path.exists(temp_dir):
        import shutil
        shutil.rmtree(temp_dir)
        log("临时文件已清理")


def print_summary(df):
    """打印数据摘要"""
    print("\n" + "="*60)
    print("中国国债收益率数据摘要")
    print("="*60)
    
    print(f"\n数据时间范围: {df['date'].min()} 至 {df['date'].max()}")
    print(f"总记录数: {len(df)}")
    
    print("\n最新收益率 (%):")
    latest = df.iloc[-1]
    for maturity in CONFIG['maturities']:
        col = f'X{maturity}'
        if col in df.columns:
            value = latest[col]
            if pd.notna(value):
                print(f"  {maturity:>3}期: {value:.2f}%")
    
    print("\n" + "="*60)


def main():
    """主函数"""
    print("="*60)
    print("中国国债收益率数据更新")
    print("="*60)
    
    try:
        # 获取日期范围
        start_date, end_date = get_date_range()
        
        # 如果开始日期大于结束日期，说明数据已是最新
        if start_date > end_date:
            log("数据已是最新，无需更新")
            return
        
        # 获取新数据
        file_list = fetch_new_data(start_date, end_date)
        
        if not file_list or len(file_list) == 0:
            log("未获取到新数据")
            return
        
        log(f"成功获取 {len(file_list)} 个期限的数据")
        
        # 处理数据
        new_df = process_data(file_list)
        
        if new_df is None or len(new_df) == 0:
            log("数据处理失败或无数据")
            return
        
        # 合并数据
        combined_df = merge_with_existing(new_df)
        
        # 验证数据
        validate_data(combined_df)
        
        # 保存数据
        save_data(combined_df)
        
        # 打印摘要
        print_summary(combined_df)
        
    finally:
        # 清理临时文件
        cleanup_temp()
    
    print("\n" + "="*60)
    print("更新完成!")
    print("="*60)


if __name__ == "__main__":
    main()
