---
name: ifind-quotation
description: 查询同花顺iFind股票行情数据
metadata: { "clawdbot": { "emoji": "📈", "requires": { "bins": ["curl"], "env": ["QVERIS_API_KEY"] }, "primaryEnv": "QVERIS_API_KEY" } }
---

# iFind 股票行情查询

查询同花顺 iFind 的历史行情数据，包括 K 线、成交量等指标。

## 什么时候使用这个技能

当用户询问以下类似问题时，使用此技能：
- "茅台最近一个月的股价走势"
- "查一下某股票的历史行情"
- "获取 K 线数据"
- "某股票的周线/月线数据"
- 需要分析股价走势、技术指标

## 如何使用

使用 Qveris iFind Quotation API 查询行情：

```bash
curl -X POST "https://qveris.ai/api/v1/tools/execute?tool_id=ths_ifind.quotation.v1" \
  -H "Authorization: Bearer ${QVERIS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "codes": "600519.SH",
      "startdate": "2024-01-01",
      "enddate": "2024-12-31",
      "indicators": "all",
      "interval": "D",
      "cps": "1",
      "fill": "Previous"
    },
    "max_response_size": 20480
  }'
```

### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `codes` | string | 是 | - | 证券代码，多个用逗号分隔 |
| `startdate` | string | 是 | - | 开始日期（支持 YYYY-MM-DD、YYYY/MM/DD、YYYYMMDD） |
| `enddate` | string | 是 | - | 结束日期（同上） |
| `indicators` | string | 否 | 'all' | 指标列表（见下方说明） |
| `interval` | string | 否 | 'D' | 时间周期（见下表） |
| `cps` | string | 否 | '1' | 复权方式（见下表） |
| `fill` | string | 否 | 'Previous' | 非交易日处理（见下表） |
| `max_response_size` | int | 否 | 20480 | 最大响应字节数 |

### interval 时间周期

| 值 | 说明 |
|----|------|
| `D` | 日线（默认） |
| `W` | 周线 |
| `M` | 月线 |
| `Q` | 季线 |
| `S` | 半年线 |
| `Y` | 年线 |

### cps 复权方式

| 值 | 说明 |
|----|------|
| `1` | 不复权（默认） |
| `2` | 前复权 |
| `3` | 后复权 |
| `6` | 前复权（现金分红） |
| `7` | 后复权（现金分红） |

### fill 非交易日处理

| 值 | 说明 |
|----|------|
| `Previous` | 使用前一交易日数据（默认） |
| `Blank` | 留空 |

### indicators 指标

| 值 | 说明 |
|----|------|
| `all` | 全部指标（默认） |
| `common` | 常用指标（开高低收、成交量等） |
| 自定义 | 逗号分隔的指标列表 |

## 返回结果说明

API 返回的 JSON 包含行情数据列表，每条记录包含：
- `date`: 交易日期
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量
- `amount`: 成交额
- 其他技术指标...

## 使用示例

用户说："帮我查一下茅台最近3个月的周线数据"

你应该：
1. 设置 codes="600519.SH"
2. 计算日期范围（最近3个月）
3. 设置 interval="W"（周线）
4. 调用 API 获取结果
5. 以表格形式展示周线数据（日期、开高低收、成交量）

## 常见分析场景

1. **趋势分析**：使用日线/周线数据判断涨跌趋势
2. **回测研究**：获取历史数据进行策略回测
3. **比较分析**：同时查询多只股票进行对比
4. **技术分析**：配合技术指标分析买卖点

## 复权说明

- **不复权**：原始价格，适合查看实际成交价
- **前复权**：以最新价格为基准向前调整，适合技术分析
- **后复权**：以上市价格为基准向后调整，适合计算真实收益率

## 错误处理

- **401 错误**：API Key 无效
- **空结果**：可能是日期范围内无交易数据
- **参数错误**：检查日期格式和参数值是否正确

## 注意事项

- 支持同时查询多只股票
- 日期范围过长可能返回大量数据，注意 max_response_size
- 每次查询消耗 5 credits
- 非交易日（周末、节假日）默认用前值填充
- 建议技术分析使用前复权数据（cps=2）

