from langchain_core.messages import AIMessage, SystemMessage
from g_state import SearchState
from config import llm


def generate_answer_node(state: SearchState) -> dict:
    """步骤3：基于搜索结果生成最终答案"""
    if state.get("step") == "search_failed":
        # 如果搜索失败，执行回退策略，基于LLM自身知识回答
        fallback_prompt = f"搜索API暂时不可用，请基于您的知识回答用户的问题：\n用户问题：{state['user_query']}"
        try:
            response = llm.invoke([SystemMessage(content=fallback_prompt)])
        except Exception as e:
            return {
                "final_answer": f"抱歉，生成答案时遇到问题：{e}",
                "step": "completed",
                "messages": [AIMessage(content=f"抱歉，生成答案时遇到问题：{e}")]
            }
    else:
        # 搜索成功，基于搜索结果生成答案
        answer_prompt = f"""基于以下搜索结果为用户提供完整、准确的答案：
用户问题：{state['user_query']}
搜索结果：\n{state['search_results']}
请综合搜索结果，提供准确、有用的回答..."""
        try:
            response = llm.invoke([SystemMessage(content=answer_prompt)])
        except Exception as e:
            return {
                "final_answer": f"抱歉，生成答案时遇到问题：{e}",
                "step": "completed",
                "messages": [AIMessage(content=f"抱歉，生成答案时遇到问题：{e}")]
            }

    content_text = response.content if isinstance(response.content, str) else str(response.content)
    return {
        "final_answer": content_text,
        "step": "completed",
        "messages": [AIMessage(content=content_text)]
    }
