"""
LLM 工具 — 提供 ChatOpenAI 实例

为什么单独一个文件？
- graph 层的多个节点都需要用 LLM，但创建方式只需要定义一次
- 如果以后要换模型（比如从 GPT-4o 换成 DeepSeek），只改这一个文件
- 相当于 Java 里的 @Bean 工厂方法

为什么用 langchain-openai 的 ChatOpenAI？
- 它兼容所有 OpenAI 格式的 API（OpenAI / DeepSeek / 通义千问等）
- 只需要改 base_url 就能切换服务商
- LangGraph 的节点直接调用 model.invoke() 就行
"""

from langchain_openai import ChatOpenAI
from app.config import settings

# 模块级缓存，避免重复创建
_chat_model: ChatOpenAI | None = None


def get_chat_model() -> ChatOpenAI:
    """
    获取 ChatOpenAI 实例（单例）

    Returns:
        配置好的 ChatOpenAI，可以直接 model.invoke([messages])
    """
    global _chat_model

    if _chat_model is None:
        _chat_model = ChatOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
            temperature=0.7,  # 旅行规划需要一些创造性，不要太死板
        )

    return _chat_model