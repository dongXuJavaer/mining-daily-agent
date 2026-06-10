"""Price Server tools — get_price and get_price_trend."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# 商品名称到 key 的映射
COMMODITY_ALIASES = {
    "锂": "Li2CO3",
    "lithium": "Li2CO3",
    "碳酸锂": "Li2CO3",
    "li2co3": "Li2CO3",
    "铜": "Cu",
    "copper": "Cu",
    "金": "Au",
    "gold": "Au",
    "黄金": "Au",
    "铁矿石": "Fe",
    "iron ore": "Fe",
    "iron": "Fe",
    "铁": "Fe",
    "镍": "Ni",
    "nickel": "Ni",
}


def _load_prices() -> dict:
    with open(DATA_DIR / "prices.json", encoding="utf-8") as f:
        return json.load(f)


def _resolve_commodity(commodity: str) -> str | None:
    """将用户输入的商品名解析为标准 key。"""
    lower = commodity.lower().strip()
    if lower in COMMODITY_ALIASES:
        return COMMODITY_ALIASES[lower]
    # 直接匹配 key
    data = _load_prices()
    for key in data["commodities"]:
        if lower == key.lower():
            return key
    return None


def get_price(commodity: str) -> dict | None:
    """获取某商品的最新价格。

    Args:
        commodity: 商品名称，支持中文或英文 (如 "lithium", "铜", "Au", "Li2CO3")

    Returns:
        价格信息 {commodity, name, price, currency, unit, change_24h, change_7d, date}
    """
    key = _resolve_commodity(commodity)
    if not key:
        return None

    data = _load_prices()
    info = data["commodities"][key]
    return {
        "commodity": key,
        "name": info["name"],
        "price": info["latest_price"],
        "currency": info["currency"],
        "unit": info["unit"],
        "change_24h": info["change_24h"],
        "change_7d": info["change_7d"],
        "date": info["latest_date"],
    }


def get_price_trend(commodity: str, days: int = 30) -> list[dict] | None:
    """获取某商品的价格趋势。

    Args:
        commodity: 商品名称
        days: 获取最近N天的趋势数据，默认30天

    Returns:
        价格趋势列表 [{date, price, volume}]
    """
    key = _resolve_commodity(commodity)
    if not key:
        return None

    data = _load_prices()
    trend = data["commodities"][key]["trend"]
    return trend[-days:] if days < len(trend) else trend


def get_all_prices() -> list[dict]:
    """获取所有商品的最新价格概览。"""
    data = _load_prices()
    result = []
    for key, info in data["commodities"].items():
        result.append({
            "commodity": key,
            "name": info["name"],
            "price": info["latest_price"],
            "unit": info["unit"],
            "change_24h": info["change_24h"],
            "change_7d": info["change_7d"],
            "date": info["latest_date"],
        })
    return result
