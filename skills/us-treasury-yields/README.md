# 美国国债收益率工作流

## 快速开始

### 1. 数据更新

```bash
cd skills/us-treasury-yields
python scripts/update_us_treasury_data.py
```

### 2. 仅生成可视化

```bash
cd skills/us-treasury-yields
Rscript scripts/us_treasury_workflow_v2.R
```

## 工作流程

1. **数据获取**: Python脚本调用 mx-macro-data 获取最新数据
2. **数据处理**: 合并新旧数据，自动去重
3. **数据验证**: 检查数据质量，排除异常值
4. **可视化**: R脚本生成交互式 Plotly 图表

## 输出文件

| 文件 | 说明 |
|------|------|
| `data/us_treasury_yields_all_terms.csv` | 历史收益率数据 |
| `data/us_treasury_all_terms.html` | 交互式可视化图表 |

## 可视化功能

- **图例多选**: 点击图例标签显示/隐藏对应期限
- **时间范围**: 底部滑块选择时间范围
- **快捷按钮**: 3月/6月/1年/2年/全部 快速切换
- **悬停提示**: 鼠标悬停显示具体数值

## 数据说明

覆盖11个期限：1月、3月、6月、1年、2年、3年、5年、7年、10年、20年、30年

数据源：东方财富妙想服务
