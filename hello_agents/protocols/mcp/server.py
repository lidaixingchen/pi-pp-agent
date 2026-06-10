"""MCP协议服务器，封装FastMCP

提供简洁的装饰器API来注册工具和资源。
"""

from typing import Any, Callable, Literal


class MCPServer:
    """MCP协议服务器

    封装FastMCP，提供简洁的装饰器API。

    Example:
        >>> server = MCPServer(name="My Tools Server")
        >>>
        >>> @server.tool()
        ... def search(query: str) -> str:
        ...     '''搜索互联网'''
        ...     return f"搜索结果: {query}"
        >>>
        >>> @server.resource("file://documents/{path}")
        ... def get_document(path: str) -> str:
        ...     '''获取文档内容'''
        ...     with open(path) as f:
        ...         return f.read()
        >>>
        >>> server.run()
    """

    def __init__(
        self,
        name: str = "HelloAgents MCP Server",
        description: str = "一个基于FastMCP的MCP协议服务器",
        transport: Literal["stdio", "sse", "streamable_http"] = "stdio",
        host: str = "0.0.0.0",
        port: int = 8000,
    ) -> None:
        """初始化MCP服务器

        Args:
            name: 服务器名称
            description: 服务器描述
            transport: 传输方式
            host: 监听地址（sse/streamable_http模式）
            port: 监听端口（sse/streamable_http模式）
        """
        self.name = name
        self.description = description
        self.transport = transport
        self.host = host
        self.port = port

        self._tools: dict[str, dict[str, Any]] = {}
        self._resources: dict[str, dict[str, Any]] = {}
        self._fastmcp: Any = None

        # 检查依赖
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """检查必要的依赖是否已安装"""
        try:
            from mcp.server.fastmcp import FastMCP
            self._has_fastmcp = True
        except ImportError:
            self._has_fastmcp = False

    def _get_fastmcp(self) -> Any:
        """获取FastMCP实例（懒加载）"""
        if not self._has_fastmcp:
            raise ImportError(
                "MCP服务器需要 mcp SDK。请运行: pip install 'hello_agents[mcp]'"
            )

        if self._fastmcp is None:
            from mcp.server.fastmcp import FastMCP
            self._fastmcp = FastMCP(
                self.name,
                host=self.host,
                port=self.port,
            )

            # 注册已定义的工具
            for tool_name, tool_info in self._tools.items():
                self._fastmcp.tool()(tool_info["func"])

            # 注册已定义的资源
            for uri, resource_info in self._resources.items():
                self._fastmcp.resource(uri)(resource_info["func"])

        return self._fastmcp

    def tool(self, name: str | None = None, description: str | None = None) -> Callable:
        """装饰器：注册工具

        Args:
            name: 工具名称（默认使用函数名）
            description: 工具描述（默认使用函数docstring）

        Returns:
            装饰器函数

        Example:
            >>> @server.tool()
            ... def search(query: str) -> str:
            ...     '''搜索互联网'''
            ...     return f"搜索结果: {query}"
            >>>
            >>> @server.tool(name="custom_name", description="自定义描述")
            ... def my_func(input: str) -> str:
            ...     return input
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or ""

            # 保存工具信息
            self._tools[tool_name] = {
                "func": func,
                "name": tool_name,
                "description": tool_desc,
            }

            # 如果FastMCP已初始化，直接注册
            if self._fastmcp is not None:
                self._fastmcp.tool()(func)

            return func

        return decorator

    def resource(self, uri: str, name: str | None = None, description: str | None = None) -> Callable:
        """装饰器：注册资源

        Args:
            uri: 资源URI（支持模板参数，如 "file://documents/{path}"）
            name: 资源名称
            description: 资源描述

        Returns:
            装饰器函数

        Example:
            >>> @server.resource("file://documents/{path}")
            ... def get_document(path: str) -> str:
            ...     '''获取文档内容'''
            ...     with open(path) as f:
            ...         return f.read()
        """
        def decorator(func: Callable) -> Callable:
            resource_name = name or func.__name__
            resource_desc = description or func.__doc__ or ""

            # 保存资源信息
            self._resources[uri] = {
                "func": func,
                "name": resource_name,
                "description": resource_desc,
                "uri": uri,
            }

            # 如果FastMCP已初始化，直接注册
            if self._fastmcp is not None:
                self._fastmcp.resource(uri)(func)

            return func

        return decorator

    def run(self) -> None:
        """启动服务器

        根据传输方式选择不同的启动方式：
        - stdio: 标准输入/输出
        - sse: HTTP Server-Sent Events
        - streamable_http: 可流式HTTP
        """
        fastmcp = self._get_fastmcp()

        if self.transport == "stdio":
            fastmcp.run(transport="stdio")
        elif self.transport == "sse":
            fastmcp.run(transport="sse")
        elif self.transport == "streamable_http":
            fastmcp.run(transport="streamable_http")
        else:
            raise ValueError(f"不支持的传输方式: {self.transport}")

    def get_tool_list(self) -> list[dict[str, Any]]:
        """获取已注册的工具列表

        Returns:
            工具信息列表
        """
        return [
            {
                "name": info["name"],
                "description": info["description"],
            }
            for info in self._tools.values()
        ]

    def get_resource_list(self) -> list[dict[str, Any]]:
        """获取已注册的资源列表

        Returns:
            资源信息列表
        """
        return [
            {
                "uri": info["uri"],
                "name": info["name"],
                "description": info["description"],
            }
            for info in self._resources.values()
        ]
    
    def add_tool(self, func: Callable, name: str | None = None, description: str | None = None) -> None:
        """动态添加工具

        Args:
            func: 工具函数
            name: 工具名称
            description: 工具描述
        """
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or ""

        # 保存工具信息
        self._tools[tool_name] = {
            "func": func,
            "name": tool_name,
            "description": tool_desc,
        }

        # 如果FastMCP已初始化，直接注册
        if self._fastmcp is not None:
            self._fastmcp.tool()(func)
