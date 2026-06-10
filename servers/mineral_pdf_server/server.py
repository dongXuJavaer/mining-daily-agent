"""MCP Server 2: mineral-pdf-mcp — NI 43-101 PDF 解析。

提供 extract_resources 工具，从 NI 43-101 矿业报告 PDF 中提取
Indicated Resources 和 Inferred Resources 表格数据:
矿石量 (Mt), 品位 (g/t Au 或 % Cu), 金属量 (oz 或 t)
"""

import json
import sys
from mcp.server.fastmcp import FastMCP
from servers.mineral_pdf_server.tools import extract_resources

mcp = FastMCP(
    name="MineralPdfServer",
    instructions="从 NI 43-101 矿业报告 PDF 中提取储量和资源数据。支持 Indicated Resources 和 Inferred Resources 的矿石量、品位、金属量提取。",
)


@mcp.tool()
def extract_resources_tool(pdf_url: str) -> str:
    """从 NI 43-101 报告 PDF 中提取 Indicated 和 Inferred Resources 数据。

    提取字段: 矿石量 (Mt), 品位 (g/t Au 或 % Cu), 金属量 (oz 或 t)
    支持公司名简写: "newmont", "barrick", "pilbara"

    Args:
        pdf_url: PDF 文件的 URL 或公司名简写
            示例: "newmont", "barrick", "pilbara",
            或完整 URL: "https://barrick.com/investors/annual-report/2025.pdf"
    """
    result = extract_resources(pdf_url)
    if not result:
        return (
            f"无法解析 PDF: {pdf_url}\n"
            f"支持的报告: Newmont, Barrick Gold, Pilbara Minerals"
        )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.resource("mineral-pdfs://available")
def get_available_reports() -> str:
    """列出可解析的 NI 43-101 报告。"""
    from servers.mineral_pdf_server.tools import _load_extractions
    extractions = _load_extractions()

    lines = ["# 可解析的 NI 43-101 报告\n"]
    for url, data in extractions.items():
        ind_count = len(data.get("indicated_resources", []))
        inf_count = len(data.get("inferred_resources", []))
        lines.append(f"- **{data['company']}** — {data['report_title']}")
        lines.append(f"  URL: {url}")
        lines.append(f"  Indicated: {ind_count} 条, Inferred: {inf_count} 条\n")

    return "\n".join(lines)


def main():
    transport = "stdio"
    port = 8002
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
