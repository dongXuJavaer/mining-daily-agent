"""LangGraph Agent — 矿权日报 Agent 主流程。

采用 Plan-and-Execute 模式:
1. plan: LLM 分析用户意图，决定调用哪些工具
2. execute: 并行调用 MCP tools
3. generate: LLM 整合数据，生成 Markdown 简报
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Annotated, Any, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END

from client.mcp_client import MCPClientManager, create_client
from client.prompts import SYSTEM_PROMPT


# ── 配置 (直接在这里修改) ───────────────────────────────────

OPENAI_API_KEY = "sk-b1833533e8f24261b459dd1fda679bfe"
OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 代理地址, 如 "https://api.openai-proxy.com/v1"
OPENAI_MODEL = "qwen3.6-flash"
MCP_BASE_URL = "http://localhost"  # SSE 模式下的 MCP Server 地址


# ── LLM 工厂 ────────────────────────────────────────────────

def _create_llm(temperature: float = 0) -> ChatOpenAI:
    """创建 ChatOpenAI 实例。"""
    kwargs: dict[str, Any] = {
        "model": OPENAI_MODEL,
        "temperature": temperature,
        "api_key": OPENAI_API_KEY,
    }
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL

    return ChatOpenAI(**kwargs)


# ── State 定义 ──────────────────────────────────────────────

class AgentState(TypedDict):
    """Agent 状态。"""
    user_query: str
    tools_schema: list[dict]  # OpenAI function calling 格式的工具列表
    tool_calls: list[dict]  # plan 阶段输出的工具调用计划
    tool_results: dict[str, str]  # execute 阶段收集的工具结果
    report: str  # generate 阶段输出的简报
    mcp_manager: MCPClientManager  # MCP 连接管理器


# ── Plan 节点 ────────────────────────────────────────────────

async def plan_tools(state: AgentState) -> dict:
    """分析用户意图，决定需要调用哪些 MCP 工具。"""
    llm = _create_llm(temperature=0)

    # 构造工具描述给 LLM
    tools_desc = []
    for t in state["tools_schema"]:
        params = t.get("parameters", {})
        param_desc = ""
        if "properties" in params:
            parts = []
            for pname, pinfo in params["properties"].items():
                ptype = pinfo.get("type", "string")
                pdesc = pinfo.get("description", "")
                parts.append(f"    - {pname} ({ptype}): {pdesc}")
            param_desc = "\n".join(parts)
        tools_desc.append(f"- {t['name']}: {t['description']}\n  参数:\n{param_desc}")

    tools_text = "\n".join(tools_desc)

    plan_prompt = f"""你是一个工具调用规划器。根据用户的查询，决定需要调用哪些工具。

## 可用工具

{tools_text}

## 用户查询

{state['user_query']}

## 要求

输出一个 JSON 数组，每个元素是一次工具调用，格式:
[
  {{"tool": "工具名", "args": {{"参数名": "参数值"}}}},
  ...
]

只输出 JSON，不要其他文字。确保调用足够覆盖用户需求的所有维度。"""

    response = await llm.ainvoke([HumanMessage(content=plan_prompt)])
    content = response.content.strip()

    # 解析 JSON（处理可能的 markdown code block）
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1])

    try:
        tool_calls = json.loads(content)
    except json.JSONDecodeError:
        tool_calls = []

    return {"tool_calls": tool_calls}


# ── Execute 节点 ─────────────────────────────────────────────

async def execute_tools(state: AgentState) -> dict:
    """并行调用所有计划的 MCP 工具。"""
    manager: MCPClientManager = state["mcp_manager"]
    tool_calls = state["tool_calls"]

    if not tool_calls:
        return {"tool_results": {"error": "没有规划任何工具调用"}}

    # 并行调用所有工具
    async def call_one(tc: dict) -> tuple[str, str]:
        tool_name = tc["tool"]
        args = tc.get("args", {})
        try:
            result = await manager.call_tool(tool_name, args)
            return tool_name, result
        except Exception as e:
            return tool_name, f"工具调用失败: {e}"

    tasks = [call_one(tc) for tc in tool_calls]
    results = await asyncio.gather(*tasks)

    tool_results = {}
    for tool_name, result in results:
        # 如果同一个工具被调用多次，合并结果
        if tool_name in tool_results:
            tool_results[tool_name] += "\n---\n" + result
        else:
            tool_results[tool_name] = result

    return {"tool_results": tool_results}


# ── Generate 节点 ────────────────────────────────────────────

async def generate_report(state: AgentState) -> dict:
    """整合所有工具结果，生成 Markdown 简报。"""
    llm = _create_llm(temperature=0.3)

    # 构造工具结果摘要
    results_text = ""
    for tool_name, result in state["tool_results"].items():
        results_text += f"\n### 工具: {tool_name}\n```\n{result[:5000]}\n```\n"

    gen_prompt = f"""你是矿权日报生成器。根据以下工具查询结果，生成一份专业的 Markdown 简报。

## 用户查询
{state['user_query']}

## 工具查询结果
{results_text}

## 简报格式要求

生成一份完整的 Markdown 简报，包含:
1. 标题: # 矿权日报 — {{主题}} — {{日期}}
2. ## 📰 新闻摘要 — 每条新闻一行: - [标题](url) — 来源, 日期 + 摘要
3. ## 📊 储量数据 — 表格形式展示储量信息
4. ## 📈 价格走势 — 当前价格、涨跌幅、趋势分析
5. ## ⚠️ 风险提示 — 基于数据的风险分析要点
6. ## 📎 引用源 — 编号列出所有数据来源

使用中文。如果某个维度没有数据，跳该章节。今天是 {datetime.now().strftime('%Y-%m-%d')}。"""

    response = await llm.ainvoke([HumanMessage(content=gen_prompt)])
    return {"report": response.content}


# ── Graph 构建 ────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """构建 LangGraph Plan-and-Execute 图。"""
    graph = StateGraph(AgentState)

    graph.add_node("plan", plan_tools)
    graph.add_node("execute", execute_tools)
    graph.add_node("generate", generate_report)

    graph.add_edge("plan", "execute")
    graph.add_edge("execute", "generate")
    graph.add_edge("generate", END)

    graph.set_entry_point("plan")
    return graph


# ── 主入口 ────────────────────────────────────────────────────

async def run_agent(user_query: str, transport: str = "stdio") -> str:
    """运行 Agent，返回生成的简报。

    Args:
        user_query: 用户查询
        transport: "stdio" 或 "sse"

    Returns:
        Markdown 简报
    """
    # 连接 MCP Servers
    manager = await create_client(transport=transport, base_url=MCP_BASE_URL)

    try:
        # 获取工具列表
        tools = await manager.list_all_tools()

        # 构建并运行 Graph
        graph = build_graph()
        app = graph.compile()

        initial_state: AgentState = {
            "user_query": user_query,
            "tools_schema": tools,
            "tool_calls": [],
            "tool_results": {},
            "report": "",
            "mcp_manager": manager,
        }

        final_state = await app.ainvoke(initial_state)
        return final_state["report"]

    finally:
        await manager.close()


async def interactive_mode(transport: str = "stdio"):
    """交互模式，支持多轮对话。"""
    manager = await create_client(transport=transport, base_url=MCP_BASE_URL)

    try:
        tools = await manager.list_all_tools()
        graph = build_graph()
        app = graph.compile()

        print("=" * 60)
        print("  矿权日报 Agent — 输入查询获取矿业简报")
        print("  输入 'quit' 或 'exit' 退出")
        print("=" * 60)
        print()

        while True:
            try:
                query = input("请输入查询: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not query or query.lower() in ("quit", "exit", "q"):
                break

            print("\n正在生成简报...\n")

            initial_state: AgentState = {
                "user_query": query,
                "tools_schema": tools,
                "tool_calls": [],
                "tool_results": {},
                "report": "",
                "mcp_manager": manager,
            }

            final_state = await app.ainvoke(initial_state)
            print(final_state["report"])
            print("\n" + "=" * 60 + "\n")

    finally:
        await manager.close()


def main():
    """CLI 入口。"""
    print(f"  Model: {OPENAI_MODEL}")
    print(f"  Base URL: {OPENAI_BASE_URL or '(default)'}")

    transport = "stdio"
    args = sys.argv[1:]

    # 解析 --transport 参数
    for i, arg in enumerate(args):
        if arg == "--transport" and i + 1 < len(args):
            transport = args[i + 1]

    # 如果有 --query 参数，单次运行
    query = None
    for i, arg in enumerate(args):
        if arg == "--query" and i + 1 < len(args):
            query = args[i + 1]

    if query:
        report = asyncio.run(run_agent(query, transport))
        print(report)
    else:
        asyncio.run(interactive_mode(transport))


if __name__ == "__main__":
    main()
