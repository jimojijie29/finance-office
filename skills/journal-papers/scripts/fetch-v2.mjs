#!/usr/bin/env node
/**
 * Journal Papers Fetcher - 优化版
 * 采用缓存+LLM翻译的架构，提供高质量中英文对照
 */

import { parseArgs } from 'node:util';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CACHE_DIR = join(__dirname, '..', 'cache');

// 确保缓存目录存在
if (!existsSync(CACHE_DIR)) {
  mkdirSync(CACHE_DIR, { recursive: true });
}

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
    rss: 'https://link.springer.com/journal/40104/articles?format=rss&flavour=recent',
    publisher: 'BMC/Springer Nature',
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
    format: { type: 'string', short: 'f', default: 'markdown' },
    translate: { type: 'boolean', short: 't', default: false },
    help: { type: 'boolean', short: 'h' }
  }
});

if (values.help) {
  console.log(`
用法: node fetch.mjs [选项]

选项:
  -j, --journal <name>    特定期刊 (food-chemistry|jep|jasb|fsi)
  -d, --date <date>       指定日期 (YYYY-MM-DD，默认今天)
  -n, --days <days>       获取最近 N 天的论文 (默认 7)
  -f, --format <format>   输出格式 (json|markdown|text|raw，默认 markdown)
  -t, --translate         启用LLM翻译模式（生成待翻译文件）
  -h, --help              显示帮助

示例:
  node fetch.mjs                          # 获取所有期刊最近7天论文
  node fetch.mjs -j food-chemistry        # 只获取 Food Chemistry
  node fetch.mjs -n 3                     # 获取最近3天的论文
  node fetch.mjs -t                       # 获取并生成待翻译文件
  node fetch.mjs -f raw                   # 仅获取原文，不翻译
`);
  process.exit(0);
}

// 获取目标日期和天数范围
const targetDate = values.date || new Date().toISOString().split('T')[0];
const recentDays = parseInt(values.days) || 7;

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
 * 从 RSS feed 获取论文
 */
async function fetchFromRSS(journalKey, journalConfig) {
  try {
    const response = await fetch(journalConfig.rss);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const xml = await response.text();
    const papers = parseRSS(xml, targetDate, recentDays);
    
    return {
      key: journalKey,
      name: journalConfig.name,
      field: journalConfig.field,
      publisher: journalConfig.publisher,
      papers: papers
    };
  } catch (error) {
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
function parseRSS(xml, targetDate, recentDays) {
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
    
    // 提取发布日期（多种格式）
    // 1. 尝试从 <pubDate> 获取
    const pubDateMatch = item.match(/<pubDate>(.*?)<\/pubDate>/);
    let pubDate = pubDateMatch ? parseRSSDate(pubDateMatch[1]) : null;
    
    // 2. 尝试从 <dc:date> 获取（BMC期刊格式）
    if (!pubDate) {
      const dcDateMatch = item.match(/<dc:date>(.*?)<\/dc:date>/);
      if (dcDateMatch) {
        pubDate = new Date(dcDateMatch[1]);
        if (isNaN(pubDate.getTime())) pubDate = null;
      }
    }
    
    // 3. 尝试从 <prism:publicationDate> 获取
    if (!pubDate) {
      const prismDateMatch = item.match(/<prism:publicationDate>(.*?)<\/prism:publicationDate>/);
      if (prismDateMatch) {
        pubDate = new Date(prismDateMatch[1]);
        if (isNaN(pubDate.getTime())) pubDate = null;
      }
    }
    
    // 4. 尝试从 description 中的 Publication date 获取（Elsevier 格式）
    const descMatch = item.match(/<description>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/description>/);
    let abstract = '';
    
    if (descMatch) {
      const descContent = cleanXmlText(descMatch[1]);
      
      // 提取 Publication date（如果还没有获取到）
      if (!pubDate) {
        const pubDateMatch = descContent.match(/Publication date:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})/);
        if (pubDateMatch) {
          pubDate = parsePublicationDate(pubDateMatch[1]);
        }
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
    
    // 如果获取到日期，进行日期过滤
    if (itemDateStr) {
      const itemDate = new Date(itemDateStr);
      const targetDateObj = new Date(targetDate);
      const daysDiff = (targetDateObj - itemDate) / (1000 * 60 * 60 * 24);
      
      // 只保留已发表的论文（发表日期 <= 目标日期）且在 N 天内
      // daysDiff >= 0 表示已发表，daysDiff <= recentDays 表示在 N 天内
      if (daysDiff < 0 || daysDiff > recentDays) {
        continue;
      }
    }
    // 如果没有获取到日期，默认保留（可能是RSS格式问题）
    
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
 * 解析 RSS pubDate 格式 (如 "Mon, 16 Mar 2026 00:00:00 GMT")
 */
function parseRSSDate(dateStr) {
  try {
    const date = new Date(dateStr);
    if (!isNaN(date.getTime())) {
      return date;
    }
    return null;
  } catch {
    return null;
  }
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
 * 保存原始数据到缓存文件
 */
function saveToCache(results) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const cacheFile = join(CACHE_DIR, `papers-${timestamp}.json`);
  
  const cacheData = {
    fetchDate: new Date().toISOString(),
    targetDate: targetDate,
    daysRange: recentDays,
    results: results
  };
  
  writeFileSync(cacheFile, JSON.stringify(cacheData, null, 2), 'utf-8');
  console.log(`\n💾 原始数据已保存到: ${cacheFile}`);
  
  return cacheFile;
}

/**
 * 生成待翻译的 Markdown 文件
 */
function generateTranslationTemplate(results) {
  let output = `# 待翻译论文列表\n\n`;
  output += `> 生成时间: ${new Date().toLocaleString('zh-CN')}\n`;
  output += `> 日期范围: ${targetDate} 前 ${recentDays} 天\n\n`;
  output += `---\n\n`;
  
  let totalCount = 0;
  
  for (const journal of results) {
    if (journal.papers.length === 0) continue;
    
    output += `## ${journal.name}\n`;
    output += `*${journal.field} | ${journal.publisher}*\n\n`;
    
    for (let i = 0; i < journal.papers.length; i++) {
      const paper = journal.papers[i];
      totalCount++;
      
      output += `### ${totalCount}. [待翻译]\n\n`;
      output += `**英文标题**: ${paper.title}\n\n`;
      output += `**中文标题**: \n\n`;
      output += `**作者**: ${paper.authors.join(', ')}\n\n`;
      output += `**期刊**: ${journal.name}\n\n`;
      output += `**链接**: ${paper.url}\n\n`;
      output += `**发表日期**: ${paper.published}\n\n`;
      output += `---\n\n`;
    }
  }
  
  output += `\n*总计 ${totalCount} 篇论文待翻译*\n`;
  
  const templateFile = join(CACHE_DIR, `to-translate-${targetDate}.md`);
  writeFileSync(templateFile, output, 'utf-8');
  console.log(`📝 翻译模板已生成: ${templateFile}`);
  
  return templateFile;
}

/**
 * 生成填充了翻译的 Markdown 文件（模拟LLM翻译结果）
 */
function generateTranslatedOutput(results) {
  let output = `# 📄 期刊论文日报 - ${targetDate}\n\n`;
  output += `> 本报告包含最新期刊论文的中英文对照\n`;
  output += `> 数据来源: Food Chemistry, Journal of Ethnopharmacology, Journal of Animal Science and Biotechnology, Fish & Shellfish Immunology\n\n`;
  output += `---\n\n`;
  
  let totalCount = 0;
  let journalCount = 0;
  
  for (const journal of results) {
    if (journal.papers.length === 0) continue;
    
    journalCount++;
    output += `## ${journal.name}\n`;
    output += `*${journal.field} | ${journal.publisher}*\n\n`;
    
    for (let i = 0; i < Math.min(journal.papers.length, 10); i++) {
      const paper = journal.papers[i];
      totalCount++;
      
      // 使用术语映射进行基础翻译
      const translatedTitle = translateByMap(paper.title);
      
      output += `### ${totalCount}. ${translatedTitle}\n\n`;
      output += `**英文标题**: ${paper.title}\n\n`;
      output += `**作者**: ${paper.authors.join(', ')}${paper.authors.length >= 5 ? ' 等' : ''}\n\n`;
      output += `**期刊**: ${journal.name}\n\n`;
      output += `**链接**: ${paper.url}\n\n`;
      if (paper.published !== targetDate) {
        output += `**发表日期**: ${paper.published}\n\n`;
      }
      output += `---\n\n`;
    }
  }
  
  output += `\n*总计 ${totalCount} 篇论文*\n`;
  
  return output;
}

/**
 * 学术术语中英对照映射（增强版）
 */
const TERM_MAP = {
  // 研究方法
  'proteomics': '蛋白质组学',
  'metabolomics': '代谢组学',
  'transcriptomics': '转录组学',
  'genomics': '基因组学',
  'analysis': '分析',
  'investigation': '研究',
  'evaluation': '评价',
  'assessment': '评估',
  'characterization': '表征',
  'identification': '鉴定',
  'quantification': '定量',
  'comparison': '比较',
  'correlation': '相关性',
  'mechanism': '机制',
  'insight': '深入探讨',
  
  // 处理技术
  'cold plasma': '冷等离子体',
  'pretreatment': '预处理',
  'treatment': '处理',
  'processing': '加工',
  'preparation': '制备',
  'extraction': '提取',
  'purification': '纯化',
  'separation': '分离',
  
  // 食品相关
  'sensory': '感官',
  'flavor': '风味',
  'taste': '味道',
  'aroma': '香气',
  'texture': '质地',
  'quality': '品质',
  'freshness': '新鲜度',
  'shelf life': '保质期',
  'storage': '贮藏',
  
  // 成分相关
  'protein': '蛋白质',
  'starch': '淀粉',
  'lipid': '脂质',
  'polysaccharide': '多糖',
  'peptide': '肽',
  'amino acid': '氨基酸',
  'fatty acid': '脂肪酸',
  'phenolic': '酚类',
  'antioxidant': '抗氧化',
  'bioactive': '生物活性',
  
  // 生物体
  'squid': '鱿鱼',
  'sea cucumber': '海参',
  'sea bass': '海鲈',
  'fish': '鱼类',
  'shellfish': '贝类',
  'honey': '蜂蜜',
  'tea': '茶叶',
  'beef': '牛肉',
  'meat': '肉类',
  'zebrafish': '斑马鱼',
  
  // 品质指标
  'physicochemical': '理化',
  'properties': '性质',
  'nutritional': '营养',
  'digestibility': '消化率',
  'bioavailability': '生物利用度',
  
  // 动词/形容词
  'enhance': '增强',
  'promote': '促进',
  'improve': '改善',
  'increase': '增加',
  'reduce': '降低',
  'decrease': '减少',
  'effect': '影响',
  'impact': '作用',
  'role': '作用',
  
  // 其他
  'structure': '结构',
  'function': '功能',
  'activity': '活性',
  'stability': '稳定性',
  'formation': '形成',
  'degradation': '降解',
  'oxidation': '氧化',
  'hydrolysis': '水解',
  'fermentation': '发酵',
  'gelation': '凝胶化',
  'emulsification': '乳化',
  'crosslinking': '交联',
  'esterification': '酯化',
  'microstructure': '微观结构',
  'molecular': '分子',
  'cellular': '细胞',
  'across': '在...条件下',
  'simulated': '模拟的',
  'conditions': '条件',
  'variation': '变化',
  'variations': '变化',
  'accumulation': '积累',
  'impart': '赋予',
  'imparting': '赋予',
  'development': '开发',
  'analogue': '类似物',
  
  // 药理学相关
  'antimalarial': '抗疟疾',
  'antiplasmodial': '抗疟原虫',
  'immunomodulatory': '免疫调节',
  'toxicity': '毒性',
  'cardiotoxicity': '心脏毒性',
  'developmental toxicity': '发育毒性',
  'in vitro': '体外',
  'in vivo': '体内',
  'network pharmacology': '网络药理学',
  'extract': '提取物',
  'compound': '化合物'
};

/**
 * 使用术语映射进行快速翻译
 */
function translateByMap(text) {
  let translated = text;
  
  // 按术语长度降序排序，优先替换长词组
  const sortedTerms = Object.keys(TERM_MAP).sort((a, b) => b.length - a.length);
  
  for (const term of sortedTerms) {
    const regex = new RegExp(`\\b${term}\\b`, 'gi');
    translated = translated.replace(regex, TERM_MAP[term]);
  }
  
  return translated;
}

/**
 * 格式化输出
 */
function formatOutput(results, format) {
  switch (format) {
    case 'json':
      return JSON.stringify({ date: targetDate, journals: results }, null, 2);
    
    case 'raw':
      // 仅返回原文，不翻译
      return formatRaw(results);
    
    case 'text':
      return formatText(results);
    
    case 'markdown':
    default:
      return generateTranslatedOutput(results);
  }
}

/**
 * 原始格式（无翻译）
 */
function formatRaw(results) {
  let output = `期刊论文原始数据 - ${targetDate}\n\n`;
  
  for (const journal of results) {
    output += `## ${journal.name}\n`;
    output += `Field: ${journal.field} | Publisher: ${journal.publisher}\n\n`;
    
    if (journal.error) {
      output += `Error: ${journal.error}\n\n`;
      continue;
    }
    
    if (journal.papers.length === 0) {
      output += `No papers found.\n\n`;
      continue;
    }
    
    for (let i = 0; i < journal.papers.length; i++) {
      const paper = journal.papers[i];
      output += `${i + 1}. ${paper.title}\n`;
      output += `   Authors: ${paper.authors.join(', ')}\n`;
      output += `   URL: ${paper.url}\n`;
      output += `   Published: ${paper.published}\n\n`;
    }
  }
  
  return output;
}

/**
 * 纯文本格式
 */
function formatText(results) {
  let output = `期刊论文日报 - ${targetDate}\n\n`;
  
  for (const journal of results) {
    output += `${journal.name} (${journal.field})\n`;
    output += `${'='.repeat(40)}\n\n`;
    
    if (journal.error) {
      output += `获取失败: ${journal.error}\n\n`;
      continue;
    }
    
    if (journal.papers.length === 0) {
      output += `暂无新论文\n\n`;
      continue;
    }
    
    for (let i = 0; i < journal.papers.length; i++) {
      const paper = journal.papers[i];
      const translatedTitle = translateByMap(paper.title);
      
      output += `${i + 1}. ${translatedTitle}\n`;
      output += `   英文: ${paper.title}\n`;
      output += `   作者: ${paper.authors.join(', ')}\n`;
      output += `   链接: ${paper.url}\n\n`;
    }
  }
  
  return output;
}

// 主函数
async function main() {
  console.log(`正在获取 ${targetDate} 前${recentDays}天的期刊论文...\n`);
  
  const results = [];
  
  for (const [key, config] of Object.entries(journalsToFetch)) {
    console.log(`📚 正在获取: ${config.name}...`);
    const result = await fetchFromRSS(key, config);
    results.push(result);
  }
  
  // 保存到缓存
  const cacheFile = saveToCache(results);
  
  // 如果启用翻译模式，生成待翻译模板
  if (values.translate) {
    const templateFile = generateTranslationTemplate(results);
    console.log(`\n✅ 完成！请查看翻译模板文件，填入中文翻译后保存。`);
    console.log(`   模板文件: ${templateFile}`);
  }
  
  // 输出结果
  const output = formatOutput(results, values.format);
  console.log('\n' + output);
  
  // 保存最终输出
  if (values.format === 'markdown') {
    const outputFile = join(CACHE_DIR, `journal-papers-${targetDate}.md`);
    writeFileSync(outputFile, output, 'utf-8');
    console.log(`\n📄 报告已保存: ${outputFile}`);
  }
}

main().catch(console.error);
