"""
LangGraph 工作流组装 — 把节点连成流水线

这个文件做的事情相当于 LangGraph 版的"main 方法"：
1. 创建 StateGraph
2. 注册 5 个节点
3. 用 add_edge 按顺序连接
4. 编译成可执行的 app

对比原项目：
- 原项目在 plan_trip() 方法里手写 4 个 agent.run() 顺序调用
- 我们用 LangGraph 的 add_edge 声明式定义流程
- 好处：流程可视化、可插入条件分支、可加重试逻辑、状态可追踪
"""

from langgraph.graph import StateGraph, START, END
from app.graph.state import TripState
from app.graph.nodes import (
    search_attractions,
    query_weather,
    search_hotels,
    plan_itinerary,
    parse_output,
    fetch_photos,
)


def build_trip_workflow() -> StateGraph:
    """
    构建旅行规划工作流

    流程：
    START → search_attractions → query_weather → search_hotels
          → plan_itinerary → parse_output → fetch_photos → END

    Returns:
        编译后的 LangGraph app，可以直接 app.invoke(state) 调用
    """

    # 1. 创建 StateGraph，指定状态类型
    graph = StateGraph(TripState)

    # 2. 注册节点（名字 → 函数）
    graph.add_node("search_attractions", search_attractions)
    graph.add_node("query_weather", query_weather)
    graph.add_node("search_hotels", search_hotels)
    graph.add_node("plan_itinerary", plan_itinerary)
    graph.add_node("parse_output", parse_output)
    graph.add_node("fetch_photos", fetch_photos)

    # 3. 连接边（定义执行顺序）
    graph.add_edge(START, "search_attractions")
    graph.add_edge("search_attractions", "query_weather")
    graph.add_edge("query_weather", "search_hotels")
    graph.add_edge("search_hotels", "plan_itinerary")
    graph.add_edge("plan_itinerary", "parse_output")
    graph.add_edge("parse_output", "fetch_photos")
    graph.add_edge("fetch_photos", END)

    # 4. 编译
    app = graph.compile()

    return app


# 模块级单例，避免每次请求都重新构建 graph
_workflow = None


def get_workflow():
    """获取工作流实例（单例）"""
    global _workflow
    if _workflow is None:
        _workflow = build_trip_workflow()
        print("✅ LangGraph 工作流构建完成")
    return _workflow