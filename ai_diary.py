#!/usr/bin/env python3
"""
AI日记整理任务
每天21:00自动整理当日记录
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
    task_id = "ai-diary"
    task_name = "AI日记整理"
    schedule = "21:00"
    
    # 记录任务开始
    if TASK_LOGGER_AVAILABLE:
        log_task_status(
            task_id=task_id,
            name=task_name,
            schedule=schedule,
            status="running"
        )
    
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        memory_file = f"memory/{today}.md"
        
        # 检查今天是否已有日记
        if os.path.exists(memory_file):
            print(f"✅ 今天的日记已存在: {memory_file}")
            
            # 记录任务成功
            if TASK_LOGGER_AVAILABLE:
                log_task_status(
                    task_id=task_id,
                    status="success",
                    output_file=memory_file
                )
            return
        
        # 创建今天的日记文件（基础模板）
        os.makedirs("memory", exist_ok=True)
        
        with open(memory_file, 'w', encoding='utf-8') as f:
            f.write(f"# {today} 记忆日志\n\n")
            f.write(f"*自动创建于 {datetime.now().strftime('%H:%M')}*\n\n")
            f.write("## 今日待记录\n\n")
            f.write("- [ ] 重要决策\n")
            f.write("- [ ] 项目进展\n")
            f.write("- [ ] 新发现/偏好\n")
            f.write("- [ ] 需要记住的信息\n\n")
        
        print(f"✅ 已创建日记文件: {memory_file}")
        
        # 记录任务成功
        if TASK_LOGGER_AVAILABLE:
            log_task_status(
                task_id=task_id,
                status="success",
                output_file=memory_file
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
