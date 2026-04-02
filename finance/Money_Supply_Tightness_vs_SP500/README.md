# 美债利差与标普500可视化工作流

## 文件说明

| 文件 | 说明 |
|-----|------|
| `yield_spread_workflow.R` | **主工作流脚本** - 读取数据、计算利差、生成交互式图表 |
| `yield_spread_sp500_interactive.html` | 生成的交互式图表（用浏览器打开） |

## 使用方法

### 1. 更新数据（如有需要）

```bash
# 更新美债收益率数据
cd ../us_treasury_workflow
python update_us_treasury_data.py

# 更新标普500数据
cd ../Global-Markets/finance/Global-Markets
python workflow.py
```

### 2. 运行可视化工作流

```bash
cd D:\OpenClawData\.openclaw\workspace\finance\Money_Supply_Tightness_vs_SP500
Rscript yield_spread_workflow.R
```

### 3. 查看结果

用浏览器打开生成的HTML文件：
```bash
start yield_spread_sp500_interactive.html
```

## 工作流配置

在 `yield_spread_workflow.R` 文件顶部的 `CONFIG` 列表中可以修改：

```r
CONFIG <- list(
  # 输入文件路径 (相对于本目录)
  treasury_file = "../us_treasury_workflow/us_treasury_yields_all_terms.csv",
  sp500_file = "../Global-Markets/finance/Global-Markets/SP500_History.csv",
  
  # 输出文件
  output_file = "yield_spread_sp500_interactive.html",
  
  # 利差计算: 短期期限 - 长期期限
  short_term = "X3月",    # 3个月
  long_term = "X10年",    # 10年
  
  # 图表标题
  title = "S&P 500 Index vs US Treasury 3M-10Y Yield Spread"
)
```

## 输出指标

运行后会显示：
- 数据时间范围
- 利差统计（均值、标准差、极值）
- 倒挂天数及占比
- 标普500区间收益
- 当前利差水平

## 图表交互功能

生成的HTML图表支持：
- **悬停提示**: 鼠标悬停查看具体数值
- **图例切换**: 点击显示/隐藏线条
- **时间范围**: 6个月/1年/2年/5年/全部快速选择
- **范围滑块**: 底部拖拽选择时间区间
- **缩放**: 框选区域放大查看

## 依赖包

需要安装以下R包：
```r
install.packages(c("plotly", "tidyr", "dplyr", "htmlwidgets"))
```

## 注意事项

- 确保数据文件路径正确
- 美债数据文件需要包含 `X3月` 和 `X10年` 列
- 标普500数据文件需要包含 `date` 和 `close` 列
- 生成的HTML文件是独立的，可以复制到其他位置查看
