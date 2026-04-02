# 中国国债收益率数据工作流

## 概述

本工作流用于获取中国各期限国债收益率历史数据，支持两种数据源：

1. **Tushare (推荐)** - 使用 `yc_cb` 接口获取中债收益率曲线数据
2. **东方财富** - 使用 mx-macro-data Skill 获取数据

## 核心参数说明

### Tushare yc_cb 接口参数

| 参数名 | 推荐值 | 说明 |
|--------|--------|------|
| `ts_code` | `'1001.CB'` | **必须设置**。国债收益率曲线专用代码 |
| `curve_type` | `'0'` | **最常用**。`'0'`=到期收益率（标准国债收益率），`'1'`=即期收益率（零息利率） |
| `trade_date` | `'YYYYMMDD'` | 获取特定交易日的全曲线数据（如 `'20240328'`） |
| `start_date` | `'YYYYMMDD'` | 开始日期，配合 `end_date` 使用 |
| `end_date` | `'YYYYMMDD'` | 结束日期 |

### 数据期限

支持以下期限的国债收益率数据：

- 1年期 (1Y)
- 2年期 (2Y)
- 3年期 (3Y)
- 5年期 (5Y)
- 7年期 (7Y)
- 10年期 (10Y)
- 20年期 (20Y)
- 30年期 (30Y)

## 文件说明

| 文件 | 说明 |
|------|------|
| `fetch_cn_treasury_tushare.py` | **主脚本** - 使用 Tushare `yc_cb` 接口获取数据 |
| `update_cn_treasury_data.py` | 东方财富版本（备用） |
| `analyze_cn_treasury.py` | 数据分析示例脚本 |
| `cn_treasury_yields.csv` | 数据文件（自动生成） |
| `tushare_config.txt` | Tushare Token 配置文件 |
| `README.md` | 本说明文档 |

## 使用方法

### 方法一：使用 Tushare (推荐)

#### 1. 配置 Tushare Token

编辑 `tushare_config.txt` 文件，将你的 Tushare Token 粘贴进去（替换 `your_token_here`）：

```
你的_token_在这里
```

或者设置环境变量：

```bash
# Windows
set TUSHARE_TOKEN=你的_token_在这里

# Linux/Mac
export TUSHARE_TOKEN=你的_token_在这里
```

#### 2. 运行脚本

```bash
cd finance/cn_treasury_workflow
python fetch_cn_treasury_tushare.py
```

#### 特点

- 使用 `yc_cb` 接口，核心参数 `ts_code='1001.CB'` 获取国债收益率曲线
- 支持到期收益率 (`curve_type='0'`) 和即期收益率 (`curve_type='1'`)
- 单次最大2000条，自动循环提取全部历史数据
- 遵守API频率限制（每分钟2次）
- 自动合并新旧数据，避免重复

### 方法二：使用东方财富

```bash
cd finance/cn_treasury_workflow
python update_cn_treasury_data.py
```

#### 特点

- 使用自然语言查询获取数据
- 无需额外配置 Token
- 数据更新频率可能较低

## 数据格式

CSV 文件包含以下列：

| 列名 | 说明 |
|------|------|
| `date` | 日期 (YYYY-MM-DD) |
| `X1年` | 1年期国债收益率 (%) |
| `X2年` | 2年期国债收益率 (%) |
| `X3年` | 3年期国债收益率 (%) |
| `X5年` | 5年期国债收益率 (%) |
| `X7年` | 7年期国债收益率 (%) |
| `X10年` | 10年期国债收益率 (%) |
| `X20年` | 20年期国债收益率 (%) |
| `X30年` | 30年期国债收益率 (%) |

## 数据分析

运行分析脚本查看数据摘要：

```bash
python analyze_cn_treasury.py
```

分析内容包括：
- 最新各期限收益率
- 期限利差分析 (10年 - 1年)
- 收益率曲线形态判断
- 移动平均线分析
- 数据完整性统计

## 定时更新

可以设置定时任务自动更新数据：

```bash
# 使用 cron (Linux/Mac)
0 9 * * * cd /path/to/cn_treasury_workflow && python fetch_cn_treasury_tushare.py

# 使用任务计划程序 (Windows)
# 创建每天上午9点运行的任务
```

## 注意事项

1. **Tushare 积分要求**: `yc_cb` 接口需要一定的积分权限，请确保你的账号有足够的积分
2. **API 频率限制**: 每分钟最多2次调用，脚本已自动处理
3. **数据延迟**: 中债数据通常有1个工作日的延迟
4. **数据范围**: 建议每次获取不超过3年的历史数据

## 依赖安装

```bash
pip install pandas tushare
```

## 故障排除

### 问题："未找到 Tushare Token"

**解决**: 确保已正确配置 `tushare_config.txt` 文件或设置了 `TUSHARE_TOKEN` 环境变量

### 问题："权限不足或积分不够"

**解决**: 
- 检查 Tushare 账号积分是否足够
- 访问 https://tushare.pro 查看积分要求
- 考虑升级会员或完成积分任务

### 问题："获取数据失败"

**解决**:
- 检查网络连接
- 确认 Tushare 服务是否正常
- 查看错误日志获取详细信息

## 参考

- [Tushare 官网](https://tushare.pro)
- [yc_cb 接口文档](https://tushare.pro/document/2?doc_id=267)
- [中债收益率曲线](https://yield.chinabond.com.cn/cbweb-pbc-web/pbc/historyQuery?startDate=&endDate=&gjqx=0&qxId=2c9081e50a2f9606010a3068cae70001&locale=cn_ZH)
