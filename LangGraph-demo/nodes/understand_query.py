from langchain_core.messages import AIMessage, SystemMessage
from g_state import SearchState
from config import llm


def understand_query_node(state: SearchState) -> dict:
    """步骤1：理解用户查询并生成搜索关键词"""
    user_message = state["user_query"]

    understand_prompt = f"""分析用户的查询："{user_message}"
请完成两个任务：
1. 简洁总结用户想要了解什么
2. 生成最适合搜索引擎的关键词（中英文均可，要精准）

格式：
理解：[用户需求总结]
搜索词：[最佳搜索关键词]"""

    try:
        response = llm.invoke([SystemMessage(content=understand_prompt)])
        response_text = response.content if isinstance(response.content, str) else str(response.content)
    except Exception:
        # LLM调用失败时，回退使用原始查询
        return {
            "user_query": user_message,
            "search_query": user_message,
            "step": "understood",
            "messages": [AIMessage(content=f"理解查询失败，将使用原始查询搜索：{user_message}")]
        }

    # 解析LLM的输出，提取搜索关键词
    search_query = user_message  # 默认使用原始查询
    if "搜索词：" in response_text:
        search_query = response_text.split("搜索词：")[1].strip()

    return {
        "user_query": user_message,
        "search_query": search_query,
        "step": "understood",
        "messages": [AIMessage(content=f"我将为您搜索：{search_query}")]
    }
