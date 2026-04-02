#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Tushare数据结构
"""

import pandas as pd
import tushare as ts
import os

os.environ['PYTHONIOENCODING'] = 'utf-8'

token = os.environ.get('TUSHARE_TOKEN')
pro = ts.pro_api(token)

# 获取2023年1月的数据
df = pro.yc_cb(
    ts_code='1001.CB',
    curve_type='0',
    start_date='20230101',
    end_date='20230131',
    limit=2000
)

print(f"总记录数: {len(df)}")
print("\n列名:")
print(df.columns.tolist())
print("\n前10条数据:")
print(df.head(10))
print("\n日期唯一值数量:")
print(f"trade_date唯一值: {df['trade_date'].nunique()}")
print("\n期限唯一值:")
print(df['curve_term'].unique())
print("\n按日期分组统计:")
print(df.groupby('trade_date').size())
