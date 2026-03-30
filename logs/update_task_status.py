#!/usr/bin/env python3
"""
任务状态更新工具 - 供其他脚本调用
用法: python update_task_status.py <task_id> <status> [error_message]
"""
import json
import os
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'task-status.json')

def update_task_status(task_id, status, error=None):
    """更新任务状态"""
    log_path = os.path.abspath(LOG_FILE)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # 读取现有日志
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            data = {"version": "1.0", "last_updated": "", "tasks": {}}
    else:
        data = {"version": "1.0", "last_updated": "", "tasks": {}}
    
    # 更新任务状态
    now = datetime.now(timezone.utc).astimezone().isoformat()
    
    if task_id not in data["tasks"]:
        data["tasks"][task_id] = {}
    
    task = data["tasks"][task_id]
    task["status"] = status
    task["last_run"] = now
    
    if error is not None:
        task["error"] = error
    
    # 重试计数
    if status == "failed":
        task["retry_count"] = task.get("retry_count", 0) + 1
    elif status == "success":
        task["retry_count"] = 0
    
    data["last_updated"] = now
    
    # 保存
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Task {task_id} status updated: {status}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python update_task_status.py <task_id> <status> [error_message]")
        print("Example: python update_task_status.py a-stock-market-update success")
        sys.exit(1)
    
    task_id = sys.argv[1]
    status = sys.argv[2]
    error = sys.argv[3] if len(sys.argv) > 3 else None
    
    update_task_status(task_id, status, error)
