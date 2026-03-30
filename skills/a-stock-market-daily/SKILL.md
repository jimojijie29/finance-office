---
name: a-stock-market-daily
description: A股两市行情数据每日自动更新Skill。获取上证指数、深证成指日线数据，融资融券交易汇总数据，生成综合市场数据文件和可视化图表。支持定时任务执行。
---

# A股两市行情数据每日更新

## 概述

本Skill用于自动获取A股两市行情数据，包括：
- 上证指数 (000001.SH) 日线数据
- 深证成指 (399001.SZ) 日线数据
- 沪深两市融资融券交易汇总数据
- 生成综合市场数据文件
- 自动生成Plotly交互式可视化图表

## 功能特点

1. **自动数据合并**：智能合并新旧数据，去重并排序
2. **增量更新**：只获取最近7天的数据，避免重复下载
3. **数据可视化**：自动生成R语言Plotly交互式图表
4. **任务日志**：集成任务状态记录，便于监控
5. **定时任务支持**：可通过cron设置每日自动执行

## 使用方法

### 手动执行

```bash
# 执行今日数据更新
python skills/a-stock-market-daily/scripts/update_daily_market_data.py

# 指定日期更新
python skills/a-stock-market-daily/scripts/update_daily_market_data.py --date 20260330
```

### 定时任务配置

建议设置每日09:30执行（开盘后）：

```json
{
  "name": "A股两市行情数据每日更新",
  "schedule": {"kind": "cron", "expr": "30 9 * * MON-FRI", "tz": "Asia/Shanghai"},
  "payload": {
    "kind": "agentTurn",
    "message": "执行A股两市行情数据每日更新任务"
  }
}
```

## 输出文件

| 文件 | 说明 |
|------|------|
| `finance/tushare/index_sh_000001_daily.csv` | 上证指数日线数据 |
| `finance/tushare/index_sz_399001_daily.csv` | 深证成指日线数据 |
| `finance/tushare/margin_trading_sse_szse.csv` | 融资融券数据 |
| `finance/tushare/market_combined_data.csv` | 综合市场数据 |
| `finance/visualization/*.html` | Plotly交互式图表 |

## 数据字段说明

### 指数数据字段
- `trade_date`: 交易日期 (YYYYMMDD)
- `close`: 收盘价
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `pre_close`: 昨收价
- `change`: 涨跌额
- `pct_chg`: 涨跌幅 (%)
- `vol`: 成交量 (手)
- `amount`: 成交额 (千元)

### 融资融券数据字段
- `trade_date`: 交易日期
- `exchange_id`: 交易所 (SSE/SZSE)
- `rzye`: 融资余额 (元)
- `rqye`: 融券余额 (元)
- `rzrqye`: 融资融券余额 (元)

### 综合数据字段
- `trade_date`: 交易日期
- `sh_close`: 上证指数收盘
- `sz_close`: 深证成指收盘
- `avg_close`: 平均收盘
- `total_turnover`: 两市成交额 (亿元)
- `margin_balance`: 融资余额 (亿元)
- `short_balance`: 融券余额 (亿元)
- `total_margin_balance`: 融资融券总额 (亿元)

## 依赖要求

- Python 3.7+
- pandas
- requests
- R + plotly (用于可视化)
- Tushare API Token

## Tushare配置

设置环境变量或在脚本中配置：
```bash
export TUSHARE_TOKEN=your_token_here
```

或在脚本中修改：
```python
token = 'your_token_here'
```

## 注意事项

1. Tushare部分接口需要积分权限
2. 数据更新时间为每个交易日18:00后
3. 节假日无数据，脚本会自动处理
4. 首次运行会获取历史数据，耗时较长

## 版本历史

- v1.0.0: 初始版本，支持基础数据获取和可视化
