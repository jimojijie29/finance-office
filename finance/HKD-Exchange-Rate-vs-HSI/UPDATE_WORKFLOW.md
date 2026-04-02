# HKD-Exchange-Rate-vs-HSI 数据增量更新工作流

## 🎯 目标
在原有 `Hang_Seng_Index.csv` 和 `HKD_USD_Exchange_Rate.csv` 基础上，只下载新增数据，实现增量更新。

---

## 📁 文件结构

```
finance/HKD-Exchange-Rate-vs-HSI/
├── HKD_USD_Exchange_Rate.csv    # 现有数据（2002-05-10 至 2026-03-31）
├── Hang_Seng_Index.csv          # 现有数据（2013-08-20 至 2026-03-30）
├── update_data.py               # 增量更新脚本
└── UPDATE_WORKFLOW.md           # 本文档
```

---

## 🔄 增量更新步骤

### 步骤1: 检查现有数据最后日期

```python
import pandas as pd
from datetime import datetime, timedelta

# 读取现有数据
df_hkd = pd.read_csv('HKD_USD_Exchange_Rate.csv')
df_hsi = pd.read_csv('Hang_Seng_Index.csv')

# 获取最后日期
last_date_hkd = pd.to_datetime(df_hkd['Date']).max()
last_date_hsi = pd.to_datetime(df_hsi['Date']).max()

print(f"USD/HKD 最后日期: {last_date_hkd.strftime('%Y-%m-%d')}")
print(f"HSI 最后日期: {last_date_hsi.strftime('%Y-%m-%d')}")
```

### 步骤2: 计算需要更新的日期范围

```python
from datetime import datetime, timedelta

# 从最后日期的下一天开始
today = datetime.now()
start_date_hkd = (last_date_hkd + timedelta(days=1)).strftime('%Y%m%d')
start_date_hsi = (last_date_hsi + timedelta(days=1)).strftime('%Y%m%d')
end_date = today.strftime('%Y%m%d')

print(f"需要更新的范围: {start_date_hkd} 至 {end_date}")
```

### 步骤3: 获取新增数据

```python
import requests

def fetch_new_data(secid, start_date, end_date):
    """获取指定日期范围的新数据"""
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": "0",
        "beg": start_date,  # 开始日期
        "end": end_date,    # 结束日期
        "lmt": "10000"
    }
    
    response = requests.get(url, params=params, timeout=30)
    data = response.json()
    
    if data.get('rc') == 0 and data.get('data') and data['data'].get('klines'):
        return data['data']['klines']
    return []

# 获取新增数据
new_hkd = fetch_new_data("119.USDHKD", start_date_hkd, end_date)
new_hsi = fetch_new_data("100.HSI", start_date_hsi, end_date)

print(f"USD/HKD 新增: {len(new_hkd)} 条")
print(f"HSI 新增: {len(new_hsi)} 条")
```

### 步骤4: 合并并保存

```python
def append_new_data(existing_df, new_klines):
    """将新数据追加到现有数据"""
    if not new_klines:
        return existing_df
    
    # 解析新数据
    new_records = []
    for line in new_klines:
        parts = line.split(',')
        new_records.append({
            'Date': parts[0],
            'Open': float(parts[1]),
            'Close': float(parts[2]),
            'High': float(parts[3]),
            'Low': float(parts[4]),
            'Volume': float(parts[5]),
            'Amount': float(parts[6]),
            'Amplitude': float(parts[7]),
            'Pct_Change': float(parts[8]),
            'Change': float(parts[9]),
            'Turnover': float(parts[10])
        })
    
    new_df = pd.DataFrame(new_records)
    
    # 合并（去重，以Date为准）
    combined = pd.concat([existing_df, new_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=['Date'], keep='last')
    combined = combined.sort_values('Date').reset_index(drop=True)
    
    return combined

# 更新数据
df_hkd_updated = append_new_data(df_hkd, new_hkd)
df_hsi_updated = append_new_data(df_hsi, new_hsi)

# 保存
 df_hkd_updated.to_csv('HKD_USD_Exchange_Rate.csv', index=False, encoding='utf-8-sig')
df_hsi_updated.to_csv('Hang_Seng_Index.csv', index=False, encoding='utf-8-sig')

print(f"USD/HKD: {len(df_hkd)} → {len(df_hkd_updated)} 条")
print(f"HSI: {len(df_hsi)} → {len(df_hsi_updated)} 条")
```

---

## 📜 完整更新脚本

创建 `update_data.py`:

```python
#!/usr/bin/env python3
"""
HKD-Exchange-Rate-vs-HSI 数据增量更新脚本
在原有CSV基础上追加新数据，避免重复下载全部历史
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import sys

def get_last_date(filepath):
    """获取CSV文件的最后日期"""
    try:
        df = pd.read_csv(filepath)
        return pd.to_datetime(df['Date']).max()
    except FileNotFoundError:
        return None

def fetch_data(secid, start_date, end_date):
    """从东方财富API获取数据"""
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": "0",
        "beg": start_date,
        "end": end_date,
        "lmt": "10000"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if data.get('rc') == 0 and data.get('data'):
            return data['data'].get('klines', [])
    except Exception as e:
        print(f"请求失败: {e}")
    
    return []

def parse_klines(klines):
    """解析K线数据为DataFrame"""
    if not klines:
        return pd.DataFrame()
    
    records = []
    for line in klines:
        parts = line.split(',')
        records.append({
            'Date': parts[0],
            'Open': float(parts[1]),
            'Close': float(parts[2]),
            'High': float(parts[3]),
            'Low': float(parts[4]),
            'Volume': float(parts[5]),
            'Amount': float(parts[6]),
            'Amplitude': float(parts[7]),
            'Pct_Change': float(parts[8]),
            'Change': float(parts[9]),
            'Turnover': float(parts[10])
        })
    
    return pd.DataFrame(records)

def update_csv(filepath, secid, name):
    """更新单个CSV文件"""
    print(f"\n{'='*50}")
    print(f"更新: {name}")
    print(f"{'='*50}")
    
    # 获取现有数据最后日期
    last_date = get_last_date(filepath)
    
    if last_date is None:
        print(f"文件不存在: {filepath}")
        print("请使用初始下载脚本获取完整历史数据")
        return False
    
    print(f"现有数据最后日期: {last_date.strftime('%Y-%m-%d')}")
    
    # 计算更新范围
    today = datetime.now()
    start_date = (last_date + timedelta(days=1)).strftime('%Y%m%d')
    end_date = today.strftime('%Y%m%d')
    
    if start_date > end_date:
        print("数据已是最新，无需更新")
        return True
    
    print(f"获取范围: {start_date} 至 {end_date}")
    
    # 获取新数据
    klines = fetch_data(secid, start_date, end_date)
    
    if not klines:
        print("无新数据")
        return True
    
    print(f"获取到 {len(klines)} 条新数据")
    
    # 读取现有数据
    df_existing = pd.read_csv(filepath)
    df_new = parse_klines(klines)
    
    # 合并（去重）
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset=['Date'], keep='last')
    df_combined = df_combined.sort_values('Date').reset_index(drop=True)
    
    # 保存
    df_combined.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    print(f"更新完成: {len(df_existing)} → {len(df_combined)} 条")
    print(f"时间范围: {df_combined['Date'].min()} 至 {df_combined['Date'].max()}")
    
    return True

def main():
    """主函数"""
    print("="*60)
    print("HKD-Exchange-Rate-vs-HSI 数据增量更新")
    print(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 更新USD/HKD
    update_csv('HKD_USD_Exchange_Rate.csv', '119.USDHKD', 'USD/HKD 汇率')
    
    # 更新HSI
    update_csv('Hang_Seng_Index.csv', '100.HSI', '恒生指数')
    
    print("\n" + "="*60)
    print("所有更新完成!")
    print("="*60)

if __name__ == '__main__':
    main()
```

---

## 🚀 使用方法

### 日常更新（推荐）

```bash
# 进入目录
cd finance/HKD-Exchange-Rate-vs-HSI

# 运行更新脚本
python update_data.py
```

### 首次下载（完整历史）

如果CSV文件不存在，需要先获取完整历史数据：

```python
# 使用初始脚本（end=20500101 获取全部历史）
# 参考 DATA_FETCH_GUIDE.md
```

---

## ⚠️ 注意事项

1. **交易日问题**: API只返回交易日数据，周末和节假日自动跳过
2. **数据延迟**: 当日数据可能在收盘后才更新
3. **重复数据**: 脚本会自动去重，同一日期保留最新数据
4. **备份建议**: 更新前可备份原CSV文件

---

## 📊 更新记录模板

每次更新后记录：

```markdown
### 2026-XX-XX 更新
- USD/HKD: XXXX 条 → XXXX 条 (+XX)
- HSI: XXXX 条 → XXXX 条 (+XX)
- 更新日期范围: YYYY-MM-DD 至 YYYY-MM-DD
```

---

*创建时间: 2026-03-31*
