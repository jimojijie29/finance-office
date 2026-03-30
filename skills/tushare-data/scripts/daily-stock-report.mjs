#!/usr/bin/env node
/**
 * 每日股票数据抓取与分析脚本
 * 运行时间：每天 15:10（收盘后）
 * 功能：抓取持仓股数据、融资融券、龙虎榜、技术指标
 */

import { execSync } from 'child_process';
import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const WORKSPACE_DIR = 'D:\\OpenClawData\\.openclaw\\workspace';
const OUTPUT_DIR = join(WORKSPACE_DIR, 'stock-daily');

// 持仓股列表
const HOLDINGS = [
  { code: '300932.SZ', name: '三友联众', strategy: '等日线/周线底背离确认后入场' },
  { code: '603162.SH', name: '海通发展', strategy: '持仓，等大结构推进' },
  { code: '301327.SZ', name: '华宝新能', strategy: '逢低配，金字塔加仓' },
  { code: '300145.SZ', name: '南方泵业', strategy: '长期目标20+，套住也不怕' },
  { code: '300777.SZ', name: '中简科技', strategy: '历史新高可期' }
];

// 获取今天日期
const today = new Date();
const dateStr = today.toISOString().split('T')[0].replace(/-/g, '');
const dateDisplay = today.toISOString().split('T')[0];

// 确保输出目录存在
if (!existsSync(OUTPUT_DIR)) {
  mkdirSync(OUTPUT_DIR, { recursive: true });
}

// 运行 Python 脚本获取数据
function runPythonScript(script) {
  try {
    const result = execSync(`python -c "${script}"`, { 
      encoding: 'utf-8',
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
    });
    return JSON.parse(result);
  } catch (error) {
    console.error('Python execution error:', error.stderr || error.message);
    return null;
  }
}

// 获取持仓股日线数据
function getDailyData() {
  const codes = HOLDINGS.map(h => h.code).join(',');
  const script = `
import os
import json
import tushare as ts
from datetime import datetime, timedelta

token = os.getenv('TUSHARE_TOKEN')
if not token:
    print(json.dumps({"error": "TUSHARE_TOKEN not set"}))
    exit(1)

pro = ts.pro_api(token)
codes = "${codes}".split(',')
result = {}

# 获取最近5个交易日
trade_cal = pro.trade_cal(exchange='SSE', start_date=(datetime.now() - timedelta(days=10)).strftime('%Y%m%d'), end_date=datetime.now().strftime('%Y%m%d'))
trade_days = trade_cal[trade_cal['is_open'] == 1]['cal_date'].tolist()[-5:]

for code in codes:
    try:
        # 获取日线数据
        df = pro.daily(ts_code=code, start_date=trade_days[0], end_date=trade_days[-1])
        if not df.empty:
            # 获取基本面指标
            basic = pro.daily_basic(ts_code=code, trade_date=trade_days[-1])
            
            result[code] = {
                "daily": df.to_dict('records'),
                "basic": basic.to_dict('records')[0] if not basic.empty else {}
            }
    except Exception as e:
        result[code] = {"error": str(e)}

print(json.dumps(result, ensure_ascii=False))
`;
  return runPythonScript(script);
}

// 获取融资融券数据
function getMarginData() {
  const script = `
import os
import json
import tushare as ts
from datetime import datetime, timedelta

token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

# 获取最近5个交易日的两融数据
end_date = datetime.now().strftime('%Y%m%d')
start_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')

try:
    # 沪市两融
    margin_sh = pro.margin(trade_date=end_date, exchange_id='SH')
    # 深市两融  
    margin_sz = pro.margin(trade_date=end_date, exchange_id='SZ')
    
    result = {
        "sh": margin_sh.to_dict('records')[0] if not margin_sh.empty else {},
        "sz": margin_sz.to_dict('records')[0] if not margin_sz.empty else {}
    }
except Exception as e:
    result = {"error": str(e)}

print(json.dumps(result, ensure_ascii=False))
`;
  return runPythonScript(script);
}

// 获取龙虎榜数据
function getTopListData() {
  const script = `
import os
import json
import tushare as ts
from datetime import datetime, timedelta

token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

end_date = datetime.now().strftime('%Y%m%d')
start_date = (datetime.now() - timedelta(days=5)).strftime('%Y%m%d')

try:
    # 获取龙虎榜数据
    top_list = pro.top_list(trade_date=end_date)
    
    # 筛选拉萨团结路第二营业部的数据
    lhasa_data = top_list[top_list['exalter'].str.contains('拉萨.*团结路.*第二', na=False)] if not top_list.empty else []
    
    result = {
        "total_count": len(top_list) if not top_list.empty else 0,
        "lhasa_count": len(lhasa_data) if not isinstance(lhasa_data, list) else 0,
        "lhasa_stocks": lhasa_data[['ts_code', 'name', 'exalter', 'buy', 'sell', 'net_buy']].to_dict('records') if not isinstance(lhasa_data, list) and not lhasa_data.empty else []
    }
except Exception as e:
    result = {"error": str(e)}

print(json.dumps(result, ensure_ascii=False))
`;
  return runPythonScript(script);
}

// 获取神奇九转指标
function getMagicNineData() {
  const codes = HOLDINGS.map(h => h.code).join(',');
  const script = `
import os
import json
import tushare as ts

token = os.getenv('TUSHARE_TOKEN')
pro = ts.pro_api(token)

codes = "${codes}".split(',')
result = {}

for code in codes:
    try:
        # 获取九转序列数据
        df = pro.magic_nine(ts_code=code)
        if not df.empty:
            result[code] = df.head(5).to_dict('records')
    except Exception as e:
        result[code] = {"error": str(e)}

print(json.dumps(result, ensure_ascii=False))
`;
  return runPythonScript(script);
}

// 生成报告
function generateReport(dailyData, marginData, topListData, magicNineData) {
  let report = `# 每日股票数据分析报告 - ${dateDisplay}\n\n`;
  
  // 持仓股分析
  report += `## 📈 持仓股行情\n\n`;
  report += `| 股票 | 代码 | 最新价 | 涨跌幅 | 成交量 | PE_TTM | 策略提醒 |\n`;
  report += `|------|------|--------|--------|--------|--------|----------|\n`;
  
  for (const holding of HOLDINGS) {
    const data = dailyData?.[holding.code];
    if (data && data.daily && data.daily.length > 0) {
      const latest = data.daily[0];
      const changePct = ((latest.close - latest.pre_close) / latest.pre_close * 100).toFixed(2);
      const peTtm = data.basic?.pe_ttm ? data.basic.pe_ttm.toFixed(2) : 'N/A';
      
      report += `| ${holding.name} | ${holding.code} | ${latest.close} | ${changePct}% | ${(latest.vol / 10000).toFixed(2)}万 | ${peTtm} | ${holding.strategy} |\n`;
    } else {
      report += `| ${holding.name} | ${holding.code} | - | - | - | - | ${holding.strategy} |\n`;
    }
  }
  
  // 融资融券分析
  report += `\n## 💰 融资融券数据\n\n`;
  if (marginData && !marginData.error) {
    const sh = marginData.sh;
    const sz = marginData.sz;
    const totalRzye = (parseFloat(sh.rzye || 0) + parseFloat(sz.rzye || 0)) / 100000000;
    const totalRqye = (parseFloat(sh.rqye || 0) + parseFloat(sz.rqye || 0)) / 100000000;
    
    report += `- **沪市融资余额**: ${(parseFloat(sh.rzye || 0) / 100000000).toFixed(2)} 亿元\n`;
    report += `- **深市融资余额**: ${(parseFloat(sz.rzye || 0) / 100000000).toFixed(2)} 亿元\n`;
    report += `- **两市融资余额合计**: ${totalRzye.toFixed(2)} 亿元\n`;
    report += `- **两市融券余额合计**: ${totalRqye.toFixed(2)} 亿元\n`;
  } else {
    report += `- 数据获取失败: ${marginData?.error || '未知错误'}\n`;
  }
  
  // 龙虎榜分析
  report += `\n## 🔥 龙虎榜数据\n\n`;
  if (topListData && !topListData.error) {
    report += `- **今日龙虎榜总条数**: ${topListData.total_count}\n`;
    report += `- **拉萨团结路第二营业部上榜数**: ${topListData.lhasa_count}\n\n`;
    
    if (topListData.lhasa_stocks && topListData.lhasa_stocks.length > 0) {
      report += `**拉萨团结路第二营业部今日操作**:\n\n`;
      report += `| 股票 | 营业部 | 买入(万) | 卖出(万) | 净买入(万) |\n`;
      report += `|------|--------|----------|----------|------------|\n`;
      for (const stock of topListData.lhasa_stocks.slice(0, 10)) {
        report += `| ${stock.name} | ${stock.exalter.substring(0, 20)}... | ${(stock.buy / 10000).toFixed(2)} | ${(stock.sell / 10000).toFixed(2)} | ${(stock.net_buy / 10000).toFixed(2)} |\n`;
      }
      report += `\n> ⚠️ 提示：拉萨团结路第二营业部上榜的股票，后续5日表现普遍不佳，需谨慎追高。\n`;
    }
  } else {
    report += `- 数据获取失败: ${topListData?.error || '未知错误'}\n`;
  }
  
  // 神奇九转指标
  report += `\n## 🎯 神奇九转指标\n\n`;
  if (magicNineData && !magicNineData.error) {
    for (const holding of HOLDINGS) {
      const nineData = magicNineData[holding.code];
      if (nineData && !nineData.error && nineData.length > 0) {
        const latest = nineData[0];
        const signal = latest.nine_count === 9 ? (latest.nine_type === 'buy' ? '🟢 买入信号' : '🔴 卖出信号') : `计数 ${latest.nine_count}/9`;
        report += `- **${holding.name}**: ${signal}\n`;
      }
    }
  } else {
    report += `- 数据获取失败: ${magicNineData?.error || '未知错误'}\n`;
  }
  
  // 总结
  report += `\n---\n\n`;
  report += `*报告生成时间: ${new Date().toLocaleString('zh-CN')}*\n`;
  report += `*数据来源: Tushare Pro*\n`;
  
  return report;
}

// 主函数
async function main() {
  console.log(`[${new Date().toLocaleString('zh-CN')}] 开始抓取股票数据...`);
  
  // 并行获取数据
  const [dailyData, marginData, topListData, magicNineData] = await Promise.all([
    getDailyData(),
    getMarginData(),
    getTopListData(),
    getMagicNineData()
  ]);
  
  // 生成报告
  const report = generateReport(dailyData, marginData, topListData, magicNineData);
  
  // 保存报告
  const outputFile = join(OUTPUT_DIR, `stock-report-${dateDisplay}.md`);
  writeFileSync(outputFile, report, 'utf-8');
  
  console.log(`[${new Date().toLocaleString('zh-CN')}] 报告已保存: ${outputFile}`);
  
  // 输出摘要到控制台
  console.log('\n========== 数据抓取摘要 ==========');
  console.log(`持仓股数据: ${dailyData ? '✅' : '❌'}`);
  console.log(`融资融券: ${marginData ? '✅' : '❌'}`);
  console.log(`龙虎榜: ${topListData ? '✅' : '❌'}`);
  console.log(`神奇九转: ${magicNineData ? '✅' : '❌'}`);
  console.log('==================================\n');
  
  return report;
}

main().catch(console.error);
