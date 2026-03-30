#!/usr/bin/env node
/**
 * Journal Papers Fetcher - PubMed API 版本
 * 使用 PubMed E-utilities API 从期刊获取最新论文
 * API Key: 110ca033b6321c49110dd352b7265c50b508
 */

import { parseArgs } from 'node:util';
import { writeFileSync } from 'node:fs';

// PubMed API 配置
const PUBMED_API_KEY = '110ca033b6321c49110dd352b7265c50b508';
const PUBMED_BASE_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils';



// 期刊配置（PubMed 期刊名）
const JOURNALS = {
  'food-chemistry': {
    name: 'Food Chemistry',
    pubmedName: 'Food Chem',
    publisher: 'Elsevier',
    field: '食品化学'
  },
  'jep': {
    name: 'Journal of Ethnopharmacology',
    pubmedName: 'J Ethnopharmacol',
    publisher: 'Elsevier',
    field: '民族药理学'
  },
  'jasb': {
    name: 'Journal of Animal Science and Biotechnology',
    pubmedName: 'J Anim Sci Biotechnol',
    publisher: 'BMC',
    field: '动物科学与生物技术'
  },
  'fsi': {
    name: 'Fish & Shellfish Immunology',
    pubmedName: 'Fish Shellfish Immunol',
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
    output: { type: 'string', short: 'o' },
    help: { type: 'boolean', short: 'h' }
  }
});

if (values.help) {
  console.log(`
用法: node fetch-pubmed.mjs [选项]

选项:
  -j, --journal <name>    特定期刊 (food-chemistry|jep|jasb|fsi)
  -d, --date <date>       指定日期 (YYYY-MM-DD，默认今天)
  -n, --days <days>       获取最近 N 天的论文 (默认 7)
  -f, --format <format>   输出格式 (json|markdown|text，默认 markdown)
  -o, --output <path>     输出文件路径
  -h, --help              显示帮助

示例:
  node fetch-pubmed.mjs                          # 获取所有期刊最近7天论文
  node fetch-pubmed.mjs -j jep                   # 只获取 Journal of Ethnopharmacology
  node fetch-pubmed.mjs -n 3                     # 获取最近3天的论文
  node fetch-pubmed.mjs -o papers.md             # 保存到指定文件
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
 * 使用 PubMed E-utilities API 搜索论文
 */
async function searchPubMed(journalName, startDate, endDate) {
  const query = `"${journalName}"[Journal] AND ("${startDate}"[Date - Publication] : "${endDate}"[Date - Publication])`;
  const url = `${PUBMED_BASE_URL}/esearch.fcgi?db=pubmed&term=${encodeURIComponent(query)}&retmax=100&sort=date&retmode=json&api_key=${PUBMED_API_KEY}`;
  
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    return data.esearchresult.idlist || [];
  } catch (error) {
    console.error(`搜索 ${journalName} 失败:`, error.message);
    return [];
  }
}

/**
 * 使用 PubMed E-utilities API 获取论文详情
 */
async function fetchPubMedDetails(pmids) {
  if (pmids.length === 0) return [];
  
  const url = `${PUBMED_BASE_URL}/esummary.fcgi?db=pubmed&id=${pmids.join(',')}&retmode=json&api_key=${PUBMED_API_KEY}`;
  
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    
    const papers = [];
    for (const pmid of pmids) {
      const article = data.result[pmid];
      if (!article) continue;
      
      const authors = article.authors 
        ? article.authors.map(a => a.name).slice(0, 5)
        : [];
      
      papers.push({
        title: article.title || '',
        authors: authors,
        doi: article.elocationid || '',
        pmid: pmid,
        url: `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`,
        published: article.pubdate || '',
        abstract: ''
      });
    }
    return papers;
  } catch (error) {
    console.error(`获取论文详情失败:`, error.message);
    return [];
  }
}

/**
 * 学术术语中英对照映射
 */
const TERM_MAP = {
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
  'cold plasma': '冷等离子体',
  'pretreatment': '预处理',
  'treatment': '处理',
  'processing': '加工',
  'preparation': '制备',
  'extraction': '提取',
  'purification': '纯化',
  'separation': '分离',
  'sensory': '感官',
  'flavor': '风味',
  'taste': '味道',
  'aroma': '香气',
  'texture': '质地',
  'quality': '品质',
  'freshness': '新鲜度',
  'shelf life': '保质期',
  'storage': '贮藏',
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
  'squid': '鱿鱼',
  'sea cucumber': '海参',
  'sea bass': '海鲈',
  'fish': '鱼类',
  'shellfish': '贝类',
  'honey': '蜂蜜',
  'tea': '茶叶',
  'beef': '牛肉',
  'meat': '肉类',
  'physicochemical': '理化',
  'properties': '性质',
  'nutritional': '营养',
  'digestibility': '消化率',
  'bioavailability': '生物利用度',
  'enhance': '增强',
  'promote': '促进',
  'improve': '改善',
  'increase': '增加',
  'reduce': '降低',
  'decrease': '减少',
  'effect': '影响',
  'impact': '作用',
  'role': '作用',
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
  'antimalarial': '抗疟疾',
  'antiplasmodial': '抗疟原虫',
  'immunomodulatory': '免疫调节',
  'toxicity': '毒性',
  'cardiotoxicity': '心脏毒性',
  'developmental toxicity': '发育毒性',
  'in vitro': '体外',
  'in vivo': '体内',
  'network pharmacology': '网络药理学',
  'zebrafish': '斑马鱼',
  'extract': '提取物',
  'compound': '化合物'
};

/**
 * 使用术语映射进行快速翻译
 */
function translateByMap(text) {
  let translated = text;
  const sortedTerms = Object.keys(TERM_MAP).sort((a, b) => b.length - a.length);
  
  for (const term of sortedTerms) {
    const regex = new RegExp(`\\b${term}\\b`, 'gi');
    translated = translated.replace(regex, TERM_MAP[term]);
  }
  
  return translated;
}

/**
 * 翻译论文标题 - 仅使用术语映射
 */
function translateTitle(text) {
  // 直接使用术语映射翻译，不调用大模型 API
  return translateByMap(text);
}

/**
 * 格式化输出
 */
function formatOutput(results, format) {
  switch (format) {
    case 'json':
      return JSON.stringify({ date: targetDate, journals: results }, null, 2);
    case 'text':
      return formatText(results);
    case 'markdown':
    default:
      return formatMarkdown(results);
  }
}

/**
 * Markdown 格式
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
    
    for (const paper of journal.papers.slice(0, 20)) {
      output += `### ${paper.title}\n`;
      output += `**中文标题**: ${paper.titleZh || '翻译中...'}\n\n`;
      if (paper.authors.length > 0) {
        output += `**作者**: ${paper.authors.join(', ')}\n`;
      }
      if (paper.doi) {
        output += `**DOI**: ${paper.doi}\n`;
      }
      output += `**PMID**: ${paper.pmid}\n`;
      output += `**链接**: ${paper.url}\n`;
      output += '\n---\n\n';
      totalPapers++;
    }
  }
  
  output += `\n*总计 ${totalPapers} 篇论文*\n`;
  return output;
}

/**
 * 纯文本格式
 */
function formatText(results) {
  let output = `期刊论文日报 - ${targetDate}\n`;
  output += '='.repeat(50) + '\n\n';
  
  for (const journal of results) {
    output += `${journal.name} (${journal.field})\n`;
    output += '-'.repeat(40) + '\n';
    
    if (journal.error) {
      output += `获取失败: ${journal.error}\n\n`;
      continue;
    }
    
    if (journal.papers.length === 0) {
      output += `暂无新论文\n\n`;
      continue;
    }
    
    for (const paper of journal.papers.slice(0, 10)) {
      output += `英文: ${paper.title}\n`;
      output += `中文: ${paper.titleZh || '翻译中...'}\n`;
      if (paper.authors.length > 0) {
        output += `作者: ${paper.authors.join(', ')}\n`;
      }
      output += `PMID: ${paper.pmid}\n`;
      output += `链接: ${paper.url}\n\n`;
    }
    output += '\n';
  }
  
  return output;
}

// 主函数
async function main() {
  console.error(`正在使用 PubMed API 获取 ${targetDate} 前 ${recentDays} 天的期刊论文...\n`);
  
  // 计算日期范围
  const endDate = new Date(targetDate);
  const startDate = new Date(endDate);
  startDate.setDate(startDate.getDate() - recentDays);
  
  const startDateStr = startDate.toISOString().split('T')[0];
  const endDateStr = endDate.toISOString().split('T')[0];
  
  console.error(`日期范围: ${startDateStr} 至 ${endDateStr}\n`);
  
  const results = [];
  
  for (const [key, config] of Object.entries(journalsToFetch)) {
    if (!config) continue;
    
    console.error(`📚 正在获取: ${config.name}...`);
    
    // 搜索 PubMed
    const pmids = await searchPubMed(config.pubmedName, startDateStr, endDateStr);
    console.error(`  找到 ${pmids.length} 篇论文`);
    
    // 获取论文详情
    const papers = await fetchPubMedDetails(pmids);
    
    results.push({
      key: key,
      name: config.name,
      field: config.field,
      publisher: config.publisher,
      papers: papers
    });
    
    // PubMed API 有速率限制，添加延迟
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  // 翻译论文标题
  console.error("\n🌐 正在将论文标题翻译为中文（术语映射模式）...");

  for (const journal of results) {
    if (!journal.papers || journal.papers.length === 0) continue;

    console.error(`  正在翻译 ${journal.name} 的 ${journal.papers.length} 篇论文...`);

    for (let i = 0; i < journal.papers.length; i++) {
      const paper = journal.papers[i];
      paper.titleZh = translateByMap(paper.title);
    }
    console.error(`    完成 ${journal.papers.length} 篇翻译`);
  }

  console.error("\n✅ 翻译完成！\n");
  
  // 输出结果
  const output = formatOutput(results, values.format);
  
  // 如果指定了输出文件，写入文件
  if (values.output) {
    writeFileSync(values.output, output, 'utf-8');
    console.error(`结果已保存到: ${values.output}`);
  }
  
  console.log(output);
}

main().catch(error => {
  console.error('错误:', error);
  process.exit(1);
});
