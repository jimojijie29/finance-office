#!/usr/bin/env node
/**
 * Journal Papers Fetcher - MD文件批量翻译版本
 * 1. 获取论文生成英文MD文件
 * 2. 提取所有标题一次性批量翻译
 * 3. 替换标题生成最终中文MD文件
 */

import { parseArgs } from 'node:util';
import { writeFileSync, readFileSync, existsSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const WORKSPACE_DIR = join(__dirname, '..', '..');

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
    output: { type: 'string', short: 'o' },
    help: { type: 'boolean', short: 'h' }
  }
});

if (values.help) {
  console.log(`
用法: node fetch-md-translate.mjs [选项]

选项:
  -j, --journal <name>    特定期刊 (food-chemistry|jep|jasb|fsi)
  -d, --date <date>       指定日期 (YYYY-MM-DD，默认今天)
  -n, --days <days>       获取最近 N 天的论文 (默认 7)
  -l, --limit <num>       每期刊最多显示 N 篇 (默认 10)
  -o, --output <path>     输出文件路径 (默认自动生成)
  -h, --help              显示帮助
`);
  process.exit(0);
}

// 获取目标日期和参数
const targetDate = values.date || new Date().toISOString().split('T')[0];
const recentDays = parseInt(values.days) || 7;
const limitPerJournal = parseInt(values.limit) || 10;

// 自动生成输出文件路径
const outputPath = values.output || join(WORKSPACE_DIR, `journal-papers-${targetDate}.md`);

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
    console.error(`📚 正在获取: ${journalConfig.name}...`);
    const response = await fetch(journalConfig.rss);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const xml = await response.text();
    
    const papers = parseRSS(xml, targetDate);
    console.error(`  📄 获取到 ${papers.length} 篇论文`);
    
    return {
      key: journalKey,
      name: journalConfig.name,
      field: journalConfig.field,
      publisher: journalConfig.publisher,
      papers: papers.slice(0, limitPerJournal)
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
  const itemRegex = /<item>([\s\S]*?)<\/item>/g;
  let match;
  
  while ((match = itemRegex.exec(xml)) !== null) {
    const item = match[1];
    
    const titleMatch = item.match(/<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/);
    const title = titleMatch ? cleanXmlText(titleMatch[1]) : 'Unknown Title';
    
    const linkMatch = item.match(/<link>(.*?)<\/link>/);
    const url = linkMatch ? linkMatch[1] : '';
    
    const authorMatch = item.match(/<author>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/author>/) ||
                        item.match(/<dc:creator>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/dc:creator>/);
    const authors = authorMatch ? parseAuthors(cleanXmlText(authorMatch[1])) : [];
    
    const doiMatch = item.match(/<prism:doi>(.*?)<\/prism:doi>/);
    const doi = doiMatch ? doiMatch[1] : '';
    
    const descMatch = item.match(/<description>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/description>/);
    let abstract = '';
    let pubDate = null;
    
    if (descMatch) {
      const descContent = cleanXmlText(descMatch[1]);
      const pubDateMatch = descContent.match(/Publication date:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})/);
      if (pubDateMatch) {
        pubDate = parsePublicationDate(pubDateMatch[1]);
      }
      
      abstract = descContent.replace(/<[^>]+>/g, ' ').trim();
      if (abstract.length > 500) {
        abstract = abstract.substring(0, 500) + '...';
      }
    }
    
    const itemDateStr = pubDate ? pubDate.toISOString().split('T')[0] : null;
    
    if (itemDateStr) {
      const itemDate = new Date(itemDateStr);
      const targetDateObj = new Date(targetDate);
      const daysDiff = (targetDateObj - itemDate) / (1000 * 60 * 60 * 24);
      
      if (daysDiff < 0 || daysDiff > recentDays) {
        continue;
      }
    }
    
    papers.push({ title, authors, doi, url, abstract, published: itemDateStr || targetDate });
  }
  
  return papers;
}

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

function parseAuthors(authorStr) {
  if (!authorStr) return [];
  return authorStr
    .split(/,|;/)
    .map(a => a.trim())
    .filter(a => a.length > 0)
    .slice(0, 5);
}

/**
 * 生成英文MD文件（不含翻译）
 */
function generateEnglishMD(results) {
  let output = `# 📄 Journal Papers Daily - ${targetDate}\n\n`;
  
  let totalPapers = 0;
  
  for (const journal of results) {
    output += `## ${journal.name}\n`;
    output += `*${journal.field} | ${journal.publisher}*\n\n`;
    
    if (journal.error) {
      output += `⚠️ Fetch failed: ${journal.error}\n\n`;
      continue;
    }
    
    if (journal.papers.length === 0) {
      output += `*No new papers*\n\n`;
      continue;
    }
    
    for (const paper of journal.papers) {
      output += `### ${paper.title}\n`;
      output += `**Title_CN**: {{TRANSLATE:${paper.title}}}\n\n`;
      if (paper.authors.length > 0) {
        output += `**Authors**: ${paper.authors.join(', ')}\n`;
      }
      if (paper.doi) {
        output += `**DOI**: ${paper.doi}\n`;
      }
      if (paper.url) {
        output += `**Link**: ${paper.url}\n`;
      }
      if (paper.abstract) {
        output += `\n${paper.abstract}\n`;
      }
      output += '\n---\n\n';
      totalPapers++;
    }
  }
  
  output += `*Total ${totalPapers} papers*\n`;
  return { content: output, totalPapers };
}

/**
 * 提取所有需要翻译的标题
 */
function extractTitlesForTranslation(mdContent) {
  const titles = [];
  const regex = /\{\{TRANSLATE:(.+?)\}\}/g;
  let match;
  
  while ((match = regex.exec(mdContent)) !== null) {
    titles.push(match[1]);
  }
  
  return titles;
}

/**
 * 使用本地模型批量翻译标题 - 死命令法
 */
async function translateTitlesWithLocalModel(titles) {
  if (titles.length === 0) return {};
  
  console.error(`\n🌐 正在批量翻译 ${titles.length} 个标题...`);
  
  // 构建翻译列表
  const titlesList = titles.map((t, i) => `${i + 1}. ${t}`).join('\n');
  
  // 死命令式提示词
  const prompt = `你是一个专业的学术论文翻译专家。禁止输出任何 <think> 标签或思考过程。禁止进行任何解释。请直接、立即给出翻译结果，不准多说一个字。

将以下学术论文标题翻译成中文。每行格式：序号. 中文标题。只输出译文，无任何解释。

${titlesList}

译文：`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 600000); // 10分钟超时
    
    console.error('  ⏳ 正在调用本地模型...');
    
    const response = await fetch('http://127.0.0.1:8090/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer sk-5070ti'
      },
      body: JSON.stringify({
        model: 'qwen3.5',
        messages: [
          { 
            role: 'system', 
            content: '你是学术论文翻译专家。禁止输出任何 <think> 标签或思考过程。禁止进行任何解释。请直接、立即给出翻译结果，不准多说一个字。' 
          },
          { role: 'user', content: prompt }
        ],
        temperature: 0.1,
        max_tokens: 4096
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
      
      // 移除可能的 <think> 标签（以防万一）
      content = content.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
      
      // 解析翻译结果
      const translations = {};
      const lines = content.split('\n').filter(line => line.trim());
      
      for (const line of lines) {
        const match = line.match(/^\d+\.\s*(.+)$/);
        if (match) {
          const translatedTitle = match[1].trim();
          const index = parseInt(line.match(/^(\d+)\./)[1]) - 1;
          if (index >= 0 && index < titles.length) {
            translations[titles[index]] = translatedTitle;
          }
        }
      }
      
      console.error(`  ✅ 翻译完成 (${Object.keys(translations).length}/${titles.length})`);
      return translations;
    }
    
    throw new Error('Invalid response format');
  } catch (error) {
    if (error.name === 'AbortError') {
      console.error(`  ⚠️ 翻译超时`);
    } else {
      console.error(`  ⚠️ 翻译失败: ${error.message}`);
    }
    // 返回原文作为后备
    const fallback = {};
    for (const title of titles) {
      fallback[title] = title;
    }
    return fallback;
  }
}

/**
 * 替换MD中的翻译占位符
 */
function replaceTranslations(mdContent, translations) {
  let result = mdContent;
  
  for (const [original, translated] of Object.entries(translations)) {
    const placeholder = `{{TRANSLATE:${original.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}}}`;
    result = result.replace(new RegExp(placeholder, 'g'), translated);
  }
  
  // 清理任何剩余的占位符
  result = result.replace(/\{\{TRANSLATE:(.+?)\}\}/g, '$1');
  
  return result;
}

/**
 * 将英文期刊名和字段名翻译为中文
 */
function translateHeaders(mdContent) {
  const translations = {
    'Journal Papers Daily': '期刊论文日报',
    'Food Chemistry': 'Food Chemistry（食品化学）',
    'Journal of Ethnopharmacology': 'Journal of Ethnopharmacology（民族药理学）',
    'Journal of Animal Science and Biotechnology': 'Journal of Animal Science and Biotechnology（动物科学与生物技术）',
    'Fish & Shellfish Immunology': 'Fish & Shellfish Immunology（鱼类与贝类免疫学）',
    'Fetch failed': '获取失败',
    'No new papers': '暂无新论文',
    'Authors': '作者',
    'Link': '链接',
    'Total': '总计'
  };
  
  let result = mdContent;
  for (const [en, zh] of Object.entries(translations)) {
    result = result.replace(new RegExp(en, 'g'), zh);
  }
  
  return result;
}

// 主函数
async function main() {
  console.error(`正在获取 ${targetDate} 前 ${recentDays} 天的期刊论文...\n`);
  
  // 1. 获取所有期刊论文
  const results = [];
  for (const [key, config] of Object.entries(journalsToFetch)) {
    if (!config) continue;
    const result = await fetchFromRSS(key, config);
    results.push(result);
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  // 2. 生成英文MD文件
  console.error('\n📝 正在生成英文MD文件...');
  const { content: englishMD, totalPapers } = generateEnglishMD(results);
  
  if (totalPapers === 0) {
    console.error('⚠️ 未获取到任何论文，跳过翻译');
    writeFileSync(outputPath, englishMD, 'utf-8');
    console.error(`\n✅ 文件已保存: ${outputPath}`);
    return;
  }
  
  // 3. 提取需要翻译的标题
  const titlesToTranslate = extractTitlesForTranslation(englishMD);
  console.error(`📋 共需翻译 ${titlesToTranslate.length} 个标题`);
  
  // 4. 批量翻译标题
  const translations = await translateTitlesWithLocalModel(titlesToTranslate);
  
  // 5. 替换翻译内容
  console.error('🔄 正在替换翻译内容...');
  let finalMD = replaceTranslations(englishMD, translations);
  
  // 6. 翻译标题和字段名
  finalMD = translateHeaders(finalMD);
  
  // 7. 保存最终文件
  writeFileSync(outputPath, finalMD, 'utf-8');
  
  console.error(`\n✅ 完成！文件已保存: ${outputPath}`);
  console.error(`📊 总计: ${totalPapers} 篇论文`);
  
  // 输出文件内容到控制台
  console.log(finalMD);
}

main().catch(error => {
  console.error('错误:', error);
  process.exit(1);
});
