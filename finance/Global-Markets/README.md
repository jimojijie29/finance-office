# Global Markets Data

外盘行情数据 - 美国三大指数和黄金/白银历史数据

## 数据概览

| 类型 | 名称 | 代码 | 记录数 | 时间范围 | 最新价格 |
|-----|------|------|--------|---------|---------|
| 指数 | S&P 500 | .INX | 5,597 | 2004-2026 | 6368.85 |
| 指数 | Dow Jones | .DJI | 5,596 | 2004-2026 | 45166.64 |
| 指数 | NASDAQ | .IXIC | 5,594 | 2004-2026 | 20948.36 |
| 商品 | Gold | XAU | 5,184 | 2006-2026 | 4557.48 |
| 商品 | Silver | XAG | 5,185 | 2006-2026 | 71.22 |

## 数据文件

- `SP500_History.csv` - 标普500历史数据
- `DJI_History.csv` - 道琼斯历史数据
- `NASDAQ_History.csv` - 纳斯达克历史数据
- `XAU_Gold_History.csv` - 黄金历史数据
- `XAG_Silver_History.csv` - 白银历史数据
- `DATA_SUMMARY.csv` - 数据摘要

## 字段说明

- `date` - 日期
- `open` - 开盘价
- `high` - 最高价
- `low` - 最低价
- `close` - 收盘价
- `volume` - 成交量

## 使用方法

```bash
python workflow.py
```

## 数据来源

- 美股指数: akshare - 新浪财经美股指数接口
- 黄金/白银: akshare - 新浪财经外盘期货接口
