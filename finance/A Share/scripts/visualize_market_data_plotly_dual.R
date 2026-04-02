#!/usr/bin/env Rscript
#
# A股两市行情数据可视化脚本 - Plotly双Y轴版本
# 参考用户初始版本风格：上方情绪指数线 + 下方成交额柱状图
#
# 依赖: install.packages(c('readr','dplyr','plotly','htmlwidgets'))
#
# 用法: Rscript visualize_market_data_plotly_dual.R [days]

library(readr)
library(dplyr)
library(plotly)
library(htmlwidgets)
library(lubridate)  # 用于日期计算

# 文件路径配置
DATA_FILE <- "A Share/tushare/market_combined_data.csv"
OUTPUT_DIR <- "A Share/visualization"

# 创建输出目录
dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)

# 读取数据
cat("Loading data from", DATA_FILE, "...\n")
df <- read_csv(DATA_FILE, show_col_types = FALSE) %>%
  mutate(trade_date = as.Date(as.character(trade_date), format = "%Y%m%d")) %>%
  arrange(trade_date)  # 按日期升序排列

cat("Loaded", nrow(df), "records\n")

# 获取日期范围
cat("Date range:", format(min(df$trade_date), "%Y-%m-%d"), "to", format(max(df$trade_date), "%Y-%m-%d"), "\n")

# 获取命令行参数
days_num <- 365 * 6  # 默认6年
args <- commandArgs(trailingOnly = TRUE)
if (length(args) > 0) {
  days_num <- as.numeric(args[1])
}

# 过滤数据
end_date_obj <- max(df$trade_date)
start_date_obj <- end_date_obj - days(days_num)  # 使用lubridate的days()函数
df_filtered <- df %>% filter(trade_date >= start_date_obj)

start_date <- format(start_date_obj, "%Y%m%d")
end_date <- format(end_date_obj, "%Y%m%d")

cat("Filtered:", nrow(df_filtered), "records from", start_date, "to", end_date, "\n")

# 获取最新数据
latest <- tail(df_filtered, 1)
latest_date_label <- format(latest$trade_date, "%m月%d日")

# 计算日环比
if (nrow(df_filtered) >= 2) {
  prev <- df_filtered[nrow(df_filtered) - 1, ]
  turnover_change <- latest$total_turnover - prev$total_turnover
  margin_change <- latest$margin_balance - prev$margin_balance
}

# ==================== 图表1: 情绪指数 + 成交额（双Y轴） ====================
cat("\nGenerating Price vs Turnover chart (dual Y-axis)...\n")

# 上方：情绪指数线
p1 <- plot_ly(df_filtered, x = ~trade_date) %>%
  add_lines(
    y = ~avg_close,
    name = '情绪指数',
    line = list(color = '#E67E22', width = 2),
    yaxis = 'y1',
    hovertemplate = paste(
      "日期: %{x|%Y-%m-%d}<br>",
      "情绪指数: %{y:.2f} 点<br>",
      "<extra></extra>"
    )
  ) %>%
  layout(
    title = list(
      text = paste0('沪+深（指数均值）收盘与两市成交金额<br><sup>',
                    latest_date_label, format(latest$avg_close, nsmall=2), '点 | ',
                    '成交额 ', round(latest$total_turnover, 0), '亿</sup>'),
      font = list(size = 32),
      y = 0.85  # 向下调整十分之一（从默认0.9到0.85）
    ),
    xaxis = list(
      title = '',
      tickformat = '%Y/%m/%d',
      tickangle = 0,
      gridcolor = '#E5E5E5',
      zeroline = FALSE
    ),
    yaxis = list(
      title = '',
      side = 'right',
      titlefont = list(color = '#E67E22'),
      tickfont = list(color = '#E67E22'),
      gridcolor = '#F0F0F0',
      zeroline = FALSE
    ),
    hovermode = 'x unified',
    plot_bgcolor = '#FAFAFA',
    paper_bgcolor = 'white',
    margin = list(t = 80, b = 40),
    showlegend = FALSE
  )

# 下方：成交额柱状图
p2 <- plot_ly(df_filtered, x = ~trade_date) %>%
  add_bars(
    y = ~total_turnover,
    name = '成交额',
    marker = list(color = '#5B9BD5', opacity = 0.8),
    hovertemplate = paste(
      "日期: %{x|%Y-%m-%d}<br>",
      "成交额: %{y:.0f} 亿元<br>",
      "<extra></extra>"
    )
  ) %>%
  layout(
    xaxis = list(
      title = '日期',
      tickformat = '%Y/%m/%d',
      tickangle = -30,
      gridcolor = '#E5E5E5'
    ),
    yaxis = list(
      title = '',
      titlefont = list(color = '#5B9BD5'),
      tickfont = list(color = '#5B9BD5'),
      gridcolor = '#F0F0F0',
      zeroline = FALSE
    ),
    hovermode = 'x unified',
    plot_bgcolor = '#FAFAFA',
    paper_bgcolor = 'white',
    margin = list(t = 20, b = 60),
    showlegend = FALSE
  )

# 添加日环比标注 - 固定在水平方向右侧五分之一处
if (exists("turnover_change")) {
  change_text <- paste0("较前1日", ifelse(turnover_change > 0, "增", "减"), 
                        round(abs(turnover_change), 0), "亿")
  change_color <- ifelse(turnover_change > 0, "#27AE60", "#E74C3C")
  
  # 计算右侧五分之一位置的日期
  date_range <- max(df_filtered$trade_date) - min(df_filtered$trade_date)
  right_fifth_date <- min(df_filtered$trade_date) + date_range * 0.8
  
  p2 <- p2 %>% add_annotations(
    x = right_fifth_date,
    y = max(df_filtered$total_turnover) * 0.9,
    text = change_text,
    font = list(color = change_color, size = 28),
    showarrow = FALSE,
    xref = "x",
    yref = "y"
  )
}

# 合并子图
fig1 <- subplot(p1, p2, nrows = 2, shareX = TRUE, heights = c(0.6, 0.4), margin = 0.05) %>%
  config(
    displayModeBar = TRUE,
    displaylogo = FALSE,
    toImageButtonOptions = list(
      format = 'png',
      filename = paste0('收盘与成交额_', start_date, '_', end_date),
      height = 900,
      width = 1600,
      scale = 2
    )
  )

# 保存图表1
out_html1 <- file.path(OUTPUT_DIR, paste0('收盘与成交额_plotly_', start_date, '_', end_date, '.html'))
htmlwidgets::saveWidget(fig1, out_html1, selfcontained = TRUE, 
                        title = '沪+深收盘与成交额')

cat('Saved:', out_html1, '\n')

# ==================== 图表2: 情绪指数 + 融资余额（双Y轴） ====================
cat("\nGenerating Price vs Margin chart (dual Y-axis)...\n")

df_margin <- df_filtered %>% filter(!is.na(margin_balance))

if (nrow(df_margin) > 0) {
  latest_margin <- tail(df_margin, 1)
  latest_margin_label <- format(latest_margin$trade_date, "%m月%d日")
  
  if (nrow(df_margin) >= 2) {
    prev_margin <- df_margin[nrow(df_margin) - 1, ]
    margin_change_val <- latest_margin$margin_balance - prev_margin$margin_balance
  }
  
  # 上方：情绪指数线
  p3 <- plot_ly(df_margin, x = ~trade_date) %>%
    add_lines(
      y = ~avg_close,
      name = '情绪指数',
      line = list(color = '#E67E22', width = 2),
      hovertemplate = paste(
        "日期: %{x|%Y-%m-%d}<br>",
        "情绪指数: %{y:.2f} 点<br>",
        "<extra></extra>"
      )
    ) %>%
    layout(
      title = list(
        text = paste0('沪+深（指数均值）收盘与两市融资余额<br><sup>',
                      latest_margin_label, format(latest_margin$avg_close, nsmall=2), '点 | ',
                      '融资余额 ', round(latest_margin$margin_balance, 0), '亿</sup>'),
        font = list(size = 32),
        y = 0.85
      ),
      xaxis = list(
        title = '',
        tickformat = '%Y/%m/%d',
        tickangle = 0,
        gridcolor = '#E5E5E5',
        zeroline = FALSE
      ),
      yaxis = list(
        title = '',
        side = 'right',
        titlefont = list(color = '#E67E22'),
        tickfont = list(color = '#E67E22'),
        gridcolor = '#F0F0F0',
        zeroline = FALSE
      ),
      hovermode = 'x unified',
      plot_bgcolor = '#FAFAFA',
      paper_bgcolor = 'white',
      margin = list(t = 80, b = 40),
      showlegend = FALSE
    )
  
  # 下方：融资余额柱状图
  p4 <- plot_ly(df_margin, x = ~trade_date) %>%
    add_bars(
      y = ~margin_balance,
      name = '融资余额',
      marker = list(color = '#27AE60', opacity = 0.8),
      hovertemplate = paste(
        "日期: %{x|%Y-%m-%d}<br>",
        "融资余额: %{y:.0f} 亿元<br>",
        "<extra></extra>"
      )
    ) %>%
    layout(
      xaxis = list(
        title = '日期',
        tickformat = '%Y/%m/%d',
        tickangle = -30,
        gridcolor = '#E5E5E5'
      ),
      yaxis = list(
        title = '',
        titlefont = list(color = '#27AE60'),
        tickfont = list(color = '#27AE60'),
        gridcolor = '#F0F0F0',
        zeroline = FALSE
      ),
      hovermode = 'x unified',
      plot_bgcolor = '#FAFAFA',
      paper_bgcolor = 'white',
      margin = list(t = 20, b = 60),
      showlegend = FALSE
    )
  
  # 添加日环比标注 - 融资余额图表使用固定红色
  if (exists("margin_change_val")) {
    change_text_m <- paste0("较前1日", ifelse(margin_change_val > 0, "增", "减"), 
                            round(abs(margin_change_val), 0), "亿")
    # 固定使用红色，不根据增减变化
    change_color_m <- "#E74C3C"
    
    # 计算右侧五分之一位置的日期
    date_range_m <- max(df_margin$trade_date) - min(df_margin$trade_date)
    right_fifth_date_m <- min(df_margin$trade_date) + date_range_m * 0.8
    
    p4 <- p4 %>% add_annotations(
      x = right_fifth_date_m,
      y = max(df_margin$margin_balance) * 0.95,
      text = change_text_m,
      font = list(color = change_color_m, size = 28),
      showarrow = FALSE,
      xref = "x",
      yref = "y"
    )
  }
  
  # 合并子图
  fig2 <- subplot(p3, p4, nrows = 2, shareX = TRUE, heights = c(0.6, 0.4), margin = 0.05) %>%
    config(
      displayModeBar = TRUE,
      displaylogo = FALSE,
      toImageButtonOptions = list(
        format = 'png',
        filename = paste0('收盘与融资余额_', start_date, '_', end_date),
        height = 900,
        width = 1600,
        scale = 2
      )
    )
  
  # 保存图表2
  out_html2 <- file.path(OUTPUT_DIR, paste0('收盘与融资余额_plotly_', start_date, '_', end_date, '.html'))
  htmlwidgets::saveWidget(fig2, out_html2, selfcontained = TRUE,
                          title = '沪+深收盘与融资余额')
  
  cat('Saved:', out_html2, '\n')
} else {
  cat("Warning: No margin data available for chart 2\n")
}

cat('\n============================================================\n')
cat('Interactive charts generated successfully!\n')
cat('============================================================\n')
cat('Open the HTML files in a web browser to view interactive charts.\n')
