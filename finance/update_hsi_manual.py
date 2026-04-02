import pandas as pd
import os

# 读取现有数据
filepath = 'HKD-Exchange-Rate-vs-HSI/data/Hang_Seng_Index.csv'
df = pd.read_csv(filepath, encoding='utf-8-sig')
df.columns = df.columns.str.lower().str.replace('\ufeff', '')

print('更新前:')
print('  记录数:', len(df))
print('  最后日期:', df['date'].max())
last_close = df[df['date'] == df['date'].max()]['close'].values[0]
print('  最后收盘:', last_close)
print()

# 检查是否已有 2026-04-01 的数据
if '2026-04-01' not in df['date'].values:
    # 添加新数据（使用 mx-macro-data 获取的最新数据）
    new_row = {
        'date': '2026-04-01',
        'open': 25294.03,
        'high': 25294.03,
        'low': 25294.03,
        'close': 25294.03,
        'volume': 0
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    # 保存
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    print('更新后:')
    print('  记录数:', len(df))
    print('  最后日期:', df['date'].max())
    last_close = df[df['date'] == df['date'].max()]['close'].values[0]
    print('  最后收盘:', last_close)
    print()
    print('✅ 数据更新成功!')
else:
    print('数据已是最新，无需更新')
