#!/usr/bin/env node
/**
 * Journal Papers - 完整工作流
 * 一键获取、翻译、生成报告
 */

import { execSync } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUTPUT_DIR = join(__dirname, '..', 'output');

if (!existsSync(OUTPUT_DIR)) mkdirSync(OUTPUT_DIR, { recursive: true });

// 简化的术语映射（核心术语）
const TERM_MAP = {
  // 研究方法
  'proteomics analysis': '蛋白质组学分析',
  'comparative proteomics': '比较蛋白质组学',
  'analysis': '分析',
  'investigation': '研究',
  'evaluation': '评价',
  'characterization': '表征',
  'identification': '鉴定',
  'quantification': '定量',
  'comparison': '比较',
  'mechanism': '机制',
  
  // 处理技术
  'cold plasma': '冷等离子体',
  'pretreatment': '预处理',
  'extraction': '提取',
  'fermentation': '发酵',
  
  // 食品相关
  'sensory': '感官',
  'flavor': '风味',
  'quality': '品质',
  'cold-chain': '冷链',
  'simulated': '模拟的',
  
  // 成分
  'protein': '蛋白质',
  'starch': '淀粉',
  'lipid': '脂质',
  'polysaccharide': '多糖',
  'peptide': '肽',
  'amino acid': '氨基酸',
  'fatty acid': '脂肪酸',
  'antioxidant': '抗氧化',
  'bioactive': '生物活性',
  'compound': '化合物',
  'metabolite': '代谢物',
  'accumulation': '积累',
  
  // 生物体
  'squid': '鱿鱼',
  'sea cucumber': '海参',
  'fish': '鱼类',
  'shellfish': '贝类',
  'honey': '蜂蜜',
  'tea': '茶叶',
  'beef': '牛肉',
  'zebrafish': '斑马鱼',
  'rainbow trout': '虹鳟',
  'grass carp': '草鱼',
  'olive flounder': '牙鲆',
  'largemouth bass': '大口黑鲈',
  'Nile tilapia': '尼罗罗非鱼',
  'Atlantic salmon': '大西洋鲑',
  'white shrimp': '南美白对虾',
  'Yangtze sturgeon': '长江鲟',
  'oyster': '牡蛎',
  'mussel': '贻贝',
  
  // 品质
  'physicochemical': '理化',
  'nutritional': '营养',
  'digestibility': '消化率',
  'bioavailability': '生物利用度',
  
  // 动词
  'enhance': '增强',
  'promote': '促进',
  'improve': '改善',
  'increase': '增加',
  'reduce': '降低',
  'boost': '增强',
  'alleviate': '缓解',
  'facilitate': '促进',
  'mediate': '介导',
  'induce': '诱导',
  'inhibit': '抑制',
  'regulate': '调控',
  'modulate': '调节',
  'activate': '激活',
  'suppress': '抑制',
  'reveal': '揭示',
  
  // 其他
  'structure': '结构',
  'function': '功能',
  'activity': '活性',
  'stability': '稳定性',
  'formation': '形成',
  'degradation': '降解',
  'oxidation': '氧化',
  'crosslinking': '交联',
  'esterification': '酯化',
  'microstructure': '微观结构',
  'molecular': '分子',
  'cellular': '细胞',
  'development': '开发',
  'analogue': '类似物',
  'variation': '变化',
  'based on': '基于',
  'through': '通过',
  'via': '通过',
  'during': '在...期间',
  
  // 药理学
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
  'host': '宿主',
  'model': '模型',
  
  // 免疫学
  'immune': '免疫',
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
  'T cell': 'T细胞',
  'B cell': 'B细胞',
  'NK cell': 'NK细胞',
  'complement': '补体',
  'inflammation': '炎症',
  'phagocytosis': '吞噬作用',
  'vaccine': '疫苗',
  'adjuvant': '佐剂',
  'serum': '血清',
  'spleen': '脾脏',
  'liver-spleen axis': '肝-脾轴',
  'intestinal barrier': '肠道屏障',
  
  // 病毒学
  'virus': '病毒',
  'viral': '病毒的',
  'replication': '复制',
  'viral replication': '病毒复制',
  'viral infection': '病毒感染',
  'antiviral': '抗病毒',
  'antiviral activity': '抗病毒活性',
  'VHSV': '病毒性出血性败血症病毒',
  'IHNV': '传染性造血器官坏死病毒',
  'SVCV': '鲤春病毒血症病毒',
  'SGIV': '新加坡石斑鱼虹彩病毒',
  'WSSV': '白斑综合征病毒',
  'GCRV': '草鱼呼肠孤病毒',
  'LMBV': '大口黑鲈蛙病毒',
  'TGV': '鳟鱼肉芽肿病毒',
  'infection': '感染',
  'disease': '疾病',
  'disease resistance': '抗病力',
  'mortality': '死亡率',
  
  // 细菌学
  'bacteria': '细菌',
  'bacterial': '细菌的',
  'antibiotic': '抗生素',
  'antimicrobial': '抗菌',
  'antimicrobial peptide': '抗菌肽',
  'pathogen': '病原体',
  'Aeromonas hydrophila': '嗜水气单胞菌',
  'Edwardsiella piscicida': '杀鱼爱德华氏菌',
  'Vibrio': '弧菌',
  'Vibrio alginolyticus': '溶藻弧菌',
  'Bacillus cereus': '蜡样芽孢杆菌',
  'low-salinity': '低盐',
  
  // 分子生物学
  'DNA': 'DNA',
  'RNA': 'RNA',
  'mRNA': 'mRNA',
  'gene': '基因',
  'protein': '蛋白质',
  'enzyme': '酶',
  'receptor': '受体',
  'signaling pathway': '信号通路',
  'apoptosis': '细胞凋亡',
  'autophagy': '自噬',
  'oxidative stress': '氧化应激',
  'cell cycle': '细胞周期',
  'cell proliferation': '细胞增殖',
  'tissue': '组织',
  'strain': '菌株',
  'wild type': '野生型',
  'mutant': '突变体',
  'knockout': '敲除',
  'overexpression': '过表达',
  'transgenic': '转基因',
  
  // 纳米技术
  'nanoparticle': '纳米颗粒',
  'nanoparticles': '纳米颗粒',
  'self-assembled': '自组装的',
  'CpG': 'CpG',
  'nanovaccine': '纳米疫苗',
  'chitosan-based': '壳聚糖基',
  
  // 其他技术
  'ELISA': 'ELISA',
  'sandwich ELISA': '夹心ELISA',
  'single-cell RNA-seq': '单细胞RNA测序',
  'RNA-sequencing': 'RNA测序',
  'transcriptome': '转录组',
  'multi-omics': '多组学',
  'genome-wide': '全基因组',
  'probiotic': '益生菌',
  'dietary': '膳食',
  'oral administration': '口服',
  'intraperitoneal injection': '腹腔注射',
  'evisceration': '内脏去除'
};

function translateByMap(text) {
  let translated = text;
  const sortedTerms = Object.keys(TERM_MAP).sort((a, b) => b.length - a.length);
  
  for (const term of sortedTerms) {
    const regex = new RegExp(`\\b${term}\\b`, 'gi');
    translated = translated.replace(regex, TERM_MAP[term]);
  }
  
  return translated;
}

// 主函数
async function main() {
  console.log('🚀 期刊论文翻译工作流\n');
  
  // 这里可以集成实际的论文获取逻辑
  console.log('✅ 术语映射已加载，包含 ' + Object.keys(TERM_MAP).length + ' 个术语');
  console.log('\n使用示例:');
  console.log('  英文: Comparative proteomics analysis of physicochemical variations in squid');
  console.log('  中文: ' + translateByMap('Comparative proteomics analysis of physicochemical variations in squid'));
}

main().catch(console.error);
