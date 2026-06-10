"""MCP Server 3: 商品价格数据。

提供 get_price 和 get_price_trend 两个工具，
以及 prices://overview 资源。
"""

import json
import sys
from mcp.server.fastmcp import FastMCP
from servers.price_server.tools import get_price, get_price_trend, get_all_prices

mcp = FastMCP(
    name="MiningPriceServer",
    instructions="提供矿产品价格查询服务。可查询锂、铜、金、铁矿石、镍等商品的最新价格和历史趋势。",
)


@mcp.tool()
def get_price_tool(commodity: str) -> str:
    """获取某矿产品的最新价格、24小时和7天涨跌幅。

    Args:
        commodity: 商品名称，支持: "锂"/"lithium", "铜"/"copper", "金"/"gold",
                   "铁矿石"/"iron ore", "镍"/"nickel", 或直接用 "Li2CO3", "Cu", "Au", "Fe", "Ni"
    """
    result = get_price(commodity)
    if not result:
        return f"未找到商品 '{commodity}' 的价格数据。支持的商品: Li2CO3(锂), Cu(铜), Au(金), Fe(铁矿石), Ni(镍)"
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def get_price_trend_tool(commodity: str, days: int = 30) -> str:
    """获取某矿产品的价格趋势数据，用于分析价格走势。

    Args:
        commodity: 商品名称 (同 get_price_tool)
        days: 获取最近N天的趋势数据，默认30天
    """
    result = get_price_trend(commodity, days)
    if not result:
        return f"未找到商品 '{commodity}' 的价格趋势数据。"
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.resource("prices://overview")
def get_prices_overview() -> str:
    """获取所有矿产品最新价格一览。"""
    prices = get_all_prices()
    lines = ["# 矿产品价格概览\n"]
    lines.append("| 商品 | 最新价格 | 单位 | 24h涨跌 | 7d涨跌 | 日期 |")
    lines.append("|------|---------|------|---------|--------|------|")
    for p in prices:
        chg_24h = f"+{p['change_24h']}%" if p["change_24h"] > 0 else f"{p['change_24h']}%"
        chg_7d = f"+{p['change_7d']}%" if p["change_7d"] > 0 else f"{p['change_7d']}%"
        lines.append(
            f"| {p['name']} | {p['price']:,.1f} | {p['unit']} | {chg_24h} | {chg_7d} | {p['date']} |"
        )
    return "\n".join(lines)


def main():
    transport = "stdio"
    port = 8003
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
