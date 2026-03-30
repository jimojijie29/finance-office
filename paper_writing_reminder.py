#!/usr/bin/env python3
"""
论文写作提醒任务
每天20:00提醒用户进行论文写作
"""
import os
import sys
from datetime import datetime

# 添加日志工具路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'logs'))
try:
    from task_logger import log_task_status
    TASK_LOGGER_AVAILABLE = True
except ImportError:
    TASK_LOGGER_AVAILABLE = False

def main():
    task_id = "paper-writing-reminder"
    task_name = "论文写作提醒"
    schedule = "20:00"
    
    # 记录任务开始
    if TASK_LOGGER_AVAILABLE:
        log_task_status(
            task_id=task_id,
            name=task_name,
            schedule=schedule,
            status="running"
        )
    
    try:
        # 检查今天的日记是否已创建（作为写作是否开始的参考）
        today = datetime.now().strftime("%Y-%m-%d")
        memory_file = f"memory/{today}.md"
        
        writing_started = False
        if os.path.exists(memory_file):
            with open(memory_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 检查是否有论文写作相关内容
                if '论文' in content or '写作' in content or 'SCI' in content:
                    writing_started = True
        
        # 输出提醒信息
        print("=" * 60)
        print("📝 论文写作提醒")
        print("=" * 60)
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"项目: 诺丽果SCI论文")
        print(f"目标: JCR Q1")
        print("-" * 60)
        
        if writing_started:
            print("✅ 今天已开始论文写作")
        else:
            print("⚠️ 今天尚未开始论文写作")
            print("建议: 立即开始写作，每天至少200字")
        
        print("=" * 60)
        
        # 记录任务成功
        if TASK_LOGGER_AVAILABLE:
            log_task_status(
                task_id=task_id,
                status="success"
            )
        
    except Exception as e:
        # 记录任务失败
        if TASK_LOGGER_AVAILABLE:
            log_task_status(
                task_id=task_id,
                status="failed",
                error=str(e)
            )
        print(f"\n❌ 任务失败: {e}")
        raise

if __name__ == "__main__":
    main()
