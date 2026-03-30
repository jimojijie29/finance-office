import os
import glob

# 获取所有html文件并按修改时间排序
folder = r"F:\穷爸爸富爸爸\分享文件"
files = glob.glob(os.path.join(folder, "*.html"))
files.sort(key=os.path.getmtime)

# 读取第3个文件（索引2）
target_file = files[2]

# 将内容写入临时文件，避免终端编码问题
output_file = "temp_html_content.txt"

try:
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 保存到临时文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"内容已保存到: {output_file}")
    print(f"文件大小: {len(content)} 字符")
    
except Exception as e:
    print(f"错误: {e}")
