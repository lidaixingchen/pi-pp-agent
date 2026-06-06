import os
from llm import LLM
from react_agent import ReactAgent
from plan_and_solve_agent import PlanAndSolveAgent
from reflection_agent import ReflectionAgent
from tool_executor import ToolExecutor, Tool
from tools.search_tool import search as search_tool
from tools.calculator_tool import calculate as calculator_tool

def main_react_agent():
    # 1. 初始化工具执行器
    tool_executor = ToolExecutor()
    llm = LLM()

    # 2. 注册搜索工具
    search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    tool_executor.register_tool(Tool("Search", search_description, search_tool, {"query": "搜索查询字符串"}))

    # 3. 注册计算器工具
    calculator_description = "一个数学计算器。当你需要进行数学计算时使用，支持基本运算(+,-,*,/)和函数(sqrt,sin,cos,log等)。"
    tool_executor.register_tool(Tool("Calculator", calculator_description, calculator_tool, {"expression": "数学表达式，如 2+3*4 或 sqrt(16)"}))

    # 4. 初始化ReAct Agent
    react_agent = ReactAgent(llm, tool_executor)

    # 4. 处理用户问题
    question = input("请输入您的问题: ")
    answer = react_agent.run(question)
    print(f"\n最终答案: {answer}")

def main_plan_and_solve_agent():
    # 1. 初始化PlanAndSolveAgent
    llm = LLM()
    plan_and_solve_agent = PlanAndSolveAgent(llm)

    # 2. 处理用户问题
    question = input("请输入您的问题: ")
    answer = plan_and_solve_agent.answer_question(question)
    print(f"\n最终答案: {answer}")

def main_reflection_agent():
    # 1. 初始化ReflectionAgent
    llm = LLM()
    reflection_agent = ReflectionAgent(llm)

    # 2. 处理用户问题
    question = input("请输入您的问题: ")
    answer = reflection_agent.answer_question(question)
    print(f"\n最终答案: {answer}")

if __name__ == "__main__":
    main_reflection_agent()