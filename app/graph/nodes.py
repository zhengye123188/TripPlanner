"""
LangGraph 节点函数 — 工作流的 5 个步骤

每个节点都是一个纯函数：
- 输入：TripState（当前的完整状态）
- 输出：dict（只包含需要更新的字段，LangGraph 会自动合并回 State）

节点之间不直接调用，而是通过 State 传递数据。
这样每个节点都可以单独测试，互不依赖。

执行顺序：
search_attractions → query_weather → search_hotels → plan_itinerary → parse_output
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from app.graph.state import TripState
from app.tools.amap import search_pois, get_weather
from app.tools.llm import get_chat_model


# ============================================================
# 节点 1：搜索景点
# ============================================================

def search_attractions(state: TripState) -> dict:
    """
    从高德地图搜索景点

    读取：state["request"] 里的 city 和 preferences
    写入：state["raw_attractions"]
    """
    request = state["request"]

    # 用第一个偏好作为关键词，没有偏好就搜"景点"
    keywords = request.preferences[0] if request.preferences else "景点"

    print(f"📍 搜索景点: city={request.city}, keywords={keywords}")
    results = search_pois(keywords=keywords, city=request.city)
    print(f"   找到 {len(results)} 个景点")

    return {"raw_attractions": results}


# ============================================================
# 节点 2：查询天气
# ============================================================

def query_weather(state: TripState) -> dict:
    """
    从高德地图查询天气

    读取：state["request"] 里的 city
    写入：state["raw_weather"]
    """
    request = state["request"]

    print(f"🌤️ 查询天气: city={request.city}")
    results = get_weather(city=request.city)
    print(f"   获取 {len(results)} 天天气数据")

    return {"raw_weather": results}


# ============================================================
# 节点 3：搜索酒店
# ============================================================

def search_hotels(state: TripState) -> dict:
    """
    从高德地图搜索酒店

    读取：state["request"] 里的 city 和 accommodation
    写入：state["raw_hotels"]

    注意：复用 search_pois，只是 keywords 不同
    """
    request = state["request"]

    # 用住宿偏好作为关键词，如 "经济型酒店"
    keywords = request.accommodation if request.accommodation else "酒店"

    print(f"🏨 搜索酒店: city={request.city}, keywords={keywords}")
    results = search_pois(keywords=keywords, city=request.city)
    print(f"   找到 {len(results)} 个酒店")

    return {"raw_hotels": results}


# ============================================================
# 节点 4：LLM 生成行程计划
# ============================================================

PLANNER_SYSTEM_PROMPT = """你是一位专业的旅行规划师。请根据提供的景点、天气和酒店信息，生成详细的旅行计划。

请严格按照以下 JSON 格式返回，不要添加任何其他文字：

```json
{
  "city": "城市名",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "当天行程概述",
      "transportation": "交通方式",
      "accommodation": "住宿类型",
      "hotel": {
        "name": "酒店名", "address": "地址",
        "location": {"longitude": 116.397, "latitude": 39.916},
        "price_range": "300-500元", "rating": "4.5",
        "distance": "距景点2公里", "type": "酒店类型", "estimated_cost": 400
      },
      "attractions": [
        {
          "name": "景点名", "address": "地址",
          "location": {"longitude": 116.397, "latitude": 39.916},
          "visit_duration": 120, "description": "描述",
          "category": "类别", "ticket_price": 60
        }
      ],
      "meals": [
        {"type": "breakfast", "name": "早餐", "description": "描述", "estimated_cost": 30},
        {"type": "lunch", "name": "午餐", "description": "描述", "estimated_cost": 50},
        {"type": "dinner", "name": "晚餐", "description": "描述", "estimated_cost": 80}
      ]
    }
  ],
  "weather_info": [
    {
      "date": "YYYY-MM-DD", "day_weather": "晴", "night_weather": "多云",
      "day_temp": 25, "night_temp": 15, "wind_direction": "南风", "wind_power": "1-3级"
    }
  ],
  "overall_suggestions": "总体建议",
  "budget": {
    "total_attractions": 180, "total_hotels": 1200,
    "total_meals": 480, "total_transportation": 200, "total": 2060
  }
}
```

要求：
1. 每天安排 2-3 个景点，优先使用提供的真实景点数据
2. 每天包含早中晚三餐
3. 景点的经纬度必须使用提供的真实数据，不要编造
4. 天气信息使用提供的真实数据
5. 温度必须是纯数字，不带单位
6. 必须包含预算信息"""


def plan_itinerary(state: TripState) -> dict:
    """
    调用 LLM 生成完整行程

    读取：state 里的 request + raw_attractions + raw_weather + raw_hotels
    写入：state["raw_plan_text"]

    这个节点做的事情：
    1. 把前三个节点收集的数据组装成一个大 prompt
    2. 调用 LLM 让它生成 JSON 格式的行程
    3. 把 LLM 返回的原始文本存入 State
    """
    request = state["request"]
    attractions = state["raw_attractions"]
    weather = state["raw_weather"]
    hotels = state["raw_hotels"]

    # 组装给 LLM 的 prompt
    user_prompt = f"""请为以下旅行需求生成详细行程：

**基本信息：**
- 城市：{request.city}
- 日期：{request.start_date} 至 {request.end_date}
- 天数：{request.travel_days} 天
- 交通：{request.transportation}
- 住宿：{request.accommodation}
- 偏好：{', '.join(request.preferences) if request.preferences else '无'}

**搜索到的景点（请优先使用这些真实数据）：**
{json.dumps(attractions, ensure_ascii=False, indent=2)}

**天气预报：**
{json.dumps(weather, ensure_ascii=False, indent=2)}

**搜索到的酒店：**
{json.dumps(hotels, ensure_ascii=False, indent=2)}
"""

    if request.free_text_input:
        user_prompt += f"\n**用户额外要求：** {request.free_text_input}"

    print(f"📋 调用 LLM 生成行程计划...")

    model = get_chat_model()
    response = model.invoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    raw_text = response.content
    print(f"   LLM 返回 {len(raw_text)} 字符")

    return {"raw_plan_text": raw_text}


# ============================================================
# 节点 5：解析 LLM 输出
# ============================================================

def parse_output(state: TripState) -> dict:
    """
    将 LLM 返回的文本解析为结构化的 TripPlan

    读取：state["raw_plan_text"] + state["request"]
    写入：state["trip_plan"] 或 state["error"]

    LLM 返回的文本可能有三种情况：
    1. ```json ... ```  代码块包裹
    2. 直接就是 JSON
    3. JSON 混在其他文字中间
    所以需要逐一尝试提取
    """
    from app.schemas.models import TripPlan, DayPlan, Attraction, Meal, Location

    raw_text = state["raw_plan_text"]
    request = state["request"]

    try:
        # 尝试提取 JSON
        json_str = _extract_json(raw_text)
        data = json.loads(json_str)

        # 用 Pydantic 模型验证和转换
        trip_plan = TripPlan(**data)
        print(f"✅ 行程解析成功: {len(trip_plan.days)} 天")

        return {"trip_plan": trip_plan, "error": ""}

    except Exception as e:
        print(f"⚠️ 解析失败: {e}，使用备用计划")

        # 生成备用计划
        fallback = _create_fallback_plan(request)
        return {"trip_plan": fallback, "error": f"LLM 输出解析失败: {str(e)}"}


def _extract_json(text: str) -> str:
    """从 LLM 返回的文本中提取 JSON 字符串"""

    # 情况1：```json ... ``` 代码块
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        return text[start:end].strip()

    # 情况2：``` ... ``` 代码块（没有 json 标记）
    if "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        return text[start:end].strip()

    # 情况3：直接找 { ... }
    if "{" in text and "}" in text:
        start = text.find("{")
        end = text.rfind("}") + 1
        return text[start:end]

    raise ValueError("文本中未找到 JSON 数据")


def _create_fallback_plan(request) -> "TripPlan":
    """当 LLM 输出解析失败时，生成一个基本的备用计划"""
    from datetime import datetime, timedelta
    from app.schemas.models import TripPlan, DayPlan, Attraction, Meal, Location

    start = datetime.strptime(request.start_date, "%Y-%m-%d")
    days = []

    for i in range(request.travel_days):
        current = start + timedelta(days=i)
        days.append(DayPlan(
            date=current.strftime("%Y-%m-%d"),
            day_index=i,
            description=f"第{i + 1}天行程",
            transportation=request.transportation,
            accommodation=request.accommodation,
            attractions=[
                Attraction(
                    name=f"{request.city}景点{j + 1}",
                    address=f"{request.city}市",
                    location=Location(longitude=116.4 + j * 0.01, latitude=39.9 + j * 0.01),
                    visit_duration=120,
                    description=f"{request.city}的热门景点",
                )
                for j in range(2)
            ],
            meals=[
                Meal(type="breakfast", name="当地早餐", estimated_cost=30),
                Meal(type="lunch", name="当地午餐", estimated_cost=50),
                Meal(type="dinner", name="当地晚餐", estimated_cost=80),
            ],
        ))

    return TripPlan(
        city=request.city,
        start_date=request.start_date,
        end_date=request.end_date,
        days=days,
        overall_suggestions=f"这是{request.city}{request.travel_days}日游的备用行程，建议提前查看各景点开放时间。",
    )