#!/usr/bin/env python3
"""
莫大仙岳居阅读任务 - 带内容提取和记忆
每天阅读1份HTML文件，提取关键内容并记录
"""
import os
import glob
import sys
import re
from datetime import datetime

# 添加日志工具路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
try:
    from task_logger import log_task_status
    TASK_LOGGER_AVAILABLE = True
except ImportError:
    TASK_LOGGER_AVAILABLE = False

def extract_content_from_html(file_path):
    """从HTML文件中提取文本内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取标题
        title = "未知标题"
        if '<title>' in content:
            start = content.find('<title>') + 7
            end = content.find('</title>')
            title = content[start:end]
        
        # 移除HTML标签，提取正文
        # 简单处理：移除script和style，然后移除所有标签
        text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)
        
        # 清理空白字符
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        return {
            'title': title,
            'content': text.strip()[:5000]  # 限制长度
        }
    except Exception as e:
        return {'title': '读取失败', 'content': str(e)}

def extract_key_insights(text):
    """提取关键投资观点"""
    insights = []
    
    # 常见的投资哲学关键词
    patterns = [
        r'([^。]*?(?:强制函数|戴维斯|思维模型|摩尔定律|安全边际|复利|杠杆)[^。]*。)',
        r'([^。]*?(?:风险|收益|利润|估值|市场)[^。]{0,30}(?:大于|高于|优于|关键)[^。]*。)',
        r'"([^"]{10,100})"',  # 引用的名言
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        insights.extend(matches[:3])  # 每种类型最多3条
    
    return list(set(insights))[:5]  # 去重，最多5条

def save_reading_notes(filename, title, insights):
    """保存阅读笔记到 memory"""
    today = datetime.now().strftime("%Y-%m-%d")
    memory_file = f"memory/{today}.md"
    
    # 确保目录存在
    os.makedirs("memory", exist_ok=True)
    
    # 追加到今日日记
    with open(memory_file, 'a', encoding='utf-8') as f:
        f.write(f"\n\n## {datetime.now().strftime('%H:%M')} [阅读] 莫大仙岳居\n\n")
        f.write(f"**文件**: {filename}\n\n")
        f.write(f"**标题**: {title}\n\n")
        f.write("**关键观点**:\n")
        for i, insight in enumerate(insights, 1):
            f.write(f"{i}. {insight}\n")
        f.write("\n")

def main():
    task_id = "moyu-reading-am" if "10" in sys.argv else "moyu-reading-pm"
    task_name = "莫大仙岳居阅读-上午" if task_id == "moyu-reading-am" else "莫大仙岳居阅读-下午"
    
    # 记录任务开始
    if TASK_LOGGER_AVAILABLE:
        log_task_status(
            task_id=task_id,
            name=task_name,
            schedule="10:00" if task_id == "moyu-reading-am" else "15:00",
            status="running"
        )
    
    try:
        # 获取所有html文件
        folder = r"F:\穷爸爸富爸爸\分享文件"
        
        if not os.path.exists(folder):
            raise FileNotFoundError(f"文件夹不存在: {folder}")
        
        files = glob.glob(os.path.join(folder, "*.html"))
        
        if not files:
            raise FileNotFoundError(f"未找到HTML文件: {folder}")
        
        files.sort(key=os.path.getmtime)
        
        # 读取第一个未读文件
        target_file = files[0]
        filename = os.path.basename(target_file)
        
        print(f"正在读取: {filename}")
        
        # 提取内容
        result = extract_content_from_html(target_file)
        title = result['title']
        content = result['content']
        
        print(f"标题: {title}")
        print(f"内容长度: {len(content)} 字符")
        
        # 提取关键观点
        insights = extract_key_insights(content)
        print(f"\n提取到 {len(insights)} 条关键观点:")
        for i, insight in enumerate(insights, 1):
            print(f"{i}. {insight[:80]}...")
        
        # 保存阅读笔记
        save_reading_notes(filename, title, insights)
        print(f"\n[OK] 阅读笔记已保存到 memory/{datetime.now().strftime('%Y-%m-%d')}.md")
        
        # 记录任务成功
        if TASK_LOGGER_AVAILABLE:
            log_task_status(
                task_id=task_id,
                status="success"
            )
        
        print(f"\n[OK] {task_name} 完成")
        
    except Exception as e:
        # 记录任务失败
        if TASK_LOGGER_AVAILABLE:
            log_task_status(
                task_id=task_id,
                status="failed",
                error=str(e)
            )
        print(f"\n[ERROR] 任务失败: {e}")
        raise

if __name__ == "__main__":
    main()
