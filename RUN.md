# 矿权日报 Agent — 运行指南

## 配置

运行前，先在 `client/agent.py` 顶部修改配置：

```python
# ── 配置 (直接在这里修改) ───────────────────────────────────

OPENAI_API_KEY = "sk-你的key"          # API Key
OPENAI_BASE_URL = ""                    # 代理地址, 如 "https://api.openai-proxy.com/v1"
OPENAI_MODEL = "qwen3.6-flash"         # 模型名
MCP_BASE_URL = "http://localhost"       # SSE 模式下的 MCP Server 地址
```

- **OPENAI_API_KEY**: 必填，你的 API Key
- **OPENAI_BASE_URL**: 如果用代理服务就填代理地址，直连 OpenAI 留空
- **OPENAI_MODEL**: 模型名称，根据你的代理支持的模型填写
- **MCP_BASE_URL**: Docker SSE 模式才需要改，本地运行不用动

---

## 方式一：本地运行 (stdio, 推荐)

### 1. 安装依赖

```bash
cd mining-daily-agent
pip install -r requirements.txt
```

### 2. 修改配置

编辑 `client/agent.py` 顶部的 4 个变量。

### 3. 运行 Agent

```bash
# 交互模式 (推荐)
python -m client.agent

# 单次查询模式
python -m client.agent --query "给我生成一份关于 Pilbara 锂矿的今日简报"
```

Agent 会自动启动 3 个 MCP Server 子进程，通过 stdio 通信。

### 4. 测试 MCP Server (可选)

单独测试某个 Server:

```bash
python -m servers.news_server.server
python -m servers.mineral_pdf_server.server
python -m servers.price_server.server
```

---

## 方式二：Docker Compose (SSE)

### 1. 修改配置

编辑 `client/agent.py` 顶部的 4 个变量，将 `MCP_BASE_URL` 改为 `http://news-server` 等容器名。

### 2. 启动所有服务

```bash
docker-compose up --build
```

这会启动:
- `news-server` (端口 8001) — 新闻聚合
- `mineral-pdf-server` (端口 8002) — NI 43-101 PDF 解析
- `price-server` (端口 8003) — 商品价格
- `agent` (交互模式)

### 3. 停止服务

```bash
docker-compose down
```

---

## 接入 Claude Desktop / Cursor

将 `mcp-config.json` 的内容添加到 Claude Desktop 或 Cursor 的 MCP 配置中:

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "news": {
      "command": "python",
      "args": ["-m", "servers.news_server.server"],
      "cwd": "/path/to/mining-daily-agent"
    },
    "mineral-pdf": {
      "command": "python",
      "args": ["-m", "servers.mineral_pdf_server.server"],
      "cwd": "/path/to/mining-daily-agent"
    },
    "price": {
      "command": "python",
      "args": ["-m", "servers.price_server.server"],
      "cwd": "/path/to/mining-daily-agent"
    }
  }
}
```

---

## 示例查询

- "给我生成一份关于 Pilbara 锂矿的今日简报"
- "近7天澳洲锂出口政策有何变化?"
- "Barrick Gold 的铜矿储量情况如何?"
- "铜价最近一个月走势怎样?"
- "对比一下锂和镍的价格趋势"
- "解析 Newmont 的 NI 43-101 报告中的储量数据"
