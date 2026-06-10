"""MCP协议客户端，支持多种传输方式

支持的传输方式：
- stdio: 标准输入/输出（本地进程）
- sse: Server-Sent Events（HTTP长连接）
- streamable_http: 可流式HTTP
- websocket: WebSocket
- in_memory: 内存传输（测试用）
"""

import asyncio
from typing import Any, Literal

from .utils import format_tool_descriptions, validate_tool_call


class MCPClient:
    """MCP协议客户端

    支持5种传输方式与MCP服务器通信。

    Example:
        >>> client = MCPClient(
        ...     server_command=["npx", "-y", "@modelcontextprotocol/server-github"],
        ...     transport="stdio"
        ... )
        >>> await client.connect()
        >>> tools = await client.list_tools()
        >>> result = await client.call_tool("search", {"query": "hello"})
        >>> await client.disconnect()
    """

    def __init__(
        self,
        server_command: list[str] | None = None,
        server_url: str | None = None,
        transport: Literal["stdio", "sse", "streamable_http", "websocket", "in_memory"] = "stdio",
        env: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        """初始化MCP客户端

        Args:
            server_command: 服务器启动命令（stdio模式）
            server_url: 服务器URL（sse/websocket模式）
            transport: 传输方式
            env: 环境变量
            timeout: 超时时间（秒）
        """
        self.server_command = server_command
        self.server_url = server_url
        self.transport = transport
        self.env = env or {}
        self.timeout = timeout

        self._connected: bool = False
        self._process: Any = None
        self._session: Any = None
        self._tools: list[dict[str, Any]] = []
        self._resources: list[dict[str, Any]] = []

        # 检查依赖
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """检查必要的依赖是否已安装"""
        if self.transport == "stdio":
            # stdio 不需要额外依赖
            pass
        elif self.transport in ("sse", "streamable_http"):
            try:
                import httpx  # noqa: F401
            except ImportError:
                raise ImportError(
                    f"传输方式 '{self.transport}' 需要 httpx。"
                    f"请运行: pip install 'hello_agents[mcp]'"
                )
        elif self.transport == "websocket":
            try:
                import websockets  # noqa: F401
            except ImportError:
                raise ImportError(
                    "传输方式 'websocket' 需要 websockets。"
                    "请运行: pip install 'hello_agents[mcp]'"
                )

    async def connect(self) -> None:
        """连接到MCP服务器

        Raises:
            ConnectionError: 连接失败
            ValueError: 配置错误
        """
        if self._connected:
            return

        try:
            if self.transport == "stdio":
                await self._connect_stdio()
            elif self.transport == "sse":
                await self._connect_sse()
            elif self.transport == "streamable_http":
                await self._connect_streamable_http()
            elif self.transport == "websocket":
                await self._connect_websocket()
            elif self.transport == "in_memory":
                await self._connect_in_memory()
            else:
                raise ValueError(f"不支持的传输方式: {self.transport}")

            self._connected = True

            # 获取可用工具和资源
            await self._discover_capabilities()

        except Exception as e:
            raise ConnectionError(f"连接MCP服务器失败: {e}") from e

    async def _connect_stdio(self) -> None:
        """通过stdio连接"""
        if not self.server_command:
            raise ValueError("stdio模式需要提供 server_command")

        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            server_params = StdioServerParameters(
                command=self.server_command[0],
                args=self.server_command[1:],
                env=self.env if self.env else None,
            )

            # 创建stdio客户端
            self._stdio_context = stdio_client(server_params)
            streams = await self._stdio_context.__aenter__()  # type: ignore[func-returns-value]
            read_stream, write_stream = streams[0], streams[1]

            # 创建会话
            self._session_context = ClientSession(read_stream, write_stream)
            self._session = await self._session_context.__aenter__()

            # 初始化
            await self._session.initialize()

        except ImportError:
            # 如果没有 mcp SDK，使用简化的子进程方式
            await self._connect_stdio_fallback()

    async def _connect_stdio_fallback(self) -> None:
        """stdio连接的备用方案（不依赖mcp SDK）"""
        import subprocess

        if not self.server_command:
            raise ValueError("stdio模式需要提供 server_command")

        self._process = subprocess.Popen(
            self.server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.env if self.env else None,
            text=True,
        )

    async def _connect_sse(self) -> None:
        """通过SSE连接"""
        if not self.server_url:
            raise ValueError("SSE模式需要提供 server_url")

        try:
            from mcp import ClientSession
            from mcp.client.sse import sse_client

            self._sse_context = sse_client(self.server_url)
            streams = await self._sse_context.__aenter__()  # type: ignore[func-returns-value]
            read_stream, write_stream = streams[0], streams[1]

            self._session_context = ClientSession(read_stream, write_stream)
            self._session = await self._session_context.__aenter__()

            await self._session.initialize()

        except ImportError:
            raise ImportError(
                "SSE传输需要 mcp SDK。请运行: pip install 'hello_agents[mcp]'"
            )

    async def _connect_streamable_http(self) -> None:
        """通过可流式HTTP连接"""
        if not self.server_url:
            raise ValueError("streamable_http模式需要提供 server_url")

        try:
            from mcp import ClientSession
            from mcp.client.streamable_http import streamable_http_client

            self._http_context = streamable_http_client(self.server_url)
            # streamable_http_client 返回 (read_stream, write_stream, get_session_id)
            streams = await self._http_context.__aenter__()  # type: ignore[func-returns-value]
            read_stream, write_stream = streams[0], streams[1]
            self._get_session_id = streams[2] if len(streams) > 2 else None

            self._session_context = ClientSession(read_stream, write_stream)
            self._session = await self._session_context.__aenter__()

            await self._session.initialize()

        except ImportError:
            raise ImportError(
                "streamable_http传输需要 mcp SDK。请运行: pip install 'hello_agents[mcp]'"
            )

    async def _connect_websocket(self) -> None:
        """通过WebSocket连接"""
        if not self.server_url:
            raise ValueError("websocket模式需要提供 server_url")

        try:
            import websockets

            self._ws = await websockets.connect(self.server_url)

        except ImportError:
            raise ImportError(
                "WebSocket传输需要 websockets。请运行: pip install 'hello_agents[mcp]'"
            )

    async def _connect_in_memory(self) -> None:
        """内存连接（用于测试）"""
        # 内存模式不需要实际连接
        pass

    async def disconnect(self) -> None:
        """断开连接"""
        if not self._connected:
            return

        try:
            # 清理会话
            if hasattr(self, "_session_context") and self._session_context:
                await self._session_context.__aexit__(None, None, None)

            # 清理传输层
            if self.transport == "stdio" and hasattr(self, "_stdio_context"):
                await self._stdio_context.__aexit__(None, None, None)
            elif self.transport == "sse" and hasattr(self, "_sse_context"):
                await self._sse_context.__aexit__(None, None, None)
            elif self.transport == "streamable_http" and hasattr(self, "_http_context"):
                await self._http_context.__aexit__(None, None, None)
            elif self.transport == "websocket" and hasattr(self, "_ws"):
                await self._ws.close()
            elif self.transport == "stdio" and hasattr(self, "_process") and self._process:
                self._process.terminate()

        except Exception:
            pass

        finally:
            self._connected = False
            self._session = None
            self._tools = []
            self._resources = []

    async def _discover_capabilities(self) -> None:
        """发现服务器能力（工具和资源）"""
        if not self._session:
            return

        try:
            # 获取工具列表
            tools_result = await self._session.list_tools()
            self._tools = [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema if hasattr(tool, "inputSchema") else {},
                }
                for tool in tools_result.tools
            ]

            # 获取资源列表
            try:
                resources_result = await self._session.list_resources()
                self._resources = [
                    {
                        "uri": resource.uri,
                        "name": resource.name,
                        "description": resource.description or "",
                    }
                    for resource in resources_result.resources
                ]
            except Exception:
                # 某些服务器可能不支持资源
                self._resources = []

        except Exception as e:
            raise ConnectionError(f"获取服务器能力失败: {e}") from e

    async def list_tools(self) -> list[dict[str, Any]]:
        """列出可用工具

        Returns:
            工具列表

        Example:
            >>> tools = await client.list_tools()
            >>> for tool in tools:
            ...     print(f"{tool['name']}: {tool['description']}")
        """
        if not self._connected:
            raise ConnectionError("未连接到服务器，请先调用 connect()")

        return self._tools.copy()

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """调用工具

        Args:
            name: 工具名称
            arguments: 调用参数

        Returns:
            工具执行结果

        Raises:
            ToolNotFoundError: 工具不存在
            ToolExecutionError: 工具执行失败

        Example:
            >>> result = await client.call_tool("search", {"query": "hello"})
        """
        if not self._connected:
            raise ConnectionError("未连接到服务器，请先调用 connect()")

        if not validate_tool_call(name, arguments, self._tools):
            raise ValueError(f"工具不存在: {name}")

        try:
            if self._session:
                result = await self._session.call_tool(name, arguments)
                return result.content if hasattr(result, "content") else result
            else:
                # 备用方案
                return {"error": "会话未建立"}

        except Exception as e:
            raise RuntimeError(f"工具 '{name}' 执行失败: {e}") from e

    async def list_resources(self) -> list[dict[str, Any]]:
        """列出可用资源

        Returns:
            资源列表
        """
        if not self._connected:
            raise ConnectionError("未连接到服务器，请先调用 connect()")

        return self._resources.copy()

    async def read_resource(self, uri: str) -> str:
        """读取资源

        Args:
            uri: 资源URI

        Returns:
            资源内容

        Example:
            >>> content = await client.read_resource("file://document.txt")
        """
        if not self._connected:
            raise ConnectionError("未连接到服务器，请先调用 connect()")

        try:
            if self._session:
                result = await self._session.read_resource(uri)
                return result.contents[0].text if result.contents else ""
            else:
                return ""

        except Exception as e:
            raise RuntimeError(f"读取资源 '{uri}' 失败: {e}") from e

    def get_tool_descriptions(self) -> str:
        """获取工具描述（用于注入提示词）

        Returns:
            格式化的工具描述字符串

        Example:
            >>> print(client.get_tool_descriptions())
            - search: 搜索互联网信息
            - weather: 查询天气
        """
        return format_tool_descriptions(self._tools)

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected

    @property
    def tools(self) -> list[dict[str, Any]]:
        """获取工具列表（只读）"""
        return self._tools.copy()

    @property
    def resources(self) -> list[dict[str, Any]]:
        """获取资源列表（只读）"""
        return self._resources.copy()

    async def __aenter__(self) -> "MCPClient":
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """异步上下文管理器出口"""
        await self.disconnect()
