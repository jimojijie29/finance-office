# 美国国债收益率曲线图绘制脚本（全期限版本）
# 支持 1月/3月/6月/1年/2年/3年/5年/7年/10年/20年/30年 共11个期限
# 生成支持多选叠加的交互式图表

library(plotly)
library(tidyr)
library(dplyr)
library(htmlwidgets)

# ============================================
# Step 1: 读取数据（更新为全期限版本）
# ============================================
df <- read.csv("us_treasury_yields_all_terms.csv", fileEncoding = "UTF-8")
df$date <- as.Date(df$date)

# ============================================
# Step 2: 数据重塑（宽格式 → 长格式）
# ============================================
# 获取所有可用的期限列（排除date列）
available_cols <- setdiff(names(df), "date")

# 定义完整的期限映射
all_maturities <- c("X1月", "X3月", "X6月", "X1年", "X2年", "X3年", "X5年", "X7年", "X10年", "X20年", "X30年")
all_labels <- c("1月期", "3月期", "6月期", "1年期", "2年期", "3年期", "5年期", "7年期", "10年期", "20年期", "30年期")

# 过滤出实际存在的列
maturity_cols <- intersect(all_maturities, available_cols)
label_map <- setNames(all_labels, all_maturities)

# 重塑数据
df_long <- df %>%
  pivot_longer(cols = all_of(maturity_cols), names_to = "maturity_raw", values_to = "yield") %>%
  mutate(
    maturity = factor(maturity_raw, 
                      levels = maturity_cols,
                      labels = label_map[maturity_cols])
  ) %>%
  arrange(date, maturity)

# ============================================
# Step 3: 定义颜色映射（动态根据可用期限）
# ============================================
colors <- c(
  "1月期" = "#E53935",   # 红色（超短期）
  "3月期" = "#FB8C00",   # 橙色
  "6月期" = "#FDD835",   # 黄色
  "1年期" = "#7CB342",   # 浅绿
  "2年期" = "#00897B",   # 青绿
  "3年期" = "#039BE5",   # 浅蓝
  "5年期" = "#3949AB",   # 靛蓝
  "7年期" = "#8E24AA",   # 紫色
  "10年期" = "#D81B60",  # 玫红（长期基准）
  "20年期" = "#5E35B1",  # 深紫
  "30年期" = "#1E88E5"   # 深蓝
)

# 只保留实际存在的期限的颜色
active_colors <- colors[names(colors) %in% label_map[maturity_cols]]
active_maturities <- label_map[maturity_cols]

# ============================================
# Step 4: 创建交互式图表
# ============================================
fig <- plot_ly()

for (mat in active_maturities) {
  data_subset <- df_long %>% filter(maturity == mat)
  
  fig <- fig %>% add_trace(
    data = data_subset,
    x = ~date,
    y = ~yield,
    type = 'scatter',
    mode = 'lines',
    name = mat,
    line = list(color = active_colors[[mat]], width = 2.5),
    hovertemplate = paste0(
      "<b>", mat, "</b><br>",
      "日期: %{x|%Y-%m-%d}<br>",
      "收益率: %{y:.3f}%<br>",
      "<extra></extra>"
    ),
    visible = TRUE
  )
}

# 构建预设按钮的可见性配置
n_maturities <- length(active_maturities)
all_visible <- rep(TRUE, n_maturities)
none_visible <- rep(FALSE, n_maturities)

# 根据期限名称确定索引
get_visibility <- function(selected_labels) {
  vis <- rep(FALSE, n_maturities)
  for (i in 1:n_maturities) {
    if (active_maturities[i] %in% selected_labels) {
      vis[i] <- TRUE
    }
  }
  return(vis)
}

# ============================================
# Step 5: 配置布局（关键：多选交互）
# ============================================
fig <- fig %>% layout(
  title = list(
    text = "<b>美国国债收益率走势（全期限）</b><br><sub>点击图例显示/隐藏，点击按钮选择预设组合</sub>",
    font = list(size = 18),
    x = 0.5,
    xanchor = "center"
  ),
  
  xaxis = list(
    title = "",
    tickformat = "%Y-%m",
    tickangle = -45,
    rangeslider = list(visible = TRUE),
    rangeselector = list(
      buttons = list(
        list(count = 3, label = "3月", step = "month", stepmode = "backward"),
        list(count = 6, label = "6月", step = "month", stepmode = "backward"),
        list(count = 1, label = "1年", step = "year", stepmode = "backward"),
        list(count = 2, label = "2年", step = "year", stepmode = "backward"),
        list(step = "all", label = "全部")
      )
    ),
    showgrid = TRUE,
    gridcolor = "#E0E0E0"
  ),
  
  yaxis = list(
    title = "收益率 (%)",
    tickformat = ".2f",
    hoverformat = ".3f",
    showgrid = TRUE,
    gridcolor = "#E0E0E0"
  ),
  
  hovermode = "x unified",
  
  # 图例配置 - 关键：itemclick = "toggle" 实现多选
  legend = list(
    orientation = "h",
    yanchor = "top",
    y = -0.15,
    xanchor = "center",
    x = 0.5,
    bgcolor = "rgba(255,255,255,0.95)",
    bordercolor = "#BDBDBD",
    borderwidth = 1,
    font = list(size = 12),
    title = list(text = "<b>点击切换显示/隐藏:</b>"),
    itemclick = "toggle",
    itemdoubleclick = "toggleothers"
  ),
  
  plot_bgcolor = "#FAFAFA",
  paper_bgcolor = "white",
  margin = list(l = 60, r = 40, t = 100, b = 160),
  
  # 预设按钮组（动态根据可用期限）
  updatemenus = list(
    list(
      type = "buttons",
      direction = "right",
      x = 0.5,
      y = 1.06,
      xanchor = "center",
      yanchor = "top",
      pad = list(t = 10, b = 10),
      font = list(size = 11),
      bgcolor = "#E3F2FD",
      bordercolor = "#1976D2",
      borderwidth = 1,
      buttons = list(
        list(
          label = "全部",
          method = "update",
          args = list(list(visible = all_visible), list())
        ),
        list(
          label = "清空",
          method = "update",
          args = list(list(visible = none_visible), list())
        ),
        list(
          label = "超短期(1/3/6月)",
          method = "update",
          args = list(list(visible = get_visibility(c("1月期", "3月期", "6月期"))), list())
        ),
        list(
          label = "短期(1/2/3年)",
          method = "update",
          args = list(list(visible = get_visibility(c("1年期", "2年期", "3年期"))), list())
        ),
        list(
          label = "中期(3/5/7年)",
          method = "update",
          args = list(list(visible = get_visibility(c("3年期", "5年期", "7年期"))), list())
        ),
        list(
          label = "长期(7/10年)",
          method = "update",
          args = list(list(visible = get_visibility(c("7年期", "10年期"))), list())
        ),
        list(
          label = "关键(2/10年)",
          method = "update",
          args = list(list(visible = get_visibility(c("2年期", "10年期"))), list())
        ),
        list(
          label = "超长期(20/30年)",
          method = "update",
          args = list(list(visible = get_visibility(c("20年期", "30年期"))), list())
        )
      )
    )
  )
)

# ============================================
# Step 6: 保存HTML
# ============================================
htmlwidgets::saveWidget(fig, "../us_treasury_all_terms.html", selfcontained = TRUE)

cat("\n✅ 美国国债收益率全期限交互式图表生成完成！\n")
cat("输出文件: us_treasury_all_terms.html\n")
cat("包含期限:", paste(active_maturities, collapse = "/"), "\n\n")
