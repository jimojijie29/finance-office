# HEARTBEAT.md

## 检查清单

每次 heartbeat 时，按以下顺序检查：

### 1. 定时任务状态检查

**执行以下 Python 代码检查任务状态：**

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'logs'))
from task_logger import check_all_tasks, format_task_report

issues = check_all_tasks()
if issues:
    report = format_task_report(issues)
    print(report)  # 输出报告，不回复 HEARTBEAT_OK
else:
    print("所有定时任务正常")
```

**当前监控任务：**

| 任务名称 | 计划时间 | 输出文件检查 |
|----------|----------|--------------|
| A股两市行情数据每日更新 | 09:30 | `finance/tushare/market_combined_data.csv` |
| 期刊论文日报 | 08:00 | `journal-papers-daily.md` |
| 莫大仙岳居阅读-上午 | 10:00 | - |
| 莫大仙岳居阅读-下午 | 15:00 | - |
| 论文写作提醒 | 20:00 | - |
| AI日记整理 | 21:00 | `memory/YYYY-MM-DD.md` |
| 记忆提炼 | 17:25 | `MEMORY.md` |

**异常回复格式：**
```
[!] 定时任务异常:
- [任务名]: [具体原因]
- [任务名]: [具体原因]
```

### 2. 记忆记录任务
检查当前 session 是否有以下重要内容需要记录：

#### 需要记录的内容类型
- 重要决策或结论
- 新发现的偏好或习惯
- 项目进展或状态变化
- 需要记住的人名、地点、事件
- 学到的教训或最佳实践
- 用户明确说"记下来"的内容

#### 记录方式
1. **日常记忆** → 写入 `memory/YYYY-MM-DD.md`
   - 格式：`HH:mm [事件类型] 内容`
   - 例如：`09:47 [偏好] 用户希望自动化记忆管理，设置了两层记忆机制`

2. **长期记忆** → 用户说"记下来"时，同时更新 `MEMORY.md`

3. **系统规则** → 涉及工作流程的改进，更新 `AGENTS.md`

#### 记忆文件位置
- 日常记忆：`memory/YYYY-MM-DD.md`（今天）
- 长期记忆：`MEMORY.md`
- 系统规则：`AGENTS.md`
- 工具配置：`TOOLS.md`

#### 注意
- 如果今天还没有创建 daily memory 文件，先创建
- 记录要简洁，避免冗余
- 敏感信息（密码、私钥等）不要记录

---

## 回复规则

- **有任务异常或需记录内容** → 输出具体内容，不回复 HEARTBEAT_OK
- **无异常且无需记录** → 回复 HEARTBEAT_OK

---

*更新于 2026-03-27*
