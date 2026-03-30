#!/usr/bin/env node
/**
 * Journal Papers Fetcher
 * 从 PubMed API 获取指定期刊最新论文，并使用本地模型进行中英文对照翻译
 */

import { parseArgs } from 'node:util';

// PubMed API Key
const PUBMED_API_KEY = '110ca033b6321c49110dd352b7265c50b508';

// 期刊配置 - PubMed 期刊名称
const JOURNALS = {
  'food-chemistry': {
    name: 'Food Chemistry',
    pubmedName: 'Food Chem',
    publisher: 'Elsevier',
    field: '食品化学',
    systemPrompt: '你是食品化学领域的学术论文翻译专家，熟悉食品成分、加工工艺、品质分析、风味化学、贮藏保鲜等专业术语。翻译时保持学术规范，术语准确。直接输出译文，禁止思考过程。'
  },
  'jep': {
    name: 'Journal of Ethnopharmacology',
    pubmedName: 'J Ethnopharmacol',
    publisher: 'Elsevier',
    field: '民族药理学',
    systemPrompt: '你是民族药理学领域的学术论文翻译专家，熟悉天然产物、药理活性、传统药物、植物化学、分子机制等专业术语。翻译时保持学术规范，术语准确。直接输出译文，禁止思考过程。'
  },
  'jasb': {
    name: 'Journal of Animal Science and Biotechnology',
    pubmedName: 'J Anim Sci Biotechnol',
    publisher: 'BMC',
    field: '动物科学与生物技术',
    systemPrompt: '你是动物科学与生物技术领域的学术论文翻译专家，熟悉动物营养、基因工程、畜牧生产、饲料科学、繁殖技术等专业术语。翻译时保持学术规范，术语准确。直接输出译文，禁止思考过程。'
  },
  'fsi': {
    name: 'Fish & Shellfish Immunology',
    pubmedName: 'Fish Shellfish Immunol',
    publisher: 'Elsevier',
    field: '鱼类与贝类免疫学',
    systemPrompt: '你是水产免疫学领域的学术论文翻译专家，熟悉鱼类免疫、贝类免疫、病害防控、疫苗开发、免疫应答等专业术语。翻译时保持学术规范，术语准确。直接输出译文，禁止思考过程。'
  }
};

// 解析命令行参数
const { values } = parseArgs({
  options: {
    journal: { type: 'string', short: 'j' },
    date: { type: 'string', short: 'd' },
    days: { type: 'string', short: 'n', default: '7' },
    format: { type: 'string', short: 'f', default: 'markdown' },
    'no-translate': { type: 'boolean', default: false },
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
  -f, --format <format>   输出格式 (json|markdown|text，默认 markdown)
  --no-translate          不使用大模型翻译，仅用术语映射
  -h, --help              显示帮助

示例:
  node fetch.mjs                          # 获取所有期刊最近7天论文
  node fetch.mjs -j food-chemistry        # 只获取 Food Chemistry
  node fetch.mjs -n 3                     # 获取最近3天的论文
  node fetch.mjs -d 2026-03-16 -n 7       # 获取指定日期前7天的论文
  node fetch.mjs -f json                  # JSON 格式输出
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
 * 学术术语中英对照映射（作为 API 失败时的后备）
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
  'zebrafish': '斑马鱼',
  'extract': '提取物',
  'compound': '化合物'
};

/**
 * 用户研究方向关键词（用于智能筛选）
 */
const RESEARCH_KEYWORDS = {
  // 南药相关
  '南药': ['herbal', 'traditional medicine', 'medicinal plant', 'natural product', 'ethnopharmacology', 'phytochemical', 'Callicarpa', 'Morinda', 'noni'],
  // 动物饲料相关
  '动物饲料': ['feed', 'animal nutrition', 'livestock', 'poultry', 'aquaculture', 'probiotic', 'gut health', 'intestinal', 'growth performance'],
  // 食品科学相关
  '食品科学': ['food preservation', 'storage', 'freshness', 'shelf life', 'active compound', 'antioxidant', 'bioactive', 'phenolic'],
  // 药理活性相关
  '药理活性': ['anti-inflammatory', 'antimicrobial', 'antibacterial', 'antiviral', 'immunomodulatory', 'antioxidant activity', 'pharmacological']
};

/**
 * 计算论文与用户研究方向的匹配分数
 * @param {string} title - 论文标题
 * @returns {number} - 匹配分数（越高越相关）
 */
function calculateRelevanceScore(title) {
  const lowerTitle = title.toLowerCase();
  let score = 0;
  
  for (const [category, keywords] of Object.entries(RESEARCH_KEYWORDS)) {
    for (const keyword of keywords) {
      if (lowerTitle.includes(keyword.toLowerCase())) {
        score += 1;
        // 南药和动物饲料相关权重更高
        if (category === '南药' || category === '动物饲料') {
          score += 1;
        }
      }
    }
  }
  
  return score;
}

/**
 * 智能筛选论文（超过30篇时根据研究方向筛选）
 * @param {Array} papers - 论文列表
 * @param {number} maxPapers - 最大返回数量
 * @returns {Array} - 筛选后的论文列表
 */
function filterPapersByRelevance(papers, maxPapers = 30) {
  if (papers.length <= maxPapers) {
    return papers;
  }
  
  // 计算每篇论文的相关性分数
  const papersWithScore = papers.map(paper => ({
    ...paper,
    relevanceScore: calculateRelevanceScore(paper.title)
  }));
  
  // 按相关性分数排序（高到低）
  papersWithScore.sort((a, b) => b.relevanceScore - a.relevanceScore);
  
  // 返回前 maxPapers 篇
  return papersWithScore.slice(0, maxPapers);
}

/**
 * 使用术语映射进行快速翻译（作为后备方案）
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
 * 从 PubMed API 搜索论文（带超时和 RSS 备用）
 * @param {string} journalName - PubMed 期刊名称
 * @param {string} startDate - 开始日期 (YYYY/MM/DD)
 * @param {string} endDate - 结束日期 (YYYY/MM/DD)
 * @param {string} journalKey - 期刊 key（用于 RSS 备用）
 * @returns {Promise<Object>} - { source: 'pubmed'|'rss', pmids: Array, rssPapers: Array }
 */
async function searchPubMed(journalName, startDate, endDate, journalKey) {
  const query = `"${journalName}"[Journal] AND ("${startDate}"[Date - Publication] : "${endDate}"[Date - Publication])`;
  const url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=${encodeURIComponent(query)}&retmax=100&sort=date&retmode=json&api_key=${PUBMED_API_KEY}`;

  // 创建带超时的 fetch
  const fetchWithTimeout = async (url, timeout = 30000) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  };

  try {
    const response = await fetchWithTimeout(url, 30000); // 30秒超时
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    const pmids = data.esearchresult.idlist || [];

    // 如果 PubMed 返回结果，直接返回
    if (pmids.length > 0) {
      return { source: 'pubmed', pmids, rssPapers: [] };
    }

    // PubMed 返回空结果，尝试 RSS 备用
    console.error(`  PubMed 返回空结果，尝试 RSS 备用...`);
    const rssPapers = await fetchFromRSS(journalKey, startDate, endDate);
    return { source: 'rss', pmids: [], rssPapers };

  } catch (error) {
    console.error(`  PubMed API 失败: ${error.message}，尝试 RSS 备用...`);
    const rssPapers = await fetchFromRSS(journalKey, startDate, endDate);
    return { source: 'rss', pmids: [], rssPapers };
  }
}

/**
 * RSS 备用方案 - 从期刊官网 RSS 获取论文
 * @param {string} journalKey - 期刊 key
 * @param {string} startDate - 开始日期 (YYYY/MM/DD)
 * @param {string} endDate - 结束日期 (YYYY/MM/DD)
 * @returns {Promise<Array>} - 论文列表
 */
async function fetchFromRSS(journalKey, startDate, endDate) {
  // RSS 源配置
  const RSS_SOURCES = {
    'food-chemistry': {
      name: 'Food Chemistry',
      rssUrl: 'https://rss.sciencedirect.com/publication/science/03088146',
      publisher: 'Elsevier'
    },
    'jep': {
      name: 'Journal of Ethnopharmacology',
      rssUrl: 'https://rss.sciencedirect.com/publication/science/03788741',
      publisher: 'Elsevier'
    },
    'jasb': {
      name: 'Journal of Animal Science and Biotechnology',
      rssUrl: 'https://jasbsci.biomedcentral.com/rss.xml',
      publisher: 'BMC'
    },
    'fsi': {
      name: 'Fish & Shellfish Immunology',
      rssUrl: 'https://rss.sciencedirect.com/publication/science/10504648',
      publisher: 'Elsevier'
    }
  };

  const config = RSS_SOURCES[journalKey];
  if (!config) {
    console.error(`  未配置 RSS 源: ${journalKey}`);
    return [];
  }

  try {
    console.error(`  从 RSS 获取: ${config.name}...`);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000);

    const response = await fetch(config.rssUrl, {
      signal: controller.signal,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const xml = await response.text();
    
    // 检查返回的是否是有效的 RSS XML，还是 HTML 页面（如 BMC 迁移后的情况）
    if (!xml.includes('<?xml') && !xml.includes('<rss') && !xml.includes('<feed')) {
      console.error(`  RSS 返回的不是 XML，可能是 HTML 页面`);
      throw new Error('Invalid RSS format - received HTML instead of XML');
    }
    
    const papers = parseRSSXML(xml, startDate, endDate);

    console.error(`  RSS 获取成功: ${papers.length} 篇论文`);
    return papers;

  } catch (error) {
    console.error(`  RSS 获取失败: ${error.message}`);
    
    // JASB 特殊处理：如果 RSS 失败，尝试从 Springer Link 页面抓取
    if (journalKey === 'jasb') {
      console.error(`  尝试从 Springer Link 页面抓取...`);
      return await fetchFromSpringerLink(startDate, endDate);
    }
    
    return [];
  }
}

/**
 * 从 Springer Link 页面抓取 JASB 论文
 * 作为 RSS 失败时的备用方案
 * @param {string} startDate - 开始日期 (YYYY/MM/DD)
 * @param {string} endDate - 结束日期 (YYYY/MM/DD)
 * @returns {Promise<Array>} - 论文列表
 */
async function fetchFromSpringerLink(startDate, endDate) {
  const url = 'https://link.springer.com/journal/40104/articles';
  
  try {
    console.error(`  从 Springer Link 获取: Journal of Animal Science and Biotechnology...`);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000);
    
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
      }
    });
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const html = await response.text();
    const papers = parseSpringerHTML(html, startDate, endDate);
    
    console.error(`  Springer Link 获取成功: ${papers.length} 篇论文`);
    return papers;
    
  } catch (error) {
    console.error(`  Springer Link 获取失败: ${error.message}`);
    return [];
  }
}

/**
 * 解析 Springer Link HTML 页面
 * @param {string} html - HTML 内容
 * @param {string} startDate - 开始日期 (YYYY/MM/DD)
 * @param {string} endDate - 结束日期 (YYYY/MM/DD)
 * @returns {Array} - 论文列表
 */
function parseSpringerHTML(html, startDate, endDate) {
  const papers = [];
  
  // 解析日期范围
  const start = new Date(startDate.replace(/\//g, '-'));
  const end = new Date(endDate.replace(/\//g, '-'));
  end.setHours(23, 59, 59);
  
  // 扩展日期范围：向后延伸180天以捕获预发布论文
  const extendedEnd = new Date(end);
  extendedEnd.setDate(extendedEnd.getDate() + 180);
  
  // 提取文章数据 - 匹配 Springer Link 的文章结构
  // 文章标题
  const titleRegex = /<h2[^>]*class="[^"]*c-card__title[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)<\/a>.*?<\/h2>/gi;
  // 发布日期
  const dateRegex = /<span[^>]*class="[^"]*c-meta__item[^"]*"[^>]*>(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})<\/span>/gi;
  
  let titleMatch;
  let dateMatch;
  const articles = [];
  
  // 先提取所有文章信息
  const articleRegex = /<article[^>]*class="[^"]*c-card[^"]*"[^>]*>([\s\S]*?)<\/article>/gi;
  let articleMatch;
  
  while ((articleMatch = articleRegex.exec(html)) !== null) {
    const articleHtml = articleMatch[1];
    
    // 提取标题和链接
    const titleLinkMatch = articleHtml.match(/<h2[^>]*class="[^"]*c-card__title[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/i);
    if (!titleLinkMatch) continue;
    
    let title = titleLinkMatch[2].replace(/<[^>]+>/g, '').trim();
    let url = titleLinkMatch[1];
    if (!url.startsWith('http')) {
      url = 'https://link.springer.com' + url;
    }
    
    // 提取日期
    const dateMatch = articleHtml.match(/<span[^>]*class="[^"]*c-meta__item[^"]*"[^>]*>(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})<\/span>/i);
    let pubDate = null;
    
    if (dateMatch) {
      const day = dateMatch[1].padStart(2, '0');
      const monthMap = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
        'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12',
        'January': '01', 'February': '02', 'March': '03', 'April': '04', 'June': '06',
        'July': '07', 'August': '08', 'September': '09', 'October': '10', 'November': '11', 'December': '12'
      };
      const month = monthMap[dateMatch[2]] || '01';
      const year = dateMatch[3];
      pubDate = new Date(`${year}-${month}-${day}`);
    }
    
    // 检查日期是否在范围内
    if (pubDate && pubDate >= start && pubDate <= extendedEnd) {
      papers.push({
        title,
        url,
        published: pubDate.toISOString().split('T')[0]
      });
    }
  }
  
  return papers;
}

/**
 * 解析 RSS XML
 * 支持预发布论文（未来日期）的获取
 */
function parseRSSXML(xml, startDate, endDate) {
  const papers = [];

  // 解析日期范围
  const start = new Date(startDate.replace(/\//g, '-'));
  const end = new Date(endDate.replace(/\//g, '-'));
  end.setHours(23, 59, 59);

  // 扩展日期范围：向后延伸180天以捕获预发布论文
  const extendedEnd = new Date(end);
  extendedEnd.setDate(extendedEnd.getDate() + 180);

  // 提取 item 元素
  const itemRegex = /<item>([\s\S]*?)<\/item>/g;
  let match;

  while ((match = itemRegex.exec(xml)) !== null) {
    const item = match[1];

    // 提取标题
    const titleMatch = item.match(/<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/);
    const title = titleMatch ? cleanXmlText(titleMatch[1]) : '';

    // 提取链接
    const linkMatch = item.match(/<link>([^<]+)<\/link>/);
    const url = linkMatch ? linkMatch[1] : '';

    // 提取发布日期 - 优先从 description 中提取 Publication date
    let pubDate = null;
    
    // 尝试从 description 中提取 Publication date: DD MMM YYYY
    const descMatch = item.match(/<description>[\s\S]*?Publication date:\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})[\s\S]*?<\/description>/);
    if (descMatch) {
      const day = descMatch[1].padStart(2, '0');
      const monthMap = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
        'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
      };
      const month = monthMap[descMatch[2]] || '01';
      const year = descMatch[3];
      pubDate = new Date(`${year}-${month}-${day}`);
    } else {
      // 尝试提取格式: "Publication date: June 2026" (只有月份)
      const monthYearMatch = item.match(/<description>[\s\S]*?Publication date:\s*([A-Za-z]+)\s+(\d{4})[\s\S]*?<\/description>/);
      if (monthYearMatch) {
        const monthMap = {
          'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
          'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12',
          'January': '01', 'February': '02', 'March': '03', 'April': '04', 'June': '06',
          'July': '07', 'August': '08', 'September': '09', 'October': '10', 'November': '11', 'December': '12'
        };
        const month = monthMap[monthYearMatch[1]] || '01';
        const year = monthYearMatch[2];
        // 使用月份第一天作为默认日期
        pubDate = new Date(`${year}-${month}-01`);
      } else {
        // 尝试提取 "Available online DD MMM YYYY" 格式
        const onlineMatch = item.match(/<description>[\s\S]*?Available online\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})[\s\S]*?<\/description>/);
        if (onlineMatch) {
          const day = onlineMatch[1].padStart(2, '0');
          const monthMap = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
            'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
          };
          const month = monthMap[onlineMatch[2]] || '01';
          const year = onlineMatch[3];
          pubDate = new Date(`${year}-${month}-${day}`);
        } else {
          // 回退到 pubDate
          const dateMatch = item.match(/<pubDate>([^<]+)<\/pubDate>/);
          if (dateMatch) {
            pubDate = new Date(dateMatch[1]);
          }
        }
      }
    }

    // 检查日期是否在扩展范围内（包含未来180天的预发布论文）
    if (pubDate && pubDate >= start && pubDate <= extendedEnd) {
      papers.push({
        title,
        url,
        published: pubDate.toISOString().split('T')[0]
      });
    }
  }

  return papers;
}

/**
 * 从 PubMed API 获取论文详情
 * @param {Array<string>} pmids - PMID 列表
 * @returns {Promise<Array>} - 论文详情列表
 */
async function fetchPubMedDetails(pmids) {
  if (pmids.length === 0) return [];

  const url = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=${pmids.join(',')}&retmode=xml&api_key=${PUBMED_API_KEY}`;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const xml = await response.text();
    return parsePubMedXML(xml);
  } catch (error) {
    console.error(`获取论文详情失败:`, error.message);
    return [];
  }
}

/**
 * 解析 PubMed XML 响应
 * @param {string} xml - XML 字符串
 * @returns {Array} - 论文列表
 */
function parsePubMedXML(xml) {
  const papers = [];

  // 提取 PubmedArticle 元素
  const articleRegex = /<PubmedArticle>([\s\S]*?)<\/PubmedArticle>/g;
  let match;

  while ((match = articleRegex.exec(xml)) !== null) {
    const article = match[1];

    // 提取 PMID
    const pmidMatch = article.match(/<PMID[^>]*>(\d+)<\/PMID>/);
    const pmid = pmidMatch ? pmidMatch[1] : '';

    // 提取标题
    const titleMatch = article.match(/<ArticleTitle>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/ArticleTitle>/);
    const title = titleMatch ? cleanXmlText(titleMatch[1]) : 'Unknown Title';

    // 提取作者
    const authors = [];
    const authorRegex = /<Author[^>]*>[\s\S]*?<LastName>([^<]+)<\/LastName>[\s\S]*?<ForeName>([^<]+)<\/ForeName>[\s\S]*?<\/Author>/g;
    let authorMatch;
    while ((authorMatch = authorRegex.exec(article)) !== null) {
      authors.push(`${authorMatch[2]} ${authorMatch[1]}`);
    }

    // 提取摘要
    const abstractMatch = article.match(/<AbstractText[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/AbstractText>/);
    let abstract = abstractMatch ? cleanXmlText(abstractMatch[1]) : '';
    // 限制长度
    if (abstract.length > 500) {
      abstract = abstract.substring(0, 500) + '...';
    }

    // 提取 DOI
    const doiMatch = article.match(/<ArticleId IdType="doi">([^<]+)<\/ArticleId>/);
    const doi = doiMatch ? doiMatch[1] : '';

    // 提取发表日期
    const dateMatch = article.match(/<PubDate>.*?<Year>(\d{4})<\/Year>.*?<Month>([^<]+)<\/Month>.*?<Day>(\d+)<\/Day>.*?<\/PubDate>/);
    let published = '';
    if (dateMatch) {
      const monthMap = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
        'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
      };
      const month = monthMap[dateMatch[2]] || dateMatch[2];
      published = `${dateMatch[1]}-${month}-${dateMatch[3].padStart(2, '0')}`;
    }

    // 构建 PubMed URL
    const url = pmid ? `https://pubmed.ncbi.nlm.nih.gov/${pmid}/` : '';

    papers.push({
      title,
      authors: authors.slice(0, 10), // 最多10个作者
      doi,
      url,
      abstract,
      published,
      pmid
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
 * 使用隔离上下文翻译标题（方案B）
 * @param {string[]} titles - 英文标题数组
 * @param {string} journalKey - 期刊key
 * @returns {Promise<string[]>} - 中文标题数组
 */
async function translateTitlesIsolated(titles, journalKey) {
  if (titles.length === 0) return [];

  const config = JOURNALS[journalKey];
  const systemPrompt = config?.systemPrompt || '你是学术论文翻译专家。直接输出译文，禁止思考过程。';

  const BATCH_SIZE = 10;
  const allTranslations = [];

  for (let i = 0; i < titles.length; i += BATCH_SIZE) {
    const batch = titles.slice(i, i + BATCH_SIZE);
    const translations = await translateBatchIsolated(batch, systemPrompt, i + 1);

    if (translations) {
      allTranslations.push(...translations);
    } else {
      // 翻译失败，使用术语映射后备
      console.error(`  ⚠️ 批次 ${Math.floor(i/BATCH_SIZE) + 1} 翻译失败，使用术语映射后备`);
      const fallbackTranslations = batch.map(t => translateByMap(t));
      allTranslations.push(...fallbackTranslations);
    }

    // 批次之间添加延迟，避免触发本地模型速率限制
    if (i + BATCH_SIZE < titles.length) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  return allTranslations;
}

/**
 * 单批次隔离翻译（每次请求独立上下文）
 * @param {string[]} titles - 需要翻译的标题数组
 * @param {string} systemPrompt - 系统提示（期刊定制化）
 * @param {number} startIndex - 起始序号
 * @returns {Promise<string[]|null>} - 翻译后的标题数组，失败返回null
 */
async function translateBatchIsolated(titles, systemPrompt, startIndex) {
  const titlesList = titles.map((t, i) => `${startIndex + i}. ${t}`).join('\n');

  const prompt = `请将以下论文标题翻译为中文，要求：
1. 准确传达原意
2. 使用学术规范术语
3. 只输出翻译结果，不要有任何解释或思考过程
4. 必须严格按照格式输出，每行一个：序号. 中文标题

待翻译：
${titlesList}

译文（直接输出，不要思考）：`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1800000); // 30分钟超时

    const response = await fetch('http://127.0.0.1:1234/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer sk-5070ti'
      },
      body: JSON.stringify({
        model: 'qwen3-vl-8b',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: prompt }
        ],
        temperature: 0.1,
        max_tokens: 2048
        // 关键：不传递 conversation_id，确保每次请求独立上下文
      }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    if (data && data.choices && data.choices[0] && data.choices[0].message) {
      const message = data.choices[0].message;
      // 优先使用 content，如果为空则尝试 reasoning_content
      let content = (message.content || '').trim();
      if (!content && message.reasoning_content) {
        content = message.reasoning_content.trim();
      }
      if (!content) {
        throw new Error('Empty response from local model');
      }
      return parseTranslationOutput(content, titles.length);
    }

    throw new Error('Invalid response from local model');
  } catch (error) {
    if (error.name === 'AbortError') {
      console.error(`  ⚠️ 本地模型翻译超时`);
    } else {
      console.error(`  ⚠️ 本地模型翻译失败: ${error.message}`);
    }
    return null;
  }
}

/**
 * 解析翻译输出
 * @param {string} content - 模型返回内容
 * @param {number} expectedCount - 期望的翻译数量
 * @returns {string[]|null} - 翻译数组，解析失败返回null
 */
function parseTranslationOutput(content, expectedCount) {
  const translations = [];
  const lines = content.split('\n').filter(line => line.trim());

  for (const line of lines) {
    const trimmedLine = line.trim();
    // 跳过空行和常见的前缀词
    if (!trimmedLine ||
        trimmedLine.startsWith('译文') ||
        trimmedLine.startsWith('翻译') ||
        trimmedLine.startsWith('Thinking') ||
        trimmedLine.startsWith('思考')) {
      continue;
    }
    // 匹配 "序号. 中文标题" 格式
    const match = trimmedLine.match(/^\d+[\.\s]+(.+)$/);
    if (match) {
      translations.push(match[1].trim());
    }
  }

  // 如果解析到的数量接近预期，接受结果（允许少量缺失）
  if (translations.length >= expectedCount * 0.8) {
    // 补齐缺失的
    while (translations.length < expectedCount) {
      translations.push('[翻译缺失]');
    }
    return translations.slice(0, expectedCount);
  }

  console.error(`  ⚠️ 翻译结果数量不匹配 (${translations.length}/${expectedCount})`);
  return null;
}

/**
 * 格式化日期为 PubMed 格式 (YYYY/MM/DD)
 */
function formatPubMedDate(dateStr) {
  const date = new Date(dateStr);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}/${month}/${day}`;
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

    for (const paper of journal.papers.slice(0, 10)) { // 每期刊最多显示10篇
      output += `### ${paper.title}\n`;
      output += `**中文标题**: ${paper.titleZh}\n\n`;
      if (paper.authors.length > 0) {
        output += `**作者**: ${paper.authors.join(', ')}\n`;
      }
      if (paper.doi) {
        output += `**DOI**: ${paper.doi}\n`;
      }
      if (paper.pmid) {
        output += `**PMID**: ${paper.pmid}\n`;
      }
      if (paper.url) {
        output += `**链接**: ${paper.url}\n`;
      }
      if (paper.abstract) {
        output += `\n${paper.abstract}\n`;
      }
      output += '\n---\n\n';
      totalPapers++;
    }
  }

  output += `\n*总计 ${totalPapers} 篇论文*\n`;
  return output;
}

/**
 * 纯文本格式（含中英文对照）
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

    for (const paper of journal.papers.slice(0, 5)) {
      output += `英文: ${paper.title}\n`;
      output += `中文: ${paper.titleZh}\n`;
      if (paper.authors.length > 0) {
        output += `作者: ${paper.authors.join(', ')}\n`;
      }
      if (paper.url) {
        output += `链接: ${paper.url}\n`;
      }
      output += '\n';
    }
    output += '\n';
  }

  return output;
}

// 主函数
async function main() {
  console.error(`正在获取 ${targetDate} 前 ${recentDays} 天的期刊论文...\n`);

  // 计算日期范围
  const endDate = new Date(targetDate);
  const startDate = new Date(endDate);
  startDate.setDate(startDate.getDate() - recentDays);

  const startDateStr = formatPubMedDate(startDate);
  const endDateStr = formatPubMedDate(endDate);

  console.error(`日期范围: ${startDateStr} - ${endDateStr}\n`);

  const results = [];

  for (const [key, config] of Object.entries(journalsToFetch)) {
    if (!config) continue;

    console.error(`📚 正在获取: ${config.name}...`);

    try {
      // 搜索 PubMed（带 RSS 备用）
      const { source, pmids, rssPapers } = await searchPubMed(config.pubmedName, startDateStr, endDateStr, key);

      let papers = [];
      if (source === 'pubmed' && pmids.length > 0) {
        console.error(`  PubMed 找到 ${pmids.length} 篇论文`);
        papers = await fetchPubMedDetails(pmids);
      } else if (source === 'rss' && rssPapers.length > 0) {
        console.error(`  RSS 找到 ${rssPapers.length} 篇论文`);
        // RSS 数据需要格式化
        papers = rssPapers.map(p => ({
          title: p.title,
          titleZh: '',
          authors: [],
          abstract: '',
          doi: '',
          pmid: '',
          url: p.url,
          published: p.published
        }));
      } else {
        console.error(`  暂无新论文`);
      }

      results.push({
        key,
        name: config.name,
        field: config.field,
        publisher: config.publisher,
        papers
      });

      // 智能筛选：超过30篇时根据研究方向筛选
      const journal = results[results.length - 1];
      if (journal.papers.length > 30) {
        console.error(`  📝 论文数量超过30篇 (${journal.papers.length})，根据研究方向智能筛选...`);
        journal.papers = filterPapersByRelevance(journal.papers, 30);
        console.error(`  ✅ 筛选后保留 ${journal.papers.length} 篇最相关论文`);
      }

      // 添加延迟避免请求过快
      await new Promise(resolve => setTimeout(resolve, 200));
    } catch (error) {
      console.error(`  获取失败: ${error.message}`);
      results.push({
        key,
        name: config.name,
        field: config.field,
        publisher: config.publisher,
        papers: [],
        error: error.message
      });
    }
  }

  // 翻译论文标题 - 根据参数决定是否使用大模型
  if (values['no-translate']) {
    console.error("\n🌐 使用术语映射快速翻译论文标题（跳过大模型）...");
    for (const journal of results) {
      if (!journal.papers || journal.papers.length === 0) continue;
      console.error(`  正在翻译 ${journal.name} 的 ${journal.papers.length} 篇论文...`);
      for (const paper of journal.papers) {
        paper.titleZh = translateByMap(paper.title);
      }
    }
  } else {
    console.error("\n🌐 正在使用隔离上下文翻译论文标题...");
    for (const journal of results) {
      if (!journal.papers || journal.papers.length === 0) continue;
      console.error(`  正在翻译 ${journal.name} 的 ${journal.papers.length} 篇论文...`);
      const titles = journal.papers.map(p => p.title);
      const translations = await translateTitlesIsolated(titles, journal.key);
      for (let i = 0; i < journal.papers.length; i++) {
        journal.papers[i].titleZh = translations[i] || translateByMap(journal.papers[i].title);
      }
    }
  }

  console.error("✅ 翻译完成！\n");

  // 输出结果
  const output = formatOutput(results, values.format);
  console.log(output);
}

main().catch(error => {
  console.error('错误:', error);
  process.exit(1);
});
