"""简单 Agent 实现"""
import re
from typing import Optional

from ..core.agent import Agent
from ..core.config import Config
from ..core.llm import LLM
from ..core.message import Message
from ..tools.base import Tool
from ..tools.registry import ToolRegistry


class SimpleAgent(Agent):
    """一个简单的 Agent 实现，支持可选的工具调用"""

    def __init__(
        self,
        name: str,
        llm: LLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        tool_registry: Optional[ToolRegistry] = None,
        enable_tool_calling: bool = True,
    ):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.enable_tool_calling = enable_tool_calling and tool_registry is not None
        print(f"✅ {name} 初始化完成，工具调用: {'启用' if self.enable_tool_calling else '禁用'}")

    def add_tool(self, tool: Tool) -> None:
        """添加工具到Agent

        Args:
            tool: 工具实例（如 MCPTool, A2ATool 等）

        Example:
            >>> agent = SimpleAgent(name="助手", llm=llm)
            >>> mcp_tool = MCPTool(name="github", server_command=[...])
            >>> agent.add_tool(mcp_tool)
        """
        # 如果没有工具注册表，创建一个
        if self.tool_registry is None:
            self.tool_registry = ToolRegistry()

        # 注册工具
        self.tool_registry.register_tool(tool)

        # 启用工具调用
        self.enable_tool_calling = True
        print(f"✅ 工具 '{tool.name}' 已添加到 {self.name}")

    def run(self, input_text: str, max_tool_iterations: int = 3, **kwargs) -> str:
        """运行方法 - 实现简单对话逻辑，支持可选工具调用"""

        # 构建消息列表
        messages: list[dict[str, str]] = []

        # 添加系统消息（可能包含工具信息）
        enhanced_system_prompt = self._get_enhanced_system_prompt()
        messages.append({"role": "system", "content": enhanced_system_prompt})

        # 添加历史消息
        for msg in self.get_history():
            messages.append(msg.to_dict())

        # 添加用户输入
        messages.append({"role": "user", "content": input_text})

        # 如果没有启用工具调用，使用简单对话逻辑
        if not self.enable_tool_calling:
            response = self.llm.generate_response(messages)
            if response:
                self.add_message(Message(content=input_text, role="user"))
                self.add_message(Message(content=response, role="assistant"))
                return response
            print("❌ LLM 调用失败，未能获取响应")
            return "抱歉，发生了错误。"

        # 支持多轮工具调用的逻辑
        return self._run_with_tools(messages, input_text, max_tool_iterations)

    def _get_enhanced_system_prompt(self) -> str:
        """构建增强的系统提示词，包含工具信息"""
        base_prompt = self.system_prompt or "你是一个智能助手，帮助用户解答问题。"
        if self.enable_tool_calling and self.tool_registry:
            tool_info = self.tool_registry.get_tool_descriptions()
            enhanced_prompt = (
                f"{base_prompt}\n\n"
                f"你可以使用以下工具：\n{tool_info}\n\n"
                "当需要使用工具时，请按照格式调用：\n"
                "`[TOOL_CALL:工具名:参数]`\n"
                "例如:`[TOOL_CALL:search:Python编程]`\n"
                "请确保工具调用格式正确，并且在调用工具后等待结果返回。"
            )
            return enhanced_prompt
        return base_prompt

    def _run_with_tools(
        self,
        messages: list[dict[str, str]],
        input_text: str,
        max_tool_iterations: int,
    ) -> str:
        """支持工具调用的运行逻辑，允许多轮工具调用"""
        tool_call_pattern = re.compile(r"\[TOOL_CALL:(\w+):([^\]]+)\]")
        current_messages = messages.copy()
        response = ""

        for iteration in range(max_tool_iterations):
            print(f"\n🔄 迭代 {iteration + 1}/{max_tool_iterations} - 生成响应中...")
            response = self.llm.generate_response(current_messages)
            if not response:
                print("❌ LLM 调用失败，未能获取响应")
                return "抱歉，发生了错误。"
            print(f"LLM 响应: {response}")

            # 检查是否有工具调用
            tool_calls = tool_call_pattern.findall(response)
            if not tool_calls:
                print("✅ 没有检测到工具调用，结束对话")
                break

            # 处理每个工具调用
            for tool_name, parameters in tool_calls:
                print(f"🔧 检测到工具调用: {tool_name} with parameters: {parameters}")
                tool_result = self._execute_tool(tool_name, parameters)
                print(f"工具执行结果: {tool_result}")
                # 将工具结果添加到消息列表中，供下一轮生成使用
                current_messages.append({
                    "role": "user",
                    "content": f"[TOOL_RESULT:{tool_name}:{tool_result}]",
                })
        else:
            print("⚠️ 达到最大工具调用迭代次数，结束对话")

        # 记录对话历史
        self.add_message(Message(content=input_text, role="user"))
        self.add_message(Message(content=response, role="assistant"))
        return response

    def _execute_tool(self, tool_name: str, parameters: str) -> str:
        """执行工具调用"""
        if not self.tool_registry:
            print("❌ 工具注册表未提供，无法执行工具调用")
            return "工具调用失败：工具注册表未提供"

        try:
            # 智能参数解析
            if tool_name == "calculator":
                # 计算器工具直接传入表达式
                result = self.tool_registry.execute_tool(tool_name, parameters)
            else:
                # 其他工具使用智能参数解析
                param_dict = self._parse_tool_parameters(tool_name, parameters)
                tool = self.tool_registry.get_tool(tool_name)
                if not tool:
                    return f"❌ 错误:未找到工具 '{tool_name}'"
                result = tool.run(param_dict)

            return f"🔧 工具 {tool_name} 执行结果:\n{result}"

        except Exception as e:
            return f"❌ 工具调用失败:{e}"

    def _parse_tool_parameters(self, tool_name: str, parameters: str) -> dict[str, str]:
        """智能解析工具参数，支持多种格式"""
        param_dict: dict[str, str] = {}

        if "=" in parameters:
            # 格式: key=value 或 action=search,query=Python
            if "," in parameters:
                # 多个参数: action=search,query=Python,limit=3
                for pair in parameters.split(","):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        param_dict[key.strip()] = value.strip()
            else:
                # 单个参数: key=value
                key, value = parameters.split("=", 1)
                param_dict[key.strip()] = value.strip()
        else:
            # 直接传入参数，根据工具类型智能推断
            if tool_name == "search":
                param_dict = {"query": parameters}
            elif tool_name == "memory":
                param_dict = {"action": "search", "query": parameters}
            else:
                param_dict = {"input": parameters}

        return param_dict
