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
# Step 2: 数据重塑（宽格式 \u2192 长格式）
# ============================================
# 获取所有可用的期限列（排除date列）
available_cols <- setdiff(names(df), "date")

# 定义完整的期限映射（使用Unicode转义避免编码问题）
all_maturities <- c("X1\u6708", "X3\u6708", "X6\u6708", "X1\u5e74", "X2\u5e74", "X3\u5e74", "X5\u5e74", "X7\u5e74", "X10\u5e74", "X20\u5e74", "X30\u5e74")
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
  "1\u6708\u671f" = "#E53935",   # \u7ea2\u8272\uff08\u8d85\u77ed\u671f\uff09
  "3\u6708\u671f" = "#FB8C00",   # \u6a59\u8272
  "6\u6708\u671f" = "#FDD835",   # \u9ec4\u8272
  "1\u5e74\u671f" = "#7CB342",   # \u6d45\u7eff
  "2\u5e74\u671f" = "#00897B",   # \u9752\u7eff
  "3\u5e74\u671f" = "#039BE5",   # \u6d45\u84dd
  "5\u5e74\u671f" = "#3949AB",   # \u975b\u84dd
  "7\u5e74\u671f" = "#8E24AA",   # \u7d2b\u8272
  "10\u5e74\u671f" = "#D81B60",  # \u73ab\u7ea2\uff08\u957f\u671f\u57fa\u51c6\uff09
  "20\u5e74\u671f" = "#5E35B1",  # \u6df1\u7d2b
  "30\u5e74\u671f" = "#1E88E5"   # \u6df1\u84dd
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
      "\u65e5\u671f: %{x|%Y-%m-%d}<br>",
      "\u6536\u76ca\u7387: %{y:.3f}%<br>",
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
    tickangle = -30,
    rangeslider = list(visible = TRUE, thickness = 0.08),
    rangeselector = list(
      buttons = list(
        list(count = 3, label = "3\u6708", step = "month", stepmode = "backward"),
        list(count = 6, label = "6\u6708", step = "month", stepmode = "backward"),
        list(count = 1, label = "1\u5e74", step = "year", stepmode = "backward"),
        list(count = 2, label = "2\u5e74", step = "year", stepmode = "backward"),
        list(step = "all", label = "\u5168\u90e8")
      ),
      x = 0,
      xanchor = "left",
      y = 1.12,
      yanchor = "top"
    ),
    showgrid = TRUE,
    gridcolor = "#E0E0E0",
    domain = c(0, 1)
  ),
  
  yaxis = list(
    title = "\u6536\u76ca\u7387 (%)",
    tickformat = ".2f",
    hoverformat = ".3f",
    showgrid = TRUE,
    gridcolor = "#E0E0E0"
  ),
  
  hovermode = "x unified",
  
  # 图例配置 - 关键：itemclick = "toggle" 实现多选
  # 将图例移到顶部，节省底部空间
  legend = list(
    orientation = "h",
    yanchor = "bottom",
    y = 1.02,  # 放在图表上方
    xanchor = "center",
    x = 0.5,
    bgcolor = "rgba(255,255,255,0.8)",
    bordercolor = "#BDBDBD",
    borderwidth = 1,
    font = list(size = 11),
    title = list(text = ""),
    itemclick = "toggle",
    itemdoubleclick = "toggleothers"
  ),
  
  plot_bgcolor = "#FAFAFA",
  paper_bgcolor = "white",
  # 调整边距：顶部留出图例空间，底部减小，增加图表区域
  margin = list(l = 60, r = 40, t = 120, b = 60)
  
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
