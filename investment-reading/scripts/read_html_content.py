import os
import glob
import re

# 获取所有html文件并按修改时间排序
folder = r"F:\穷爸爸富爸爸\分享文件"
files = glob.glob(os.path.join(folder, "*.html"))
files.sort(key=os.path.getmtime)

# 读取第3个文件（索引2）
target_file = files[2]
print(f"读取文件: {os.path.basename(target_file)}")

try:
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取文本内容（去除HTML标签）
    text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '\n', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # 打印前3000字符
    print("\n文件内容预览：")
    print(text[:3000])
    
except Exception as e:
    print(f"错误: {e}")
