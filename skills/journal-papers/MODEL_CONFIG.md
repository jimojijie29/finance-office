# Journal Papers Skill - 本地模型配置指南

## 最终解决方案（2026-03-24）

### 推荐模型
- **模型名称**: `qwen3-vl-8b`
- **API端点**: `http://127.0.0.1:1234/v1/chat/completions`
- **优势**:
  - ✅ 无强制思考模式（reasoning_content 为空）
  - ✅ 翻译结果直接输出在 content 字段
  - ✅ 响应速度快，稳定性好
  - ✅ 翻译质量准确流畅

### 不推荐的模型
- **qwen3.5**: 有严重的思考过度问题，翻译结果藏在 reasoning_content 中，解析困难

### 脚本配置
文件: `skills/journal-papers/scripts/fetch.mjs`

```javascript
const response = await fetch('http://127.0.0.1:1234/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer sk-5070ti'
  },
  body: JSON.stringify({
    model: 'qwen3-vl-8b',  // 推荐模型
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: prompt }
    ],
    temperature: 0.1,
    max_tokens: 2048
  })
});
```

### 批次配置
- **BATCH_SIZE**: 5（每批次翻译5篇）
- **批次间延迟**: 3秒
- **单次请求超时**: 15分钟

### 解析逻辑
优先使用 `content` 字段，无需处理 `reasoning_content`：
```javascript
const content = (data.choices[0].message.content || '').trim();
```

### 测试命令
```bash
node skills/journal-papers/scripts/fetch.mjs
```

### 备用方案
如果本地模型不可用，使用 `--no-translate` 参数：
```bash
node skills/journal-papers/scripts/fetch.mjs --no-translate
```

---
*记录时间: 2026-03-24*
*模型: qwen3-vl-8b*
*状态: ✅ 已验证可用*
