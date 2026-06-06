from llm import LLM
from planner import Planner
from executor import Executor

class PlanAndSolveAgent:
    """一个结合了Planner和Executor的智能体，能够根据用户的问题生成计划并执行以得到答案"""
    def __init__(self, llm: LLM):
        self.planner = Planner(llm)
        self.executor = Executor(llm)

    def answer_question(self, question: str) -> str:
        """主方法，根据用户的问题生成计划并执行以得到答案"""
        print(f"用户问题: {question}")
        try:
            # 1. 生成计划
            plan = self.planner.plan(question)
            if not plan:
                return "抱歉，未能生成有效的计划。"
            print(f"生成的计划: {plan}")

            # 2. 执行计划
            final_answer = self.executor.execute(question, plan)
            print(f"最终答案: {final_answer}")
            return final_answer
        except Exception as e:
            print(f"❌ 执行过程中发生异常: {e}")
            return "抱歉，处理问题时发生错误。"