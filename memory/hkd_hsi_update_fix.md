# HKD-Exchange-Rate-vs-HSI 数据更新修复记录

## 修复时间
2026-04-09

## 问题描述
USD/HKD 汇率数据停留在 2026-04-02，无法获取最新数据。

## 问题原因
原脚本使用东方财富API (`119.USDHKD`) 获取 USD/HKD 汇率数据，该API受网络代理影响，无法正常获取数据。

## 解决方案
改用 mx-macro-data skill 获取数据，避免网络代理问题。

## 脚本文件说明

### 当前使用（推荐）
| 文件 | 说明 |
|------|------|
| `update_data.py` | 主脚本，调用子脚本更新数据 |
| `update_hkd_mx.py` | 使用 mx-macro-data skill 更新 USD/HKD 汇率 |
| `update_hsi_mx.py` | 使用 mx-macro-data skill 更新恒生指数 |

### 历史版本（备用）
| 文件 | 说明 |
|------|------|
| `update_data_legacy.py` | 原脚本，使用东方财富API直接获取 |

## 切换方法

### 切换到历史版本（东方财富API）
```bash
cd "D:\OpenClawData\.openclaw\workspace\finance\HKD-Exchange-Rate-vs-HSI\scripts"
python update_data_legacy.py
```

### 使用当前版本（mx-macro-data skill）
```bash
cd "D:\OpenClawData\.openclaw\workspace\finance\HKD-Exchange-Rate-vs-HSI\scripts"
python update_data.py
```

或执行完整工作流：
```bash
python "D:\OpenClawData\.openclaw\workspace\finance\HKD-Exchange-Rate-vs-HSI\scripts\workflow.py"
```

## 数据转换说明
mx-macro-data 返回的是 HKD/USD（倒数），脚本会自动转换为 USD/HKD：
```python
value = round(1.0 / value, 4)
```

## 注意事项
- 4月3日-6日为清明节假期，香港金融市场休市，数据正常
- mx-macro-data skill 需要正确配置才能使用
- 如遇到网络问题，可尝试切换回历史版本
