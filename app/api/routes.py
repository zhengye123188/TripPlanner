"""
FastAPI 路由 — 对外暴露 HTTP 接口

这个文件的职责非常薄：
1. 接收前端请求 → Pydantic 自动校验
2. 调用 LangGraph 工作流
3. 从 State 里取出结果 → 包装成响应返回

不包含任何业务逻辑。业务全在 graph 层。
相当于 Java 里的 @RestController —— 只做转发，不做计算。
"""

from fastapi import APIRouter, HTTPException
from app.schemas.models import TripRequest, TripPlanResponse
from app.graph.workflow import get_workflow
from app.tools.unsplash import get_photo_url

router = APIRouter(prefix="/api", tags=["旅行规划"])


@router.post("/trip/plan", response_model=TripPlanResponse)
async def plan_trip(request: TripRequest):
    """
    生成旅行计划

    前端 POST JSON → Pydantic 自动解析为 TripRequest
    → 调用 LangGraph 工作流 → 返回 TripPlanResponse
    """
    try:
        # 获取工作流
        workflow = get_workflow()

        # 构造初始 State 并执行
        initial_state = {
            "request": request,
            "raw_attractions": [],
            "raw_weather": [],
            "raw_hotels": [],
            "raw_plan_text": "",
            "trip_plan": None,
            "attraction_photos": {},
            "error": "",
        }

        print(f"\n{'=' * 50}")
        print(f"🚀 开始规划: {request.city} {request.travel_days}天")
        print(f"{'=' * 50}")

        # 执行工作流（LangGraph 会按 edge 顺序依次执行 5 个节点）
        result = workflow.invoke(initial_state)

        print(f"{'=' * 50}")
        print(f"✅ 规划完成")
        print(f"{'=' * 50}\n")

        # 从 State 中取出最终结果
        trip_plan = result.get("trip_plan")
        error = result.get("error", "")

        return TripPlanResponse(
            success=True,
            message="旅行计划生成成功" if not error else f"计划已生成（{error}）",
            data=trip_plan,
        )

    except Exception as e:
        print(f"❌ 规划失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成旅行计划失败: {str(e)}")


@router.get("/trip/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "trip-planner"}


@router.get("/poi/photo")
async def get_attraction_photo(name: str):
    """
    获取景点图片

    前端在渲染结果页时，会为每个景点请求这个接口获取配图。
    """
    try:
        # 用景点名 + "China landmark" 提高搜索准确度
        photo_url = get_photo_url(f"{name} China landmark")

        if not photo_url:
            # 退一步，只用景点名搜
            photo_url = get_photo_url(name)

        return {
            "success": True,
            "message": "获取图片成功",
            "data": {
                "name": name,
                "photo_url": photo_url,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")