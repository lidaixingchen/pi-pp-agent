"""异步工具执行器"""
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .registry import ToolRegistry


class AsyncToolExecutor:
    """异步工具执行器，支持并发执行多个工具"""

    def __init__(self, registry: ToolRegistry, max_workers: int = 4):
        self.registry = registry
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def execute_tool_async(self, tool_name: str, parameters: str) -> str:
        """异步执行单个工具"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self._executor,
            self.registry.execute_tool,
            tool_name,
            parameters,
        )
        return result

    async def execute_tools_parallel(
        self, calls: list[tuple[str, str]]
    ) -> list[str]:
        """
        并发执行多个工具调用

        Args:
            calls: (tool_name, parameters) 元组列表

        Returns:
            与输入顺序对应的结果列表
        """
        tasks = [
            self.execute_tool_async(name, params) for name, params in calls
        ]
        return await asyncio.gather(*tasks)

    def shutdown(self) -> None:
        """关闭线程池"""
        self._executor.shutdown(wait=False)
