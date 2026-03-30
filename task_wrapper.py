#!/usr/bin/env python3
"""
通用任务包装器 - 为任意命令添加状态记录
用法: python task_wrapper.py <task_id> <task_name> <schedule> <command> [args...]

示例:
  python task_wrapper.py ai-diary "AI日记整理" "21:00" python -c "print('diary done')"
  python task_wrapper.py memory-extraction "记忆提炼" "17:25" python memory/merge_to_memory.py
"""
import subprocess
import sys
import os

# 添加日志工具路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'logs'))
try:
    from task_logger import log_task_status
    TASK_LOGGER_AVAILABLE = True
except ImportError:
    TASK_LOGGER_AVAILABLE = False
    print("Warning: task_logger not available")

def main():
    if len(sys.argv) < 5:
        print("Usage: python task_wrapper.py <task_id> <task_name> <schedule> <command> [args...]")
        print("Example: python task_wrapper.py ai-diary 'AI日记整理' '21:00' python diary_script.py")
        sys.exit(1)
    
    task_id = sys.argv[1]
    task_name = sys.argv[2]
    schedule = sys.argv[3]
    command = sys.argv[4]
    args = sys.argv[5:]
    
    # 记录任务开始
    if TASK_LOGGER_AVAILABLE:
        log_task_status(
            task_id=task_id,
            name=task_name,
            schedule=schedule,
            status="running"
        )
    
    try:
        # 执行命令
        result = subprocess.run(
            [command] + args,
            capture_output=True,
            text=True,
            check=True
        )
        
        # 输出命令的输出
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # 记录任务成功
        if TASK_LOGGER_AVAILABLE:
            log_task_status(
                task_id=task_id,
                status="success"
            )
        
        print(f"\n✅ {task_name} 完成")
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or str(e)
        
        # 记录任务失败
        if TASK_LOGGER_AVAILABLE:
            log_task_status(
                task_id=task_id,
                status="failed",
                error=error_msg[:200]
            )
        
        print(f"\n❌ {task_name} 失败: {error_msg}")
        sys.exit(1)
    except Exception as e:
        # 记录任务失败
        if TASK_LOGGER_AVAILABLE:
            log_task_status(
                task_id=task_id,
                status="failed",
                error=str(e)[:200]
            )
        
        print(f"\n❌ {task_name} 失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
