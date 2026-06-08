from typing import TypedDict, Annotated, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class SearchState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_query: str      # 经过LLM理解后的用户需求总结
    search_query: str    # 优化后用于Tavily API的搜索查询
    search_results: str  # Tavily搜索返回的结果
    final_answer: str    # 最终生成的答案
    step: Literal["start", "understood", "searched", "search_failed", "completed"]  # 标记当前步骤
