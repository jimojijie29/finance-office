# 港元汇率与恒生指数数据获取方法

## 概述
本文档记录了获取港元/美元汇率和恒生指数历史行情数据的完整方法，包括数据源、API参数和Python实现代码。

---

## 数据源

**东方财富 (East Money)** - 免费历史行情数据API
- 基础URL: `https://push2his.eastmoney.com/api/qt/stock/kline/get`
- 支持A股、港股、外汇等多种资产类型
- 返回JSON格式的K线数据

---

## 1. 港元/美元汇率 (USD/HKD)

### API参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `secid` | `119.USDHKD` | 市场119=外汇，USDHKD=美元兑港元 |
| `klt` | `101` | K线类型：101=日线 |
| `fqt` | `0` | 复权类型：0=不复权 |
| `lmt` | `10000` | 返回记录数上限 |
| `end` | `20500101` | 结束日期（设为未来日期获取全部历史） |
| `fields1` | `f1,f2,f3,f4,f5,f6` | 基础字段 |
| `fields2` | `f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61` | K线详细字段 |

### 完整URL
```
https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=119.USDHKD&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=0&end=20500101&lmt=10000
```

### Python获取代码

```python
import requests
import pandas as pd
import json

# API配置
url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
params = {
    "secid": "119.USDHKD",
    "fields1": "f1,f2,f3,f4,f5,f6",
    "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
    "klt": "101",      # 日线
    "fqt": "0",        # 不复权
    "end": "20500101", # 未来日期，获取全部历史
    "lmt": "10000"     # 最大记录数
}

# 发送请求
response = requests.get(url, params=params, timeout=30)
data = response.json()

# 解析数据
klines = data['data']['klines']  # K线数据列表

# 转换为DataFrame
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

df = pd.DataFrame(records)

# 保存为CSV
df.to_csv('HKD_USD_Exchange_Rate.csv', index=False, encoding='utf-8-sig')
print(f"数据已保存，共 {len(df)} 条记录")
print(f"时间范围: {df['Date'].min()} 至 {df['Date'].max()}")
```

### 数据字段说明

| 字段 | 说明 |
|------|------|
| `Date` | 交易日期 (YYYY-MM-DD) |
| `Open` | 开盘价 |
| `Close` | 收盘价 |
| `High` | 最高价 |
| `Low` | 最低价 |
| `Volume` | 成交量 |
| `Amount` | 成交额 |
| `Amplitude` | 振幅 (%) |
| `Pct_Change` | 涨跌幅 (%) |
| `Change` | 涨跌额 |
| `Turnover` | 换手率 |

---

## 2. 恒生指数 (Hang Seng Index, HSI)

### API参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `secid` | `100.HSI` | 市场100=香港，HSI=恒生指数代码 |
| `klt` | `101` | K线类型：101=日线 |
| `fqt` | `0` | 复权类型：0=不复权 |
| `lmt` | `10000` | 返回记录数上限 |
| `end` | `20500101` | 结束日期（设为未来日期获取全部历史） |
| `fields1` | `f1,f2,f3,f4,f5,f6` | 基础字段 |
| `fields2` | `f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61` | K线详细字段 |

### 完整URL
```
https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=100.HSI&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=0&end=20500101&lmt=10000
```

### 市场代码对照表

| 市场代码 | 市场 |
|---------|------|
| `100` | 香港交易所 |
| `119` | 外汇 |
| `124` | 港股（备用）|
| `116` | 港股（备用）|

### Python获取代码

```python
import requests
import pandas as pd

# API配置
url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
params = {
    "secid": "100.HSI",  # 香港市场恒生指数
    "fields1": "f1,f2,f3,f4,f5,f6",
    "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
    "klt": "101",      # 日线
    "fqt": "0",        # 不复权
    "end": "20500101", # 未来日期，获取全部历史
    "lmt": "10000"     # 最大记录数
}

# 发送请求
response = requests.get(url, params=params, timeout=30)
data = response.json()

# 检查响应
if data.get('rc') == 0 and data.get('data'):
    klines = data['data']['klines']
    print(f"获取到 {len(klines)} 条K线数据")
    
    # 转换为DataFrame
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
    
    df = pd.DataFrame(records)
    
    # 保存为CSV
    df.to_csv('Hang_Seng_Index.csv', index=False, encoding='utf-8-sig')
    print(f"数据已保存，共 {len(df)} 条记录")
    print(f"时间范围: {df['Date'].min()} 至 {df['Date'].max()}")
else:
    print(f"请求失败: {data.get('rc', 'Unknown')}")
```

---

## 3. 备用方案：浏览器自动化

当Python requests因网络代理问题无法连接API时，可使用浏览器自动化获取数据。

### 步骤

1. **打开浏览器访问API URL**
   ```python
   # 使用browser工具打开API URL
   browser.open(url="https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=100.HSI&...")
   ```

2. **提取JSON数据**
   ```javascript
   // 在浏览器控制台执行
   const data = JSON.parse(document.body.innerText);
   const klines = data.data.klines;
   ```

3. **生成CSV**
   ```javascript
   // 生成CSV并下载
   let csv = 'Date,Open,Close,High,Low,Volume,Amount,Amplitude,Pct_Change,Change,Turnover\n';
   klines.forEach(line => {
       csv += line + '\n';
   });
   
   const blob = new Blob([csv], { type: 'text/csv' });
   const url = URL.createObjectURL(blob);
   const a = document.createElement('a');
   a.href = url;
   a.download = 'Hang_Seng_Index.csv';
   a.click();
   ```

---

## 4. 通用参数说明

### K线类型 (klt)

| 值 | 说明 |
|-----|------|
| `101` | 日线 |
| `102` | 周线 |
| `103` | 月线 |
| `60` | 1小时线 |
| `30` | 30分钟线 |
| `15` | 15分钟线 |
| `5` | 5分钟线 |
| `1` | 1分钟线 |

### 复权类型 (fqt)

| 值 | 说明 |
|-----|------|
| `0` | 不复权 |
| `1` | 前复权 |
| `2` | 后复权 |

### Fields2字段映射

| 字段 | 说明 |
|------|------|
| `f51` | 日期 |
| `f52` | 开盘价 |
| `f53` | 收盘价 |
| `f54` | 最高价 |
| `f55` | 最低价 |
| `f56` | 成交量 |
| `f57` | 成交额 |
| `f58` | 振幅 |
| `f59` | 涨跌幅 |
| `f60` | 涨跌额 |
| `f61` | 换手率 |

---

## 5. 数据存储路径

```
D:\OpenClawData\.openclaw\workspace\finance\HKD-Exchange-Rate-vs-HSI\
├── HKD_USD_Exchange_Rate.csv    # 港元/美元汇率数据
└── Hang_Seng_Index.csv          # 恒生指数数据
```

---

## 6. 实际获取结果

### 2026-03-31 获取结果

| 数据 | 记录数 | 时间范围 | 文件大小 |
|------|--------|----------|----------|
| USD/HKD 汇率 | 6,225 条 | 2002-05-10 至 2026-03-31 | 398.67 KB |
| 恒生指数 HSI | 3,103 条 | 2013-08-20 至 2026-03-30 | 184.80 KB |

---

## 7. 数据源变更记录

### 2026-04-09 重要更新

**问题**: USD/HKD 汇率数据停留在 2026-04-02，无法获取最新数据

**原因**: 东方财富API (`119.USDHKD`) 受网络代理影响，无法正常获取数据

**解决方案**: 改用 mx-macro-data skill 获取数据

| 数据 | 原方案 | 新方案 | 状态 |
|------|--------|--------|------|
| USD/HKD 汇率 | 东方财富API (`119.USDHKD`) | mx-macro-data skill | 已切换 |
| 恒生指数 HSI | 东方财富API (`100.HSI`) | mx-macro-data skill | 已切换 |

**数据转换说明**:
mx-macro-data 返回的是 HKD/USD（倒数），需要转换为 USD/HKD：
```python
value = round(1.0 / value, 4)
```

**相关脚本**:
- `update_data.py` - 主脚本（当前使用 mx-macro-data skill）
- `update_hkd_mx.py` - USD/HKD 汇率更新（mx-macro-data）
- `update_hsi_mx.py` - 恒生指数更新（mx-macro-data）
- `update_data_legacy.py` - 历史版本（东方财富API，备用）

---

## 参考

- 东方财富网: https://quote.eastmoney.com/
- 恒生指数官网: https://www.hsi.com.hk/
- mx-macro-data skill: `skills/mx-macro-data/`

---

*记录时间: 2026-03-31*  
*更新时间: 2026-04-09（添加数据源变更记录）*
