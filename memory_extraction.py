#!/usr/bin/env python3
"""
记忆提炼任务
每天17:25从 daily memory 提炼到 MEMORY.md
"""
import os
import sys
import re
from datetime import datetime, timedelta

# 添加日志工具路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'logs'))
try:
    from task_logger import log_task_status
    TASK_LOGGER_AVAILABLE = True
except ImportError:
    TASK_LOGGER_AVAILABLE = False

def extract_key_memories(memory_file):
    """从 daily memory 提取关键信息"""
    if not os.path.exists(memory_file):
        return []
    
    with open(memory_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取重要事件类型
    key_patterns = [
        r'## \d{2}:\d{2} \[(偏好|系统规则|配置信息|数据更新|项目进展)\].*?(?=## \d{2}:\d{2} |\Z)',
    ]
    
    memories = []
    for pattern in key_patterns:
        matches = re.findall(pattern, content, re.DOTALL)
        memories.extend(matches)
    
    return memories

def main():
    task_id = "memory-extraction"
    task_name = "记忆提炼"
    schedule = "17:25"
    
    # 记录任务开始
    if TASK_LOGGER_AVAILABLE:
        log_task_status(
            task_id=task_id,
            name=task_name,
            schedule=schedule,
            status="running"
        )
    
    try:
        # 获取今天的日记文件
        today = datetime.now().strftime("%Y-%m-%d")
        memory_file = f"memory/{today}.md"
        
        if not os.path.exists(memory_file):
            print(f"⚠️ 今天的日记文件不存在: {memory_file}")
            # 记录任务成功（无内容可提炼）
            if TASK_LOGGER_AVAILABLE:
                log_task_status(
                    task_id=task_id,
                    status="success"
                )
            return
        
        print(f"📖 正在提炼记忆: {memory_file}")
        
        # 提取关键记忆
        memories = extract_key_memories(memory_file)
        
        if memories:
            print(f"✅ 提取到 {len(memories)} 条关键记忆")
            
            # 追加到 MEMORY.md
            memory_md = "MEMORY.md"
            if os.path.exists(memory_md):
                with open(memory_md, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n## {today} 提炼\n\n")
                    for i, mem in enumerate(memories, 1):
                        f.write(f"{i}. {mem[:100]}...\n")
                print(f"✅ 已追加到 {memory_md}")
        else:
            print("ℹ️ 今天没有需要提炼的关键记忆")
        
        # 记录任务成功
        if TASK_LOGGER_AVAILABLE:
            log_task_status(
                task_id=task_id,
                status="success",
                output_file="MEMORY.md"
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
