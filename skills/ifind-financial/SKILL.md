---
name: ifind-financial
description: 查询同花顺iFind财务报表数据
metadata: { "clawdbot": { "emoji": "📊", "requires": { "bins": ["curl"], "env": ["QVERIS_API_KEY"] }, "primaryEnv": "QVERIS_API_KEY" } }
---

# iFind 财务报表查询

查询同花顺 iFind 的财务报表数据，支持资产负债表、利润表、现金流量表。

## 什么时候使用这个技能

当用户询问以下类似问题时，使用此技能：
- "查一下茅台的资产负债表"
- "腾讯2024年的利润表"
- "某公司的现金流量表"
- "查询财务数据"
- 需要分析公司的财务状况

## 如何使用

使用 Qveris iFind Financial API 查询财报：

```bash
curl -X POST "https://qveris.ai/api/v1/tools/execute?tool_id=ths_ifind.financial_statements.v1" \
  -H "Authorization: Bearer ${QVERIS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "statement_type": "balance",
      "codes": "600519.SH",
      "year": "2024",
      "period": "1231",
      "type": "1"
    },
    "max_response_size": 20480
  }'
```

### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `statement_type` | string | 是 | - | 报表类型（见下表） |
| `codes` | string | 是 | - | 证券代码，多个用逗号分隔，如 "600519.SH,000001.SZ" |
| `year` | string | 是 | - | 年份，如 "2024" |
| `period` | string | 是 | - | 报告期（见下表） |
| `type` | string | 是 | - | 报表类别（见下表） |
| `max_response_size` | int | 否 | 20480 | 最大响应字节数 |

### statement_type 报表类型

| 值 | 说明 |
|----|------|
| `balance` | 资产负债表 |
| `income` | 利润表 |
| `cash_flow` | 现金流量表 |

### period 报告期

| 值 | 说明 |
|----|------|
| `0331` | 一季报（Q1） |
| `0630` | 半年报（H1） |
| `0930` | 三季报（Q3） |
| `1231` | 年报（Annual） |

### type 报表类别

| 值 | 说明 |
|----|------|
| `1` | 合并报表 |
| `2` | 母公司报表 |
| `3` | 合并调整报表 |
| `4` | 母公司调整报表 |

## 返回结果说明

API 返回的 JSON 包含财务数据列表，每条记录包含：
- 科目名称（如"总资产"、"净利润"等）
- 科目值
- 比较期数据等

## 使用示例

用户说："查一下茅台2024年年报的利润表"

你应该：
1. 设置 statement_type="income"
2. 设置 codes="600519.SH"
3. 设置 year="2024"
4. 设置 period="1231"（年报）
5. 设置 type="1"（合并报表）
6. 调用 API 获取结果
7. 以表格形式展示关键财务指标（营收、净利润、毛利率等）

## 常见分析场景

1. **盈利能力分析**：查利润表，关注营收、净利润、毛利率
2. **偿债能力分析**：查资产负债表，关注资产负债率、流动比率
3. **现金流分析**：查现金流量表，关注经营现金流、自由现金流
4. **同比分析**：查询多个期间的数据进行对比

## 错误处理

- **401 错误**：API Key 无效
- **空结果**：可能是报告期尚未披露，或证券代码错误
- **参数错误**：检查 statement_type、period、type 的值是否正确

## 注意事项

- 支持同时查询多只股票（codes 用逗号分隔）
- 财报数据通常有披露延迟，最新数据可能尚未更新
- 每次查询消耗 5 credits
- 建议使用合并报表（type=1）进行分析

