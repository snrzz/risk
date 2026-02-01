---
name: ifind-report
description: 搜索同花顺iFind研报和公告
metadata: { "clawdbot": { "emoji": "📄", "requires": { "bins": ["curl"], "env": ["QVERIS_API_KEY"] }, "primaryEnv": "QVERIS_API_KEY" } }
---

# iFind 研报公告搜索

搜索同花顺 iFind 的研报和公告数据。支持按证券代码、日期范围和关键词筛选。

## 什么时候使用这个技能

当用户询问以下类似问题时，使用此技能：
- "帮我查一下茅台最近的研报"
- "查询某公司的年报公告"
- "搜索关于某股票的分析报告"
- "最近有什么重大公告？"
- 需要获取上市公司的公告、研报、财报发布信息

## 如何使用

使用 Qveris iFind Report API 搜索研报公告：

```bash
curl -X POST "https://qveris.ai/api/v1/tools/execute?tool_id=ths_ifind.report_query.v1" \
  -H "Authorization: Bearer ${QVERIS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "codes": "600519.SH",
      "keyword": "",
      "beginrDate": "2024-01-01",
      "endrDate": "2024-12-31"
    },
    "max_response_size": 20480
  }'
```

### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `codes` | string | 是 | - | 证券代码，如 "600519.SH"（茅台）、"920000.BJ"。不能为空 |
| `keyword` | string | 否 | '' | 公告关键词，用于搜索公告标题 |
| `beginrDate` | string | 是 | - | 开始日期，格式 "YYYY-MM-DD" |
| `endrDate` | string | 是 | - | 结束日期，格式 "YYYY-MM-DD" |
| `max_response_size` | int | 否 | 20480 | 最大响应字节数，-1 表示不限制 |

## 常用证券代码格式

| 市场 | 格式 | 示例 |
|------|------|------|
| 上海 A 股 | XXXXXX.SH | 600519.SH（茅台） |
| 深圳 A 股 | XXXXXX.SZ | 000001.SZ（平安银行） |
| 创业板 | XXXXXX.SZ | 300750.SZ（宁德时代） |
| 科创板 | XXXXXX.SH | 688981.SH（中芯国际） |
| 北交所 | XXXXXX.BJ | 920000.BJ |

## 返回结果说明

API 返回的 JSON 包含研报/公告列表，每条记录包含：
- 公告日期
- 公告标题
- 公告类型（年报、季报、公告等）
- 证券代码
- 公告链接等

## 使用示例

用户说："帮我查一下贵州茅台2024年的年报"

你应该：
1. 使用 codes="600519.SH"（茅台的代码）
2. 使用 keyword="年报" 过滤
3. 设置合适的日期范围（如 2024-01-01 到 2024-12-31）
4. 调用 API 获取结果
5. 向用户展示年报列表，包括发布日期和标题

## 错误处理

- **401 错误**：API Key 无效
- **空结果**：可能是日期范围内没有公告，或证券代码错误
- **证券代码错误**：检查代码格式是否正确（如 .SH/.SZ/.BJ 后缀）

## 注意事项

- codes 参数不能为空
- 日期格式必须是 "YYYY-MM-DD"
- 关键词搜索针对公告标题
- 每次查询消耗 5 credits
- 建议日期范围不要太长，以免返回数据过多

