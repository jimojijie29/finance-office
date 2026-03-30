import os
import glob

# 获取所有html文件并按修改时间排序
folder = r"F:\穷爸爸富爸爸\分享文件"
files = glob.glob(os.path.join(folder, "*.html"))
files.sort(key=os.path.getmtime)

# 打印前10个文件
print("前10个HTML文件（按时间排序）：")
for i, f in enumerate(files[:10]):
    print(f"{i+1}. {os.path.basename(f)}")

# 读取第3个文件（索引2）
if len(files) >= 3:
    target_file = files[2]
    print(f"\n正在读取第3个文件: {os.path.basename(target_file)}")
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"文件大小: {len(content)} 字符")
            # 提取标题
            if '<title>' in content:
                start = content.find('<title>') + 7
                end = content.find('</title>')
                print(f"标题: {content[start:end]}")
    except Exception as e:
        print(f"错误: {e}")
