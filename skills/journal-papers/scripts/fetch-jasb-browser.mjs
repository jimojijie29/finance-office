#!/usr/bin/env node
/**
 * Journal of Animal Science and Biotechnology - 浏览器自动化抓取
 * 由于 RSS 失效，使用 Playwright 抓取最新论文
 */

import { chromium } from 'playwright';
import { writeFileSync, existsSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUTPUT_DIR = join(__dirname, '..', 'output');

if (!existsSync(OUTPUT_DIR)) mkdirSync(OUTPUT_DIR, { recursive: true });

const JOURNAL_URL = 'https://link.springer.com/journal/40104/articles';

/**
 * 抓取最新论文
 */
async function fetchLatestPapers(maxPapers = 10) {
  console.log('🚀 启动浏览器...');
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  });
  
  try {
    const page = await context.newPage();
    
    console.log('📄 访问期刊页面...');
    await page.goto(JOURNAL_URL, { waitUntil: 'networkidle', timeout: 60000 });
    
    // 等待文章列表加载
    await page.waitForSelector('article', { timeout: 30000 });
    
    console.log('🔍 提取论文信息...');
    
    // 提取论文数据
    const papers = await page.evaluate((max) => {
      const articles = document.querySelectorAll('article');
      const results = [];
      
      for (let i = 0; i < Math.min(articles.length, max); i++) {
        const article = articles[i];
        
        // 标题
        const titleEl = article.querySelector('h2 a');
        const title = titleEl ? titleEl.textContent.trim() : '';
        const url = titleEl ? titleEl.href : '';
        
        // 作者
        const authorEls = article.querySelectorAll('ul li');
        const authors = Array.from(authorEls).map(el => el.textContent.trim()).filter(a => a && !a.includes('...'));
        
        // 日期
        const dateEl = article.querySelector('[data-test="article-date"]');
        const date = dateEl ? dateEl.textContent.trim() : '';
        
        // 文章类型
        const typeEl = article.querySelector('[data-test="article-type"]');
        const type = typeEl ? typeEl.textContent.trim() : 'Research';
        
        // 开放获取状态
        const oaEl = article.querySelector('[data-test="open-access"]');
        const isOA = oaEl ? true : false;
        
        if (title) {
          results.push({ title, authors, date, type, isOA, url });
        }
      }
      
      return results;
    }, maxPapers);
    
    console.log(`✅ 成功获取 ${papers.length} 篇论文`);
    
    return papers;
    
  } catch (error) {
    console.error('❌ 抓取失败:', error.message);
    return [];
  } finally {
    await browser.close();
    console.log('🔒 浏览器已关闭');
  }
}

/**
 * 生成 Markdown 报告
 */
function generateReport(papers) {
  const today = new Date().toISOString().split('T')[0];
  
  let md = `# 📄 Journal of Animal Science and Biotechnology - 最新论文\n\n`;
  md += `> 期刊: Journal of Animal Science and Biotechnology\n`;
  md += `> 出版商: BMC/Springer Nature\n`;
  md += `> 领域: 动物科学与生物技术\n`;
  md += `> 获取日期: ${today}\n\n`;
  md += `---\n\n`;
  md += `## 最新论文列表（前${papers.length}篇）\n\n`;
  
  papers.forEach((paper, idx) => {
    // 简单翻译（使用术语映射）
    const translatedTitle = translateTitle(paper.title);
    
    md += `### ${idx + 1}. ${translatedTitle}\n\n`;
    md += `**英文标题**: ${paper.title}\n\n`;
    md += `**作者**: ${paper.authors.join(', ')}${paper.authors.length >= 3 ? ' 等' : ''}\n\n`;
    md += `**发表日期**: ${paper.date}\n\n`;
    md += `**文章类型**: ${paper.type}${paper.isOA ? ' | Open access' : ''}\n\n`;
    md += `**链接**: ${paper.url}\n\n`;
    md += `---\n\n`;
  });
  
  md += `*总计 ${papers.length} 篇论文*\n`;
  
  return md;
}

/**
 * 简单的标题翻译
 */
function translateTitle(title) {
  const translations = {
    'alleviates': '缓解',
    'zearalenone-induced': '玉米赤霉烯酮诱导的',
    'swine testicular cell': '猪睾丸细胞',
    'ferroptosis': '铁死亡',
    'mitophagy': '线粒体自噬',
    'insights': '见解',
    'skeletal muscle': '骨骼肌',
    'circadian clock': '昼夜节律钟',
    'ruminants': '反刍动物',
    'rosemary-derived': '迷迭香来源的',
    'triterpene acids': '三萜酸',
    'growth': '生长',
    'lipid metabolism': '脂质代谢',
    'juvenile': '幼鱼',
    'grass carp': '草鱼',
    'gut–liver axis': '肠-肝轴',
    'tissue-specifically': '组织特异性地',
    'regulating': '调控',
    'farnesoid X receptor': '法尼醇X受体',
    'epigenetic regulation': '表观遗传调控',
    'fat metabolism': '脂肪代谢',
    'pigs': '猪',
    'integrated analysis': '整合分析',
    'DNA methylation': 'DNA甲基化',
    'gene expression networks': '基因表达网络',
    'multi-omics': '多组学',
    'sow colostrum': '母猪初乳',
    'faecal microbiota': '粪便微生物群',
    'parity-dependent': '胎次依赖性',
    'piglet survival': '仔猪存活',
    'growth': '生长',
    'pangenome': '泛基因组',
    'assembly': '组装',
    'cattle': '牛',
    'genetic diversity': '遗传多样性',
    'high-energy': '高能量',
    'high-lysine': '高赖氨酸',
    'transition diet': '过渡日粮',
    'nutritional': '营养',
    'metabolomic': '代谢组学',
    'microRNA': 'microRNA',
    'profile': '谱',
    'thermal stress': '热应激',
    'heat stress': '热应激',
    'resilience': '抗性',
    'genes': '基因',
    'chickens': '鸡',
    'combinatorial': '组合',
    'supplementation': '补充',
    'fish feeds': '鱼类饲料',
    'growth performance': '生长性能',
    'disease resilience': '疾病抗性',
    'aquaculture': '水产养殖',
    'selection': '选择',
    'production parameters': '生产参数',
    'intestinal microbiota': '肠道微生物群',
    'heritage': '传统',
    'modern': '现代',
    'broiler chickens': '肉鸡'
  };
  
  let translated = title;
  for (const [en, zh] of Object.entries(translations)) {
    const regex = new RegExp(`\\b${en}\\b`, 'gi');
    translated = translated.replace(regex, zh);
  }
  
  return translated;
}

// 主函数
async function main() {
  const args = process.argv.slice(2);
  const maxPapers = parseInt(args[0]) || 10;
  
  console.log(`📚 获取 Journal of Animal Science and Biotechnology 最新 ${maxPapers} 篇论文...\n`);
  
  const papers = await fetchLatestPapers(maxPapers);
  
  if (papers.length === 0) {
    console.log('❌ 未获取到论文');
    process.exit(1);
  }
  
  // 生成报告
  const report = generateReport(papers);
  const outputFile = join(OUTPUT_DIR, `jasb-${new Date().toISOString().split('T')[0]}.md`);
  writeFileSync(outputFile, report, 'utf-8');
  
  console.log(`\n✅ 报告已保存: ${outputFile}`);
  console.log(`\n📊 获取结果:`);
  papers.forEach((p, i) => {
    console.log(`  ${i + 1}. ${p.title.substring(0, 60)}...`);
  });
}

main().catch(console.error);
