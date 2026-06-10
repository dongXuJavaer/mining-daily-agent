# CLAUDE.md — 矿业日报 Agent

## 项目概述

矿业日报 Agent（mining-daily-agent），基于 **MCP + LangGraph Plan-and-Execute** 架构，自动整合矿业新闻、储量数据、价格行情，生成结构化日报。

## 技术栈

- **语言**: Python 3.12+
- **Agent 框架**: LangGraph (Plan-and-Execute) + LangChain ChatOpenAI
- **MCP SDK**: `mcp` (FastMCP 服务端 / ClientSession 客户端)
- **LLM**: OpenAI 兼容 API（默认 DashScope / Qwen3.6-flash）

## 项目结构

```
mining-daily-agent/
├── client/
│   ├── agent.py           # 入口：LangGraph agent，plan → execute → generate
│   ├── mcp_client.py      # MCP 客户端管理器（stdio / SSE 双模式）
│   └── prompts.py         # 系统提示词和报告模板
├── servers/
│   ├── news_server/       # 新闻服务器 (port 8001)
│   ├── mineral_pdf_server/ # 矿产 PDF 服务器 (port 8002)
│   └── price_server/      # 价格服务器 (port 8003)
├── tests/                 # 测试目录（暂无测试）
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── mcp-config.json        # Claude Desktop / Cursor MCP 配置
```

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 本地运行（stdio 模式，推荐）
python -m client.agent
python -m client.agent --query "查询铜价和相关新闻"

# 单独启动 MCP 服务器（测试用）
python -m servers.news_server.server
python -m servers.mineral_pdf_server.server
python -m servers.price_server.server

# Docker Compose（SSE 模式）
docker-compose up --build
```

## MCP 工具清单

| 服务器 | 工具 | 功能 |
|--------|------|------|
| News Server | `search_news_tool` | 搜索矿业新闻 |
| News Server | `get_policy_updates_tool` | 获取政策法规更新 |
| Reserve Server | `query_reserves_tool` | 查询矿企储量数据 |
| Reserve Server | `get_company_resources_tool` | 获取公司全部资源概况 |
| Price Server | `get_price_tool` | 获取最新价格 |
| Price Server | `get_price_trend_tool` | 获取价格趋势 |

## 架构流程

```
用户查询 → plan_tools (LLM 规划工具调用)
         → execute_tools (并行执行 MCP 工具)
         → generate_report (LLM 生成 Markdown 日报)
```

## 编码规范

- 所有代码注释、docstring、提示词使用**中文**
- MCP 工具遵循 `tools.py`（业务逻辑）+ `server.py`（`@mcp.tool()` 注册）分离模式
- 工具命名约定：`<function_name>_tool` 为 MCP 注册名

## 注意事项

- 当前数据为 mock JSON（`servers/*/data/`），可替换为真实 API
- 配置硬编码在 `client/agent.py` 顶部，生产环境应迁移至环境变量
- 测试目录为空，新增功能请同步编写测试
