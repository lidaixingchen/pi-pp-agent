from llm import LLM
from memory import Memory
from prompt import INITIAL_PROMPT_TEMPLATE, REFLECT_PROMPT_TEMPLATE, REFINE_PROMPT_TEMPLATE
from typing import Optional

class ReflectionAgent:
    """一个基于反思机制的智能体，能够根据任务要求生成代码，并通过自我反思不断优化。"""
    def __init__(self, llm: LLM, max_iterations: int = 5):
        self.llm = llm
        self.memory = Memory()
        self.max_iterations = max_iterations

    def generate_initial_code(self, task: str) -> Optional[str]:
        """根据任务要求生成初始代码"""
        sanitized_task = task.strip()
        prompt = INITIAL_PROMPT_TEMPLATE.format(task=sanitized_task)
        response = self.llm.generate_response([{"role": "user", "content": prompt}])
        if not response:
            print("❌ LLM调用失败，未能获取初始代码")
            return None
        self.memory.add_entry("action", f"生成初始代码:\n{response}")
        return response

    def reflect_on_code(self, task: str, code: str) -> Optional[str]:
        """对生成的代码进行反思，找出性能瓶颈并提出改进建议"""
        prompt = REFLECT_PROMPT_TEMPLATE.format(task=task, code=code)
        response = self.llm.generate_response([{"role": "user", "content": prompt}])
        if not response:
            print("❌ LLM调用失败，未能获取反思反馈")
            return None
        if response.strip().endswith("无需改进") or "无需改进" in response.split("\n")[0]:
            self.memory.add_entry("reflection", "代码经过评审，无需改进。")
        else:
            self.memory.add_entry("reflection", f"对代码的反思反馈:\n{response}")
        return response

    def refine_code(self, task: str, last_code_attempt: str, feedback: str) -> Optional[str]:
        """根据评审员的反馈优化代码"""
        prompt = REFINE_PROMPT_TEMPLATE.format(task=task, last_code_attempt=last_code_attempt, feedback=feedback)
        response = self.llm.generate_response([{"role": "user", "content": prompt}])
        if not response:
            print("❌ LLM调用失败，未能获取优化后的代码")
            return None
        self.memory.add_entry("action", f"根据反馈优化后的代码:\n{response}")
        return response
    
    def answer_question(self, question: str) -> str:
        """主流程：根据用户问题生成代码，并通过反思不断优化，最终返回答案"""
        task = question  
        code = self.generate_initial_code(task)
        if not code:
            return "抱歉，未能生成初始代码。"
        
        for iteration in range(self.max_iterations):
            print(f"\n--- 迭代 {iteration + 1} ---")
            feedback = self.reflect_on_code(task, code)
            if feedback is None:
                return "抱歉，反思过程中发生错误。"
            if feedback.strip().endswith("无需改进") or "无需改进" in feedback.split("\n")[0]:
                print("代码经过评审，无需改进。")
                return code  # 返回最终代码作为答案
            
            print(f"评审反馈:\n{feedback}")
            refined_code = self.refine_code(task, code, feedback)
            if not refined_code:
                return "抱歉，优化过程中发生错误。"
            code = refined_code
        
        return "抱歉，未能在规定的迭代次数内找到满意的答案。"