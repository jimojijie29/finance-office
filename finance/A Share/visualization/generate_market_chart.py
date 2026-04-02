import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv('finance/tushare/market_combined_data.csv')
df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
df = df.sort_values('trade_date')

# 最近30天数据
df_recent = df.tail(30).copy()

# 创建图表
fig, axes = plt.subplots(3, 1, figsize=(14, 12))
fig.suptitle('A股市场数据可视化 - 凯的偏好视图', fontsize=16, fontweight='bold')

# ===== 图1: 指数走势与融资融券余额 =====
ax1 = axes[0]
ax1_twin = ax1.twinx()

# 指数走势
ax1.plot(df_recent['trade_date'], df_recent['sh_close'], 'b-', linewidth=2, label='上证指数', marker='o', markersize=4)
ax1.plot(df_recent['trade_date'], df_recent['sz_close']/3.5, 'g-', linewidth=2, label='深证成指(缩放)', marker='s', markersize=4)

# 融资融券余额（右轴）
ax1_twin.plot(df_recent['trade_date'], df_recent['total_margin_balance'], 'r--', linewidth=2, label='融资余额(亿)', alpha=0.8)

ax1.set_ylabel('指数点位', fontsize=11)
ax1_twin.set_ylabel('融资余额(亿元)', fontsize=11, color='red')
ax1_twin.tick_params(axis='y', labelcolor='red')
ax1.set_title('指数走势 vs 融资融券余额', fontsize=13, fontweight='bold')
ax1.legend(loc='upper left')
ax1_twin.legend(loc='upper right')
ax1.grid(True, alpha=0.3)

# ===== 图2: 成交额与融资买入额 =====
ax2 = axes[1]
ax2_twin = ax2.twinx()

# 成交额柱状图
colors = ['green' if x > 0 else 'red' for x in df_recent['total_turnover'].diff().fillna(0)]
ax2.bar(df_recent['trade_date'], df_recent['total_turnover'], color=colors, alpha=0.6, label='两市成交额(亿)')

# 融资买入额（右轴）- 需要计算
margin_df = pd.read_csv('finance/tushare/margin_trading_sse_szse.csv')
margin_df['trade_date'] = pd.to_datetime(margin_df['trade_date'], format='%Y%m%d')
margin_daily = margin_df.groupby('trade_date')['rzmre'].sum() / 1e8  # 转换为亿元
margin_daily = margin_daily.reindex(df_recent['trade_date']).fillna(0)

ax2_twin.plot(df_recent['trade_date'], margin_daily, 'orange', linewidth=2, label='融资买入额(亿)', marker='D', markersize=4)

ax2.set_ylabel('成交额(亿元)', fontsize=11)
ax2_twin.set_ylabel('融资买入额(亿元)', fontsize=11, color='orange')
ax2_twin.tick_params(axis='y', labelcolor='orange')
ax2.set_title('两市成交额 vs 融资买入额', fontsize=13, fontweight='bold')
ax2.legend(loc='upper left')
ax2_twin.legend(loc='upper right')
ax2.grid(True, alpha=0.3)

# ===== 图3: 融资余额变化率（市场情绪指标） =====
ax3 = axes[2]

# 计算融资余额变化率
df_recent['margin_change_pct'] = df_recent['total_margin_balance'].pct_change() * 100

# 绘制变化率柱状图
colors_margin = ['red' if x > 0 else 'green' for x in df_recent['margin_change_pct'].fillna(0)]
ax3.bar(df_recent['trade_date'], df_recent['margin_change_pct'], color=colors_margin, alpha=0.7)

# 添加零线
ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.8)

# 标注关键数值
for i, (date, val) in enumerate(zip(df_recent['trade_date'], df_recent['margin_change_pct'])):
    if not pd.isna(val) and abs(val) > 0.3:
        ax3.annotate(f'{val:.2f}%', xy=(date, val), xytext=(0, 5 if val > 0 else -15), 
                     textcoords='offset points', fontsize=8, ha='center')

ax3.set_ylabel('融资余额变化率(%)', fontsize=11)
ax3.set_title('融资余额日变化率 - 市场情绪指标', fontsize=13, fontweight='bold')
ax3.grid(True, alpha=0.3)

# 格式化x轴日期
for ax in axes:
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

plt.tight_layout()
plt.savefig('finance/visualization/market_overview.png', dpi=150, bbox_inches='tight')
print("图表已保存: finance/visualization/market_overview.png")

# ===== 打印关键数据摘要 =====
print("\n" + "="*60)
print("A股市场数据摘要 (最近5个交易日)")
print("="*60)
latest = df.tail(5)
for _, row in latest.iterrows():
    date_str = row['trade_date'].strftime('%Y-%m-%d')
    sh_change = (row['sh_close'] / df.iloc[_-1]['sh_close'] - 1) * 100 if _ > 0 else 0
    print(f"{date_str} | 上证: {row['sh_close']:.2f} ({sh_change:+.2f}%) | "
          f"成交额: {row['total_turnover']:.0f}亿 | 融资余额: {row['total_margin_balance']:.0f}亿")

print("\n融资余额趋势:")
margin_5d = df['total_margin_balance'].tail(5)
margin_20d = df['total_margin_balance'].tail(20)
print(f"  5日变化: {((margin_5d.iloc[-1]/margin_5d.iloc[0])-1)*100:+.2f}%")
print(f"  20日变化: {((margin_20d.iloc[-1]/margin_20d.iloc[0])-1)*100:+.2f}%")
