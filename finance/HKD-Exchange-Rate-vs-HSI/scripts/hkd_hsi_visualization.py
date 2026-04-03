#!/usr/bin/env python3
"""
HKD-Exchange-Rate-vs-HSI 可视化脚本（Python版本）
使用 plotly 创建双Y轴交互式图表
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

# 配置路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')

def log(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def main():
    log("="*60)
    log("HKD-Exchange-Rate-vs-HSI 可视化生成")
    log("="*60)
    
    # Step 1: 读取数据
    log("读取数据...")
    
    df_hkd = pd.read_csv(os.path.join(DATA_DIR, 'HKD_USD_Exchange_Rate.csv'), encoding='utf-8-sig')
    df_hsi = pd.read_csv(os.path.join(DATA_DIR, 'Hang_Seng_Index.csv'), encoding='utf-8-sig')
    
    # 统一列名
    df_hkd.columns = df_hkd.columns.str.lower().str.replace('\ufeff', '')
    df_hsi.columns = df_hsi.columns.str.lower().str.replace('\ufeff', '')
    
    # 转换日期
    df_hkd['date'] = pd.to_datetime(df_hkd['date'])
    df_hsi['date'] = pd.to_datetime(df_hsi['date'])
    
    log(f"USD/HKD: {df_hkd['date'].min().date()} 至 {df_hkd['date'].max().date()} ({len(df_hkd)} 条)")
    log(f"HSI: {df_hsi['date'].min().date()} 至 {df_hsi['date'].max().date()} ({len(df_hsi)} 条)")
    
    # Step 2: 数据对齐
    common_start = max(df_hkd['date'].min(), df_hsi['date'].min())
    common_end = min(df_hkd['date'].max(), df_hsi['date'].max())
    
    log(f"共同范围: {common_start.date()} 至 {common_end.date()}")
    
    # 合并数据
    df_merged = pd.merge(
        df_hkd[['date', 'close']].rename(columns={'close': 'hkd_close'}),
        df_hsi[['date', 'close']].rename(columns={'close': 'hsi_close'}),
        on='date',
        how='inner'
    )
    
    df_merged = df_merged[(df_merged['date'] >= common_start) & (df_merged['date'] <= common_end)]
    
    log(f"合并后数据: {len(df_merged)} 条")
    
    # Step 3: 创建双Y轴图表
    log("生成图表...")
    
    color_hkd = "#1976D2"  # 蓝色
    color_hsi = "#D32F2F"  # 红色
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 添加 USD/HKD 汇率（左Y轴）
    fig.add_trace(
        go.Scatter(
            x=df_merged['date'],
            y=df_merged['hkd_close'],
            name='USD/HKD 汇率',
            line=dict(color=color_hkd, width=2),
            hovertemplate='<b>USD/HKD 汇率</b><br>日期: %{x|%Y-%m-%d}<br>汇率: %{y:.4f}<extra></extra>'
        ),
        secondary_y=False
    )
    
    # 添加恒生指数（右Y轴）
    fig.add_trace(
        go.Scatter(
            x=df_merged['date'],
            y=df_merged['hsi_close'],
            name='恒生指数',
            line=dict(color=color_hsi, width=2),
            hovertemplate='<b>恒生指数</b><br>日期: %{x|%Y-%m-%d}<br>指数: %{y:.2f}<extra></extra>'
        ),
        secondary_y=True
    )
    
    # 配置布局
    fig.update_layout(
        title=dict(
            text='<b>港元汇率 vs 恒生指数走势对比</b><br><sup>双Y轴显示：左轴=汇率，右轴=指数 | 数据期间: 2013-08 至 2026-04</sup>',
            font=dict(size=18),
            x=0.5,
            xanchor='center'
        ),
        
        xaxis=dict(
            title='',
            tickformat='%Y-%m',
            tickangle=-45,
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=[
                    dict(count=3, label='3月', step='month', stepmode='backward'),
                    dict(count=6, label='6月', step='month', stepmode='backward'),
                    dict(count=1, label='1年', step='year', stepmode='backward'),
                    dict(count=3, label='3年', step='year', stepmode='backward'),
                    dict(count=5, label='5年', step='year', stepmode='backward'),
                    dict(step='all', label='全部')
                ]
            ),
            showgrid=True,
            gridcolor='#E0E0E0'
        ),
        
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.15,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(255,255,255,0.95)',
            bordercolor='#BDBDBD',
            borderwidth=1
        ),
        
        hovermode='x unified',
        plot_bgcolor='#FAFAFA',
        paper_bgcolor='white',
        margin=dict(l=80, r=80, t=100, b=120)
    )
    
    # 配置Y轴
    fig.update_yaxes(
        title_text='USD/HKD 汇率',
        title_font_color=color_hkd,
        tickfont_color=color_hkd,
        tickformat='.4f',
        showgrid=True,
        gridcolor='#E0E0E0',
        secondary_y=False
    )
    
    fig.update_yaxes(
        title_text='恒生指数',
        title_font_color=color_hsi,
        tickfont_color=color_hsi,
        tickformat='.0f',
        showgrid=False,
        secondary_y=True
    )
    
    # Step 4: 保存图表
    output_path = os.path.join(DATA_DIR, 'hkd_vs_hsi_dual_axis.html')
    fig.write_html(output_path, include_plotlyjs='cdn')
    
    log(f"图表已保存: {output_path}")
    
    # Step 5: 输出统计摘要
    log("\n" + "="*60)
    log("数据摘要")
    log("="*60)
    
    log(f"\n共同数据期间: {common_start.date()} 至 {common_end.date()}")
    log(f"总交易日数: {len(df_merged)}")
    
    log("\nUSD/HKD 汇率统计:")
    log(f"  起始值: {df_merged['hkd_close'].iloc[0]:.4f}")
    log(f"  结束值: {df_merged['hkd_close'].iloc[-1]:.4f}")
    log(f"  均值: {df_merged['hkd_close'].mean():.4f}")
    log(f"  最小值: {df_merged['hkd_close'].min():.4f} ({df_merged.loc[df_merged['hkd_close'].idxmin(), 'date'].date()})")
    log(f"  最大值: {df_merged['hkd_close'].max():.4f} ({df_merged.loc[df_merged['hkd_close'].idxmax(), 'date'].date()})")
    
    log("\n恒生指数统计:")
    log(f"  起始值: {df_merged['hsi_close'].iloc[0]:.2f}")
    log(f"  结束值: {df_merged['hsi_close'].iloc[-1]:.2f}")
    log(f"  均值: {df_merged['hsi_close'].mean():.2f}")
    log(f"  最小值: {df_merged['hsi_close'].min():.2f} ({df_merged.loc[df_merged['hsi_close'].idxmin(), 'date'].date()})")
    log(f"  最大值: {df_merged['hsi_close'].max():.2f} ({df_merged.loc[df_merged['hsi_close'].idxmax(), 'date'].date()})")
    
    log("\n" + "="*60)
    log("可视化生成完成!")
    log("="*60)

if __name__ == '__main__':
    main()
