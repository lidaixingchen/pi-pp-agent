from tool_executor import ToolExecutor
from llm import LLM
from prompt import REACT_PROMPT_TEMPLATE


class ReactAgent:
    """ReAct Agent实现类，负责与LLM交互、解析LLM输出、执行工具并生成最终响应。"""

    def __init__(self, llm: LLM, tool_executor: ToolExecutor, max_iterations: int = 10) -> None:
        """初始化ReAct Agent实例，设置LLM和工具执行器。"""
        self.llm = llm
        self.tool_executor = tool_executor
        self.max_iterations = max_iterations
        self.history = []  # 用于存储对话历史
    
    def run(self, question: str) -> str:
        """运行ReAct Agent，处理用户问题并生成最终响应。"""
        self.history = [] # 每次运行前清空历史记录
        for iteration in range(self.max_iterations):
            print(f"\n--- 步 {iteration + 1} ---")
            # 1. 构建提示词
            tools_description = self.tool_executor.get_tools_description()
            history_str = "\n".join(self.history) if self.history else "无"
            prompt = REACT_PROMPT_TEMPLATE.format(
                question=question,
                tools=tools_description,
                history=history_str
            )
            # 2. 调用LLM生成响应
            llm_response = self.llm.generate_response([{"role": "system", "content": prompt}])
            print(f"LLM Response:\n{llm_response}\n")
            if not llm_response:
                return "抱歉，LLM未能生成响应。"
            
            # 3. 解析LLM输出
            thought, action = self.parse_llm_response(llm_response)
            self.history.append(f"Thought: {thought}")
            self.history.append(f"Action: {action}")
            
            # 4. 执行工具或返回最终答案
            if action.startswith("Finish[") and action.endswith("]"):
                final_answer = action[len("Finish["):-1]
                return final_answer
            elif action.startswith("{{") and action.endswith("}}"):
                tool_name, tool_input = self.parse_tool_action(action)
                observation = self.tool_executor.execute_tool(tool_name, query=tool_input)
                self.history.append(f"Observation: {observation}")
            else:
                self.history.append(f"Invalid Action Format: {action}")
        return "抱歉，未能在规定的迭代次数内找到答案。"
    
    def parse_llm_response(self, response: str) -> tuple[str, str]:
        """解析LLM响应，提取Thought和Action。"""
        thought = ""
        action = ""
        lines = response.splitlines()
        for line in lines:
            if line.startswith("Thought:"):
                thought = line[len("Thought:"):].strip()
            elif line.startswith("Action:"):
                action = line[len("Action:"):].strip()
        return thought, action
    
    def parse_tool_action(self, action: str) -> tuple[str, str]:
        """解析工具调用Action，提取工具名称和输入。"""
        try:
            tool_part = action[2:-2]  # 去掉{{和}}
            tool_name, tool_input = tool_part.split("[", 1)
            tool_name = tool_name.strip()
            tool_input = tool_input[:-1].strip()  # 去掉最后的]
            return tool_name, tool_input
        except Exception as e:
            print(f"Error parsing tool action: {e}")
            return "", ""