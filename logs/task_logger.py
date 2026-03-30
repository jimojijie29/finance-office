"""
任务状态日志工具
用于记录和检查定时任务执行状态
"""
import json
import os
from datetime import datetime, timezone, timedelta

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "task-status.json")

def log_task_status(task_id, name=None, schedule=None, status=None, output_file=None, error=None):
    """记录任务状态
    
    Args:
        task_id: 任务唯一标识
        name: 任务显示名称（可选，首次记录时需提供）
        schedule: 计划执行时间 HH:MM（可选，首次记录时需提供）
        status: 状态 - running/success/failed/skipped
        output_file: 输出文件路径（可选）
        error: 错误信息（失败时）
    """
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
    
    if name:
        task["name"] = name
    if schedule:
        task["schedule"] = schedule
    if status:
        task["status"] = status
        task["last_run"] = now
    if output_file is not None:
        task["output_file"] = output_file
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

def get_task_status(task_id):
    """获取任务状态"""
    log_path = os.path.abspath(LOG_FILE)
    if not os.path.exists(log_path):
        return None
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data["tasks"].get(task_id)
    except (json.JSONDecodeError, IOError):
        return None

def check_task_health(task_id, max_delay_minutes=60):
    """检查任务健康状态
    
    Returns:
        dict: {"healthy": bool, "reason": str}
    """
    task = get_task_status(task_id)
    if not task:
        return {"healthy": False, "reason": "无状态记录"}
    
    # 检查状态
    if task.get("status") == "failed":
        error_msg = task.get('error', '未知错误')
        return {"healthy": False, "reason": f"上次执行失败: {error_msg}"}
    
    if task.get("status") == "running":
        # 检查是否运行太久（超过2小时）
        last_run = task.get("last_run")
        if last_run:
            try:
                last_run_time = datetime.fromisoformat(last_run)
                if datetime.now(timezone.utc).astimezone() - last_run_time > timedelta(hours=2):
                    return {"healthy": False, "reason": "任务运行超过2小时，可能卡住"}
            except:
                pass
        return {"healthy": True, "reason": "任务正在运行中"}
    
    # 检查输出文件
    output_file = task.get("output_file")
    if output_file:
        # 处理 YYYY-MM-DD 占位符
        today = datetime.now().strftime("%Y-%m-%d")
        output_file = output_file.replace("YYYY-MM-DD", today)
        
        if not os.path.exists(output_file):
            return {"healthy": False, "reason": f"输出文件不存在: {output_file}"}
        
        # 检查文件修改时间
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(output_file))
            mtime = mtime.replace(tzinfo=None)  # 转为本地时间比较
            
            # 获取今天的计划执行时间
            schedule_time = task.get("schedule", "00:00")
            hour, minute = map(int, schedule_time.split(":"))
            
            # 计算预期完成时间（计划时间 + 延迟容忍）
            now = datetime.now()
            expected_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if expected_time > now:
                # 计划时间还没到，检查昨天的
                expected_time = expected_time - timedelta(days=1)
            
            if mtime < expected_time:
                return {"healthy": False, "reason": f"输出文件过期 (最后修改: {mtime.strftime('%Y-%m-%d %H:%M')})"}
        except Exception as e:
            return {"healthy": False, "reason": f"检查文件时间出错: {e}"}
    
    return {"healthy": True}

def check_all_tasks():
    """检查所有任务健康状态
    
    Returns:
        list: 有问题的任务列表
    """
    log_path = os.path.abspath(LOG_FILE)
    if not os.path.exists(log_path):
        return [{"task_id": "all", "task_name": "所有任务", "healthy": False, "reason": "无任务日志文件"}]
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return [{"task_id": "all", "task_name": "所有任务", "healthy": False, "reason": f"读取日志文件失败: {e}"}]
    
    issues = []
    for task_id, task in data.get("tasks", {}).items():
        health = check_task_health(task_id)
        if not health["healthy"]:
            issues.append({
                "task_id": task_id,
                "task_name": task.get("name", task_id),
                "healthy": False,
                "reason": health["reason"]
            })
    
    return issues

def format_task_report(issues):
    """格式化任务检查报告"""
    if not issues:
        return None
    
    lines = ["[!] 定时任务异常:"]
    for issue in issues:
        lines.append(f"- {issue['task_name']}: {issue['reason']}")
    
    return "\n".join(lines)

if __name__ == "__main__":
    # 测试
    print("检查所有任务...")
    issues = check_all_tasks()
    if issues:
        print(format_task_report(issues))
    else:
        print("所有任务正常")
