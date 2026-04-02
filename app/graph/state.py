"""
LangGraph 状态定义 — 所有节点共享的数据结构

在 LangGraph 中，State 就像流水线上的托盘：
- 每个节点从 State 里读取自己需要的数据
- 处理完后把结果写回 State
- 下一个节点接着读

为什么用 TypedDict 而不是 Pydantic？
- LangGraph 的 StateGraph 要求 State 是 TypedDict
- TypedDict 只做类型提示，不做运行时校验（轻量）
- 真正的数据校验在最后的 parse_output 节点里由 Pydantic 完成
"""

from typing import TypedDict
from app.schemas.models import TripRequest, TripPlan


class TripState(TypedDict):
    """
    旅行规划工作流的共享状态

    数据流向：
    ┌─────────────────┐
    │  request         │ ← API 路由写入（用户的原始请求）
    │  raw_attractions │ ← search_attractions 节点写入
    │  raw_weather     │ ← query_weather 节点写入
    │  raw_hotels      │ ← search_hotels 节点写入
    │  raw_plan_text   │ ← plan_itinerary 节点写入（LLM 生成的原始文本）
    │  trip_plan       │ ← parse_output 节点写入（最终结构化结果）
    │  error           │ ← 任何节点出错时写入
    └─────────────────┘
    """

    # 输入：用户请求（API 路由在调用 graph 之前填入）
    request: TripRequest

    # 中间结果：各节点依次填入
    raw_attractions: list[dict]   # search_attractions → 高德返回的景点列表
    raw_weather: list[dict]       # query_weather → 高德返回的天气列表
    raw_hotels: list[dict]        # search_hotels → 高德返回的酒店列表
    raw_plan_text: str            # plan_itinerary → LLM 生成的 JSON 文本

    # 最终输出
    trip_plan: TripPlan | None    # parse_output → 解析后的结构化旅行计划

    # 错误信息
    error: str                    # 出错时记录原因，不出错为空字符串