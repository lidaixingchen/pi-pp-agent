from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from g_state import SearchState
from config import tavily_client


def tavily_search_node(state: SearchState) -> dict:
    """步骤2：使用Tavily API进行真实搜索"""
    search_query = state["search_query"]
    try:
        print(f"🔍 正在搜索: {search_query}")
        response = tavily_client.search(
            query=search_query, search_depth="basic", max_results=5, include_answer=True
        )

        # 格式化搜索结果
        results = response.get("results", [])
        answer = response.get("answer", "")

        search_parts = []
        if answer:
            search_parts.append(f"**AI摘要：** {answer}\n")

        for i, result in enumerate(results, 1):
            title = result.get("title", "无标题")
            url = result.get("url", "")
            content = result.get("content", "")
            search_parts.append(f"**{i}. {title}**\n链接：{url}\n摘要：{content}\n")

        search_results = "\n".join(search_parts) if search_parts else "未找到相关结果"

        return {
            "search_results": search_results,
            "step": "searched",
            "messages": [AIMessage(content="✅ 搜索完成！正在整理答案...")]
        }
    except Exception as e:
        print(f"❌ 搜索出错: {e}")
        return {
            "search_results": f"搜索失败：{e}",
            "step": "search_failed",
            "messages": [AIMessage(content="❌ 搜索遇到问题，请稍后重试")]
        }
