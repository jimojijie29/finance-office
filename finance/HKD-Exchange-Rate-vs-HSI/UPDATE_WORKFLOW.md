# HKD-Exchange-Rate-vs-HSI 数据增量更新工作流

## 🎯 目标
在原有 `Hang_Seng_Index.csv` 和 `HKD_USD_Exchange_Rate.csv` 基础上，只下载新增数据，实现增量更新。

---

## 📁 文件结构

```
finance/HKD-Exchange-Rate-vs-HSI/
├── data/
│   ├── HKD_USD_Exchange_Rate.csv    # 现有数据（2002-05-10 至 2026-04-08）
│   ├── Hang_Seng_Index.csv          # 现有数据（2013-08-20 至 2026-04-08）
│   └── hkd_vs_hsi_dual_axis.html    # 可视化图表
├── scripts/
│   ├── update_data.py               # 主更新脚本（调用子脚本）
│   ├── update_hkd_mx.py             # USD/HKD 更新（mx-macro-data skill）
│   ├── update_hsi_mx.py             # HSI 更新（mx-macro-data skill）
│   ├── update_data_legacy.py        # 历史版本（东方财富API，备用）
│   ├── hkd_hsi_visualization.py     # Python可视化
│   └── hkd_hsi_visualization.R      # R可视化（备用）
├── DATA_FETCH_GUIDE.md              # 数据获取方法文档
└── UPDATE_WORKFLOW.md               # 本文档
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

### 当前方案（推荐）：使用 mx-macro-data skill

主脚本 `update_data.py` 调用子脚本获取数据：

```python
#!/usr/bin/env python3
"""
HKD-Exchange-Rate-vs-HSI 数据增量更新脚本
使用 mx-macro-data skill 获取数据，避免网络代理问题
"""

import os
import subprocess
from datetime import datetime

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def main():
    log("="*60)
    log("HKD-Exchange-Rate-vs-HSI 数据增量更新")
    log(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("="*60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 更新USD/HKD (使用mx-macro-data skill)
    log("更新 USD/HKD 汇率 (使用 mx-macro-data skill)...")
    result = subprocess.run(
        ['python', os.path.join(script_dir, 'update_hkd_mx.py')],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode == 0:
        log("USD/HKD 汇率更新成功")
    else:
        log(f"USD/HKD 汇率更新失败: {result.stderr}")
    
    # 更新HSI (使用mx-macro-data skill)
    log("更新恒生指数 (使用 mx-macro-data skill)...")
    result = subprocess.run(
        ['python', os.path.join(script_dir, 'update_hsi_mx.py')],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode == 0:
        log("恒生指数更新成功")
    else:
        log(f"恒生指数更新失败: {result.stderr}")
    
    log("\n" + "="*60)
    log("所有更新完成!")
    log("="*60)

if __name__ == '__main__':
    main()
```

### 历史方案：使用东方财富API

原脚本已保存为 `update_data_legacy.py`，使用东方财富API直接获取：

```bash
# 使用历史版本（如遇网络问题可切换）
python scripts/update_data_legacy.py
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
5. **网络代理**: 如使用东方财富API遇到代理问题，请切换到 mx-macro-data skill 方案

---

## 📊 更新记录

### 2026-04-09 重要更新
- **问题**: USD/HKD 汇率数据停留在 2026-04-02
- **原因**: 东方财富API受网络代理影响
- **解决方案**: 改用 mx-macro-data skill 获取数据
- **数据转换**: mx-macro-data 返回 HKD/USD，脚本自动转换为 USD/HKD
- **新增文件**:
  - `update_hkd_mx.py` - USD/HKD 汇率更新（mx-macro-data）
  - `update_hsi_mx.py` - 恒生指数更新（mx-macro-data）
  - `update_data_legacy.py` - 历史版本（东方财富API，备用）
- **更新后数据**:
  - USD/HKD: 6227 条 → 6231 条 (+4)
  - HSI: 3105 条 → 3106 条 (+1)
  - 更新日期范围: 2026-04-03 至 2026-04-08

### 更新记录模板

```markdown
### 2026-XX-XX 更新
- USD/HKD: XXXX 条 → XXXX 条 (+XX)
- HSI: XXXX 条 → XXXX 条 (+XX)
- 更新日期范围: YYYY-MM-DD 至 YYYY-MM-DD
```

---

*创建时间: 2026-03-31*
