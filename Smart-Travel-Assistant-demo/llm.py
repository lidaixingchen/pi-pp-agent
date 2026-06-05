from __future__ import annotations

from collections.abc import Generator
from typing import Any

from openai import OpenAI


class LLM:
    """
    一个简单的语言模型类，用于与OpenAI API进行交互，生成响应。
    """

    def __init__(self, model_name: str, api_key: str, base_url: str) -> None:
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name

    def generate_response(self, messages: list[dict[str, Any]]) -> str:
        """根据消息列表生成响应（非流式）。"""
        print("正在生成响应...")
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,  # type: ignore[arg-type]
                stream=True
            )
            # 遍历流，逐块拼接响应
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
            return full_response
        except Exception as e:
            print(f"生成响应时发生错误: {e}")
            return "抱歉，生成响应时发生了错误。"

    def generate_response_stream(self, messages: list[dict[str, Any]]) -> Generator[str, None, None]:
        """根据消息列表生成响应（流式），逐块返回内容。"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,  # type: ignore[arg-type]
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"生成响应时发生错误: {e}"
        