#!/usr/bin/env python3
"""
查询其他期限中国国债收益率数据
==========================
查询 1年、2年、5年、10年、20年、30年 期限的中国国债数据
"""

import pandas as pd
import sys
import os
import asyncio
import re
from datetime import datetime, timedelta
from pathlib import Path

# 配置
MX_MACRO_SKILL_PATH = r'D:\OpenClawData\.openclaw\workspace\skills\mx-macro-data'
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))

# 要查询的期限
MATURITIES = ['1年', '2年', '5年', '10年', '20年', '30年']


def log(message):
    """打印带时间戳的日志"""
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
    except UnicodeEncodeError:
        # 如果编码失败，过滤掉非ASCII字符
        safe_message = message.encode('ascii', 'ignore').decode('ascii')
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {safe_message}")


async def fetch_single_maturity_async(maturity):
    """获取单个期限的数据"""
    log(f"查询 {maturity}期 数据...")
    
    # 构建查询
    query = f"中国{maturity}期国债收益率日度数据，最近3年"
    
    try:
        # 添加 mx-macro-data 路径
        if MX_MACRO_SKILL_PATH not in sys.path:
            sys.path.insert(0, MX_MACRO_SKILL_PATH)
        
        # 导入 mx-macro-data 模块
        from scripts.get_data import query_mx_macro_data
        
        # 创建临时输出目录
        temp_dir = os.path.join(WORKING_DIR, 'temp_query', maturity)
        os.makedirs(temp_dir, exist_ok=True)
        
        # 设置环境变量
        os.environ['MX_MACRO_DATA_OUTPUT_DIR'] = temp_dir
        
        # 调用查询函数
        result = await query_mx_macro_data(query, output_dir=Path(temp_dir))
        
        if 'error' in result:
            log(f"  {maturity}期 查询出错: {result['error']}")
            return None
        
        if 'csv_paths' in result and len(result['csv_paths']) > 0:
            csv_file = result['csv_paths'][0]
            log(f"  [OK] {maturity} data retrieved: {csv_file}")
            
            # 读取并显示数据摘要
            try:
                df = pd.read_csv(csv_file, encoding='utf-8')
                log(f"  数据形状: {df.shape}")
                log(f"  列名: {list(df.columns[:5])}...")
                return {'maturity': maturity, 'file': csv_file, 'df': df}
            except Exception as e:
                log(f"  读取数据失败: {e}")
                return {'maturity': maturity, 'file': csv_file, 'df': None}
        else:
            log(f"  [X] {maturity} no data retrieved")
            return None
            
    except Exception as e:
        log(f"  {maturity}期 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def query_all_maturities():
    """查询所有期限"""
    print("="*60)
    print("查询中国国债各期限收益率数据")
    print("="*60)
    
    tasks = []
    for maturity in MATURITIES:
        tasks.append(fetch_single_maturity_async(maturity))
    
    results = await asyncio.gather(*tasks)
    
    # 过滤掉 None 结果
    valid_results = [r for r in results if r is not None]
    
    print("\n" + "="*60)
    print("查询结果汇总")
    print("="*60)
    
    for result in valid_results:
        maturity = result['maturity']
        df = result.get('df')
        if df is not None:
            print(f"\n{maturity}期:")
            print(f"  文件: {result['file']}")
            print(f"  记录数: {len(df)}")
            print(f"  列数: {len(df.columns)}")
            
            # 尝试提取最新收益率
            date_cols = [col for col in df.columns if re.match(r'\d{4}-\d{2}(-\d{2})?', str(col))]
            if date_cols:
                latest_col = date_cols[-1]
                if 'indicator_name' in df.columns:
                    for idx, row in df.iterrows():
                        indicator = str(row.get('indicator_name', ''))
                        value = row.get(latest_col)
                        if pd.notna(value) and value != '-' and value != '':
                            print(f"  最新数据 ({latest_col}): {indicator} = {value}%")
                            break
    
    print("\n" + "="*60)
    print(f"成功获取: {len(valid_results)}/{len(MATURITIES)} 个期限")
    print("="*60)
    
    return valid_results


def cleanup_temp():
    """清理临时文件"""
    temp_dir = os.path.join(WORKING_DIR, 'temp_query')
    if os.path.exists(temp_dir):
        import shutil
        shutil.rmtree(temp_dir)
        log("临时文件已清理")


def main():
    """主函数"""
    try:
        results = asyncio.run(query_all_maturities())
        
        if len(results) > 0:
            log(f"成功获取 {len(results)} 个期限的数据")
            
            # 保存结果信息
            summary_file = os.path.join(WORKING_DIR, 'query_results_summary.txt')
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("中国国债收益率数据查询结果\n")
                f.write("="*60 + "\n\n")
                f.write(f"查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"查询期限: {', '.join(MATURITIES)}\n")
                f.write(f"成功获取: {len(results)}/{len(MATURITIES)}\n\n")
                
                for result in results:
                    maturity = result['maturity']
                    f.write(f"\n{maturity}期:\n")
                    f.write(f"  文件: {result['file']}\n")
                    if result.get('df') is not None:
                        f.write(f"  记录数: {len(result['df'])}\n")
            
            log(f"结果摘要已保存: {summary_file}")
        else:
            log("未获取到任何数据")
            
    finally:
        cleanup_temp()


if __name__ == "__main__":
    main()
