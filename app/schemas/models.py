"""
数据模型定义 — 整个项目的地基

设计原则：
1. 自底向上：先定义最小的（Location），再组合成大的（DayPlan → TripPlan）
2. 请求和响应分开：TripRequest 是前端传进来的，TripPlan 是我们返回的
3. 每个字段都有类型 + 默认值 + 描述，Pydantic 会自动校验

对照 API 文档的第 3 节阅读本文件。
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


# =====================================================
# 第一层：基础类型（被所有人依赖）
# =====================================================

class Location(BaseModel):
    """经纬度坐标 — 景点、酒店、餐厅都需要"""
    longitude: float = Field(..., description="经度", ge=-180, le=180)
    latitude: float = Field(..., description="纬度", ge=-90, le=90)


# =====================================================
# 第二层：业务实体（景点、酒店、餐饮、天气）
# =====================================================

class Attraction(BaseModel):
    """景点信息"""
    name: str = Field(..., description="景点名称")
    address: str = Field(..., description="详细地址")
    location: Location = Field(..., description="经纬度坐标")
    visit_duration: int = Field(..., description="建议游览时间（分钟）")
    description: str = Field(..., description="景点描述")
    category: str = Field(default="景点", description="景点类别")
    rating: Optional[float] = Field(default=None, description="评分")
    image_url: Optional[str] = Field(default=None, description="图片URL")
    ticket_price: int = Field(default=0, description="门票价格（元）")


class Hotel(BaseModel):
    """酒店信息"""
    name: str = Field(..., description="酒店名称")
    address: str = Field(default="", description="酒店地址")
    location: Optional[Location] = Field(default=None, description="经纬度")
    price_range: str = Field(default="", description="价格范围")
    rating: str = Field(default="", description="评分")
    distance: str = Field(default="", description="距景点距离")
    type: str = Field(default="", description="酒店类型")
    estimated_cost: int = Field(default=0, description="预估每晚费用（元）")


class Meal(BaseModel):
    """餐饮信息"""
    type: str = Field(..., description="breakfast / lunch / dinner / snack")
    name: str = Field(..., description="餐饮名称")
    address: Optional[str] = Field(default=None, description="地址")
    location: Optional[Location] = Field(default=None, description="经纬度")
    description: Optional[str] = Field(default=None, description="描述")
    estimated_cost: int = Field(default=0, description="预估费用（元）")


class WeatherInfo(BaseModel):
    """天气信息 — 高德 API 返回的温度可能带 °C 后缀，validator 自动处理"""
    date: str = Field(..., description="日期 YYYY-MM-DD")
    day_weather: str = Field(default="", description="白天天气")
    night_weather: str = Field(default="", description="夜间天气")
    day_temp: int | str = Field(default=0, description="白天温度")
    night_temp: int | str = Field(default=0, description="夜间温度")
    wind_direction: str = Field(default="", description="风向")
    wind_power: str = Field(default="", description="风力")

    @field_validator("day_temp", "night_temp", mode="before")
    @classmethod
    def parse_temperature(cls, v):
        """'25°C' → 25，纯数字直接返回"""
        if isinstance(v, str):
            v = v.replace("°C", "").replace("℃", "").replace("°", "").strip()
            try:
                return int(v)
            except ValueError:
                return 0
        return v


class Budget(BaseModel):
    """预算汇总"""
    total_attractions: int = Field(default=0, description="门票总费用")
    total_hotels: int = Field(default=0, description="酒店总费用")
    total_meals: int = Field(default=0, description="餐饮总费用")
    total_transportation: int = Field(default=0, description="交通总费用")
    total: int = Field(default=0, description="总费用")


# =====================================================
# 第三层：组合类型（由上面的实体组合而成）
# =====================================================

class DayPlan(BaseModel):
    """单日行程 — 一天包含多个景点 + 三餐 + 一个酒店"""
    date: str = Field(..., description="日期 YYYY-MM-DD")
    day_index: int = Field(..., description="第几天（从0开始）")
    description: str = Field(..., description="当日行程概述")
    transportation: str = Field(..., description="交通方式")
    accommodation: str = Field(..., description="住宿类型")
    hotel: Optional[Hotel] = Field(default=None, description="推荐酒店")
    attractions: list[Attraction] = Field(default_factory=list, description="景点列表")
    meals: list[Meal] = Field(default_factory=list, description="餐饮列表")


class TripPlan(BaseModel):
    """完整旅行计划 — 最终返回给前端的核心数据"""
    city: str = Field(..., description="目的地城市")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    days: list[DayPlan] = Field(..., description="每日行程")
    weather_info: list[WeatherInfo] = Field(default_factory=list, description="天气信息")
    overall_suggestions: str = Field(..., description="总体建议")
    budget: Optional[Budget] = Field(default=None, description="预算信息")


# =====================================================
# 第四层：请求 & 响应（API 层直接使用）
# =====================================================

class TripRequest(BaseModel):
    """前端表单提交的数据 — 对应 Home.vue 的表单"""
    city: str = Field(..., description="目的地城市")
    start_date: str = Field(..., description="开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期 YYYY-MM-DD")
    travel_days: int = Field(..., description="旅行天数", ge=1, le=30)
    transportation: str = Field(..., description="交通方式")
    accommodation: str = Field(..., description="住宿偏好")
    preferences: list[str] = Field(default_factory=list, description="偏好标签")
    free_text_input: str = Field(default="", description="额外要求")


class TripPlanResponse(BaseModel):
    """API 统一响应格式"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="消息")
    data: Optional[TripPlan] = Field(default=None, description="旅行计划")


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = Field(default=False)
    message: str = Field(..., description="错误描述")
    error_code: Optional[str] = Field(default=None, description="错误代码")