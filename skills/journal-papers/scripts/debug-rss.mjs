import { readFileSync } from 'fs';

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const xml = readFileSync(join(__dirname, 'test-rss.xml'), 'utf-8');

// 提取所有 item
const itemRegex = /<item>([\s\S]*?)<\/item>/g;
let match;
let count = 0;

while ((match = itemRegex.exec(xml)) !== null && count < 3) {
  count++;
  const item = match[1];
  
  // 提取标题
  const titleMatch = item.match(/<title>([<\s\S]*?)<\/title>/);
  console.log(`\n=== Paper ${count} ===`);
  console.log('Title:', titleMatch ? titleMatch[1].substring(0, 100) : 'N/A');
  
  // 提取日期
  const dcDateMatch = item.match(/<dc:date>(.*?)<\/dc:date>/);
  console.log('dc:date:', dcDateMatch ? dcDateMatch[1] : 'N/A');
  
  const pubDateMatch = item.match(/<pubDate>(.*?)<\/pubDate>/);
  console.log('pubDate:', pubDateMatch ? pubDateMatch[1] : 'N/A');
  
  const prismDateMatch = item.match(/<prism:publicationDate>(.*?)<\/prism:publicationDate>/);
  console.log('prism:publicationDate:', prismDateMatch ? prismDateMatch[1] : 'N/A');
}
