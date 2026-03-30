---
name: us-treasury-yields
description: 美国国债收益率数据获取与可视化Skill。自动获取各期限国债收益率数据（1月-30年），生成交互式可视化图表。支持数据更新和增量合并。
---

# 美国国债收益率数据工作流

## 概述

本Skill用于自动获取美国国债收益率数据，包括1月期到30年期共11个期限，生成交互式Plotly可视化图表。

## 功能特点

1. **自动数据获取**：从东方财富数据库获取最新数据
2. **增量更新**：智能合并新旧数据，自动去重
3. **全期限覆盖**：1月、3月、6月、1年、2年、3年、5年、7年、10年、20年、30年
4. **交互式图表**：Plotly可视化，支持图例多选切换
5. **数据验证**：自动检查数据质量，排除异常值

## 使用方法

### 手动执行

```bash
# 进入工作流目录
cd skills/us-treasury-yields

# 执行数据更新
python scripts/update_us_treasury_data.py
```

### 定时任务配置

建议每周运行一次（数据为日度更新）：

```json
{
  "name": "美国国债收益率数据更新",
  "schedule": {"kind": "cron", "expr": "0 9 * * MON", "tz": "America/New_York"},
  "payload": {
    "kind": "agentTurn",
    "message": "执行美国国债收益率数据更新"
  }
}
```

## 文件结构

```
skills/us-treasury-yields/
├── SKILL.md                          # 本说明文档
├── _meta.json                        # Skill元数据
├── README.md                         # 使用说明
├── scripts/
│   ├── update_us_treasury_data.py    # Python数据更新脚本
│   └── us_treasury_workflow_v2.R     # R可视化脚本
└── data/
    ├── us_treasury_yields_all_terms.csv    # 数据文件
    └── us_treasury_all_terms.html          # 可视化结果
```

## 输出文件

| 文件 | 说明 |
|------|------|
| `data/us_treasury_yields_all_terms.csv` | 历史收益率数据 |
| `data/us_treasury_all_terms.html` | 交互式可视化图表 |

## 数据字段说明

| 字段 | 说明 |
|------|------|
| `date` | 日期 (YYYY-MM-DD) |
| `X1月` | 1个月期国债收益率 (%) |
| `X3月` | 3个月期国债收益率 (%) |
| `X6月` | 6个月期国债收益率 (%) |
| `X1年` | 1年期国债收益率 (%) |
| `X2年` | 2年期国债收益率 (%) |
| `X3年` | 3年期国债收益率 (%) |
| `X5年` | 5年期国债收益率 (%) |
| `X7年` | 7年期国债收益率 (%) |
| `X10年` | 10年期国债收益率 (%) |
| `X20年` | 20年期国债收益率 (%) |
| `X30年` | 30年期国债收益率 (%) |

## 数据源

- **提供商**: 东方财富妙想服务
- **API**: `https://ai-saas.eastmoney.com/proxy/b/mcp/tool/searchMacroData`
- **频率**: 日度
- **更新延迟**: 通常 T+1（次日更新）

## 依赖要求

- Python 3.7+
- pandas
- R + plotly + htmlwidgets
- mx-macro-data Skill

## 数据范围

- **历史数据**: 2020年4月至今
- **数据点数**: 约1500条日度记录
- **更新频率**: 建议每周更新

## 注意事项

1. **TIPS数据排除**: 自动排除通胀保值债券数据
2. **数据去重**: 合并时自动去重，保留最新数据
3. **编码兼容**: 已修复Windows中文编码问题

## 版本历史

- v1.0.0: 初始版本，支持全期限数据获取和可视化
