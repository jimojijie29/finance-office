# Workspace 文件结构规范

本文档记录 WORKSPACE 文件夹的文件归档规则，便于后续维护和查找。

---

## 📁 根目录保留文件

以下文件保留在 workspace 根目录：

| 文件 | 说明 |
|------|------|
| `AGENTS.md` | 工作区配置指南 |
| `BUDDHISM_GUIDE.md` | 佛教修习指南 |
| `HEARTBEAT.md` | 心跳任务检查清单 |
| `IDENTITY.md` | AI 身份定义 |
| `MEMORY.md` | 长期记忆库 |
| `SOUL.md` | 核心人格定义 |
| `TOOLS.md` | 工具配置说明 |
| `USER.md` | 用户画像 |
| `.gitignore` | Git 忽略规则 |
| `WORKSPACE_STRUCTURE.md` | 本文件结构规范文档 |

---

## 📂 任务文件夹结构

每个任务文件夹采用统一的子文件夹结构：

```
task-folder/                  # 任务主文件夹
├── scripts/                  # 该任务的脚本
├── data/                     # 该任务的数据（如有）
└── ...                       # 其他任务相关文件
```

---

## 📂 金融数据 (`finance/`)

金融数据相关文件和脚本：

```
finance/
├── scripts/                  # 金融数据脚本
│   ├── fetch_margin_data.py
│   ├── fetch_bond_yield_akshare.py
│   ├── fetch_bond_yield_akshare_final.py
│   ├── fetch_china_bond_yield.py
│   ├── fetch_sector_fund_flow.py
│   ├── query_margin.py
│   ├── query_margin_0314.py
│   ├── query_margin_sector.py
│   ├── query_market_stats.py
│   ├── indices.py
│   ├── margin.py
│   ├── margin_analysis.py
│   ├── sh_index.py
│   └── test_pingan.py
├── tushare/                  # Tushare 数据源数据
│   └── margin_trading_sse_szse.csv
├── eastmoney/                # 东方财富数据源数据
├── akshare/                  # AKShare 数据源数据
└── data/                     # 其他金融数据
    └── 中国国债收益率_*.csv
```

---

## 📂 期刊论文 (`journal-papers/`)

期刊论文相关文件和脚本：

```
journal-papers/
├── scripts/                  # 论文相关脚本
│   └── test_translate.mjs
├── journal-papers-daily.md   # 论文日报
├── journal-papers-daily.json
└── journal-papers-report.md
```

---

## 📂 投资阅读 (`investment-reading/`)

投资文章阅读相关文件和脚本：

```
investment-reading/
├── scripts/                  # 投资阅读脚本
│   ├── extract_html.py
│   ├── read_html_content.py
│   └── read_html_files.py
└── ...                       # 阅读笔记等
```

---

## 📂 妙想金融数据 (`miaoxiang/`)

通过妙想技能获取的数据：

```
miaoxiang/
├── mx_finance_data/          # 金融数据
└── mx_macro_data/            # 宏观数据
```

---

## 📂 临时文件 (`temp/`)

临时生成的数据文件：

```
temp/
├── journal-papers/           # 论文相关临时文件
│   ├── bmc_test.xml
│   └── jasb_api_*.json
└── rss-feeds/                # RSS订阅临时文件
    ├── fsi_rss.xml
    └── jasb_rss.xml
```

---

## 📂 记忆归档 (`memory/`)

日常记忆和日记：

```
memory/
├── 2026-03-26.md             # 每日记忆文件
├── diary/                    # AI日记
└── moxian-notes/             # 莫大仙岳居阅读笔记
```

---

## 📂 论文草稿 (`papers/`)

科研论文草稿：
- `noni-fruit-storage-review.md` - 诺丽果保鲜综述

---

## 📝 新增文件保存指引

### 脚本文件
根据脚本功能，放到对应任务文件夹的 `scripts/` 子文件夹中：

1. **金融类脚本** → `finance/scripts/`
2. **论文类脚本** → `journal-papers/scripts/`
3. **投资阅读脚本** → `investment-reading/scripts/`

### 数据文件
1. **Tushare 数据** → `finance/tushare/`
2. **东方财富数据** → `finance/eastmoney/`
3. **AKShare 数据** → `finance/akshare/`
4. **其他金融数据** → `finance/data/`

### 临时文件
1. **论文相关临时文件** → `temp/journal-papers/`
2. **RSS订阅临时文件** → `temp/rss-feeds/`

---

*最后更新：2026-03-26*
