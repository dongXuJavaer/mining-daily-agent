# 矿权日报 Agent

基于 MCP (Model Context Protocol) 协议的矿业行业智能简报系统。

## 架构

```
┌─────────────────────────────────────────────────┐
│           LangGraph Agent (Plan-and-Execute)     │
│   用户输入 → 规划工具调用 → 并行执行 → 生成简报    │
└──────┬──────────────┬──────────────┬─────────────┘
       │ MCP          │ MCP          │ MCP
  ┌────▼────┐    ┌────▼──────┐    ┌────▼────┐
  │ News    │    │ Mineral   │    │ Price   │
  │ Server  │    │ PDF MCP   │    │ Server  │
  │(新闻聚合)│    │(PDF解析)   │    │(商品价格)│
  └─────────┘    └───────────┘    └─────────┘
```

## 技术栈

- **语言**: Python
- **MCP SDK**: `mcp` Python SDK
- **Agent 编排**: LangGraph (Plan-and-Execute)
- **LLM**: OpenAI 兼容 API
- **数据**: Mock JSON (可扩展为真实 API)

## 3 个 MCP Server

| Server | 工具 | 说明 |
|--------|------|------|
| News Server | `search_tool`, `fetch_article_tool` | 矿业新闻聚合，搜索+全文获取 |
| Mineral PDF MCP | `extract_resources_tool` | NI 43-101 PDF 解析，提取 Indicated/Inferred Resources |
| Price Server | `get_price_tool`, `get_price_trend_tool` | 商品价格查询+趋势分析 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 修改配置

编辑 `client/agent.py` 顶部的配置：

```python
OPENAI_API_KEY = "sk-你的key"
OPENAI_BASE_URL = ""                    # 代理地址, 留空则直连 OpenAI
OPENAI_MODEL = "qwen3.6-flash"         # 模型名
MCP_BASE_URL = "http://localhost"       # SSE 模式才需要改
```

### 3. 运行

```bash
# 交互模式
python -m client.agent

# 单次查询
python -m client.agent --query "给我生成一份关于 Pilbara 锂矿的今日简报"
```

详细运行指南见 [RUN.md](./RUN.md)。

## 目录结构

```
mining-daily-agent/
├── servers/
│   ├── news_server/          # MCP Server 1: 新闻聚合
│   ├── mineral_pdf_server/   # MCP Server 2: NI 43-101 PDF 解析
│   └── price_server/         # MCP Server 3: 商品价格
├── client/
│   ├── agent.py              # LangGraph Agent 主流程 + 配置
│   ├── prompts.py            # System prompt + 简报模板
│   └── mcp_client.py         # MCP client 连接管理
├── mcp-config.json           # Claude Desktop / Cursor 配置
├── docker-compose.yml
├── Dockerfile
├── RUN.md
└── requirements.txt
```
