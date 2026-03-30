#!/usr/bin/env node
/**
 * 论文翻译工作流 - 三步法
 * 1. 获取原文 → 2. 保存缓存 → 3. LLM翻译
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync } from 'node:fs';
import { dirname, join, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CACHE_DIR = join(__dirname, '..', 'cache');
const OUTPUT_DIR = join(__dirname, '..', 'output');

// 确保目录存在
[CACHE_DIR, OUTPUT_DIR].forEach(dir => {
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
});

/**
 * 显示最新的缓存文件列表
 */
function listCacheFiles() {
  const files = readdirSync(CACHE_DIR)
    .filter(f => f.endsWith('.json'))
    .sort()
    .reverse();
  
  if (files.length === 0) {
    console.log('❌ 没有找到缓存文件。请先运行获取命令:');
    console.log('   node fetch-v2.mjs --format raw');
    return null;
  }
  
  console.log('\n📁 可用的缓存文件:');
  files.slice(0, 5).forEach((f, i) => {
    console.log(`   ${i + 1}. ${f}`);
  });
  
  return join(CACHE_DIR, files[0]);
}

/**
 * 生成LLM翻译提示词
 */
function generateTranslationPrompt(papers) {
  let prompt = `请将以下学术论文标题翻译为中文。要求：

1. 保持学术性和专业性
2. 符合中文表达习惯
3. 保留原文中的物种名、基因名、蛋白名等专有名词
4. 输出格式：中文标题（简洁自然）\n
待翻译论文列表：\n\n`;

  papers.forEach((paper, idx) => {
    prompt += `${idx + 1}. ${paper.title}\n`;
    prompt += `   期刊: ${paper.journal}\n`;
    prompt += `   作者: ${paper.authors.slice(0, 3).join(', ')}${paper.authors.length > 3 ? ' 等' : ''}\n\n`;
  });

  prompt += `\n请按以下格式返回翻译结果：\n\n`;
  prompt += `1. [中文标题]\n`;
  prompt += `2. [中文标题]\n`;
  prompt += `...\n`;

  return prompt;
}

/**
 * 生成待翻译的Markdown文件（用户手动翻译）
 */
function generateTranslationTemplate(papers, targetDate) {
  let md = `# 待翻译论文列表\n\n`;
  md += `> 生成时间: ${new Date().toLocaleString('zh-CN')}\n`;
  md += `> 日期: ${targetDate}\n\n`;
  md += `---\n\n`;

  papers.forEach((paper, idx) => {
    md += `## ${idx + 1}. [请在下方填入中文标题]\n\n`;
    md += `**英文标题**: ${paper.title}\n\n`;
    md += `**中文标题**: \n\n`;
    md += `**作者**: ${paper.authors.join(', ')}\n\n`;
    md += `**期刊**: ${paper.journal}\n\n`;
    md += `**链接**: ${paper.url}\n\n`;
    md += `---\n\n`;
  });

  md += `\n*总计 ${papers.length} 篇论文*\n`;
  
  return md;
}

/**
 * 生成最终的翻译报告
 */
function generateFinalReport(papers, translations, targetDate) {
  let md = `# 📄 期刊论文日报 - ${targetDate}\n\n`;
  md += `> 本报告包含最新期刊论文的中英文对照\n`;
  md += `> 数据来源: Food Chemistry, Journal of Ethnopharmacology, Journal of Animal Science and Biotechnology, Fish & Shellfish Immunology\n\n`;
  md += `---\n\n`;

  // 按期刊分组
  const byJournal = {};
  papers.forEach((paper, idx) => {
    if (!byJournal[paper.journal]) byJournal[paper.journal] = [];
    byJournal[paper.journal].push({ ...paper, idx });
  });

  let count = 0;
  for (const [journalName, journalPapers] of Object.entries(byJournal)) {
    md += `## ${journalName}\n\n`;
    
    journalPapers.forEach(paper => {
      count++;
      const translatedTitle = translations[paper.idx] || `[待翻译] ${paper.title}`;
      
      md += `### ${count}. ${translatedTitle}\n\n`;
      md += `**英文标题**: ${paper.title}\n\n`;
      md += `**作者**: ${paper.authors.join(', ')}${paper.authors.length >= 5 ? ' 等' : ''}\n\n`;
      md += `**期刊**: ${paper.journal}\n\n`;
      md += `**链接**: ${paper.url}\n\n`;
      md += `---\n\n`;
    });
  }

  md += `\n*总计 ${papers.length} 篇论文*\n`;
  
  return md;
}

/**
 * 主函数
 */
async function main() {
  const args = process.argv.slice(2);
  const command = args[0] || 'help';

  switch (command) {
    case 'list':
      listCacheFiles();
      break;

    case 'prompt':
      // 生成LLM翻译提示词
      const cacheFile = args[1] || listCacheFiles();
      if (!cacheFile) return;
      
      console.log(`\n📖 读取缓存: ${basename(cacheFile)}`);
      const data = JSON.parse(readFileSync(cacheFile, 'utf-8'));
      
      // 收集所有论文
      const allPapers = [];
      data.results.forEach(journal => {
        journal.papers.forEach(paper => {
          allPapers.push({
            ...paper,
            journal: journal.name
          });
        });
      });

      if (allPapers.length === 0) {
        console.log('❌ 缓存中没有论文数据');
        return;
      }

      // 只取前10篇
      const topPapers = allPapers.slice(0, 10);
      
      // 生成提示词文件
      const prompt = generateTranslationPrompt(topPapers);
      const promptFile = join(OUTPUT_DIR, `translation-prompt-${data.targetDate}.txt`);
      writeFileSync(promptFile, prompt, 'utf-8');
      
      console.log(`\n✅ 翻译提示词已生成: ${promptFile}`);
      console.log(`\n📝 提示词内容预览:\n`);
      console.log(prompt.slice(0, 500) + '...');
      break;

    case 'template':
      // 生成待翻译模板
      const cacheForTemplate = args[1] || listCacheFiles();
      if (!cacheForTemplate) return;
      
      const templateData = JSON.parse(readFileSync(cacheForTemplate, 'utf-8'));
      const templatePapers = [];
      templateData.results.forEach(journal => {
        journal.papers.forEach(paper => {
          templatePapers.push({ ...paper, journal: journal.name });
        });
      });

      const template = generateTranslationTemplate(templatePapers.slice(0, 10), templateData.targetDate);
      const templateFile = join(OUTPUT_DIR, `to-translate-${templateData.targetDate}.md`);
      writeFileSync(templateFile, template, 'utf-8');
      
      console.log(`\n✅ 翻译模板已生成: ${templateFile}`);
      console.log(`\n👉 请打开该文件，在"中文标题"处填入翻译内容`);
      break;

    case 'report':
      // 生成最终报告（需要翻译结果）
      console.log('使用示例翻译结果生成报告...');
      const cacheForReport = args[1] || listCacheFiles();
      if (!cacheForReport) return;
      
      const reportData = JSON.parse(readFileSync(cacheForReport, 'utf-8'));
      const reportPapers = [];
      reportData.results.forEach(journal => {
        journal.papers.forEach(paper => {
          reportPapers.push({ ...paper, journal: journal.name });
        });
      });

      // 示例翻译结果（实际使用时从LLM输出或手动翻译文件读取）
      const exampleTranslations = reportPapers.slice(0, 10).map((p, i) => {
        // 这里使用简单的术语映射作为示例
        return translateByMap(p.title);
      });

      const report = generateFinalReport(reportPapers.slice(0, 10), exampleTranslations, reportData.targetDate);
      const reportFile = join(OUTPUT_DIR, `journal-papers-report-${reportData.targetDate}.md`);
      writeFileSync(reportFile, report, 'utf-8');
      
      console.log(`\n✅ 最终报告已生成: ${reportFile}`);
      console.log(`\n📄 报告预览:\n`);
      console.log(report.slice(0, 800) + '...');
      break;

    case 'help':
    default:
      console.log(`
论文翻译工作流工具

用法: node translate-workflow.mjs <command> [options]

命令:
  list                    列出可用的缓存文件
  prompt [cache-file]     生成LLM翻译提示词
  template [cache-file]   生成待翻译的Markdown模板
  report [cache-file]     生成最终翻译报告（使用示例翻译）
  help                    显示帮助

工作流程:
  1. 获取论文: node fetch-v2.mjs --format raw
  2. 生成提示: node translate-workflow.mjs prompt
  3. LLM翻译: 将提示词发送给AI进行翻译
  4. 生成报告: node translate-workflow.mjs report

示例:
  # 获取最新论文
  node fetch-v2.mjs --days 7 --format raw
  
  # 生成翻译提示词
  node translate-workflow.mjs prompt
  
  # 生成待翻译模板（手动翻译）
  node translate-workflow.mjs template
  
  # 生成最终报告
  node translate-workflow.mjs report
`);
  }
}

/**
 * 使用术语映射进行基础翻译（作为示例/后备）
 */
function translateByMap(text) {
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
    'zebrafish': '斑马鱼',
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
    'compound': '化合物',
    'immune': '免疫',
    'immunity': '免疫力',
    'innate immune': '先天免疫',
    'adaptive immune': '适应性免疫',
    'immune response': '免疫应答',
    'immune system': '免疫系统',
    'immune cell': '免疫细胞',
    'immune gene': '免疫基因',
    'immune defense': '免疫防御',
    'immune regulation': '免疫调节',
    'antibody': '抗体',
    'antigen': '抗原',
    'cytokine': '细胞因子',
    'interferon': '干扰素',
    'interleukin': '白细胞介素',
    'lymphocyte': '淋巴细胞',
    'macrophage': '巨噬细胞',
    'neutrophil': '中性粒细胞',
    'dendritic cell': '树突状细胞',
    'T cell': 'T细胞',
    'B cell': 'B细胞',
    'NK cell': 'NK细胞',
    'complement': '补体',
    'inflammation': '炎症',
    'inflammatory': '炎症性',
    'phagocytosis': '吞噬作用',
    'vaccine': '疫苗',
    'adjuvant': '佐剂',
    'virus': '病毒',
    'viral': '病毒的',
    'replication': '复制',
    'viral replication': '病毒复制',
    'viral infection': '病毒感染',
    'antiviral': '抗病毒',
    'antiviral activity': '抗病毒活性',
    'bacteria': '细菌',
    'bacterial': '细菌的',
    'antibiotic': '抗生素',
    'antimicrobial': '抗菌',
    'antimicrobial peptide': '抗菌肽',
    'pathogen': '病原体',
    'host': '宿主',
    'host defense': '宿主防御',
    'host immune': '宿主免疫',
    'transcription': '转录',
    'translation': '翻译',
    'gene expression': '基因表达',
    'gene regulation': '基因调控',
    'promoter': '启动子',
    'transcription factor': '转录因子',
    'protein': '蛋白质',
    'enzyme': '酶',
    'receptor': '受体',
    'ligand': '配体',
    'signaling': '信号',
    'signaling pathway': '信号通路',
    'apoptosis': '细胞凋亡',
    'autophagy': '自噬',
    'necrosis': '坏死',
    'pyroptosis': '焦亡',
    'ferroptosis': '铁死亡',
    'oxidative stress': '氧化应激',
    'reactive oxygen species': '活性氧',
    'ROS': '活性氧',
    'antioxidant': '抗氧化',
    'antioxidant capacity': '抗氧化能力',
    'lipid peroxidation': '脂质过氧化',
    'DNA damage': 'DNA损伤',
    'cell cycle': '细胞周期',
    'cell proliferation': '细胞增殖',
    'cell differentiation': '细胞分化',
    'cell migration': '细胞迁移',
    'cell adhesion': '细胞黏附',
    'extracellular matrix': '细胞外基质',
    'tissue': '组织',
    'organ': '器官',
    'system': '系统',
    'organism': '生物体',
    'species': '物种',
    'strain': '菌株',
    'isolate': '分离株',
    'wild type': '野生型',
    'mutant': '突变体',
    'knockout': '敲除',
    'knockdown': '敲低',
    'overexpression': '过表达',
    'transgenic': '转基因',
    'wild-type': '野生型'
  };

  let translated = text;
  const sortedTerms = Object.keys(TERM_MAP).sort((a, b) => b.length - a.length);
  
  for (const term of sortedTerms) {
    const regex = new RegExp(`\\b${term}\\b`, 'gi');
    translated = translated.replace(regex, TERM_MAP[term]);
  }
  
  return translated;
}

main().catch(console.error);
