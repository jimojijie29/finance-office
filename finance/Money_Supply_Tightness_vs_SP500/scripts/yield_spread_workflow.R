#!/usr/bin/env Rscript
# -*- coding: utf-8 -*-
#
# 美债3月-10年利差与标普500对比分析 - 固定工作流
# 
# 使用方法:
#   1. 更新数据: 运行 workflow.py 获取最新数据
#   2. 可视化:   Rscript yield_spread_workflow.R
#
# 输出: yield_spread_sp500_interactive.html (交互式图表)
#

suppressPackageStartupMessages({
  library(plotly)
  library(tidyr)
  library(dplyr)
  library(htmlwidgets)
})

# ============================================
# 配置
# ============================================
CONFIG <- list(
  # 输入文件路径 (使用相对于工作目录的路径)
  treasury_file = "us_treasury_workflow/data/us_treasury_yields_all_terms.csv",
  sp500_file = "Global-Markets/data/SP500_History.csv",
  
  # 输出文件
  output_file = "yield_spread_sp500_interactive.html",
  
  # 利差计算: 短期期限 - 长期期限
  short_term = "X3月",    # 3个月
  long_term = "X10年",    # 10年
  
  # 图表标题
  title = "S&P 500 Index vs US Treasury 3M-10Y Yield Spread"
)

# ============================================
# 主函数
# ============================================
main <- function() {
  cat(rep("=", 60), "\n", sep = "")
  cat("美债3月-10年利差与标普500对比分析\n")
  cat(rep("=", 60), "\n", sep = "")
  
  # Step 1: 读取数据
  cat("\n[1/3] 读取数据...\n")
  
  if (!file.exists(CONFIG$treasury_file)) {
    stop("错误: 找不到美债数据文件: ", CONFIG$treasury_file)
  }
  if (!file.exists(CONFIG$sp500_file)) {
    stop("错误: 找不到标普500数据文件: ", CONFIG$sp500_file)
  }
  
  # 读取美债数据
  treasury_df <- read.csv(CONFIG$treasury_file, fileEncoding = "UTF-8")
  treasury_df$date <- as.Date(treasury_df$date)
  
  # 检查必要的列是否存在
  if (!(CONFIG$short_term %in% names(treasury_df))) {
    stop("错误: 找不到短期期限列: ", CONFIG$short_term)
  }
  if (!(CONFIG$long_term %in% names(treasury_df))) {
    stop("错误: 找不到长期期限列: ", CONFIG$long_term)
  }
  
  # 计算利差
  treasury_df$yield_spread <- treasury_df[[CONFIG$short_term]] - treasury_df[[CONFIG$long_term]]
  
  # 读取标普500数据
  sp500_df <- read.csv(CONFIG$sp500_file, fileEncoding = "UTF-8")
  sp500_df$date <- as.Date(sp500_df$date)
  
  # 合并数据
  merged_df <- merge(
    treasury_df[, c("date", "yield_spread")],
    sp500_df[, c("date", "close")],
    by = "date",
    all = FALSE
  ) %>%
    arrange(date)
  
  cat("  数据范围:", min(merged_df$date), "至", max(merged_df$date), "\n")
  cat("  总记录数:", nrow(merged_df), "\n")
  
  # Step 2: 计算统计指标
  cat("\n[2/3] 计算统计指标...\n")
  
  stats <- list(
    spread_mean = mean(merged_df$yield_spread),
    spread_std = sd(merged_df$yield_spread),
    spread_min = min(merged_df$yield_spread),
    spread_max = max(merged_df$yield_spread),
    inversion_days = sum(merged_df$yield_spread < 0),
    sp500_start = merged_df$close[1],
    sp500_end = merged_df$close[nrow(merged_df)],
    sp500_return = (tail(merged_df$close, 1) / head(merged_df$close, 1) - 1) * 100
  )
  stats$inversion_pct <- stats$inversion_days / nrow(merged_df) * 100
  
  cat("  利差范围:", round(stats$spread_min, 3), "% ~", round(stats$spread_max, 3), "%\n")
  cat("  倒挂天数:", stats$inversion_days, "天 (", round(stats$inversion_pct, 1), "%)\n")
  cat("  标普500收益:", round(stats$sp500_return, 2), "%\n")
  
  # Step 3: 创建交互式图表
  cat("\n[3/3] 创建交互式图表...\n")
  
  fig <- create_plot(merged_df, stats)
  
  # 保存图表
  saveWidget(fig, CONFIG$output_file, selfcontained = TRUE)
  cat("  [OK] 图表已保存:", CONFIG$output_file, "\n")
  
  # 完成
  cat("\n", rep("=", 60), "\n", sep = "")
  cat("分析完成\n")
  cat(rep("=", 60), "\n", sep = "")
  
  # 关键发现
  cat("\n【关键发现】\n")
  if (stats$inversion_pct > 50) {
    cat("WARNING: 利差倒挂时间占比高达", round(stats$inversion_pct, 1), "%\n")
  } else {
    cat("利差倒挂天数:", stats$inversion_days, "天 (", round(stats$inversion_pct, 1), "%)\n")
  }
  cat("最大倒挂深度:", round(stats$spread_min, 3), "%\n")
  cat("标普500区间收益: +", round(stats$sp500_return, 1), "%\n")
  cat("当前利差水平:", round(tail(merged_df$yield_spread, 1), 3), "%\n")
}

# ============================================
# 创建图表函数
# ============================================
create_plot <- function(data, stats) {
  # 构建统计信息文本
  stats_text <- paste0(
    "<b>Statistics</b><br><br>",
    "<b>Yield Spread (3M-10Y):</b><br>",
    "  Mean: ", round(stats$spread_mean, 3), "%<br>",
    "  Std:  ", round(stats$spread_std, 3), "%<br>",
    "  Min:  ", round(stats$spread_min, 3), "%<br>",
    "  Max:  ", round(stats$spread_max, 3), "%<br>",
    "  Inversion: ", stats$inversion_days, " days (", round(stats$inversion_pct, 1), "%)\u003cbr>\u003cbr>",
    "<b>S&P 500:</b><br>",
    "  Start: ", round(stats$sp500_start, 0), "<br>",
    "  End:   ", round(stats$sp500_end, 0), "<br>",
    "  Return: ", round(stats$sp500_return, 1), "%<br>\u003cbr>",
    "<b>Current:</b><br>",
    "  Spread: ", round(tail(data$yield_spread, 1), 3), "%<br>",
    "  S&P500: ", round(tail(data$close, 1), 0)
  )
  
  # 创建图表
  fig <- plot_ly()
  
  # 添加标普500线 (左Y轴)
  fig <- fig %>% add_trace(
    data = data,
    x = ~date,
    y = ~close,
    type = 'scatter',
    mode = 'lines',
    name = 'S&P 500',
    line = list(color = '#1E88E5', width = 2.5),
    yaxis = 'y1',
    hovertemplate = paste0(
      "<b>S&P 500</b><br>",
      "日期: %{x|%Y-%m-%d}<br>",
      "收盘: %{y:.2f}<br>",
      "<extra></extra>"
    )
  )
  
  # 添加利差线 (右Y轴)
  fig <- fig %>% add_trace(
    data = data,
    x = ~date,
    y = ~yield_spread,
    type = 'scatter',
    mode = 'lines',
    name = 'Yield Spread (3M-10Y)',
    line = list(color = '#E53935', width = 2, dash = 'dash'),
    yaxis = 'y2',
    hovertemplate = paste0(
      "<b>3M-10Y Spread</b><br>",
      "日期: %{x|%Y-%m-%d}<br>",
      "利差: %{y:.3f}%<br>",
      "<extra></extra>"
    )
  )
  
  # 添加零线
  fig <- fig %>% add_trace(
    x = c(min(data$date), max(data$date)),
    y = c(0, 0),
    type = 'scatter',
    mode = 'lines',
    name = 'Zero Line',
    line = list(color = 'red', width = 1, dash = 'dot'),
    yaxis = 'y2',
    hoverinfo = 'skip',
    showlegend = TRUE
  )
  
  # 设置布局
  fig %>% layout(
    title = list(
      text = paste0(CONFIG$title, " (", min(data$date), " ~ ", max(data$date), ")"),
      font = list(size = 18, family = "Arial", color = "#333333"),
      x = 0.5
    ),
    xaxis = list(
      title = "Date",
      tickformat = "%Y-%m",
      tickangle = -45,
      showgrid = TRUE,
      gridcolor = "rgba(200,200,200,0.3)",
      rangeslider = list(visible = TRUE),
      rangeselector = list(
        buttons = list(
          list(count = 6, label = "6m", step = "month", stepmode = "backward"),
          list(count = 1, label = "1y", step = "year", stepmode = "backward"),
          list(count = 2, label = "2y", step = "year", stepmode = "backward"),
          list(count = 5, label = "5y", step = "year", stepmode = "backward"),
          list(step = "all", label = "All")
        )
      )
    ),
    yaxis = list(
      title = list(text = "S&P 500 Index", font = list(color = "#1E88E5", size = 14)),
      tickfont = list(color = "#1E88E5"),
      showgrid = TRUE,
      gridcolor = "rgba(200,200,200,0.3)",
      side = "left"
    ),
    yaxis2 = list(
      title = list(text = "Yield Spread 3M-10Y (%)", font = list(color = "#E53935", size = 14)),
      tickfont = list(color = "#E53935"),
      showgrid = FALSE,
      overlaying = "y",
      side = "right",
      zeroline = TRUE,
      zerolinecolor = "red",
      zerolinewidth = 2
    ),
    legend = list(
      x = 0.01,
      y = 0.99,
      bgcolor = "rgba(255,255,255,0.8)",
      bordercolor = "gray",
      borderwidth = 1
    ),
    hovermode = "x unified",
    plot_bgcolor = "white",
    paper_bgcolor = "white",
    margin = list(l = 80, r = 80, t = 80, b = 80),
    annotations = list(
      list(
        x = 0.02,
        y = 0.98,
        xref = "paper",
        yref = "paper",
        text = stats_text,
        showarrow = FALSE,
        font = list(size = 10, family = "Courier New, monospace"),
        bgcolor = "rgba(245,222,179,0.8)",
        bordercolor = "gray",
        borderwidth = 1,
        borderpad = 4,
        align = "left"
      )
    )
  )
}

# ============================================
# 运行主函数
# ============================================
if (!interactive()) {
  main()
}
