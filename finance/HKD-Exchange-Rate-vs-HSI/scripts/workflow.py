#!/usr/bin/env python3
"""
HKD-Exchange-Rate-vs-HSI 完整工作流
包含：数据更新 + 可视化生成
"""

import subprocess
import os
from datetime import datetime

# 配置路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')

def log(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def run_command(cmd, cwd=None, description=""):
    """运行命令并返回结果"""
    if description:
        log(f"执行: {description}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=cwd or SCRIPT_DIR
        )
        
        if result.returncode == 0:
            log(f"[OK] {description} 成功")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            log(f"[ERROR] {description} 失败")
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        log(f"[ERROR] {description} 异常: {e}")
        return False

def main():
    """主函数：执行完整工作流"""
    log("="*60)
    log("HKD-Exchange-Rate-vs-HSI 完整工作流")
    log(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("="*60)
    
    # Step 1: 更新 USD/HKD 汇率数据
    log("\n[Step 1/4] 更新 USD/HKD 汇率数据...")
    run_command(
        ['python', 'update_data.py'],
        cwd=SCRIPT_DIR,
        description="USD/HKD 汇率更新"
    )
    
    # Step 2: 更新恒生指数数据（使用 mx-macro-data skill）
    log("\n[Step 2/4] 更新恒生指数数据...")
    run_command(
        ['python', 'update_hsi_mx.py'],
        cwd=SCRIPT_DIR,
        description="恒生指数更新"
    )
    
    # Step 3: 运行可视化脚本（首选 Python，备选 R）
    log("\n[Step 3/4] 生成可视化图表...")
    
    # 首选：Python 可视化
    python_success = run_command(
        ['python', os.path.join(SCRIPT_DIR, 'hkd_hsi_visualization.py')],
        cwd=SCRIPT_DIR,
        description="Python 可视化"
    )
    
    # 备选：R 可视化（如果 Python 失败）
    if not python_success:
        log("Python 可视化失败，尝试 R 可视化...")
        r_path = r'C:\Users\Administrator\scoop\shims\rscript.exe'
        if os.path.exists(r_path):
            run_command(
                [r_path, os.path.join(SCRIPT_DIR, 'hkd_hsi_visualization.R')],
                cwd=DATA_DIR,
                description="R 可视化"
            )
        else:
            log(f"[WARN] Rscript 未找到: {r_path}")
    
    # Step 4: 验证输出
    log("\n[Step 4/4] 验证输出文件...")
    
    output_files = [
        ('HKD_USD_Exchange_Rate.csv', 'USD/HKD 汇率数据'),
        ('Hang_Seng_Index.csv', '恒生指数数据'),
        ('hkd_vs_hsi_dual_axis.html', '可视化图表')
    ]
    
    for filename, description in output_files:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            log(f"[OK] {description}: {filename} ({size:,} bytes)")
        else:
            log(f"[WARN] {description}: {filename} 不存在")
    
    log("\n" + "="*60)
    log("工作流执行完成!")
    log("="*60)

if __name__ == '__main__':
    main()
