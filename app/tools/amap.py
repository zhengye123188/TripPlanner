"""
高德地图工具 — 纯 HTTP 调用，不依赖任何 Agent 框架

职责：封装高德地图 Web API，提供两个能力：
1. search_pois()  — 关键词搜索 POI（景点、酒店、餐厅都能搜）
2. get_weather()  — 查询城市天气预报

为什么用 httpx 而不是 requests？
- httpx 支持 async，后续如果 FastAPI 用 async 路由可以无缝切换
- 但当前我们用同步版本（httpx.get），保持简单

为什么不用原项目的 MCP 协议？
- MCP 需要启动一个子进程服务器（uvx amap-mcp-server），增加复杂度
- 高德地图本身就是 REST API，直接 HTTP 调用更简单、更可控
"""

import httpx
from app.config import settings


# 高德地图 Web API 的基础地址
AMAP_BASE_URL = "https://restapi.amap.com/v3"


def search_pois(keywords: str, city: str, citylimit: bool = True) -> list[dict]:
    """
    搜索 POI（兴趣点）

    这个方法是通用的 —— 搜景点、搜酒店、搜餐厅都用它，只是 keywords 不同。
    graph 层的 search_attractions 节点会传 keywords="历史文化"
    graph 层的 search_hotels 节点会传 keywords="酒店"

    Args:
        keywords: 搜索关键词，如 "历史文化"、"酒店"、"美食"
        city: 城市名，如 "北京"
        citylimit: 是否限制在城市范围内搜索

    Returns:
        POI 列表，每个 POI 是一个 dict，包含 name/address/location 等字段
        如果调用失败返回空列表（不抛异常，让上层决定如何处理）
    """
    try:
        resp = httpx.get(
            f"{AMAP_BASE_URL}/place/text",
            params={
                "key": settings.amap_api_key,
                "keywords": keywords,
                "city": city,
                "citylimit": str(citylimit).lower(),
                "output": "json",
                "offset": 10,  # 最多返回10条
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "1":
            print(f"⚠️ 高德POI搜索失败: {data.get('info', 'unknown error')}")
            return []

        # 提取有用字段，统一格式
        pois = []
        for item in data.get("pois", []):
            # 高德返回的 location 是 "116.397128,39.916527" 格式的字符串
            loc_str = item.get("location", "")
            lng, lat = 0.0, 0.0
            if loc_str and "," in loc_str:
                parts = loc_str.split(",")
                lng, lat = float(parts[0]), float(parts[1])

            pois.append({
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "type": item.get("type", ""),
                "address": item.get("address", ""),
                "longitude": lng,
                "latitude": lat,
                "tel": item.get("tel", ""),
                "rating": item.get("biz_ext", {}).get("rating", ""),
            })

        return pois

    except Exception as e:
        print(f"❌ 高德POI搜索异常: {e}")
        return []


def get_weather(city: str) -> list[dict]:
    """
    查询城市天气预报

    Args:
        city: 城市名或城市编码，如 "北京"

    Returns:
        天气预报列表（最多4天），每条包含 date/day_weather/night_weather/temps 等
        如果失败返回空列表
    """
    try:
        resp = httpx.get(
            f"{AMAP_BASE_URL}/weather/weatherInfo",
            params={
                "key": settings.amap_api_key,
                "city": city,
                "extensions": "all",  # "all" 返回预报，"base" 只返回实况
                "output": "json",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "1":
            print(f"⚠️ 高德天气查询失败: {data.get('info', 'unknown error')}")
            return []

        # 从 forecasts 里提取每日天气
        forecasts = data.get("forecasts", [])
        if not forecasts:
            return []

        casts = forecasts[0].get("casts", [])
        weather_list = []
        for cast in casts:
            weather_list.append({
                "date": cast.get("date", ""),
                "day_weather": cast.get("dayweather", ""),
                "night_weather": cast.get("nightweather", ""),
                "day_temp": cast.get("daytemp", "0"),
                "night_temp": cast.get("nighttemp", "0"),
                "wind_direction": cast.get("daywind", ""),
                "wind_power": cast.get("daypower", ""),
            })

        return weather_list

    except Exception as e:
        print(f"❌ 高德天气查询异常: {e}")
        return []