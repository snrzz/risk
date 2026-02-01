---
name: serper-search
description: 使用 Serper API 进行 Google 搜索、学术搜索、图片搜索等
metadata: { "clawdbot": { "emoji": "🔍", "requires": { "bins": ["curl"], "env": ["SERPER_API_KEY"] }, "primaryEnv": "SERPER_API_KEY" } }
---

# Serper 搜索

使用 Serper API 进行多种类型的搜索，包括 Google 搜索、学术搜索、图片搜索、arXiv 论文搜索和 GitHub 搜索。

**官网**: https://serper.dev/

## 什么时候使用这个技能

当用户需要搜索互联网获取信息时：
- "帮我搜一下 xxx"
- "查找关于 xxx 的资料"
- "搜索 xxx 相关的论文"
- "找一些 xxx 的图片"
- "GitHub 上有没有 xxx 的项目"
- 需要获取最新的网络信息

## 支持的搜索类型

| 类型 | API 端点 | 用途 |
|------|----------|------|
| Google 搜索 | `/search` | 通用网页搜索 |
| 学术搜索 | `/scholar` | Google Scholar 学术论文搜索 |
| arXiv 论文 | `/search` + site:arxiv.org | 专门搜索 arXiv 论文 |
| GitHub 搜索 | `/search` + site:github.com | 专门搜索 GitHub 项目 |

## 如何使用

### 1. Google 通用搜索

```bash
curl -X POST "https://google.serper.dev/search" \
  -H "X-API-KEY: ${SERPER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "搜索关键词",
    "page": 1
  }'
```

### 2. Google Scholar 学术搜索

```bash
curl -X POST "https://google.serper.dev/scholar" \
  -H "X-API-KEY: ${SERPER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "论文关键词"
  }'
```

### 3. arXiv 论文搜索

```bash
curl -X POST "https://google.serper.dev/search" \
  -H "X-API-KEY: ${SERPER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "论文关键词 site:https://arxiv.org/",
    "page": 1
  }'
```

### 4. GitHub 项目搜索

```bash
curl -X POST "https://google.serper.dev/search" \
  -H "X-API-KEY: ${SERPER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "项目关键词 site:https://github.com/",
    "page": 1
  }'
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `q` | string | 是 | - | 搜索查询词 |
| `page` | int | 否 | 1 | 结果页码 |
| `tbs` | string | 否 | - | 时间过滤器 (qdr:h=1小时, qdr:d=1天, qdr:w=1周, qdr:m=1月, qdr:y=1年) |

## 返回结果说明

### 网页搜索返回 (organic)

```json
{
  "organic": [
    {
      "title": "结果标题",
      "link": "https://example.com/page",
      "snippet": "结果摘要描述..."
    }
  ],
  "credits": 1
}
```

### 学术搜索返回 (organic)

```json
{
  "organic": [
    {
      "title": "论文标题",
      "link": "https://...",
      "snippet": "论文摘要...",
      "citedBy": 100
    }
  ],
  "credits": 1
}
```

### 图片搜索返回 (images)

```json
{
  "images": [
    {
      "title": "图片标题",
      "imageUrl": "https://...",
      "link": "来源页面链接",
      "position": 1
    }
  ],
  "credits": 1
}
```

## 使用示例

**示例 1**: 用户说"帮我搜一下 Python 异步编程的资料"
1. 使用 Google 搜索 API
2. 查询词: "Python 异步编程"
3. 返回 organic 结果列表展示给用户

**示例 2**: 用户说"找一下 Transformer 相关的论文"
1. 使用 Google Scholar API
2. 查询词: "Transformer"
3. 返回学术论文列表

**示例 3**: 用户说"搜一下有没有 MCP server 的开源项目"
1. 使用 GitHub 搜索（site:github.com）
2. 查询词: "MCP server site:https://github.com/"
3. 返回 GitHub 项目列表

## 错误处理

- **401 错误**：API Key 无效，检查 SERPER_API_KEY 配置
- **空结果**：查询词可能过于宽泛或没有匹配结果，尝试调整关键词
- **429 错误**：请求频率过高，等待后重试

## 注意事项

- 搜索词会自动去除首尾引号
- 时间过滤器 tbs 仅支持特定值
- arXiv 和 GitHub 搜索是通过 site: 限定实现的
- 每页通常返回 10 条结果

