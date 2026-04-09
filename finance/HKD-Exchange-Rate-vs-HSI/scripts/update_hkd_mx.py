#!/usr/bin/env python3
"""
HKD-Exchange-Rate-vs-HSI 数据更新脚本 - 使用 mx-macro-data skill
通过东方财富妙想API获取 USD/HKD 汇率数据并更新到CSV文件
"""

import pandas as pd
import subprocess
import os
import re
from datetime import datetime
from pathlib import Path

# 配置路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')

def log(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def get_last_date(filepath):
    """获取CSV文件的最后日期"""
    try:
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        df.columns = df.columns.str.lower().str.replace('\ufeff', '')
        return pd.to_datetime(df['date']).max()
    except FileNotFoundError:
        return None

def find_latest_mx_csv():
    """查找 mx-macro-data 生成的最新CSV文件"""
    # 可能的输出目录
    possible_dirs = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))), 'miaoxiang', 'mx_macro_data'),
        os.path.join(os.path.dirname(SCRIPT_DIR), '..', '..', 'miaoxiang', 'mx_macro_data'),
        'miaoxiang/mx_macro_data',
        os.path.expanduser('~/miaoxiang/mx_macro_data'),
    ]
    
    for mx_dir in possible_dirs:
        mx_path = Path(mx_dir)
        if mx_path.exists():
            # 查找最新的 daily CSV 文件
            csv_files = list(mx_path.glob('mx_macro_data_*_daily.csv'))
            if csv_files:
                latest = max(csv_files, key=lambda x: x.stat().st_mtime)
                return str(latest)
    
    return None

def fetch_hkd_with_skill():
    """使用 mx-macro-data skill 获取 USD/HKD 汇率数据"""
    log("调用 mx-macro-data skill 获取 USD/HKD 汇率数据...")
    
    try:
        # 获取工作目录（workspace 根目录）
        workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
        skill_script = os.path.join(workspace_dir, 'skills', 'mx-macro-data', 'scripts', 'get_data.py')
        
        # 设置环境变量
        env = os.environ.copy()
        env['MX_MACRO_DATA_OUTPUT_DIR'] = os.path.join(workspace_dir, 'miaoxiang', 'mx_macro_data')
        
        result = subprocess.run(
            ['python', skill_script, '--query', '美元港币汇率日线数据'],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=workspace_dir,
            env=env
        )
        
        if result.returncode != 0:
            log(f"Skill 执行失败: {result.stderr}")
            return None
        
        # 查找生成的CSV文件
        csv_path = find_latest_mx_csv()
        
        if csv_path:
            log(f"找到数据文件: {csv_path}")
            return csv_path
        else:
            log("无法找到生成的CSV文件")
            return None
        
    except Exception as e:
        log(f"调用 skill 失败: {e}")
        return None

def parse_mx_data(csv_path):
    """解析 mx-macro-data 输出的CSV数据"""
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        
        # 查找 USD/HKD 汇率行
        hkd_row = None
        for idx, row in df.iterrows():
            indicator = str(row.get('indicator_name', ''))
            if '美元' in indicator and '港币' in indicator:
                hkd_row = row
                break
        
        # 如果没找到，使用第一行
        if hkd_row is None and len(df) >= 1:
            hkd_row = df.iloc[0]
        
        # 提取日期和数值（跳过前5列的元数据）
        records = []
        date_cols = [col for col in df.columns if col.startswith('20')]
        
        for col in date_cols:
            try:
                date = col
                value_str = str(hkd_row[col])
                
                # 跳过非数值数据（如'-'）
                if value_str == '-' or value_str == 'nan':
                    continue
                    
                # 处理可能的逗号分隔符
                value = float(value_str.replace(',', ''))
                
                # mx-macro-data 返回的是 HKD/USD，需要转换为 USD/HKD
                if value != 0:
                    value = round(1.0 / value, 4)
                
                records.append({
                    'Date': date,
                    'Open': value,
                    'High': value,
                    'Low': value,
                    'Close': value,
                    'Volume': 0.0,
                    'Amount': 0.0,
                    'Amplitude': 0.0,
                    'Pct_Change': 0.0,
                    'Change': 0.0,
                    'Turnover': 0.0
                })
            except Exception as e:
                log(f"解析日期 {col} 失败: {e}")
                continue
        
        result_df = pd.DataFrame(records)
        result_df = result_df.sort_values('Date').reset_index(drop=True)
        return result_df
        
    except Exception as e:
        log(f"解析数据失败: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def update_hkd():
    """更新 USD/HKD 汇率数据"""
    log("="*60)
    log("更新 USD/HKD 汇率数据 (mx-macro-data skill)")
    log("="*60)
    
    filepath = os.path.join(DATA_DIR, 'HKD_USD_Exchange_Rate.csv')
    
    # 获取现有数据最后日期
    last_date = get_last_date(filepath)
    
    if last_date is None:
        log(f"文件不存在: {filepath}")
        log("请使用初始下载脚本获取完整历史数据")
        return False
    
    log(f"现有数据最后日期: {last_date.strftime('%Y-%m-%d')}")
    
    # 使用 skill 获取新数据
    csv_path = fetch_hkd_with_skill()
    
    if csv_path is None:
        log("获取数据失败")
        return False
    
    # 解析数据
    df_new = parse_mx_data(csv_path)
    
    if df_new.empty:
        log("解析数据失败")
        return False
    
    log(f"解析到 {len(df_new)} 条新数据")
    log(f"数据日期范围: {df_new['Date'].min()} 至 {df_new['Date'].max()}")
    
    # 筛选出需要更新的数据（日期大于现有最后日期）
    df_new['date_dt'] = pd.to_datetime(df_new['Date'])
    df_to_add = df_new[df_new['date_dt'] > last_date].copy()
    df_to_add = df_to_add.drop(columns=['date_dt'])
    
    if df_to_add.empty:
        log("无新数据需要更新")
        return True
    
    log(f"需要添加 {len(df_to_add)} 条新记录")
    
    # 读取现有数据
    df_existing = pd.read_csv(filepath, encoding='utf-8-sig')
    
    # 合并
    df_combined = pd.concat([df_existing, df_to_add], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset=['Date'], keep='last')
    df_combined = df_combined.sort_values('Date').reset_index(drop=True)
    
    # 保存
    df_combined.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    log(f"更新完成: {len(df_existing)} -> {len(df_combined)} 条")
    log(f"最新日期: {df_combined['Date'].max()}")
    log(f"最新收盘: {df_combined[df_combined['Date'] == df_combined['Date'].max()]['Close'].values[0]}")
    
    return True

def main():
    """主函数"""
    log("="*60)
    log("HKD-Exchange-Rate-vs-HSI USD/HKD 数据增量更新")
    log(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("="*60)
    
    # 更新 USD/HKD 汇率
    success = update_hkd()
    
    log("\n" + "="*60)
    if success:
        log("更新成功!")
    else:
        log("更新失败!")
    log("="*60)

if __name__ == '__main__':
    main()
