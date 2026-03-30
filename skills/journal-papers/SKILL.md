---
name: journal-papers
description: 从 Food Chemistry、Journal of Ethnopharmacology、Journal of Animal Science and Biotechnology 和 Fish & Shellfish Immunology 期刊获取当天最新上线论文。
homepage: https://github.com/openclaw/skills/tree/main/journal-papers
metadata:
  {
    "openclaw":
      {
        "emoji": "📄",
        "requires": { "bins": ["node"] },
      },
  }
---

# Journal Papers Fetcher

从指定期刊获取当天最新上线论文的自动化工具。

## 支持的期刊

| 期刊名 | 领域 |
|--------|------|
| **Food Chemistry** | 食品化学 |
| **Journal of Ethnopharmacology** | 民族药理学 |
| **Journal of Animal Science and Biotechnology** | 动物科学与生物技术 |
| **Fish & Shellfish Immunology** | 鱼类与贝类免疫学 |

## 使用方法

### 获取所有期刊当天论文

```bash
node {baseDir}/scripts/fetch.mjs
```

### 获取特定期刊论文

```bash
# Food Chemistry
node {baseDir}/scripts/fetch.mjs --journal food-chemistry

# Journal of Ethnopharmacology
node {baseDir}/scripts/fetch.mjs --journal jep

# Journal of Animal Science and Biotechnology
node {baseDir}/scripts/fetch.mjs --journal jasb

# Fish & Shellfish Immunology
node {baseDir}/scripts/fetch.mjs --journal fsi
```

### 指定日期

```bash
# 获取特定日期的论文 (YYYY-MM-DD 格式)
node {baseDir}/scripts/fetch.mjs --date 2026-03-16
```

### 输出格式

```bash
# JSON 格式（默认）
node {baseDir}/scripts/fetch.mjs --format json

# Markdown 格式
node {baseDir}/scripts/fetch.mjs --format markdown

# 纯文本格式
node {baseDir}/scripts/fetch.mjs --format text
```

## 输出示例

```json
{
  "date": "2026-03-16",
  "journals": [
    {
      "name": "Food Chemistry",
      "papers": [
        {
          "title": "论文标题",
          "authors": ["作者1", "作者2"],
          "doi": "10.1016/xxxxx",
          "url": "https://www.sciencedirect.com/...",
          "abstract": "摘要内容...",
          "published": "2026-03-16"
        }
      ]
    }
  ]
}
```

## 注意事项

- 数据来源于各期刊官网的 RSS feed 或最新上线页面
- 部分期刊可能需要通过 PubMed 或 ScienceDirect API 获取
- 建议设置定时任务（cron）每天自动获取最新论文
