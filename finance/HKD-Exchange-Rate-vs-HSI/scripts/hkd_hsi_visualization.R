# 港元汇率与恒生指数交互式可视化脚本（双Y轴版本）
# 使用 plotly 创建支持多选叠加的交互式图表

library(plotly)
library(dplyr)
library(htmlwidgets)

# ============================================
# Step 1: 读取数据
# ============================================
df_hkd <- read.csv("HKD_USD_Exchange_Rate.csv", fileEncoding = "UTF-8")
df_hsi <- read.csv("Hang_Seng_Index.csv", fileEncoding = "UTF-8")

# 统一列名（处理大小写差异）
names(df_hkd) <- tolower(names(df_hkd))
names(df_hsi) <- tolower(names(df_hsi))

# 转换日期
df_hkd$date <- as.Date(df_hkd$date)
df_hsi$date <- as.Date(df_hsi$date)

# ============================================
# Step 2: 数据对齐（按日期合并）
# ============================================
# 找出共同日期范围
common_start <- max(min(df_hkd$date), min(df_hsi$date))
common_end <- min(max(df_hkd$date), max(df_hsi$date))

cat("数据时间范围:\n")
cat(sprintf("  USD/HKD: %s 至 %s (%d 条)\n", min(df_hkd$date), max(df_hkd$date), nrow(df_hkd)))
cat(sprintf("  HSI:     %s 至 %s (%d 条)\n", min(df_hsi$date), max(df_hsi$date), nrow(df_hsi)))
cat(sprintf("\n共同范围: %s 至 %s\n", common_start, common_end))

# 按日期合并（内连接，只保留共同日期）
df_merged <- merge(
  df_hkd %>% select(date, close),
  df_hsi %>% select(date, close),
  by = "date",
  suffixes = c("_hkd", "_hsi")
)

# 筛选共同日期范围
df_merged <- df_merged %>% filter(date >= common_start & date <= common_end)

# 重命名列
df_merged <- df_merged %>% rename(
  hkd_close = close_hkd,
  hsi_close = close_hsi
)

cat(sprintf("合并后数据: %d 条\n", nrow(df_merged)))

# ============================================
# Step 3: 创建交互式图表（双Y轴版本）
# ============================================

# 颜色定义
color_hkd <- "#1976D2"   # 蓝色 - 汇率
color_hsi <- "#D32F2F"   # 红色 - 恒生指数

fig_dual <- plot_ly()

# 添加USD/HKD汇率（左Y轴）
fig_dual <- fig_dual %>% add_trace(
  data = df_merged,
  x = ~date,
  y = ~hkd_close,
  type = 'scatter',
  mode = 'lines',
  name = 'USD/HKD 汇率',
  line = list(color = color_hkd, width = 2),
  yaxis = 'y1',
  hovertemplate = paste0(
    "<b>USD/HKD 汇率</b><br>",
    "日期: %{x|%Y-%m-%d}<br>",
    "汇率: %{y:.4f}<br>",
    "<extra></extra>"
  )
)

# 添加恒生指数（右Y轴）
fig_dual <- fig_dual %>% add_trace(
  data = df_merged,
  x = ~date,
  y = ~hsi_close,
  type = 'scatter',
  mode = 'lines',
  name = '恒生指数',
  line = list(color = color_hsi, width = 2),
  yaxis = 'y2',
  hovertemplate = paste0(
    "<b>恒生指数</b><br>",
    "日期: %{x|%Y-%m-%d}<br>",
    "指数: %{y:.2f}<br>",
    "<extra></extra>"
  )
)

# 配置双Y轴布局
fig_dual <- fig_dual %>% layout(
  title = list(
    text = "<b>港元汇率 vs 恒生指数走势对比</b><br><sub>双Y轴显示：左轴=汇率，右轴=指数 | 数据期间: 2013-08 至 2026-03</sub>",
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
        list(count = 3, label = "3年", step = "year", stepmode = "backward"),
        list(count = 5, label = "5年", step = "year", stepmode = "backward"),
        list(step = "all", label = "全部")
      )
    ),
    showgrid = TRUE,
    gridcolor = "#E0E0E0"
  ),
  
  yaxis = list(
    title = "USD/HKD 汇率",
    titlefont = list(color = color_hkd),
    tickfont = list(color = color_hkd),
    tickformat = ".4f",
    showgrid = TRUE,
    gridcolor = "#E0E0E0",
    side = "left"
  ),
  
  yaxis2 = list(
    title = "恒生指数",
    titlefont = list(color = color_hsi),
    tickfont = list(color = color_hsi),
    tickformat = ".0f",
    overlaying = "y",
    side = "right",
    showgrid = FALSE
  ),
  
  hovermode = "x unified",
  
  legend = list(
    orientation = "h",
    yanchor = "top",
    y = -0.15,
    xanchor = "center",
    x = 0.5,
    bgcolor = "rgba(255,255,255,0.95)",
    bordercolor = "#BDBDBD",
    borderwidth = 1,
    itemclick = "toggle",
    itemdoubleclick = "toggleothers"
  ),
  
  plot_bgcolor = "#FAFAFA",
  paper_bgcolor = "white",
  margin = list(l = 80, r = 80, t = 100, b = 120)
)

# ============================================
# Step 4: 保存图表
# ============================================
htmlwidgets::saveWidget(fig_dual, "hkd_vs_hsi_dual_axis.html", selfcontained = TRUE)
cat("\n✅ 双Y轴对比图表已保存: hkd_vs_hsi_dual_axis.html\n")

# ============================================
# Step 5: 输出统计摘要
# ============================================
cat(paste0("\n", paste(rep("=", 60), collapse = ""), "\n"))
cat("数据摘要\n")
cat(paste0(paste(rep("=", 60), collapse = ""), "\n"))

cat(sprintf("\n共同数据期间: %s 至 %s\n", common_start, common_end))
cat(sprintf("总交易日数: %d\n", nrow(df_merged)))

cat("\nUSD/HKD 汇率统计:\n")
cat(sprintf("  起始值: %.4f\n", df_merged$hkd_close[1]))
cat(sprintf("  结束值: %.4f\n", df_merged$hkd_close[nrow(df_merged)]))
cat(sprintf("  均值: %.4f\n", mean(df_merged$hkd_close, na.rm = TRUE)))
cat(sprintf("  最小值: %.4f (%s)\n", 
            min(df_merged$hkd_close, na.rm = TRUE),
            df_merged$date[which.min(df_merged$hkd_close)]))
cat(sprintf("  最大值: %.4f (%s)\n", 
            max(df_merged$hkd_close, na.rm = TRUE),
            df_merged$date[which.max(df_merged$hkd_close)]))

cat("\n恒生指数统计:\n")
cat(sprintf("  起始值: %.2f\n", df_merged$hsi_close[1]))
cat(sprintf("  结束值: %.2f\n", df_merged$hsi_close[nrow(df_merged)]))
cat(sprintf("  均值: %.2f\n", mean(df_merged$hsi_close, na.rm = TRUE)))
cat(sprintf("  最小值: %.2f (%s)\n", 
            min(df_merged$hsi_close, na.rm = TRUE),
            df_merged$date[which.min(df_merged$hsi_close)]))
cat(sprintf("  最大值: %.2f (%s)\n", 
            max(df_merged$hsi_close, na.rm = TRUE),
            df_merged$date[which.max(df_merged$hsi_close)]))

cat(paste0(paste(rep("=", 60), collapse = ""), "\n"))
cat("图表生成完成！\n")
cat(paste0(paste(rep("=", 60), collapse = ""), "\n"))
