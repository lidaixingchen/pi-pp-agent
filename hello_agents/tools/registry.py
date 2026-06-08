from typing import Any, Callable, Optional

from .base import Tool


class ToolRegistry:
    """HelloAgents 工具注册表"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._functions: dict[str, dict[str, Any]] = {}

    def register_tool(self, tool: Tool) -> None:
        """注册 Tool 对象"""
        if tool.name in self._tools:
            print(f"⚠️ 警告:工具 '{tool.name}' 已存在，将被覆盖。")
        self._tools[tool.name] = tool
        print(f"✅ 工具 '{tool.name}' 已注册。")

    def register_function(
        self,
        name: str,
        description: str,
        func: Callable[[str], str],
    ) -> None:
        """
        直接注册函数作为工具（简便方式）

        Args:
            name: 工具名称
            description: 工具描述
            func: 工具函数，接受字符串参数，返回字符串结果
        """
        if name in self._functions:
            print(f"⚠️ 警告:工具 '{name}' 已存在，将被覆盖。")

        self._functions[name] = {
            "description": description,
            "func": func,
        }
        print(f"✅ 工具 '{name}' 已注册。")

    def get_tool(self, name: str) -> Optional[Tool]:
        """根据名称获取 Tool 对象"""
        return self._tools.get(name)

    def get_tool_descriptions(self) -> str:
        """获取所有可用工具的格式化描述字符串"""
        descriptions: list[str] = []

        # Tool 对象描述
        for tool in self._tools.values():
            descriptions.append(f"- {tool.name}: {tool.description}")

        # 函数工具描述
        for name, info in self._functions.items():
            descriptions.append(f"- {name}: {info['description']}")

        return "\n".join(descriptions) if descriptions else "暂无可用工具"

    def execute_tool(self, name: str, parameters: str) -> str:
        """执行已注册的工具"""
        # 优先查找 Tool 对象
        if name in self._tools:
            return self._tools[name].run({"input": parameters})

        # 再查找函数工具
        if name in self._functions:
            return self._functions[name]["func"](parameters)

        return f"❌ 未找到工具: {name}"

    def list_tools(self) -> list[str]:
        """列出所有已注册的工具名称"""
        return list(self._tools.keys()) + list(self._functions.keys())
