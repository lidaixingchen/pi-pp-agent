"""协议工具包装器

将MCP、A2A、ANP协议封装为可被Agent使用的工具。

Example:
    >>> from hello_agents.tools.builtin import MCPTool, A2ATool, ANPTool
    >>>
    >>> # MCP工具
    >>> mcp_tool = MCPTool(
    ...     name="github",
    ...     server_command=["npx", "-y", "@modelcontextprotocol/server-github"]
    ... )
    >>>
    >>> # A2A工具
    >>> a2a_tool = A2ATool(
    ...     name="researcher",
    ...     server_url="http://localhost:8001"
    ... )
    >>>
    >>> # ANP工具
    >>> anp_tool = ANPTool(
    ...     name="discovery",
    ...     registry_url="http://localhost:8002"
    ... )
"""

import asyncio
from typing import Any, Literal

from ..base import Tool, ToolParameter


class MCPTool(Tool):
    """MCP协议工具包装器

    将MCP服务器封装为Agent可用的工具。

    Example:
        >>> tool = MCPTool(
        ...     name="github",
        ...     server_command=["npx", "-y", "@modelcontextprotocol/server-github"]
        ... )
        >>> result = tool.run({"query": "AI agent"})
    """

    def __init__(
        self,
        name: str,
        description: str | None = None,
        server_command: list[str] | None = None,
        server_url: str | None = None,
        transport: Literal["stdio", "sse", "streamable_http", "websocket", "in_memory"] = "stdio",
        env: dict[str, str] | None = None,
    ) -> None:
        """初始化MCP工具

        Args:
            name: 工具名称
            description: 工具描述（如果为None，从MCP服务器获取）
            server_command: MCP服务器启动命令（stdio模式）
            server_url: MCP服务器URL（sse/websocket模式）
            transport: 传输方式
            env: 环境变量
        """
        super().__init__(name=name, description=description or "MCP协议工具")
        self.server_command = server_command
        self.server_url = server_url
        self.transport = transport
        self.env = env

        self._client: Any = None
        self._tools: list[dict[str, Any]] = []
        self._initialized: bool = False

    def _ensure_initialized(self) -> None:
        """确保MCP客户端已初始化"""
        if self._initialized:
            return

        from ...protocols.mcp import MCPClient

        self._client = MCPClient(
            server_command=self.server_command,
            server_url=self.server_url,
            transport=self.transport,
            env=self.env,
        )

        # 连接并获取工具列表
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环已在运行，使用线程池
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._connect_and_discover())
                    future.result()
            else:
                loop.run_until_complete(self._connect_and_discover())
        except RuntimeError:
            # 没有事件循环
            asyncio.run(self._connect_and_discover())

        self._initialized = True

    async def _connect_and_discover(self) -> None:
        """连接并发现工具"""
        if self._client:
            await self._client.connect()
            self._tools = await self._client.list_tools()

            # 如果没有指定描述，从服务器获取
            if self.description == "MCP协议工具":
                self.description = self._client.get_tool_descriptions()

    def get_parameters(self) -> list[ToolParameter]:
        """获取参数定义

        Returns:
            参数定义列表
        """
        self._ensure_initialized()

        # 从MCP工具列表中提取参数
        if self._tools:
            # 使用第一个工具的参数作为默认
            tool = self._tools[0]
            params = tool.get("parameters", {})

            if isinstance(params, dict) and "properties" in params:
                return [
                    ToolParameter(
                        name=param_name,
                        type=param_info.get("type", "string"),
                        description=param_info.get("description", ""),
                        required=param_name in params.get("required", []),
                    )
                    for param_name, param_info in params["properties"].items()
                ]

        # 默认参数
        return [
            ToolParameter(
                name="input",
                type="string",
                description="输入参数",
                required=True,
            )
        ]

    def run(self, parameters: dict[str, Any]) -> str:
        """执行工具调用

        Args:
            parameters: 调用参数

        Returns:
            执行结果

        Raises:
            RuntimeError: 执行失败
        """
        self._ensure_initialized()

        if not self._client or not self._client.is_connected:
            return "错误: MCP客户端未连接"

        try:
            # 查找匹配的工具
            tool_name = parameters.get("tool_name") or (self._tools[0]["name"] if self._tools else None)

            if not tool_name:
                return "错误: 未指定工具名称"

            # 移除tool_name，其余作为工具参数
            tool_args = {k: v for k, v in parameters.items() if k != "tool_name"}

            # 执行工具调用
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._client.call_tool(tool_name, tool_args)
                    )
                    result = future.result()
            else:
                result = loop.run_until_complete(
                    self._client.call_tool(tool_name, tool_args)
                )

            # 格式化结果
            if isinstance(result, list):
                # MCP返回的是内容列表
                return "\n".join(
                    item.text if hasattr(item, "text") else str(item)
                    for item in result
                )
            return str(result)

        except Exception as e:
            return f"工具执行失败: {e}"

    def close(self) -> None:
        """关闭连接"""
        if self._client and self._client.is_connected:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        executor.submit(asyncio.run, self._client.disconnect())
                else:
                    loop.run_until_complete(self._client.disconnect())
            except Exception:
                pass

        self._initialized = False
        self._client = None

    def __del__(self) -> None:
        """析构函数"""
        self.close()


class A2ATool(Tool):
    """A2A协议工具包装器

    将远程A2A Agent封装为本地可用的工具。

    Example:
        >>> tool = A2ATool(
        ...     name="researcher",
        ...     server_url="http://localhost:8001"
        ... )
        >>> result = tool.run({"message": "帮我分析数据"})
    """

    def __init__(
        self,
        name: str,
        description: str | None = None,
        server_url: str = "http://localhost:8001",
        timeout: float = 30.0,
    ) -> None:
        """初始化A2A工具

        Args:
            name: 工具名称
            description: 工具描述
            server_url: A2A服务器URL
            timeout: 超时时间（秒）
        """
        super().__init__(name=name, description=description or "A2A协议工具")
        self.server_url = server_url
        self.timeout = timeout

        self._client: Any = None
        self._agent_card: Any = None
        self._initialized: bool = False

    def _ensure_initialized(self) -> None:
        """确保A2A客户端已初始化"""
        if self._initialized:
            return

        from ...protocols.a2a import A2AClient

        self._client = A2AClient(
            server_url=self.server_url,
            timeout=self.timeout,
        )

        # 发现远程Agent
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._discover_agent())
                    future.result()
            else:
                loop.run_until_complete(self._discover_agent())
        except RuntimeError:
            asyncio.run(self._discover_agent())

        self._initialized = True

    async def _discover_agent(self) -> None:
        """发现远程Agent"""
        if self._client:
            self._agent_card = await self._client.discover_agent()

            # 如果没有指定描述，从Agent卡片获取
            if self.description == "A2A协议工具" and self._agent_card:
                self.description = f"{self._agent_card.name}: {self._agent_card.description}"

    def get_parameters(self) -> list[ToolParameter]:
        """获取参数定义

        Returns:
            参数定义列表
        """
        return [
            ToolParameter(
                name="message",
                type="string",
                description="发送给Agent的消息",
                required=True,
            ),
            ToolParameter(
                name="task_id",
                type="string",
                description="任务ID（可选）",
                required=False,
                default=None,
            ),
        ]

    def run(self, parameters: dict[str, Any]) -> str:
        """执行工具调用

        Args:
            parameters: 调用参数，必须包含 "message" 字段

        Returns:
            执行结果

        Raises:
            RuntimeError: 执行失败
        """
        self._ensure_initialized()

        if not self._client:
            return "错误: A2A客户端未初始化"

        message = parameters.get("message")
        if not message:
            return "错误: 缺少必需参数 'message'"

        task_id = parameters.get("task_id")

        try:
            # 发送任务
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._client.send_task(message, task_id)
                    )
                    task = future.result()
            else:
                task = loop.run_until_complete(
                    self._client.send_task(message, task_id)
                )

            # 提取响应
            if task.messages:
                # 获取最后一条Agent消息
                agent_messages = [
                    msg for msg in task.messages
                    if msg.get("role") == "agent"
                ]
                if agent_messages:
                    return agent_messages[-1].get("content", "")

            return f"任务 {task.id} 状态: {task.status}"

        except Exception as e:
            return f"A2A调用失败: {e}"


class ANPTool(Tool):
    """ANP协议工具包装器

    用于在ANP网络中发现和调用服务。

    Example:
        >>> tool = ANPTool(
        ...     name="discovery",
        ...     registry_url="http://localhost:8002"
        ... )
        >>> result = tool.run({"action": "discover", "capabilities": ["research"]})
    """

    def __init__(
        self,
        name: str,
        description: str | None = None,
        registry_url: str = "http://localhost:8002",
        timeout: float = 30.0,
    ) -> None:
        """初始化ANP工具

        Args:
            name: 工具名称
            description: 工具描述
            registry_url: ANP注册中心URL
            timeout: 超时时间（秒）
        """
        super().__init__(name=name, description=description or "ANP服务发现工具")
        self.registry_url = registry_url
        self.timeout = timeout

        self._client: Any = None
        self._initialized: bool = False

    def _ensure_initialized(self) -> None:
        """确保ANP客户端已初始化"""
        if self._initialized:
            return

        from ...protocols.anp import ANPClient

        self._client = ANPClient(
            registry_url=self.registry_url,
            timeout=self.timeout,
        )

        self._initialized = True

    def get_parameters(self) -> list[ToolParameter]:
        """获取参数定义

        Returns:
            参数定义列表
        """
        return [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型: discover（发现服务）, get（获取服务详情）",
                required=True,
            ),
            ToolParameter(
                name="service_id",
                type="string",
                description="服务ID（get操作必需）",
                required=False,
                default=None,
            ),
            ToolParameter(
                name="capabilities",
                type="array",
                description="能力过滤列表（discover操作可选）",
                required=False,
                default=None,
            ),
        ]

    def run(self, parameters: dict[str, Any]) -> str:
        """执行工具调用

        Args:
            parameters: 调用参数

        Returns:
            执行结果

        Raises:
            RuntimeError: 执行失败
        """
        self._ensure_initialized()

        if not self._client:
            return "错误: ANP客户端未初始化"

        action = parameters.get("action", "discover")

        try:
            if action == "discover":
                capabilities = parameters.get("capabilities")
                return self._discover_services(capabilities)
            elif action == "get":
                service_id = parameters.get("service_id")
                if not service_id:
                    return "错误: get操作需要 service_id 参数"
                return self._get_service(service_id)
            else:
                return f"错误: 不支持的操作 '{action}'"

        except Exception as e:
            return f"ANP操作失败: {e}"

    def _discover_services(self, capabilities: list[str] | None = None) -> str:
        """发现服务"""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self._client.discover_services(capabilities)
                )
                services = future.result()
        else:
            services = loop.run_until_complete(
                self._client.discover_services(capabilities)
            )

        if not services:
            return "未发现匹配的服务"

        # 格式化结果
        result_lines = ["发现以下服务:\n"]
        for service in services:
            result_lines.append(f"- {service.name} (ID: {service.service_id})")
            result_lines.append(f"  描述: {service.description}")
            result_lines.append(f"  端点: {service.endpoint}")
            result_lines.append(f"  能力: {', '.join(service.capabilities)}")
            result_lines.append(f"  状态: {service.status}")
            result_lines.append("")

        return "\n".join(result_lines)

    def _get_service(self, service_id: str) -> str:
        """获取服务详情"""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self._client.get_service(service_id)
                )
                service = future.result()
        else:
            service = loop.run_until_complete(
                self._client.get_service(service_id)
            )

        return (
            f"服务详情:\n"
            f"  名称: {service.name}\n"
            f"  描述: {service.description}\n"
            f"  端点: {service.endpoint}\n"
            f"  能力: {', '.join(service.capabilities)}\n"
            f"  状态: {service.status}\n"
            f"  版本: {service.version}"
        )
