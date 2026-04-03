# Finance Office

个人金融数据管理与分析工作流

## 概述

本项目用于自动化获取、存储和分析金融市场数据，支持 A 股市场监控、美国国债收益率追踪以及学术期刊论文追踪。

## 功能模块

### 📈 A 股两市行情数据

自动获取并更新上证指数、深证成指日线数据及融资融券交易汇总数据。

**数据文件**:
- `data/index_sh_000001_daily.csv` - 上证指数日线
- `data/index_sz_399001_daily.csv` - 深证成指日线
- `data/margin_trading_sse_szse.csv` - 融资融券数据
- `data/market_combined_data.csv` - 综合市场数据

> **注意**: 2026-04-03 数据目录从 `tushare/` 迁移到 `data/` 以统一目录结构

**更新频率**: 每日 09:30 (获取上一交易日数据)

**数据源**: Tushare Pro API

---

### 📊 美国国债收益率

自动获取各期限美国国债收益率数据（1月期至30年期），生成交互式可视化图表。

**期限覆盖**: 1月、3月、6月、1年、2年、3年、5年、7年、10年、20年、30年

**输出文件**:
- `../skills/us-treasury-yields/data/us_treasury_yields_all_terms.csv` - 历史数据
- `../skills/us-treasury-yields/data/us_treasury_all_terms.html` - 交互式图表

**更新频率**: 每周一 (美东时间 09:00)

**数据源**: 东方财富妙想服务

---

### 📄 学术期刊论文追踪

自动从 PubMed 获取指定期刊最新论文，并进行中英文标题翻译。

**监控期刊**:
- Food Chemistry (食品化学)
- Journal of Ethnopharmacology (民族药理学)
- Journal of Animal Science and Biotechnology (动物科学与生物技术)
- Fish & Shellfish Immunology (鱼类与贝类免疫学)

**输出文件**: `../journal-papers-daily.md`

**更新频率**: 每日 08:00

**数据源**: PubMed API

---

## 项目结构

```
finance-office/
├── finance/                          # A股数据目录
│   ├── data/                         # A股数据文件
│   │   ├── index_sh_000001_daily.csv
│   │   ├── index_sz_399001_daily.csv
│   │   ├── margin_trading_sse_szse.csv
│   │   └── market_combined_data.csv
│   └── scripts/                      # 数据更新脚本
│       └── update_daily_market_data.py
├── skills/                           # Skill模块
│   ├── us-treasury-yields/           # 美债收益率Skill
│   │   ├── data/
│   │   └── scripts/
│   ├── journal-papers/               # 期刊论文Skill
│   │   └── scripts/
│   └── mx-macro-data/                # 宏观数据Skill
├── journal-papers/                   # 期刊论文输出
├── memory/                           # 记忆记录
│   └── YYYY-MM-DD.md
├── logs/                             # 任务日志
│   └── task-status.json
└── README.md                         # 本文件
```

---

## 快速开始

### 环境要求

- Python 3.7+
- R (用于可视化)
- Git
- SSH 密钥配置 (GitHub)

### 安装依赖

```bash
# Python依赖
pip install pandas requests

# R依赖
R -e "install.packages(c('plotly', 'htmlwidgets', 'dplyr', 'lubridate'))"
```

### 手动执行数据更新

```bash
# A股数据更新
cd finance
python scripts/update_daily_market_data.py

# 美债收益率更新
cd ../skills/us-treasury-yields
python scripts/update_us_treasury_data.py

# 期刊论文获取
cd ../journal-papers
node scripts/fetch.mjs
```

---

## 自动化配置

项目使用 OpenClaw 定时任务进行自动化：

| 任务 | 计划时间 | 说明 |
|------|----------|------|
| 期刊论文日报 | 08:00 | 获取4个期刊最新论文 |
| A股行情数据 | 09:30 | 更新指数和融资融券数据 |
| 美债收益率 | 周一 09:00 (美东) | 更新全期限收益率数据 |
| 论文写作提醒 | 20:00 | 提醒SCI论文写作任务 |
| AI日记整理 | 21:00 | 整理当日记忆记录 |

---

## 数据说明

### A股数据字段

| 字段 | 说明 |
|------|------|
| `date` | 交易日期 |
| `close` | 收盘价 |
| `open` | 开盘价 |
| `high` | 最高价 |
| `low` | 最低价 |
| `vol` | 成交量 |
| `amount` | 成交额 |
| `turnover` | 换手率 |

### 融资融券数据字段

| 字段 | 说明 |
|------|------|
| `trade_date` | 交易日期 |
| `rzye` | 融资余额 (亿元) |
| `rqye` | 融券余额 (亿元) |
| `rzrqye` | 融资融券余额合计 (亿元) |

---

## 贡献

本项目为个人使用，欢迎参考和借鉴。

## 许可证

MIT License

---

*最后更新: 2026-04-03*
