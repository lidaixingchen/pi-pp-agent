import os
from llm import LLM
from tool_executor import ToolExecutor, Tool
from tools.search_tool import search as search_tool

def main():
    # 1. 初始化工具执行器
    toolExecutor = ToolExecutor()

    # 2. 注册我们的实战搜索工具
    search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    toolExecutor.register_tool(Tool("Search", search_description, search_tool, {"query": "搜索查询字符串"}))
    
    # 3. 打印可用的工具
    print("\n--- 可用的工具 ---")
    print(toolExecutor.get_tools_description())

    # 4. 智能体的Action调用，这次我们问一个实时性的问题
    print("\n--- 执行 Action: Search['英伟达最新的GPU型号是什么'] ---")
    tool_name = "Search"
    tool_input = "英伟达最新的消费级GPU型号是什么？使用中文回答。"

    observation = toolExecutor.execute_tool(tool_name, query=tool_input)
    print("--- 观察 (Observation) ---")
    print(observation)

if __name__ == "__main__":
    main()