# Journal of Animal Science and Biotechnology 论文获取指南

## 期刊信息

- **期刊名称**: Journal of Animal Science and Biotechnology
- **出版商**: BMC/Springer Nature
- **领域**: 动物科学与生物技术
- **ISSN**: 1674-9782

## 重要说明

⚠️ **该期刊已迁移至 Springer Nature Link 平台**

- 原 BMC 网站 (jasbsci.biomedcentral.com) 已停止更新
- 新网址: https://link.springer.com/journal/40104
- **RSS 订阅功能已失效** - 无法通过传统 RSS 获取

## 最佳获取方法

### 方法一：直接网页抓取（推荐）

由于 RSS 失效，最佳方法是通过浏览器自动化抓取最新论文列表：

```javascript
// 使用 Playwright 或 Puppeteer 抓取
const url = 'https://link.springer.com/journal/40104/articles?format=rss&flavour=recent';
// 实际返回 HTML 页面，需要解析 DOM
```

**步骤：**
1. 访问 https://link.springer.com/journal/40104/articles
2. 页面默认按日期排序（最新在前）
3. 提取文章标题、作者、日期、链接等信息

### 方法二：API 查询（备用）

Springer Nature 提供 API，但需要申请 API Key：
- 文档: https://dev.springernature.com/
- 需要注册获取 API Key

### 方法三：手动整理（当前使用）

通过浏览器访问后手动整理成 Markdown 格式。

## 已获取的论文存档

| 日期 | 文件路径 | 论文数量 |
|------|---------|---------|
| 2026-03-16 | `output/jasb-latest.md` | 10篇 |

## 更新计划

考虑开发一个浏览器自动化脚本：
- 使用 Playwright 访问期刊页面
- 自动提取最新论文信息
- 生成标准格式的 Markdown 报告

## 相关文件

- 论文报告: `output/jasb-latest.md`
- 缓存目录: `cache/`
- 术语映射: 见 `fetch-v2.mjs` 中的 TERM_MAP

## 注意事项

1. Springer 网站可能有反爬虫机制，需要控制访问频率
2. 页面结构可能随网站更新而变化
3. 部分论文可能需要订阅才能查看全文
4. 建议定期检查网站结构变化

---
*记录时间: 2026-03-16*
*记录人: OpenClaw Assistant*
