"""ANP协议实现（Agent Network Protocol）

ANP是一个开放的Agent网络协议，用于服务发现和注册。

核心概念：
- ServiceDescriptor: 服务描述符
- ServiceRegistry: 服务注册中心
- ServiceDiscovery: 服务发现

本模块提供概念性实现，使用HTTP REST API。
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ANPServiceDescriptor:
    """ANP服务描述符

    Example:
        >>> service = ANPServiceDescriptor(
        ...     service_id="agent-001",
        ...     name="Research Agent",
        ...     description="专门进行研究的Agent",
        ...     endpoint="http://localhost:8001",
        ...     capabilities=["research", "analysis"]
        ... )
    """
    service_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    endpoint: str = ""
    capabilities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "active"  # active, inactive, maintenance
    version: str = "1.0.0"


class ANPServer:
    """ANP服务注册服务器

    提供服务注册、注销和查询功能。

    Example:
        >>> server = ANPServer(port=8002)
        >>>
        >>> # 注册服务
        >>> service = ANPServiceDescriptor(
        ...     name="My Agent",
        ...     endpoint="http://localhost:8001"
        ... )
        >>> server.register_service(service)
        >>>
        >>> server.run()
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8002,
    ) -> None:
        """初始化ANP服务器

        Args:
            host: 监听地址
            port: 监听端口
        """
        self.host = host
        self.port = port

        self._services: dict[str, ANPServiceDescriptor] = {}

        # 检查依赖
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """检查必要的依赖是否已安装"""
        try:
            import fastapi  # noqa: F401
            self._has_fastapi = True
        except ImportError:
            self._has_fastapi = False

    def register_service(self, service: ANPServiceDescriptor) -> None:
        """注册服务

        Args:
            service: 服务描述符
        """
        self._services[service.service_id] = service

    def deregister_service(self, service_id: str) -> bool:
        """注销服务

        Args:
            service_id: 服务ID

        Returns:
            是否成功注销
        """
        if service_id in self._services:
            del self._services[service_id]
            return True
        return False

    def get_service(self, service_id: str) -> ANPServiceDescriptor | None:
        """获取服务详情

        Args:
            service_id: 服务ID

        Returns:
            服务描述符，如果不存在返回None
        """
        return self._services.get(service_id)

    def discover_services(
        self,
        capabilities: list[str] | None = None,
        status: str | None = None,
    ) -> list[ANPServiceDescriptor]:
        """发现服务

        Args:
            capabilities: 按能力过滤
            status: 按状态过滤

        Returns:
            匹配的服务列表
        """
        services = list(self._services.values())

        # 按能力过滤
        if capabilities:
            services = [
                s for s in services
                if any(cap in s.capabilities for cap in capabilities)
            ]

        # 按状态过滤
        if status:
            services = [s for s in services if s.status == status]

        return services

    def _create_app(self) -> Any:
        """创建FastAPI应用"""
        if not self._has_fastapi:
            raise ImportError(
                "ANP服务器需要 fastapi。请运行: pip install 'hello_agents[anp]'"
            )

        from fastapi import FastAPI, HTTPException, Query
        from pydantic import BaseModel

        app = FastAPI(title="ANP Service Registry")

        class ServiceRequest(BaseModel):
            name: str
            description: str = ""
            endpoint: str = ""
            capabilities: list[str] = []
            metadata: dict[str, Any] = {}

        class ServiceResponse(BaseModel):
            service_id: str
            name: str
            description: str
            endpoint: str
            capabilities: list[str]
            metadata: dict[str, Any]
            status: str
            version: str

        @app.post("/services", response_model=ServiceResponse)
        async def register_service(request: ServiceRequest) -> dict[str, Any]:
            """注册服务"""
            service = ANPServiceDescriptor(
                name=request.name,
                description=request.description,
                endpoint=request.endpoint,
                capabilities=request.capabilities,
                metadata=request.metadata,
            )
            self._services[service.service_id] = service

            return {
                "service_id": service.service_id,
                "name": service.name,
                "description": service.description,
                "endpoint": service.endpoint,
                "capabilities": service.capabilities,
                "metadata": service.metadata,
                "status": service.status,
                "version": service.version,
            }

        @app.delete("/services/{service_id}")
        async def deregister_service(service_id: str) -> dict[str, str]:
            """注销服务"""
            if service_id not in self._services:
                raise HTTPException(status_code=404, detail="服务不存在")

            del self._services[service_id]
            return {"message": "服务已注销"}

        @app.get("/services/{service_id}", response_model=ServiceResponse)
        async def get_service(service_id: str) -> dict[str, Any]:
            """获取服务详情"""
            if service_id not in self._services:
                raise HTTPException(status_code=404, detail="服务不存在")

            service = self._services[service_id]
            return {
                "service_id": service.service_id,
                "name": service.name,
                "description": service.description,
                "endpoint": service.endpoint,
                "capabilities": service.capabilities,
                "metadata": service.metadata,
                "status": service.status,
                "version": service.version,
            }

        @app.get("/services", response_model=list[ServiceResponse])
        async def discover_services(
            capabilities: list[str] | None = Query(None),
            status: str | None = Query(None),
        ) -> list[dict[str, Any]]:
            """发现服务"""
            services = self.discover_services(capabilities, status)

            return [
                {
                    "service_id": s.service_id,
                    "name": s.name,
                    "description": s.description,
                    "endpoint": s.endpoint,
                    "capabilities": s.capabilities,
                    "metadata": s.metadata,
                    "status": s.status,
                    "version": s.version,
                }
                for s in services
            ]

        return app

    def run(self) -> None:
        """启动服务器"""
        if not self._has_fastapi:
            raise ImportError(
                "ANP服务器需要 fastapi 和 uvicorn。"
                "请运行: pip install 'hello_agents[anp]'"
            )

        import uvicorn

        app = self._create_app()
        uvicorn.run(app, host=self.host, port=self.port)


class ANPClient:
    """ANP服务发现客户端

    用于发现和连接ANP网络中的服务。

    Example:
        >>> client = ANPClient("http://localhost:8002")
        >>> services = await client.discover_services(capabilities=["research"])
        >>> service = await client.get_service("agent-001")
    """

    def __init__(
        self,
        registry_url: str = "http://localhost:8002",
        timeout: float = 30.0,
    ) -> None:
        """初始化ANP客户端

        Args:
            registry_url: 注册中心URL
            timeout: 超时时间（秒）
        """
        self.registry_url = registry_url.rstrip("/")
        self.timeout = timeout

        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """检查必要的依赖是否已安装"""
        try:
            import httpx  # noqa: F401
            self._has_httpx = True
        except ImportError:
            self._has_httpx = False

    async def discover_services(
        self,
        capabilities: list[str] | None = None,
        status: str | None = None,
    ) -> list[ANPServiceDescriptor]:
        """发现服务

        Args:
            capabilities: 按能力过滤
            status: 按状态过滤

        Returns:
            匹配的服务列表

        Raises:
            ConnectionError: 连接失败
        """
        if not self._has_httpx:
            raise ImportError(
                "ANP客户端需要 httpx。请运行: pip install 'hello_agents[anp]'"
            )

        import httpx

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                params: dict[str, Any] = {}
                if capabilities:
                    params["capabilities"] = capabilities
                if status:
                    params["status"] = status

                response = await client.get(
                    f"{self.registry_url}/services",
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

                return [
                    ANPServiceDescriptor(
                        service_id=s.get("service_id", ""),
                        name=s.get("name", ""),
                        description=s.get("description", ""),
                        endpoint=s.get("endpoint", ""),
                        capabilities=s.get("capabilities", []),
                        metadata=s.get("metadata", {}),
                        status=s.get("status", "active"),
                        version=s.get("version", "1.0.0"),
                    )
                    for s in data
                ]

            except httpx.HTTPError as e:
                raise ConnectionError(f"发现服务失败: {e}") from e

    async def get_service(self, service_id: str) -> ANPServiceDescriptor:
        """获取服务详情

        Args:
            service_id: 服务ID

        Returns:
            服务描述符

        Raises:
            ConnectionError: 连接失败
            ValueError: 服务不存在
        """
        if not self._has_httpx:
            raise ImportError(
                "ANP客户端需要 httpx。请运行: pip install 'hello_agents[anp]'"
            )

        import httpx

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.registry_url}/services/{service_id}"
                )
                response.raise_for_status()
                data = response.json()

                return ANPServiceDescriptor(
                    service_id=data.get("service_id", ""),
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    endpoint=data.get("endpoint", ""),
                    capabilities=data.get("capabilities", []),
                    metadata=data.get("metadata", {}),
                    status=data.get("status", "active"),
                    version=data.get("version", "1.0.0"),
                )

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise ValueError(f"服务不存在: {service_id}") from e
                raise ConnectionError(f"获取服务失败: {e}") from e
            except httpx.HTTPError as e:
                raise ConnectionError(f"获取服务失败: {e}") from e

    async def register_service(self, service: ANPServiceDescriptor) -> ANPServiceDescriptor:
        """注册服务

        Args:
            service: 服务描述符

        Returns:
            注册后的服务描述符（包含生成的service_id）

        Raises:
            ConnectionError: 连接失败
        """
        if not self._has_httpx:
            raise ImportError(
                "ANP客户端需要 httpx。请运行: pip install 'hello_agents[anp]'"
            )

        import httpx

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                payload = {
                    "name": service.name,
                    "description": service.description,
                    "endpoint": service.endpoint,
                    "capabilities": service.capabilities,
                    "metadata": service.metadata,
                }

                response = await client.post(
                    f"{self.registry_url}/services",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                return ANPServiceDescriptor(
                    service_id=data.get("service_id", ""),
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    endpoint=data.get("endpoint", ""),
                    capabilities=data.get("capabilities", []),
                    metadata=data.get("metadata", {}),
                    status=data.get("status", "active"),
                    version=data.get("version", "1.0.0"),
                )

            except httpx.HTTPError as e:
                raise ConnectionError(f"注册服务失败: {e}") from e

    async def deregister_service(self, service_id: str) -> bool:
        """注销服务

        Args:
            service_id: 服务ID

        Returns:
            是否成功注销

        Raises:
            ConnectionError: 连接失败
        """
        if not self._has_httpx:
            raise ImportError(
                "ANP客户端需要 httpx。请运行: pip install 'hello_agents[anp]'"
            )

        import httpx

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.delete(
                    f"{self.registry_url}/services/{service_id}"
                )
                response.raise_for_status()
                return True

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return False
                raise ConnectionError(f"注销服务失败: {e}") from e
            except httpx.HTTPError as e:
                raise ConnectionError(f"注销服务失败: {e}") from e
