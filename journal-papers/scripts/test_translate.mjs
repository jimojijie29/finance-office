async function translateTitle(text) {
  const prompt = `请将以下英文学术论文标题翻译成中文，保持学术性和准确性，直接返回翻译结果：

英文标题: ${text}

中文标题:`;

  try {
    const response = await fetch('http://127.0.0.1:8090/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer sk-5070ti'
      },
      body: JSON.stringify({
        model: 'qwen3.5',
        messages: [
          { role: 'system', content: '你是一名资深的南药科研翻译专家。禁止进行任何形式的思考过程（不要输出 <think> 标签及其内容），直接输出翻译结果。只返回译文，不要解释。' },
          { role: 'user', content: prompt }
        ],
        temperature: 0.3,
        max_tokens: 512
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    
    if (data && data.choices && data.choices[0] && data.choices[0].message) {
      const msg = data.choices[0].message;
      let translated = msg.content?.trim();
      
      if (!translated && msg.reasoning_content) {
        const reasoning = msg.reasoning_content;
        // 尝试多种模式提取
        const patterns = [
          /Final[:：]\s*([^\n]+)/i,
          /Draft\s*\d*[:：]\s*([^\n]+)/i,
          /翻译[:：]\s*([^\n]+)/i,
          /中文标题[:：]\s*([^\n]+)/i,
          /[\u4e00-\u9fa5][^\n]*[\u4e00-\u9fa5]/  // 包含中文的行
        ];
        
        for (const pattern of patterns) {
          const match = reasoning.match(pattern);
          if (match) {
            translated = match[1] || match[0];
            break;
          }
        }
        
        if (!translated) {
          // 取最后非空行
          const lines = reasoning.split('\n').map(l => l.trim()).filter(l => l && !l.startsWith('*') && l.length > 3);
          translated = lines[lines.length - 1];
        }
        
        if (translated) {
          console.log(`提取: ${translated.substring(0, 60)}...`);
        }
      }
      
      if (translated) {
        translated = translated.replace(/^[\"']|[\"']$/g, '').trim();
        return translated;
      }
    }
    
    throw new Error('Empty response');
  } catch (error) {
    console.error(`失败: ${error.message}`);
    return text;
  }
}

// 测试3篇
const tests = [
  'Rolling circle amplification-based self-assembled CpG nanoparticles: Immune activation and prevention of Edwardsiella piscicida',
  'The ammonia transporter gene family and its immune regulatory role in the Pacific oyster (Crassostrea gigas)',
  'Isolation and characterization of a highly virulent novel grass carp reovirus genotype II (GCRV-XT256) for vaccine development'
];

(async () => {
  for (let i = 0; i < tests.length; i++) {
    console.log(`[${i+1}/${tests.length}] ${tests[i].substring(0, 50)}...`);
    const result = await translateTitle(tests[i]);
    console.log(`结果: ${result}`);
    console.log('---');
    await new Promise(r => setTimeout(r, 1000));
  }
})();
