"""mineral-pdf-mcp tools — extract_resources.

从 NI 43-101 矿业报告 PDF 中提取 Indicated/Inferred Resources 表格数据。
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def _load_extractions() -> dict:
    with open(DATA_DIR / "sample_extractions.json", encoding="utf-8") as f:
        return json.load(f)


# 已知的 PDF URL 到 mock 数据的映射
# 真实场景中，这里会调用 PyPDF2 / pdfplumber / LLM 解析 PDF
KNOWN_REPORTS = {
    "newmont": "https://newmont.com/investors/annual-reports/2025-annual-report.pdf",
    "barrick": "https://barrick.com/investors/annual-report/2025.pdf",
    "pilbara": "https://pilbaraminerals.com.au/investors/annual-report-2025.pdf",
    "pilbara minerals": "https://pilbaraminerals.com.au/investors/annual-report-2025.pdf",
}


def extract_resources(pdf_url: str) -> dict | None:
    """从 NI 43-101 报告 PDF 中提取 Indicated 和 Inferred Resources 数据。

    提取字段: 矿石量 (Mt), 品位 (g/t Au 或 % Cu), 金属量 (oz 或 t)

    Args:
        pdf_url: PDF 文件的 URL 或路径
            支持直接 URL，也支持公司名简写 (如 "newmont", "barrick", "pilbara")

    Returns:
        {
            company, report_title, report_date, source_url,
            indicated_resources: [{project, commodity, ore_tonnes_mt, grade, metal_content}],
            inferred_resources: [{project, commodity, ore_tonnes_mt, grade, metal_content}]
        }
        未找到返回 None
    """
    extractions = _load_extractions()

    # 直接 URL 匹配
    if pdf_url in extractions:
        return extractions[pdf_url]

    # 公司名简写匹配
    key = pdf_url.lower().strip()
    if key in KNOWN_REPORTS:
        url = KNOWN_REPORTS[key]
        if url in extractions:
            return extractions[url]

    # 模糊匹配
    for known_key, url in KNOWN_REPORTS.items():
        if known_key in key or key in known_key:
            if url in extractions:
                return extractions[url]

    # URL 子串匹配
    for url in extractions:
        if pdf_url.lower() in url.lower() or url.lower() in pdf_url.lower():
            return extractions[url]

    return None
