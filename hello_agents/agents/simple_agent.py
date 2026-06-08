from typing import Optional, Iterator
from core.agent import Agent
from core.message import Message
from core.llm import LLM
from core.config import Config
import re


class SimpleAgent(Agent):
    """一个简单的Agent实现"""
    
    def __init__(
        self,
        name: str,
        llm: LLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        # tool_registry: Optional['ToolRegistry'] = None,
        enable_tool_calling: bool = True
    ):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.enable_tool_calling = enable_tool_calling and tool_registry is not None
        print(f"✅ {name} 初始化完成，工具调用: {'启用' if self.enable_tool_calling else '禁用'}")

    def run(self, input_text: str, max_tool_iterations: int = 3, **kwargs) -> str:
        """
        运行方法 - 实现简单对话逻辑，支持可选工具调用
        """

        # 构建消息列表
        messages = []

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
            print("⚠️ 工具调用已禁用，使用简单对话逻辑")
            response = self.llm.generate_response(messages)
            if response:
                self.add_message(Message(content=input_text, role="user"))
                self.add_message(Message(content=response, role="assistant"))
                return response
            else:
                print("❌ LLM调用失败，未能获取响应")
                return "抱歉，发生了错误。"
            
        # 支持多轮工具调用的逻辑
        return self._run_with_tools(messages, input_text, max_tool_iterations, **kwargs)


    def _get_enhanced_system_prompt(self) -> str:
        """构建增强的系统提示词，包含工具信息"""
        base_prompt = self.system_prompt or "你是一个智能助手，帮助用户解答问题。"
        if self.enable_tool_calling and self.tool_registry:
            tool_info = self.tool_registry.get_tool_descriptions()
            enhanced_prompt = f"{base_prompt}\n\n你可以使用以下工具：\n{tool_info}\n\n当需要使用工具时，请按照格式调用：\n`[TOOL_CALL:{tool_name}:{parameters}]`\n例如:`[TOOL_CALL:search:Python编程]` 或 `[TOOL_CALL:memory:recall=用户信息]`\n请确保工具调用格式正确，并且在调用工具后等待结果返回。"
            return enhanced_prompt
        return base_prompt


    def _run_with_tools(self, messages: list[dict], input_text: str, max_tool_iterations: int, **kwargs) -> str:
        """支持工具调用的运行逻辑，允许多轮工具调用"""
        tool_call_pattern = re.compile(r'\[TOOL_CALL:(\w+):([^\]]+)\]')
        current_messages = messages.copy()
        for iteration in range(max_tool_iterations):
            print(f"\n🔄 迭代 {iteration+1}/{max_tool_iterations} - 生成响应中...")
            response = self.llm.generate_response(current_messages)
            if not response:
                print("❌ LLM调用失败，未能获取响应")
                return "抱歉，发生了错误。"
            print(f"LLM响应: {response}")

            # 检查是否有工具调用
            tool_calls = tool_call_pattern.findall(response)
            if not tool_calls:
                print("✅ 没有检测到工具调用，结束对话")
                self.add_message(Message(content=input_text, role="user"))
                self.add_message(Message(content=response, role="assistant"))
                return response
            
            # 处理每个工具调用
            for tool_name, parameters in tool_calls:
                print(f"🔧 检测到工具调用: {tool_name} with parameters: {parameters}")
                tool_result = self._execute_tool(tool_name, parameters, **kwargs)
                print(f"工具执行结果: {tool_result}")
                # 将工具结果添加到消息列表中，供下一轮生成使用
                current_messages.append({"role": "tool", "content": f"[TOOL_RESULT:{tool_name}:{tool_result}]"})

        print("⚠️ 达到最大工具调用迭代次数，结束对话")
        self.add_message(Message(content=input_text, role="user"))
        self.add_message(Message(content=response, role="assistant"))
        return response