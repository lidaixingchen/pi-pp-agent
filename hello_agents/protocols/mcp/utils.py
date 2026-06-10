"""MCP协议工具函数"""

from typing import Any


def create_context(
    tools: list[dict[str, Any]] | None = None,
    resources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """创建MCP上下文

    Args:
        tools: 工具列表，每个工具包含 name, description, parameters 等信息
        resources: 资源列表，每个资源包含 uri, name, description 等信息

    Returns:
        MCP上下文字典

    Example:
        >>> context = create_context(
        ...     tools=[{"name": "search", "description": "搜索工具"}],
        ...     resources=[{"uri": "file://doc.txt", "name": "文档"}]
        ... )
    """
    return {
        "tools": tools or [],
        "resources": resources or [],
    }


def parse_context(context: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """解析MCP上下文

    Args:
        context: MCP上下文字典

    Returns:
        (tools, resources) 元组

    Example:
        >>> tools, resources = parse_context(context)
    """
    tools = context.get("tools", [])
    resources = context.get("resources", [])
    return tools, resources


def format_tool_descriptions(tools: list[dict[str, Any]]) -> str:
    """格式化工具描述为可读字符串

    Args:
        tools: 工具列表

    Returns:
        格式化的工具描述字符串
    """
    if not tools:
        return "暂无可用工具"

    descriptions: list[str] = []
    for tool in tools:
        name = tool.get("name", "unknown")
        desc = tool.get("description", "无描述")
        descriptions.append(f"- {name}: {desc}")

    return "\n".join(descriptions)


def validate_tool_call(tool_name: str, arguments: dict[str, Any], tools: list[dict[str, Any]]) -> bool:
    """验证工具调用是否有效

    Args:
        tool_name: 工具名称
        arguments: 调用参数
        tools: 可用工具列表

    Returns:
        是否有效
    """
    for tool in tools:
        if tool.get("name") == tool_name:
            return True
    return False
