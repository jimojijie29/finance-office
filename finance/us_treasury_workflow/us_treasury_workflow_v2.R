# 美国国债收益率曲线图绘制脚本（全期限版本）
# 支持 1月/3月/6月/1年/2年/3年/5年/7年/10年/20年/30年 共11个期限
# 生成支持多选叠加的交互式图表

# 设置编码（修复Windows中文输出问题）
# 尝试设置UTF-8编码，如果失败则使用系统默认
tryCatch({
  Sys.setlocale("LC_CTYPE", "en_US.UTF-8")
}, warning = function(w) {
  # 忽略警告，使用系统默认
})

library(plotly)
library(tidyr)
library(dplyr)
library(htmlwidgets)
library(htmltools)  # 用于确保正确的HTML编码

# 辅助函数：修复Windows下的编码问题
fix_encoding <- function(text) {
  # 在Windows上，如果文本已经是UTF-8，就不需要转换
  # 这个函数确保文本以UTF-8编码处理
  if (.Platform$OS.type == "windows") {
    # 使用iconv确保UTF-8编码
    text <- iconv(text, from = "", to = "UTF-8", sub = "byte")
  }
  return(text)
}

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

# 定义完整的期限映射（使用Unicode转义避免编码问题）
all_maturities <- c("X1月", "X3月", "X6月", "X1年", "X2年", "X3年", "X5年", "X7年", "X10年", "X20年", "X30年")
all_labels <- c("1\u6708\u671f", "3\u6708\u671f", "6\u6708\u671f", "1\u5e74\u671f", "2\u5e74\u671f", "3\u5e74\u671f", "5\u5e74\u671f", "7\u5e74\u671f", "10\u5e74\u671f", "20\u5e74\u671f", "30\u5e74\u671f")

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
    text = "<b>\u7f8e\u56fd\u56fd\u503a\u6536\u76ca\u7387\u8d70\u52bf\uff08\u5168\u671f\u9650\uff09</b><br><sub>\u70b9\u51fb\u56fe\u4f8b\u663e\u793a/\u9690\u85cf\uff0c\u70b9\u51fb\u6309\u94ae\u9009\u62e9\u9884\u8bbe\u7ec4\u5408</sub>",
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
    title = list(text = "<b>\u70b9\u51fb\u5207\u6362\u663e\u793a/\u9690\u85cf:</b>"),
    itemclick = "toggle",
    itemdoubleclick = "toggleothers"
  ),
  
  plot_bgcolor = "#FAFAFA",
  paper_bgcolor = "white",
  margin = list(l = 60, r = 40, t = 80, b = 160)
  
  # 注意：移除了 updatemenus 按钮组，使用图例进行多选
)

# ============================================
# Step 6: 保存HTML（使用UTF-8编码）
# ============================================
# 使用 htmltools 确保正确的编码
htmlwidgets::saveWidget(fig, "us_treasury_all_terms.html", selfcontained = TRUE)

# Windows下需要额外处理编码问题
if (.Platform$OS.type == "windows") {
  # 读取生成的HTML文件
  html_content <- readLines("us_treasury_all_terms.html", encoding = "UTF-8", warn = FALSE)
  # 确保以UTF-8编码写回
  writeLines(html_content, "us_treasury_all_terms.html", useBytes = TRUE)
}

# 使用英文输出避免编码问题
cat("\n[OK] US Treasury Yield Curve Chart Generated Successfully!\n")
cat("Output file: us_treasury_all_terms.html\n")
cat("Maturities included:", paste(active_maturities, collapse = "/"), "\n\n")
