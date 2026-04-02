#!/usr/bin/env python3
"""
中国国债收益率数据分析示例
==========================
演示如何使用获取的国债收益率数据进行常见分析

使用方法:
    python analyze_cn_treasury.py
"""

import pandas as pd
import os
from datetime import datetime, timedelta

def load_data():
    """加载国债收益率数据"""
    data_file = 'cn_treasury_yields.csv'
    
    if not os.path.exists(data_file):
        print(f"错误: 数据文件不存在: {data_file}")
        print("请先运行 fetch_cn_treasury_tushare.py 获取数据")
        return None
    
    df = pd.read_csv(data_file)
    df['date'] = pd.to_datetime(df['date'])
    return df


def print_latest_yields(df):
    """打印最新收益率"""
    print("\n" + "="*60)
    print("最新国债收益率")
    print("="*60)
    
    latest = df.iloc[-1]
    maturity_cols = ['X1年', 'X2年', 'X3年', 'X5年', 'X7年', 'X10年', 'X20年', 'X30年']
    
    print(f"\n数据日期: {latest['date']}")
    print("-" * 40)
    
    for col in maturity_cols:
        if col in df.columns and pd.notna(latest[col]):
            maturity = col.replace('X', '')
            print(f"  {maturity:>4}: {latest[col]:.2f}%")


def calculate_yield_spread(df):
    """计算期限利差"""
    print("\n" + "="*60)
    print("期限利差分析 (10年 - 1年)")
    print("="*60)
    
    if 'X10年' not in df.columns or 'X1年' not in df.columns:
        print("缺少必要的数据列")
        return
    
    # 计算期限利差
    df['spread_10y_1y'] = df['X10年'] - df['X1年']
    
    latest = df.iloc[-1]
    print(f"\n当前期限利差: {latest['spread_10y_1y']:.2f}%")
    
    # 统计信息
    spread_stats = df['spread_10y_1y'].describe()
    print(f"\n历史统计:")
    print(f"  平均值: {spread_stats['mean']:.2f}%")
    print(f"  最小值: {spread_stats['min']:.2f}%")
    print(f"  最大值: {spread_stats['max']:.2f}%")
    
    # 当前位置
    percentile = (df['spread_10y_1y'] < latest['spread_10y_1y']).mean() * 100
    print(f"  历史分位: {percentile:.1f}%")


def analyze_yield_curve_shape(df):
    """分析收益率曲线形态"""
    print("\n" + "="*60)
    print("收益率曲线形态")
    print("="*60)
    
    latest = df.iloc[-1]
    
    # 检查关键期限
    key_maturities = ['X1年', 'X5年', 'X10年', 'X30年']
    yields = {}
    
    for mat in key_maturities:
        if mat in df.columns and pd.notna(latest[mat]):
            yields[mat.replace('X', '')] = latest[mat]
    
    if len(yields) < 2:
        print("数据不足，无法分析")
        return
    
    print(f"\n数据日期: {latest['date']}")
    print("-" * 40)
    
    # 判断曲线形态
    maturity_order = ['1年', '2年', '3年', '5年', '7年', '10年', '20年', '30年']
    prev_yield = None
    trend = []
    
    for mat in maturity_order:
        if mat in yields:
            if prev_yield is not None:
                diff = yields[mat] - prev_yield
                trend.append(diff)
            prev_yield = yields[mat]
    
    if len(trend) == 0:
        print("数据不足")
        return
    
    # 判断形态
    if all(t > 0 for t in trend):
        shape = "正常向上 (Normal)"
    elif all(t < 0 for t in trend):
        shape = "倒挂 (Inverted)"
    elif trend[0] > 0 and trend[-1] < 0:
        shape = "驼峰形 (Humped)"
    else:
        shape = "平坦 (Flat)"
    
    print(f"曲线形态: {shape}")
    
    # 打印关键收益率
    print("\n关键期限收益率:")
    for mat in ['1年', '5年', '10年', '30年']:
        if mat in yields:
            print(f"  {mat:>3}: {yields[mat]:.2f}%")


def calculate_moving_average(df, window=20):
    """计算移动平均线"""
    print("\n" + "="*60)
    print(f"{window}日移动平均线 (10年期)")
    print("="*60)
    
    if 'X10年' not in df.columns:
        print("缺少10年期数据")
        return
    
    # 计算移动平均
    df[f'MA_{window}'] = df['X10年'].rolling(window=window).mean()
    
    latest = df.iloc[-1]
    ma_value = latest[f'MA_{window}']
    current = latest['X10年']
    
    if pd.notna(ma_value):
        print(f"\n当前10年期收益率: {current:.2f}%")
        print(f"{window}日移动平均: {ma_value:.2f}%")
        print(f"偏离度: {(current - ma_value):.2f}%")
        
        if current > ma_value:
            print("状态: 收益率在均线上方 (偏空)")
        else:
            print("状态: 收益率在均线下方 (偏多)")


def export_for_analysis(df, output_file='treasury_analysis.xlsx'):
    """导出数据到Excel，便于进一步分析"""
    print("\n" + "="*60)
    print("导出数据")
    print("="*60)
    
    try:
        # 创建Excel writer
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 原始数据
            df.to_excel(writer, sheet_name='原始数据', index=False)
            
            # 最新数据
            latest = df.iloc[-1:].copy()
            latest.to_excel(writer, sheet_name='最新数据', index=False)
            
            # 月度平均
            df['year_month'] = df['date'].dt.to_period('M')
            monthly_avg = df.groupby('year_month').agg({
                'X1年': 'mean',
                'X3年': 'mean',
                'X5年': 'mean',
                'X7年': 'mean',
                'X10年': 'mean',
                'X30年': 'mean',
            }).reset_index()
            monthly_avg.to_excel(writer, sheet_name='月度平均', index=False)
        
        print(f"数据已导出: {output_file}")
        print("包含工作表:")
        print("  - 原始数据")
        print("  - 最新数据")
        print("  - 月度平均")
        
    except ImportError:
        print("需要安装 openpyxl: pip install openpyxl")
    except Exception as e:
        print(f"导出失败: {e}")


def main():
    """主函数"""
    print("="*60)
    print("中国国债收益率数据分析")
    print("="*60)
    
    # 加载数据
    df = load_data()
    if df is None:
        return
    
    print(f"\n数据加载成功: {len(df)} 条记录")
    print(f"日期范围: {df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}")
    
    # 执行分析
    print_latest_yields(df)
    calculate_yield_spread(df)
    analyze_yield_curve_shape(df)
    calculate_moving_average(df, window=20)
    calculate_moving_average(df, window=60)
    
    # 导出数据
    export_for_analysis(df)
    
    print("\n" + "="*60)
    print("分析完成!")
    print("="*60)


if __name__ == "__main__":
    main()
