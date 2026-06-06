from llm import LLM
from prompt import EXECUTOR_PROMPT_TEMPLATE

class Executor:
    """执行器类，负责根据计划执行每个步骤并返回结果"""
    def __init__(self, llm: LLM):
        self.llm = llm

    def execute(self, question: str, plan: list[str]) -> str:
        """根据计划执行每个步骤，返回最终答案"""
        history = []
        step_results = []
        formatted_plan = "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan))
        for step in plan:
            current_step = step
            # 构建提示词
            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question,
                plan=formatted_plan,
                history="\n".join(history) if history else "无",
                current_step=current_step
            )
            # 调用LLM生成响应
            print(f"\n执行步骤: {current_step}")
            response = self.llm.generate_response([{"role": "user", "content": prompt}])
            if not response:
                print("❌ LLM调用失败，未能获取执行响应")
                return "抱歉，执行过程中发生错误。"
            print(f"步骤结果: {response}")
            history.append(f"步骤: {current_step}\n结果: {response}")
            step_results.append(response)

        # 最后一步的结果即为最终答案
        final_answer = step_results[-1] if step_results else "抱歉，未能生成答案。"
        return final_answer
        