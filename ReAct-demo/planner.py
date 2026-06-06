from llm import LLM
from prompt import PLANNER_PROMPT_TEMPLATE
from typing import List
import ast
import re

class Planner:
    def __init__(self, llm: LLM):
        self.llm = llm

    def plan(self, question: str) -> List[str]:
        """根据用户的问题生成一个行动计划"""
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
        # 构造消息列表        
        messages = [
            {"role": "user", "content": prompt}
        ]
        # 调用LLM生成计划
        print("生成计划中...")
        response = self.llm.generate_response(messages)
        if not response:
            print("❌ LLM调用失败，未能获取计划响应")
            return []
        # 解析响应，提取计划
        plan = self.parse_plan_response(response)
        return plan
    
    def parse_plan_response(self, response: str) -> List[str]:
        """解析LLM响应，提取计划列表"""
        try:
            # 使用正则表达式提取```python...```之间的内容
            match = re.search(r'```python\s*\n?(.*?)\n?```', response, re.DOTALL)
            if not match:
                print(f"❌ 无法从响应中提取计划代码块: {response}")
                return []
            plan_str = match.group(1).strip()
            # 使用ast.literal_eval来安全地执行字符串，将其转换为Python列表
            plan = ast.literal_eval(plan_str)
            if not isinstance(plan, list):
                print(f"⚠️ 提取的内容不是列表类型: {plan}")
                return []
            return plan
        except (ValueError, SyntaxError) as e:
            print(f"❌ 解析计划时出错: {e}, 原始响应: {response}")
            return []
        except Exception as e:
            print(f"❌ 解析计划时发生未知错误: {e}, 原始响应: {response}")
            return []