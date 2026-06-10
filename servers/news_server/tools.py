"""News Server tools — search and fetch_article."""

import json
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def _load_json(filename: str) -> list[dict]:
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def search(query: str, days: int = 7) -> list[dict]:
    """搜索矿业新闻和政策。

    Args:
        query: 搜索关键词 (如 "lithium", "pilbara", "copper price")
        days: 搜索最近N天的新闻，默认7天

    Returns:
        匹配的新闻列表 [{title, source, date, summary, url, tags}]
        按日期降序排列
    """
    # 合并搜索新闻 + 政策
    news = _load_json("news.json")
    policies = _load_json("policy.json")

    # 将政策转为统一格式
    for p in policies:
        p["source"] = p.get("source", "Policy")
        p["tags"] = ["policy", p.get("region", "").lower()]

    all_items = news + policies

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    query_lower = query.lower()

    results = []
    for item in all_items:
        if item["date"] < cutoff:
            continue
        searchable = (
            item["title"].lower()
            + " "
            + item["summary"].lower()
            + " "
            + " ".join(item.get("tags", [])).lower()
        )
        if query_lower in searchable:
            results.append(item)

    results.sort(key=lambda x: x["date"], reverse=True)
    return results


def fetch_article(url: str) -> dict | None:
    """根据 URL 获取文章全文。

    在真实场景中会爬取网页内容，这里从 mock 数据中查找并返回详细信息。

    Args:
        url: 文章链接

    Returns:
        文章详情 {title, source, date, summary, url, tags, content}
        未找到返回 None
    """
    news = _load_json("news.json")
    policies = _load_json("policy.json")

    for item in news:
        if item["url"] == url:
            return {**item, "content": item["summary"]}
    for item in policies:
        if item["url"] == url:
            return {
                "title": item["title"],
                "source": "Policy",
                "date": item["date"],
                "summary": item["summary"],
                "url": item["url"],
                "tags": ["policy", item.get("region", "").lower()],
                "content": item["summary"],
            }

    return None
