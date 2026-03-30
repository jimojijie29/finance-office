# Task Status Logging System

## 状态文件位置
`logs/task-status.json`

## 格式规范

```json
{
  "version": "1.0",
  "last_updated": "2026-03-27T23:36:00+08:00",
  "tasks": {
    "a-stock-market-update": {
      "name": "A股两市行情数据每日更新",
      "schedule": "09:30",
      "last_run": "2026-03-27T09:30:00+08:00",
      "status": "success",
      "output_file": "finance/tushare/market_combined_data.csv",
      "error": null,
      "retry_count": 0
    },
    "journal-papers-daily": {
      "name": "期刊论文日报",
      "schedule": "09:30",
      "last_run": "2026-03-27T09:30:00+08:00",
      "status": "failed",
      "output_file": "journal-papers-daily.md",
      "error": "API rate limit exceeded",
      "retry_count": 2
    }
  }
}
```

## 状态字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 任务显示名称 |
| `schedule` | string | 计划执行时间 (HH:MM) |
| `last_run` | ISO8601 | 上次执行时间 |
| `status` | enum | `success` / `failed` / `running` / `skipped` |
| `output_file` | string | 任务输出文件路径（用于检查） |
| `error` | string | 错误信息（失败时） |
| `retry_count` | int | 重试次数 |

## Python 日志工具函数

```python
import json
import os
from datetime import datetime, timezone

LOG_FILE = "logs/task-status.json"

def log_task_status(task_id, name, schedule, status, output_file=None, error=None):
    """记录任务状态"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    # 读取现有日志
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {"version": "1.0", "last_updated": "", "tasks": {}}
    
    # 更新任务状态
    now = datetime.now(timezone.utc).astimezone().isoformat()
    
    if task_id not in data["tasks"]:
        data["tasks"][task_id] = {}
    
    task = data["tasks"][task_id]
    task["name"] = name
    task["schedule"] = schedule
    task["last_run"] = now
    task["status"] = status
    
    if output_file:
        task["output_file"] = output_file
    if error:
        task["error"] = error
    
    # 重试计数
    if status == "failed":
        task["retry_count"] = task.get("retry_count", 0) + 1
    elif status == "success":
        task["retry_count"] = 0
    
    data["last_updated"] = now
    
    # 保存
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_task_status(task_id):
    """获取任务状态"""
    if not os.path.exists(LOG_FILE):
        return None
    
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data["tasks"].get(task_id)

def check_task_health(task_id, max_delay_minutes=30):
    """检查任务健康状态"""
    from datetime import datetime, timedelta
    
    task = get_task_status(task_id)
    if not task:
        return {"healthy": False, "reason": "No status record"}
    
    # 检查状态
    if task["status"] == "failed":
        return {"healthy": False, "reason": f"Last run failed: {task.get('error', 'Unknown')}"}
    
    # 检查输出文件
    if task.get("output_file"):
        if not os.path.exists(task["output_file"]):
            return {"healthy": False, "reason": "Output file missing"}
        
        # 检查文件修改时间
        mtime = datetime.fromtimestamp(os.path.getmtime(task["output_file"]))
        if datetime.now() - mtime > timedelta(minutes=max_delay_minutes):
            return {"healthy": False, "reason": f"Output file stale (last modified: {mtime})"}
    
    return {"healthy": True}
```

## 在任务脚本中使用

```python
# 任务开始时
log_task_status(
    task_id="a-stock-market-update",
    name="A股两市行情数据每日更新",
    schedule="09:30",
    status="running"
)

try:
    # 执行任务...
    
    # 任务成功
    log_task_status(
        task_id="a-stock-market-update",
        name="A股两市行情数据每日更新",
        schedule="09:30",
        status="success",
        output_file="finance/tushare/market_combined_data.csv"
    )
except Exception as e:
    # 任务失败
    log_task_status(
        task_id="a-stock-market-update",
        name="A股两市行情数据每日更新",
        schedule="09:30",
        status="failed",
        error=str(e)
    )
```

## Heartbeat 检查脚本

```python
def check_all_tasks():
    """Heartbeat 调用此函数检查所有任务"""
    if not os.path.exists(LOG_FILE):
        return [{"task": "all", "healthy": False, "reason": "No task log file"}]
    
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    issues = []
    for task_id, task in data["tasks"].items():
        health = check_task_health(task_id)
        if not health["healthy"]:
            issues.append({
                "task": task["name"],
                "healthy": False,
                "reason": health["reason"]
            })
    
    return issues
```

---

## 实施步骤

1. 创建 `logs/` 目录
2. 将日志函数添加到常用任务脚本
3. 更新定时任务，包装状态记录
4. 更新 HEARTBEAT.md，调用检查函数

需要我现在开始实施吗？
