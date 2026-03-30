#!/usr/bin/env node
/**
 * Journal Papers Fetcher - 测试版本
 * 从指定期刊获取当天最新上线论文，并测试本地模型翻译功能
 */

import { parseArgs } from 'node:util';

// 期刊配置
const JOURNALS = {
  'food-chemistry': {
    name: 'Food Chemistry',
    rss: 'https://rss.sciencedirect.com/publication/science/03088146',
    publisher: 'Elsevier',
    field: '食品化学'
  },
  'jep': {
    name: 'Journal of Ethnopharmacology',
    rss: 'https://rss.sciencedirect.com/publication/science/03788741',
    publisher: 'Elsevier',
    field: '民族药理学'
  },
  'jasb': {
    name: 'Journal of Animal Science and Biotechnology',
    rss: 'https://jasbsci.biomedcentral.com/articles/most-recent/rss.xml',
    publisher: 'BMC',
    field: '动物科学与生物技术'
  },
  'fsi': {
    name: 'Fish & Shellfish Immunology',
    rss: 'https://rss.sciencedirect.com/publication/science/10504648',
    publisher: 'Elsevier',
    field: '鱼类与贝类免疫学'
  }
};

// 解析命令行参数
const { values } = parseArgs({
  options: {
    journal: { type: 'string', short: 'j' },
    date: { type: 'string', short: 'd' },
    days: { type: 'string', short: 'n', default: '7' },
    limit: { type: 'string', short: 'l', default: '10' },
    format: { type: 'string', short: 'f', default: 'markdown' },
    help: { type: 'boolean', short: 'h' }
  }
});

if (values.help) {
  console.log(`
用法: node fetch-test.mjs [选项]

选项:
  -j, --journal <name>    特定期刊 (food-chemistry|jep|jasb|fsi)
  -d, --date <date>       指定日期 (YYYY-MM-DD，默认今天)
  -n, --days <days>       获取最近 N 天的论文 (默认 7)
  -l, --limit <num>       每期刊最多显示 N 篇 (默认 10)
  -f, --format <format>   输出格式 (json|markdown|text，默认 markdown)
  -h, --help              显示帮助
`);
  process.exit(0);
}

// 获取目标日期和天数范围
const targetDate = values.date || new Date().toISOString().split('T')[0];
const recentDays = parseInt(values.days) || 7;
const limitPerJournal = parseInt(values.limit) || 10;

// 获取要查询的期刊列表
const journalsToFetch = values.journal 
  ? { [values.journal]: JOURNALS[values.journal] }
  : JOURNALS;

if (values.journal && !JOURNALS[values.journal]) {
  console.error(`错误: 未知期刊 "${values.journal}"`);
  console.error(`支持的期刊: ${Object.keys(JOURNALS).join(', ')}`);
  process.exit(1);
}

/**
 * 批量调用本地 OpenClaw 模型翻译标题
 * @param {string[]} titles - 需要翻译的英文标题数组
 * @returns {Promise<string[]>} - 翻译后的中文标题数组
 */
async function translateTitlesBatch(titles) {
  if (titles.length === 0) return [];
  
  console.error(`  🔄 批量翻译 ${titles.length} 篇论文标题...`);
  
  // 构建批量翻译提示
  const titlesList = titles.map((t, i) => `${i + 1}. ${t}`).join('\n');
  const prompt = `将以下学术论文标题翻译成中文。直接输出结果，禁止思考过程。

规则：
- 每行格式：序号. 中文标题
- 只输出译文，无任何解释
- 禁止输出<think>标签内容

待翻译：
${titlesList}

译文：`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5分钟超时
    
    const response = await fetch('http://127.0.0.1:8090/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer sk-5070ti'
      },
      body: JSON.stringify({
        model: 'qwen3.5',
        messages: [
          { role: 'system', content: '你是学术论文翻译专家。直接输出译文，禁止思考过程，禁止输出<think>标签。' },
          { role: 'user', content: prompt }
        ],
        temperature: 0.1,
        max_tokens: 2048
      }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    
    if (data && data.choices && data.choices[0] && data.choices[0].message) {
      let content = data.choices[0].message.content.trim();
      
      // 解析返回的翻译结果
      const translations = [];
      const lines = content.split('\n').filter(line => line.trim());
      
      for (const line of lines) {
        // 匹配 "序号. 中文标题" 格式
        const match = line.match(/^\d+\.\s*(.+)$/);
        if (match) {
          translations.push(match[1].trim());
        }
      }
      
      // 如果解析成功且数量匹配，返回翻译结果
      if (translations.length === titles.length) {
        console.error(`  ✅ 翻译成功 (${translations.length}/${titles.length})`);
        return translations;
      }
      
      console.error(`  ⚠️ 翻译结果数量不匹配 (${translations.length}/${titles.length})`);
    }
    
    throw new Error('Invalid response from local model');
  } catch (error) {
    if (error.name === 'AbortError') {
      console.error(`  ⚠️ 本地模型翻译超时`);
    } else {
      console.error(`  ⚠️ 本地模型批量翻译失败: ${error.message}`);
    }
    // 失败时返回原文
    return titles;
  }
}

/**
 * 从 RSS feed 获取论文
 */
async function fetchFromRSS(journalKey, journalConfig) {
  try {
    console.error(`📚 正在获取: ${journalConfig.name}...`);
    const response = await fetch(journalConfig.rss);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const xml = await response.text();
    
    // 解析 RSS XML
    const papers = parseRSS(xml, targetDate);
    
    console.error(`  📄 获取到 ${papers.length} 篇论文`);
    
    return {
      key: journalKey,
      name: journalConfig.name,
      field: journalConfig.field,
      publisher: journalConfig.publisher,
      papers: papers.slice(0, limitPerJournal) // 限制数量
    };
  } catch (error) {
    console.error(`  ❌ 获取 ${journalConfig.name} 失败:`, error.message);
    return {
      key: journalKey,
      name: journalConfig.name,
      field: journalConfig.field,
      publisher: journalConfig.publisher,
      papers: [],
      error: error.message
    };
  }
}

/**
 * 解析 RSS XML
 */
function parseRSS(xml, targetDate) {
  const papers = [];
  
  // 提取 item 元素
  const itemRegex = /<item>([\s\S]*?)<\/item>/g;
  let match;
  
  while ((match = itemRegex.exec(xml)) !== null) {
    const item = match[1];
    
    // 提取标题
    const titleMatch = item.match(/<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/);
    const title = titleMatch ? cleanXmlText(titleMatch[1]) : 'Unknown Title';
    
    // 提取链接
    const linkMatch = item.match(/<link>(.*?)<\/link>/);
    const url = linkMatch ? linkMatch[1] : '';
    
    // 提取作者
    const authorMatch = item.match(/<author>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/author>/) ||
                        item.match(/<dc:creator>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/dc:creator>/);
    const authors = authorMatch ? parseAuthors(cleanXmlText(authorMatch[1])) : [];
    
    // 提取 DOI（如果有）
    const doiMatch = item.match(/<prism:doi>(.*?)<\/prism:doi>/);
    const doi = doiMatch ? doiMatch[1] : '';
    
    // 提取发布日期（从 description 中的 Publication date）
    const descMatch = item.match(/<description>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/description>/);
    let abstract = '';
    let pubDate = null;
    
    if (descMatch) {
      const descContent = cleanXmlText(descMatch[1]);
      
      // 提取 Publication date
      const pubDateMatch = descContent.match(/Publication date:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})/);
      if (pubDateMatch) {
        pubDate = parsePublicationDate(pubDateMatch[1]);
      }
      
      // 提取摘要（去除 HTML 标签）
      abstract = descContent.replace(/<[^>]+>/g, ' ').trim();
      // 限制长度
      if (abstract.length > 500) {
        abstract = abstract.substring(0, 500) + '...';
      }
    }
    
    // 检查日期是否匹配目标日期范围
    const itemDateStr = pubDate ? pubDate.toISOString().split('T')[0] : null;
    
    // 只保留最近 N 天内发表的论文
    if (itemDateStr) {
      const itemDate = new Date(itemDateStr);
      const targetDateObj = new Date(targetDate);
      const daysDiff = (targetDateObj - itemDate) / (1000 * 60 * 60 * 24);
      
      // 只保留已发表的论文且在 N 天内
      if (daysDiff < 0 || daysDiff > recentDays) {
        continue;
      }
    }
    
    papers.push({
      title,
      authors,
      doi,
      url,
      abstract,
      published: itemDateStr || targetDate
    });
  }
  
  return papers;
}

/**
 * 清理 XML 文本
 */
function cleanXmlText(text) {
  return text
    .replace(/<!\[CDATA\[/g, '')
    .replace(/\]\]>/g, '')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .trim();
}

/**
 * 解析 Publication date 格式 (如 "12 June 2026")
 */
function parsePublicationDate(dateStr) {
  try {
    const months = {
      'January': 0, 'February': 1, 'March': 2, 'April': 3, 'May': 4, 'June': 5,
      'July': 6, 'August': 7, 'September': 8, 'October': 9, 'November': 10, 'December': 11
    };
    
    const match = dateStr.match(/(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})/);
    if (match) {
      const day = parseInt(match[1]);
      const month = months[match[2]];
      const year = parseInt(match[3]);
      
      if (month !== undefined) {
        return new Date(year, month, day);
      }
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * 解析作者列表
 */
function parseAuthors(authorStr) {
  if (!authorStr) return [];
  return authorStr
    .split(/,|;/)
    .map(a => a.trim())
    .filter(a => a.length > 0)
    .slice(0, 5); // 最多显示5个作者
}

/**
 * Markdown 格式（含中英文对照）
 */
function formatMarkdown(results) {
  let output = `# 📄 期刊论文日报 - ${targetDate}\n\n`;
  
  let totalPapers = 0;
  
  for (const journal of results) {
    output += `## ${journal.name}\n`;
    output += `*${journal.field} | ${journal.publisher}*\n\n`;
    
    if (journal.error) {
      output += `⚠️ 获取失败: ${journal.error}\n\n`;
      continue;
    }
    
    if (journal.papers.length === 0) {
      output += `*暂无新论文*\n\n`;
      continue;
    }
    
    for (const paper of journal.papers) {
      output += `### ${paper.title}\n`;
      output += `**中文标题**: ${paper.titleZh || '(翻译失败)'}\n\n`;
      if (paper.authors.length > 0) {
        output += `**作者**: ${paper.authors.join(', ')}\n`;
      }
      if (paper.doi) {
        output += `**DOI**: ${paper.doi}\n`;
      }
      if (paper.url) {
        output += `**链接**: ${paper.url}\n`;
      }
      output += '\n---\n\n';
      totalPapers++;
    }
  }
  
  output += `*总计 ${totalPapers} 篇论文*\n`;
  return output;
}

// 主函数
async function main() {
  console.error(`正在获取 ${targetDate} 前 ${recentDays} 天的期刊论文（每期刊最多 ${limitPerJournal} 篇）...\n`);
  
  const results = [];
  
  for (const [key, config] of Object.entries(journalsToFetch)) {
    if (!config) continue;
    
    const result = await fetchFromRSS(key, config);
    results.push(result);
    
    // 添加延迟避免请求过快
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  // 翻译论文标题 - 批量模式
  console.error("\n🌐 正在批量翻译论文标题...\n");
  
  for (const journal of results) {
    if (!journal.papers || journal.papers.length === 0) continue;
    
    console.error(`${journal.name}:`);
    
    // 收集所有标题进行批量翻译
    const titles = journal.papers.map(p => p.title);
    const translations = await translateTitlesBatch(titles);
    
    // 将翻译结果分配回每篇论文
    for (let i = 0; i < journal.papers.length; i++) {
      journal.papers[i].titleZh = translations[i] || journal.papers[i].title;
    }
    
    // 批次之间添加延迟
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  console.error("\n✅ 全部完成！\n");
  
  // 输出结果
  const output = formatMarkdown(results);
  console.log(output);
}

main().catch(error => {
  console.error('错误:', error);
  process.exit(1);
});
