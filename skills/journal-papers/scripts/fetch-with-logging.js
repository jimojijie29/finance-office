#!/usr/bin/env node
/**
 * Journal Papers Daily - 带状态记录的包装脚本
 * 调用原始的 fetch.mjs 并记录执行状态
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// 任务状态日志文件
const LOG_FILE = path.join(__dirname, '..', '..', '..', 'logs', 'task-status.json');

/**
 * 记录任务状态
 */
function logTaskStatus(taskId, updates) {
  try {
    let data = { version: '1.0', last_updated: '', tasks: {} };
    
    if (fs.existsSync(LOG_FILE)) {
      data = JSON.parse(fs.readFileSync(LOG_FILE, 'utf-8'));
    }
    
    const now = new Date().toISOString();
    
    if (!data.tasks[taskId]) {
      data.tasks[taskId] = {};
    }
    
    Object.assign(data.tasks[taskId], updates);
    data.tasks[taskId].last_run = now;
    data.last_updated = now;
    
    fs.writeFileSync(LOG_FILE, JSON.stringify(data, null, 2), 'utf-8');
  } catch (error) {
    console.error('记录任务状态失败:', error.message);
  }
}

// 任务ID和名称
const TASK_ID = 'journal-papers-daily';
const TASK_NAME = '期刊论文日报';
const TASK_SCHEDULE = '08:00';
const OUTPUT_FILE = 'journal-papers-daily.md';

// 记录任务开始
logTaskStatus(TASK_ID, {
  name: TASK_NAME,
  schedule: TASK_SCHEDULE,
  status: 'running',
  output_file: OUTPUT_FILE
});

// 构建 fetch.mjs 的路径
const fetchScript = path.join(__dirname, 'fetch.mjs');

// 获取命令行参数
const args = process.argv.slice(2);

// 调用原始的 fetch.mjs
const child = spawn('node', [fetchScript, ...args], {
  stdio: ['inherit', 'pipe', 'pipe'],
  cwd: process.cwd()
});

let stdout = '';
let stderr = '';

child.stdout.on('data', (data) => {
  stdout += data.toString();
  process.stdout.write(data);
});

child.stderr.on('data', (data) => {
  stderr += data.toString();
  process.stderr.write(data);
});

child.on('close', (code) => {
  if (code === 0) {
    // 任务成功
    logTaskStatus(TASK_ID, {
      status: 'success',
      error: null
    });
    
    // 将输出保存到文件
    const outputPath = path.join(process.cwd(), OUTPUT_FILE);
    try {
      fs.writeFileSync(outputPath, stdout, 'utf-8');
      console.error(`\n✅ 结果已保存到: ${outputPath}`);
    } catch (error) {
      console.error(`\n⚠️ 保存文件失败: ${error.message}`);
    }
  } else {
    // 任务失败
    const errorMsg = stderr || `进程退出码: ${code}`;
    logTaskStatus(TASK_ID, {
      status: 'failed',
      error: errorMsg.substring(0, 200) // 限制错误信息长度
    });
    console.error(`\n❌ 任务失败: ${errorMsg}`);
  }
  
  process.exit(code);
});

child.on('error', (error) => {
  logTaskStatus(TASK_ID, {
    status: 'failed',
    error: error.message
  });
  console.error(`\n❌ 启动失败: ${error.message}`);
  process.exit(1);
});
