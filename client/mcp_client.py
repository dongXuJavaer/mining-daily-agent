"""MCP Client — 连接管理器，负责连接所有 MCP Server 并统一调用工具。"""

import asyncio
import json
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client


class MCPClientManager:
    """管理多个 MCP Server 连接，提供统一的工具发现和调用接口。"""

    def __init__(self):
        self.sessions: dict[str, ClientSession] = {}
        self._exit_stack = AsyncExitStack()
        self._connections: list[Any] = []  # 保持对连接上下文的引用

    async def connect_stdio(self, name: str, command: str, args: list[str]) -> None:
        """通过 stdio 连接一个 MCP Server。"""
        server_params = StdioServerParameters(command=command, args=args)
        read_stream, write_stream = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()
        self.sessions[name] = session
        print(f"  [OK] Connected to {name} server via stdio")

    async def connect_sse(self, name: str, url: str) -> None:
        """通过 SSE 连接一个 MCP Server。"""
        read_stream, write_stream = await self._exit_stack.enter_async_context(
            sse_client(url)
        )
        session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()
        self.sessions[name] = session
        print(f"  [OK] Connected to {name} server via SSE ({url})")

    async def list_all_tools(self) -> list[dict]:
        """获取所有已连接 Server 的工具列表，转换为 OpenAI function calling 格式。"""
        all_tools = []
        for name, session in self.sessions.items():
            result = await session.list_tools()
            for tool in result.tools:
                all_tools.append({
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema if tool.inputSchema else {"type": "object", "properties": {}},
                    "_server": name,  # 内部标记，用于路由
                })
        return all_tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """调用指定工具，自动路由到正确的 Server。"""
        for name, session in self.sessions.items():
            result = await session.list_tools()
            for tool in result.tools:
                if tool.name == tool_name:
                    call_result = await session.call_tool(tool_name, arguments)
                    # 提取文本内容
                    if call_result.content:
                        texts = []
                        for block in call_result.content:
                            if hasattr(block, "text"):
                                texts.append(block.text)
                        return "\n".join(texts)
                    return "工具调用无返回内容。"
        return f"未找到工具: {tool_name}"

    async def close(self) -> None:
        """关闭所有连接。"""
        await self._exit_stack.aclose()


async def create_client(transport: str = "stdio", base_url: str = "http://localhost") -> MCPClientManager:
    """创建并连接所有 MCP Server。

    Args:
        transport: "stdio" (本地) 或 "sse" (Docker)
        base_url: SSE 模式下的基础 URL

    Returns:
        已连接所有 Server 的 MCPClientManager
    """
    manager = MCPClientManager()

    print("正在连接 MCP Servers...")

    if transport == "stdio":
        # 通过子进程启动 Server
        import sys
        python = sys.executable

        await manager.connect_stdio("news", python, ["-m", "servers.news_server.server"])
        await manager.connect_stdio("mineral_pdf", python, ["-m", "servers.mineral_pdf_server.server"])
        await manager.connect_stdio("price", python, ["-m", "servers.price_server.server"])
    else:
        # SSE 模式
        await manager.connect_sse("news", f"{base_url}:8001/sse")
        await manager.connect_sse("mineral_pdf", f"{base_url}:8002/sse")
        await manager.connect_sse("price", f"{base_url}:8003/sse")

    tools = await manager.list_all_tools()
    print(f"  [OK] Total tools: {len(tools)}\n")

    return manager
