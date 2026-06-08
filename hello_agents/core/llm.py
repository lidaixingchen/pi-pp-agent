"""LLM 基类"""
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
import os

# 加载环境变量
load_dotenv()


class LLM:
    """一个语言模型基类，用于与 OpenAI 兼容 API 进行交互，生成响应。默认支持流式输出。"""

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        time_out: Optional[int] = None,
        temperature: Optional[float] = None,
        provider: Optional[str] = None,
    ) -> None:
        """初始化 LLM 实例。优先使用传入参数，未传入则使用环境变量。"""
        self.provider = provider or self._auto_detect_provider(api_key, base_url)

        # 根据 provider 解析凭证
        resolved_key, resolved_url = self._resolve_credentials(api_key, base_url)

        self.model_name = model_name or os.getenv("LLM_MODEL_NAME", "")
        self.api_key = resolved_key
        self.base_url = resolved_url
        self.time_out = time_out if time_out is not None else int(os.getenv("LLM_TIMEOUT", "60"))
        self.temperature = (
            temperature if temperature is not None else float(os.getenv("LLM_TEMPERATURE", "0.7"))
        )

        if not all([self.model_name, self.api_key, self.base_url]):
            raise ValueError(
                "模型名称、API 密钥和基础 URL 必须提供。请检查环境变量或传入参数。"
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.time_out,
        )

    def generate_response(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        stream: bool = True,
    ) -> str:
        """根据消息列表生成响应。默认使用流式输出，逐块返回内容。"""
        temp = temperature if temperature is not None else self.temperature
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,  # type: ignore[arg-type]
                temperature=temp,
                stream=stream,
            )
            if stream:
                full_response = ""
                for chunk in response:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta and delta.content:
                        print(delta.content, end="", flush=True)
                        full_response += delta.content
                print()  # 换行
                return full_response
            else:
                content = response.choices[0].message.content if response.choices else None
                return content or ""
        except Exception as e:
            print(f"生成响应时发生错误: {e}")
            return ""

    def _auto_detect_provider(
        self, api_key: Optional[str], base_url: Optional[str]
    ) -> str:
        """自动检测 API 提供商类型，基于 API 密钥和基础 URL 的特征进行判断。"""
        # 1. 检查特定提供商的环境变量（最高优先级）
        if os.getenv("MODELSCOPE_API_KEY"):
            return "modelscope"
        if os.getenv("DEEPSEEK_API_KEY"):
            return "deepseek"
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        if os.getenv("ZHIPU_API_KEY"):
            return "zhipu"

        # 获取通用的环境变量
        actual_api_key = api_key or os.getenv("LLM_API_KEY")
        actual_base_url = base_url or os.getenv("LLM_BASE_URL")

        # 2. 根据 base_url 判断
        if actual_base_url:
            base_url_lower = actual_base_url.lower()
            if "api-inference.modelscope.cn" in base_url_lower:
                return "modelscope"
            if "api.deepseek.com" in base_url_lower:
                return "deepseek"
            if "open.bigmodel.cn" in base_url_lower:
                return "zhipu"
            if "localhost" in base_url_lower or "127.0.0.1" in base_url_lower:
                if ":11434" in base_url_lower:
                    return "ollama"
                if ":8000" in base_url_lower:
                    return "vllm"
            return "local"

        # 3. 根据 API 密钥格式辅助判断
        if actual_api_key:
            if actual_api_key.startswith("ms-"):
                return "modelscope"
            if actual_api_key.startswith("sk-"):
                return "openai"
            if actual_api_key.startswith("zhipu-"):
                return "zhipu"
            if actual_api_key.startswith("ollama-"):
                return "ollama"

        # 4. 默认返回 'auto'
        return "auto"

    def _resolve_credentials(
        self, api_key: Optional[str], base_url: Optional[str]
    ) -> tuple[str, str]:
        """根据 provider 解析 API 密钥和 base_url"""
        if self.provider == "openai":
            resolved_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY") or ""
            resolved_url = base_url or os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1"
            return resolved_key, resolved_url

        if self.provider == "modelscope":
            resolved_key = api_key or os.getenv("MODELSCOPE_API_KEY") or os.getenv("LLM_API_KEY") or ""
            resolved_url = base_url or os.getenv("LLM_BASE_URL") or "https://api-inference.modelscope.cn/v1/"
            return resolved_key, resolved_url

        if self.provider == "deepseek":
            resolved_key = api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY") or ""
            resolved_url = base_url or os.getenv("LLM_BASE_URL") or "https://api.deepseek.com/v1"
            return resolved_key, resolved_url

        # 默认返回环境变量或空字符串
        return (
            api_key or os.getenv("LLM_API_KEY") or "",
            base_url or os.getenv("LLM_BASE_URL") or "",
        )
