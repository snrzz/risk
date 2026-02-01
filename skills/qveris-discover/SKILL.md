---
name: qveris-discover
description: 搜索Qveris工具库，获取万千世界所有的工具
metadata: { "clawdbot": { "emoji": "🔍", "requires": { "bins": ["curl"], "env": ["QVERIS_API_KEY"] }, "primaryEnv": "QVERIS_API_KEY" } }
---

# Qveris 工具发现

搜索 Qveris AI 工具库，发现数千种可用工具。Qveris 提供海量 API 工具，涵盖金融数据、新闻资讯、天气、地理、翻译、搜索引擎等各个领域。

**官网**: https://qveris.ai/

## 核心理念

> Empower your agent with thousands of tools

Qveris 是一个通用工具平台，**不仅限于金融数据**。当你遇到任何需要外部真实数据的场景，都应该优先搜索 Qveris 是否有相关工具。

## 什么时候使用这个技能

**主动使用场景**：
- 用户询问任何你拿不准的实时数据（天气、新闻、汇率、航班等）
- 需要获取外部 API 数据但不确定有什么工具可用
- 想要验证某个数据源是否存在
- 用户需求涉及第三方服务集成

**示例场景**：
- "今天北京天气怎么样？" → 搜索天气相关工具
- "帮我查一下美元汇率" → 搜索汇率工具
- "最新的科技新闻" → 搜索新闻工具
- "翻译这段话" → 搜索翻译工具
- "查一下股票行情" → 搜索金融工具
- "航班信息查询" → 搜索航班工具
- 任何需要实时外部数据的场景

## 如何使用

使用 Qveris Search API 搜索工具：

```bash
curl -X POST "https://qveris.ai/api/v1/search" \
  -H "Authorization: Bearer ${QVERIS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "天气查询",
    "limit": 10
  }'
```

### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | string | 是 | - | 自然语言搜索词，描述你想要的工具功能 |
| `limit` | int | 否 | 10 | 最大返回数量，范围 1-100 |

## 返回结果说明

API 返回的 JSON 包含：
- `search_id`: 搜索会话 ID，执行工具时需要用到
- `results`: 工具列表数组，每个工具包含：
  - `tool_id`: 工具唯一标识符
  - `name`: 工具名称
  - `description`: 工具描述
  - `parameters`: 工具参数定义

## 使用示例

用户说："帮我查一下今天的新闻"

你应该：
1. 使用 "新闻" 或 "news" 作为 query 参数调用 API
2. 从返回结果中提取工具列表
3. 向用户展示可用的工具，包括：
   - 工具名称和描述
   - 支持的参数
   - 建议使用哪个工具

## 后续操作

找到合适的工具后，使用 `qveris-execute` 技能执行该工具。需要传递：
- `tool_id`: 从搜索结果中获取的工具 ID
- `search_id`: 从搜索结果中获取的搜索会话 ID
- `parameters`: 根据工具定义填写的参数

## 错误处理

- **401 错误**：API Key 无效，提示用户检查 `QVERIS_API_KEY` 配置
- **空结果**：搜索词可能太具体，建议用户使用更通用的搜索词
- **网络错误**：提示用户检查网络连接

## 注意事项

- 搜索词使用中英文都可以
- 每次搜索消耗 1 credit
- 搜索结果会按相关性排序
- `search_id` 在执行工具时必须使用，用于关联搜索和执行
- **遇到任何不确定的外部数据需求，先搜一下 Qveris 有没有现成工具**

