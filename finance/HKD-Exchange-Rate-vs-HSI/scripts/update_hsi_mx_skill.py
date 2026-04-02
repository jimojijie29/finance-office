#!/usr/bin/env python3
"""
HKD-Exchange-Rate-vs-HSI 数据更新脚本 - 使用 mx-macro-data skill
通过东方财富妙想API获取恒生指数数据
"""

import pandas as pd
import subprocess
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# 配置路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')
MX_OUTPUT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), '..', '..', 'miaoxiang', 'mx_macro_data')

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

def fetch_hsi_with_skill():
    """使用 mx-macro-data skill 获取恒生指数数据"""
    log("使用 mx-macro-data skill 获取数据...")
    
    try:
        # 获取工作目录（workspace 根目录）
        workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
        skill_script = os.path.join(workspace_dir, 'skills', 'mx-macro-data', 'scripts', 'get_data.py')
        
        result = subprocess.run(
            ['python', skill_script, '--query', '香港恒生指数日线数据'],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=workspace_dir
        )
        
        if result.returncode != 0:
            log(f"Skill 执行失败: {result.stderr}")
            return None
        
        # 解析输出找到CSV文件路径
        output = result.stdout
        log(f"Skill 输出: {output[:200]}...")
        
        # 查找生成的CSV文件
        if 'mx_macro_data_' in output and '_daily.csv' in output:
            # 提取文件名
            import re
            match = re.search(r'mx_macro_data_[a-f0-9]+_daily\.csv', output)
            if match:
                csv_filename = match.group(0)
                csv_path = os.path.join(MX_OUTPUT_DIR, csv_filename)
                return csv_path
        
        # 如果无法从输出解析，尝试查找最新的CSV文件
        mx_dir = Path(MX_OUTPUT_DIR)
        if mx_dir.exists():
            csv_files = sorted(mx_dir.glob('mx_macro_data_*_daily.csv'), key=lambda x: x.stat().st_mtime, reverse=True)
            if csv_files:
                return str(csv_files[0])
        
        log("无法找到生成的CSV文件")
        return None
        
    except Exception as e:
        log(f"调用 skill 失败: {e}")
        return None

def parse_mx_data(csv_path):
    """解析 mx-macro-data 输出的CSV数据"""
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        
        # 找到恒生指数行（使用原始数值，不是"万"单位）
        hsi_row = None
        for idx, row in df.iterrows():
            if '恒生指数' in str(row.get('indicator_name', '')) and '万' not in str(row.get('indicator_name', '')):
                hsi_row = row
                break
        
        if hsi_row is None:
            # 使用第二行（通常是原始数值）
            hsi_row = df.iloc[1] if len(df) > 1 else df.iloc[0]
        
        # 提取日期和数值（跳过前几列的元数据）
        records = []
        for col in df.columns:
            if col.startswith('2026-') or col.startswith('2025-'):
                try:
                    date = col
                    value = float(hsi_row[col])
                    records.append({
                        'date': date,
                        'open': value,  # API只返回收盘价，用收盘价填充
                        'high': value,
                        'low': value,
                        'close': value,
                        'volume': 0  # API不返回成交量
                    })
                except:
                    continue
        
        return pd.DataFrame(records)
        
    except Exception as e:
        log(f"解析数据失败: {e}")
        return pd.DataFrame()

def update_hsi():
    """更新恒生指数数据"""
    log("="*60)
    log("更新恒生指数数据 (mx-macro-data skill 版本)")
    log("="*60)
    
    filepath = os.path.join(DATA_DIR, 'Hang_Seng_Index.csv')
    
    # 获取现有数据最后日期
    last_date = get_last_date(filepath)
    
    if last_date is None:
        log(f"文件不存在: {filepath}")
        log("请使用初始下载脚本获取完整历史数据")
        return False
    
    log(f"现有数据最后日期: {last_date.strftime('%Y-%m-%d')}")
    
    # 使用 skill 获取新数据
    csv_path = fetch_hsi_with_skill()
    
    if csv_path is None:
        log("获取数据失败")
        return False
    
    log(f"获取到数据文件: {csv_path}")
    
    # 解析数据
    df_new = parse_mx_data(csv_path)
    
    if df_new.empty:
        log("解析数据失败")
        return False
    
    log(f"解析到 {len(df_new)} 条新数据")
    log(f"最新日期: {df_new['date'].max()}")
    
    # 读取现有数据
    df_existing = pd.read_csv(filepath, encoding='utf-8-sig')
    df_existing.columns = df_existing.columns.str.lower().str.replace('\ufeff', '')
    
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
    log("HKD-Exchange-Rate-vs-HSI 数据增量更新 (mx-macro-data skill)")
    log(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("="*60)
    
    # 更新恒生指数
    success = update_hsi()
    
    log("\n" + "="*60)
    if success:
        log("更新成功!")
    else:
        log("更新失败!")
    log("="*60)

if __name__ == '__main__':
    main()
