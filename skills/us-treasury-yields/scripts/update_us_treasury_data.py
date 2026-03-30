#!/usr/bin/env python3
"""
美国国债收益率数据更新工作流
==========================
整合数据获取、处理、合并和可视化的完整流程

使用方法:
    python update_us_treasury_data.py

功能:
    1. 从 mx-macro-data 获取最新数据
    2. 处理并合并到现有数据文件
    3. 生成更新的可视化 HTML
"""

import pandas as pd
import subprocess
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# ============ 配置 ============
CONFIG = {
    # 数据文件路径
    'data_file': 'data/us_treasury_yields_all_terms.csv',
    
    # mx-macro-data 技能路径
    'mx_macro_skill_path': r'D:\OpenClawData\.openclaw\workspace\skills\mx-macro-data',
    
    # R 可视化脚本路径
    'r_script': 'scripts/us_treasury_workflow_v2.R',
    
    # 输出 HTML 文件
    'output_html': 'data/us_treasury_all_terms.html',
    
    # 工作目录（脚本所在目录的父目录）
    'working_dir': os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    
    # 数据期限列表
    'maturities': ['1月', '3月', '6月', '1年', '2年', '3年', '5年', '7年', '10年', '20年', '30年'],
    
    # 指标名称映射（用于解析 mx-macro-data 返回的数据）
    'indicator_mapping': {
        '美国:国债收益率:1月(%)': 'X1月',
        '美国:国债收益率:1个月(%)': 'X1月',
        '美国:国债收益率:3月(%)': 'X3月',
        '美国:国债收益率:3个月(%)': 'X3月',
        '美国:国债收益率:6月(%)': 'X6月',
        '美国:国债收益率:6个月(%)': 'X6月',
        '美国:国债收益率:1年(%)': 'X1年',
        '美国:国债收益率:二级市场:1年(%)': 'X1年',
        '美国:国债收益率:2年(%)': 'X2年',
        '美国:国债收益率:3年(%)': 'X3年',
        '美国:国债收益率:5年(%)': 'X5年',
        '美国:国债收益率:7年(%)': 'X7年',
        '美国:国债收益率:10年(%)': 'X10年',
        '美国:国债收益率:20年(%)': 'X20年',
        '美国:国债收益率:30年(%)': 'X30年',
    }
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
        start_date = datetime(2020, 4, 1)
        log("未找到现有数据，将从2020-04-01开始获取")
    
    # 结束日期为今天
    end_date = datetime.now()
    
    return start_date, end_date


def fetch_new_data(start_date, end_date):
    """使用 mx-macro-data 获取新数据"""
    log(f"获取数据: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    
    # 构建查询
    maturities_str = '、'.join(CONFIG['maturities'])
    query = f"美国国债收益率各期限数据，从{start_date.strftime('%Y年%m月')}到{end_date.strftime('%Y年%m月')}，包括{maturities_str}期"
    
    log(f"查询: {query}")
    
    # 执行 mx-macro-data 查询
    skill_path = CONFIG['mx_macro_skill_path']
    cmd = [
        'python',
        os.path.join(skill_path, 'scripts', 'get_data.py'),
        '--query', query
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=skill_path)
        
        if result.returncode != 0:
            log(f"错误: 数据获取失败")
            log(f"stderr: {result.stderr}")
            return None
        
        # 解析输出，找到 CSV 文件路径
        output = result.stdout
        log(f"mx-macro-data 输出:\n{output}")
        
        # 从输出中提取 CSV 路径
        csv_path = None
        for line in output.split('\n'):
            if 'daily.csv' in line and 'CSV:' in line:
                # 提取路径
                start = line.find("['") + 2
                end = line.find("']")
                if start > 1 and end > start:
                    csv_path = line[start:end]
                    break
        
        if not csv_path:
            log("错误: 无法从输出中提取 CSV 路径")
            return None
        
        log(f"获取到数据文件: {csv_path}")
        return csv_path
        
    except Exception as e:
        log(f"错误: 执行查询时发生异常: {e}")
        return None


def process_mx_data(csv_path):
    """处理 mx-macro-data 返回的 CSV 数据"""
    log(f"处理数据文件: {csv_path}")
    
    try:
        df_raw = pd.read_csv(csv_path, encoding='utf-8')
        log(f"原始数据形状: {df_raw.shape}")
        
        # 获取日期列
        date_cols = df_raw.columns[5:].tolist()
        log(f"日期列数量: {len(date_cols)}")
        
        # 创建结果数据
        result_data = []
        
        for idx, row in df_raw.iterrows():
            indicator_name = row['indicator_name']
            
            # 跳过通胀保值债券(TIPS)
            if '通胀保值' in indicator_name:
                continue
            
            # 映射到标准列名
            col_name = CONFIG['indicator_mapping'].get(indicator_name)
            
            if col_name:
                for date_col in date_cols:
                    try:
                        value = float(row[date_col])
                        result_data.append({
                            'date': date_col,
                            'maturity': col_name,
                            'yield': value
                        })
                    except (ValueError, TypeError):
                        continue
        
        # 转换为宽格式
        df_long = pd.DataFrame(result_data)
        if df_long.empty:
            log("警告: 没有提取到有效数据")
            return None
        
        df_wide = df_long.pivot_table(
            index='date', 
            columns='maturity', 
            values='yield'
        ).reset_index()
        
        # 确保列顺序
        col_order = ['date'] + [f'X{m}' for m in CONFIG['maturities']]
        available_cols = [col for col in col_order if col in df_wide.columns]
        df_wide = df_wide[available_cols]
        
        # 排序
        df_wide = df_wide.sort_values('date').reset_index(drop=True)
        
        log(f"处理后数据形状: {df_wide.shape}")
        log(f"日期范围: {df_wide['date'].min()} 至 {df_wide['date'].max()}")
        
        return df_wide
        
    except Exception as e:
        log(f"错误: 处理数据时发生异常: {e}")
        import traceback
        traceback.print_exc()
        return None


def merge_with_existing(new_df):
    """将新数据与现有数据合并"""
    working_dir = get_working_dir()
    data_file = os.path.join(working_dir, CONFIG['data_file'])
    
    if not os.path.exists(data_file):
        log(f"现有数据文件不存在，直接使用新数据")
        return new_df
    
    log(f"读取现有数据: {data_file}")
    df_existing = pd.read_csv(data_file)
    log(f"现有数据: {len(df_existing)} 行")
    
    # 合并数据
    df_combined = pd.concat([df_existing, new_df], ignore_index=True)
    
    # 去重（保留最新数据）
    df_combined = df_combined.drop_duplicates(subset=['date'], keep='last')
    
    # 排序
    df_combined = df_combined.sort_values('date').reset_index(drop=True)
    
    log(f"合并后数据: {len(df_combined)} 行")
    
    return df_combined


def validate_data(df):
    """验证数据质量"""
    log("验证数据质量...")
    
    issues = []
    
    # 检查10年期数据
    if 'X10年' in df.columns:
        min_10y = df['X10年'].min()
        max_10y = df['X10年'].max()
        
        log(f"10年期收益率范围: {min_10y:.2f}% - {max_10y:.2f}%")
        
        if min_10y < 0:
            issues.append(f"警告: 10年期收益率出现负值 ({min_10y:.2f}%)，可能包含TIPS数据")
        
        if max_10y > 10:
            issues.append(f"警告: 10年期收益率异常高 ({max_10y:.2f}%)")
    
    # 检查日期范围
    date_range = pd.to_datetime(df['date'])
    days_span = (date_range.max() - date_range.min()).days
    log(f"数据时间跨度: {days_span} 天")
    
    # 检查缺失值
    for col in df.columns:
        if col != 'date':
            null_count = df[col].isnull().sum()
            if null_count > 0:
                log(f"  {col}: {null_count} 个缺失值")
    
    if issues:
        for issue in issues:
            log(issue)
    else:
        log("数据验证通过")
    
    return len(issues) == 0


def save_data(df):
    """保存数据到 CSV"""
    working_dir = get_working_dir()
    data_file = os.path.join(working_dir, CONFIG['data_file'])
    
    # 确保数据目录存在
    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    
    temp_file = data_file + '.tmp'
    
    # 先保存到临时文件
    df.to_csv(temp_file, index=False, encoding='utf-8-sig')
    
    # 尝试替换原文件
    try:
        if os.path.exists(data_file):
            os.remove(data_file)
        os.rename(temp_file, data_file)
        log(f"数据已保存: {data_file}")
    except PermissionError:
        # 如果无法删除原文件，保存为.new文件并提示用户
        new_file = data_file + '.new'
        if os.path.exists(new_file):
            os.remove(new_file)
        os.rename(temp_file, new_file)
        log(f"警告: 原文件被占用，数据已保存为: {new_file}")
        log(f"请手动替换: 删除 {data_file}，然后将 {new_file} 重命名为 {data_file}")
    
    # 输出统计信息
    log(f"\n数据统计:")
    log(f"  总行数: {len(df)}")
    log(f"  日期范围: {df['date'].min()} 至 {df['date'].max()}")
    log(f"  包含期限: {', '.join([c for c in df.columns if c != 'date'])}")


def generate_visualization():
    """运行 R 脚本生成可视化"""
    working_dir = get_working_dir()
    r_script = os.path.join(working_dir, CONFIG['r_script'])
    
    if not os.path.exists(r_script):
        log(f"警告: R 脚本不存在: {r_script}")
        return False
    
    log(f"生成可视化: {r_script}")
    
    try:
        result = subprocess.run(
            ['Rscript', r_script],
            capture_output=True,
            text=True,
            cwd=working_dir
        )
        
        if result.returncode != 0:
            log(f"R 脚本执行失败")
            log(f"stderr: {result.stderr}")
            return False
        
        log(f"可视化生成成功: {CONFIG['output_html']}")
        log(f"R 输出:\n{result.stdout}")
        return True
        
    except Exception as e:
        log(f"错误: 执行 R 脚本时发生异常: {e}")
        return False


def main():
    """主流程"""
    log("=" * 60)
    log("美国国债收益率数据更新工作流")
    log("=" * 60)
    
    # 步骤1: 确定日期范围
    start_date, end_date = get_date_range()
    
    # 如果开始日期大于结束日期，说明数据已是最新
    if start_date > end_date:
        log("数据已是最新，无需更新")
        return
    
    # 步骤2: 获取新数据
    csv_path = fetch_new_data(start_date, end_date)
    if not csv_path:
        log("数据获取失败，终止流程")
        return
    
    # 步骤3: 处理数据
    new_df = process_mx_data(csv_path)
    if new_df is None:
        log("数据处理失败，终止流程")
        return
    
    # 步骤4: 合并数据
    combined_df = merge_with_existing(new_df)
    
    # 步骤5: 验证数据
    if not validate_data(combined_df):
        log("数据验证未通过，请检查")
    
    # 步骤6: 保存数据
    save_data(combined_df)
    
    # 步骤7: 生成可视化
    generate_visualization()
    
    log("=" * 60)
    log("更新完成!")
    log("=" * 60)


if __name__ == '__main__':
    main()
