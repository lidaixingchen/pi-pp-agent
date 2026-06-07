from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from nodes.understand_query import understand_query_node
from nodes.tavily_search import tavily_search_node
from nodes.generate_answer import generate_answer_node
from g_state import SearchState


def create_search_assistant():
    workflow = StateGraph(SearchState)
    
    # 添加节点
    workflow.add_node("understand", understand_query_node)
    workflow.add_node("search", tavily_search_node)
    workflow.add_node("answer", generate_answer_node)
    
    # 设置线性流程
    workflow.add_edge(START, "understand")
    workflow.add_edge("understand", "search")
    workflow.add_edge("search", "answer")
    workflow.add_edge("answer", END)
    
    # 编译图
    memory = InMemorySaver()
    app = workflow.compile(checkpointer=memory)
    return app
