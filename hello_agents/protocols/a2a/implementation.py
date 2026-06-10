"""A2A协议实现（Agent-to-Agent Protocol）

A2A是Google提出的Agent间通信协议，用于实现多Agent协作。

核心概念：
- AgentCard: 描述Agent的能力和端点
- Task: Agent间的任务通信
- Message: 任务中的消息交换

本模块提供两种实现：
1. 基于a2a-sdk的完整实现（如果已安装）
2. 简化的HTTP REST实现（备用）
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class A2AAgentCard:
    """Agent卡片，描述Agent能力

    Example:
        >>> card = A2AAgentCard(
        ...     name="Research Agent",
        ...     description="专门进行研究的Agent",
        ...     url="http://localhost:8001",
        ...     skills=[{"name": "research", "description": "研究能力"}]
        ... )
    """
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    skills: list[dict[str, Any]] = field(default_factory=list)
    capabilities: dict[str, Any] = field(default_factory=dict)
    authentication: dict[str, Any] | None = None


@dataclass
class A2ATask:
    """A2A任务

    Example:
        >>> task = A2ATask(
        ...     id="task-001",
        ...     status="submitted",
        ...     messages=[{"role": "user", "content": "帮我分析数据"}]
        ... )
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "submitted"  # submitted, working, completed, failed
    messages: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class A2AServer:
    """A2A协议服务器

    提供Agent注册和任务处理功能。

    Example:
        >>> card = A2AAgentCard(
        ...     name="My Agent",
        ...     description="一个示例Agent",
        ...     url="http://localhost:8001"
        ... )
        >>> server = A2AServer(agent_card=card)
        >>>
        >>> @server.task_handler("research")
        ... async def handle_research(task: A2ATask) -> A2ATask:
        ...     # 处理研究任务
        ...     task.status = "completed"
        ...     task.messages.append({"role": "agent", "content": "研究完成"})
        ...     return task
        >>>
        >>> server.run()
    """

    def __init__(
        self,
        agent_card: A2AAgentCard,
        host: str = "0.0.0.0",
        port: int = 8001,
    ) -> None:
        """初始化A2A服务器

        Args:
            agent_card: Agent卡片
            host: 监听地址
            port: 监听端口
        """
        self.agent_card = agent_card
        self.host = host
        self.port = port

        self._task_handlers: dict[str, Callable] = {}
        self._tasks: dict[str, A2ATask] = {}

        # 检查依赖
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """检查必要的依赖是否已安装"""
        try:
            import fastapi  # noqa: F401
            self._has_fastapi = True
        except ImportError:
            self._has_fastapi = False

    def task_handler(self, method: str) -> Callable:
        """装饰器：注册任务处理器

        Args:
            method: 任务方法名

        Returns:
            装饰器函数

        Example:
            >>> @server.task_handler("research")
            ... async def handle_research(task: A2ATask) -> A2ATask:
            ...     task.status = "completed"
            ...     return task
        """
        def decorator(func: Callable) -> Callable:
            self._task_handlers[method] = func
            return func
        return decorator

    def _create_app(self) -> Any:
        """创建FastAPI应用"""
        if not self._has_fastapi:
            raise ImportError(
                "A2A服务器需要 fastapi。请运行: pip install 'hello_agents[a2a]'"
            )

        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel

        app = FastAPI(title=self.agent_card.name)

        class TaskRequest(BaseModel):
            message: str
            task_id: str | None = None
            context_id: str | None = None
            metadata: dict[str, Any] = {}

        class TaskResponse(BaseModel):
            task_id: str
            status: str
            messages: list[dict[str, Any]]
            artifacts: list[dict[str, Any]]

        @app.get("/.well-known/agent.json")
        async def get_agent_card() -> dict[str, Any]:
            """返回Agent卡片"""
            return {
                "name": self.agent_card.name,
                "description": self.agent_card.description,
                "url": self.agent_card.url,
                "version": self.agent_card.version,
                "skills": self.agent_card.skills,
                "capabilities": self.agent_card.capabilities,
            }

        @app.post("/tasks/send")
        async def send_task(request: TaskRequest) -> TaskResponse:
            """发送任务"""
            task_id = request.task_id or str(uuid.uuid4())

            # 创建任务
            task = A2ATask(
                id=task_id,
                status="submitted",
                messages=[{"role": "user", "content": request.message}],
                metadata=request.metadata,
            )

            self._tasks[task_id] = task

            # 查找并执行处理器
            # 默认使用第一个注册的处理器，或根据消息内容匹配
            handler = None
            for method, h in self._task_handlers.items():
                handler = h
                break

            if handler:
                try:
                    task.status = "working"
                    task = await handler(task)
                except Exception as e:
                    task.status = "failed"
                    task.messages.append({"role": "system", "content": f"错误: {e}"})
            else:
                task.status = "completed"
                task.messages.append({
                    "role": "agent",
                    "content": f"收到任务: {request.message}"
                })

            return TaskResponse(
                task_id=task.id,
                status=task.status,
                messages=task.messages,
                artifacts=task.artifacts,
            )

        @app.get("/tasks/{task_id}")
        async def get_task(task_id: str) -> TaskResponse:
            """获取任务状态"""
            if task_id not in self._tasks:
                raise HTTPException(status_code=404, detail="任务不存在")

            task = self._tasks[task_id]
            return TaskResponse(
                task_id=task.id,
                status=task.status,
                messages=task.messages,
                artifacts=task.artifacts,
            )

        return app

    def run(self) -> None:
        """启动服务器"""
        if not self._has_fastapi:
            raise ImportError(
                "A2A服务器需要 fastapi 和 uvicorn。"
                "请运行: pip install 'hello_agents[a2a]'"
            )

        import uvicorn

        app = self._create_app()
        uvicorn.run(app, host=self.host, port=self.port)


class A2AClient:
    """A2A协议客户端

    用于与远程Agent通信。

    Example:
        >>> client = A2AClient("http://localhost:8001")
        >>> card = await client.discover_agent()
        >>> task = await client.send_task("帮我分析数据")
    """

    def __init__(self, server_url: str, timeout: float = 30.0) -> None:
        """初始化A2A客户端

        Args:
            server_url: 服务器URL
            timeout: 超时时间（秒）
        """
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout

        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """检查必要的依赖是否已安装"""
        try:
            import httpx  # noqa: F401
            self._has_httpx = True
        except ImportError:
            self._has_httpx = False

    async def discover_agent(self) -> A2AAgentCard:
        """发现远程Agent

        Returns:
            Agent卡片

        Raises:
            ConnectionError: 连接失败
        """
        if not self._has_httpx:
            raise ImportError(
                "A2A客户端需要 httpx。请运行: pip install 'hello_agents[a2a]'"
            )

        import httpx

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.server_url}/.well-known/agent.json")
                response.raise_for_status()
                data = response.json()

                return A2AAgentCard(
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    url=data.get("url", self.server_url),
                    version=data.get("version", "1.0.0"),
                    skills=data.get("skills", []),
                    capabilities=data.get("capabilities", {}),
                )

            except httpx.HTTPError as e:
                raise ConnectionError(f"发现Agent失败: {e}") from e

    async def send_task(
        self,
        message: str,
        task_id: str | None = None,
        context_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> A2ATask:
        """发送任务

        Args:
            message: 任务消息
            task_id: 任务ID（可选）
            context_id: 上下文ID（可选）
            metadata: 元数据（可选）

        Returns:
            任务对象

        Raises:
            ConnectionError: 连接失败
        """
        if not self._has_httpx:
            raise ImportError(
                "A2A客户端需要 httpx。请运行: pip install 'hello_agents[a2a]'"
            )

        import httpx

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                payload = {
                    "message": message,
                    "task_id": task_id,
                    "context_id": context_id,
                    "metadata": metadata or {},
                }

                response = await client.post(
                    f"{self.server_url}/tasks/send",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                return A2ATask(
                    id=data.get("task_id", ""),
                    status=data.get("status", "unknown"),
                    messages=data.get("messages", []),
                    artifacts=data.get("artifacts", []),
                )

            except httpx.HTTPError as e:
                raise ConnectionError(f"发送任务失败: {e}") from e

    async def get_task_status(self, task_id: str) -> A2ATask:
        """获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务对象

        Raises:
            ConnectionError: 连接失败
        """
        if not self._has_httpx:
            raise ImportError(
                "A2A客户端需要 httpx。请运行: pip install 'hello_agents[a2a]'"
            )

        import httpx

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.server_url}/tasks/{task_id}")
                response.raise_for_status()
                data = response.json()

                return A2ATask(
                    id=data.get("task_id", ""),
                    status=data.get("status", "unknown"),
                    messages=data.get("messages", []),
                    artifacts=data.get("artifacts", []),
                )

            except httpx.HTTPError as e:
                raise ConnectionError(f"获取任务状态失败: {e}") from e
