"""HelloAgents 自定义异常"""


class HelloAgentsError(Exception):
    """HelloAgents 基础异常"""


class LLMError(HelloAgentsError):
    """LLM 调用相关异常"""


class ToolError(HelloAgentsError):
    """工具执行相关异常"""


class ToolNotFoundError(ToolError):
    """工具未找到"""

    def __init__(self, tool_name: str):
        super().__init__(f"未找到工具: {tool_name}")
        self.tool_name = tool_name


class ToolExecutionError(ToolError):
    """工具执行失败"""

    def __init__(self, tool_name: str, reason: str):
        super().__init__(f"工具 '{tool_name}' 执行失败: {reason}")
        self.tool_name = tool_name
        self.reason = reason


class ConfigError(HelloAgentsError):
    """配置相关异常"""


class AgentError(HelloAgentsError):
    """Agent 运行相关异常"""
