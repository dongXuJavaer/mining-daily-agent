"""MCP Server 1: 矿业新闻聚合。

提供 search 和 fetch_article 两个工具，
以及 news://latest 和 policy://recent 两个资源。
"""

import json
import sys
from mcp.server.fastmcp import FastMCP
from servers.news_server.tools import search, fetch_article, _load_json

mcp = FastMCP(
    name="MiningNewsServer",
    instructions="矿业新闻聚合服务。搜索最新矿业新闻和政策动态，获取文章全文。",
)


@mcp.tool()
def search_tool(query: str, days: int = 7) -> str:
    """搜索矿业新闻和政策。根据关键词查找最新的行业新闻、公司动态、政策法规等。

    Args:
        query: 搜索关键词，如 "lithium", "pilbara", "copper", "澳洲政策", "镍矿"
        days: 搜索最近N天的内容，默认7天
    """
    results = search(query, days)
    if not results:
        return f"未找到与 '{query}' 相关的最近 {days} 天新闻。"
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
def fetch_article_tool(url: str) -> str:
    """根据 URL 获取文章全文。当 search 返回的结果摘要不够详细时，用此工具获取完整内容。

    Args:
        url: 文章链接，来自 search 返回结果中的 url 字段
    """
    article = fetch_article(url)
    if not article:
        return f"未找到 URL 对应的文章: {url}"
    return json.dumps(article, ensure_ascii=False, indent=2)


@mcp.resource("news://latest")
def get_latest_news() -> str:
    """获取最新10条矿业新闻摘要。"""
    news = _load_json("news.json")
    news.sort(key=lambda x: x["date"], reverse=True)
    latest = news[:10]
    lines = [f"# 最新矿业新闻 ({latest[0]['date'] if latest else 'N/A'})\n"]
    for i, item in enumerate(latest, 1):
        lines.append(f"{i}. **{item['title']}** — {item['source']}, {item['date']}")
        lines.append(f"   > {item['summary']}\n")
    return "\n".join(lines)


@mcp.resource("policy://recent")
def get_recent_policy() -> str:
    """获取近期政策变动摘要。"""
    policies = _load_json("policy.json")
    policies.sort(key=lambda x: x["date"], reverse=True)
    latest = policies[:10]
    lines = [f"# 近期矿业政策变动\n"]
    for i, item in enumerate(latest, 1):
        impact_emoji = {"high": "!!", "medium": "~", "low": "-"}.get(item["impact"], " ")
        lines.append(f"{i}. [{impact_emoji}] **{item['title']}** ({item['region']}, {item['date']})")
        lines.append(f"   > {item['summary']}\n")
    return "\n".join(lines)


def main():
    transport = "stdio"
    port = 8001
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--transport" and i + 1 < len(args):
            transport = args[i + 1]
        if arg == "--port" and i + 1 < len(args):
            port = int(args[i + 1])

    if transport == "sse":
        mcp.settings.port = port
        mcp.run("sse")
    else:
        mcp.run("stdio")


if __name__ == "__main__":
    main()
