from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Tool:
    """工具定义"""
    tool_name: str
    description: str
    func: Callable[..., Any]
    parameters: dict[str, str]  # 参数名称和类型描述


class ToolExecutor:
    """ReAct 模式的工具执行器"""

    def __init__(self) -> None:
        self.tools: dict[str, Tool] = {}

    def register_tool(self, tool: Tool) -> None:
        """注册工具"""
        self.tools[tool.tool_name] = tool

    def execute_tool(self, tool_name: str, **kwargs: Any) -> str:
        """执行工具并返回结果"""
        if tool_name not in self.tools:
            return f"错误: 未知工具 {tool_name}"

        tool = self.tools[tool_name]
        try:
            result = tool.func(**kwargs)
            return str(result)
        except Exception as e:
            return f"错误: 执行工具 {tool_name} 时发生异常 - {e}"

    def get_tools_description(self) -> str:
        """返回所有注册工具的描述，供LLM使用"""
        descriptions = []
        for tool in self.tools.values():
            param_desc = ", ".join([f"{name} ({desc})" for name, desc in tool.parameters.items()])
            descriptions.append(f"{tool.tool_name}({param_desc}): {tool.description}")
        return "\n".join(descriptions)

    def get_tools_schema(self, tool_name: str) -> dict[str, Any] | None:
        """返回指定工具的结构化描述，供LLM使用"""
        if tool_name not in self.tools:
            return None

        tool = self.tools[tool_name]
        return {
            "tool_name": tool.tool_name,
            "description": tool.description,
            "parameters": tool.parameters
            }
    