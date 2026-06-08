from typing import Optional

from openai import OpenAI
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()


class LLM:
    """一个语言模型base类，用于与OpenAI API进行交互，生成响应和工具调用,默认支持流式输出。"""

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        time_out: int | None = None,
        temperature: float | None = None,
        provider: str | None = None
    ) -> None:
        """初始化LLM实例，设置模型名称、API密钥、基础URL和超时时间。优先使用传入的参数，如果未传入则使用环境变量中的值。"""
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME", "")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "")
        self.time_out = time_out if time_out is not None else int(os.getenv("LLM_TIMEOUT", "60"))
        self.temperature = temperature if temperature is not None else float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.provider = provider or os.getenv("LLM_PROVIDER", "auto")

        if not all([self.model_name, self.api_key, self.base_url]):
            raise ValueError("模型名称、API密钥和基础URL必须提供。请检查环境变量或传入参数。")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.time_out)

    def generate_response(self, messages: list[dict[str, str]], temperature: float = 0.7, stream: bool = True) -> str:
        """根据消息列表生成响应。默认使用流式输出，逐块返回内容。"""
        # print(f"{self.model_name}正在生成响应...")
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                stream=stream
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
        
    def _auto_detect_provider(self, api_key: Optional[str], base_url: Optional[str]) -> str:
        """自动检测API提供商类型，基于API密钥和基础URL的特征进行判断。"""
        # 1. 检查特定提供商的环境变量 (最高优先级)
        if os.getenv("MODELSCOPE_API_KEY"): return "modelscope"
        if os.getenv("OPENAI_API_KEY"): return "openai"
        if os.getenv("ZHIPU_API_KEY"): return "zhipu"
        # ... 其他服务商的环境变量检查

        # 获取通用的环境变量
        actual_api_key = api_key or os.getenv("LLM_API_KEY")
        actual_base_url = base_url or os.getenv("LLM_BASE_URL")

        # 2. 根据 base_url 判断
        if actual_base_url:
            base_url_lower = actual_base_url.lower()
            if "api-inference.modelscope.cn" in base_url_lower: return "modelscope"
            if "open.bigmodel.cn" in base_url_lower: return "zhipu"
            if "localhost" in base_url_lower or "127.0.0.1" in base_url_lower:
                if ":11434" in base_url_lower: return "ollama"
                if ":8000" in base_url_lower: return "vllm"
            return "local" # 其他本地端口

        # 3. 根据 API 密钥格式辅助判断
        if actual_api_key:
            if actual_api_key.startswith("ms-"): return "modelscope"
            if actual_api_key.startswith("sk-"): return "openai"
            if actual_api_key.startswith("zhipu-"): return "zhipu"
            if actual_api_key.startswith("ollama-"): return "ollama"

        # 4. 默认返回 'auto'，使用通用配置
        return "auto"
    
    def _resolve_credentials(self, api_key: Optional[str], base_url: Optional[str]) -> tuple[str, str]:
        """根据provider解析API密钥和base_url"""
        if self.provider == "openai":
            resolved_api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY") or ""
            resolved_base_url = base_url or os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1"
            return resolved_api_key, resolved_base_url

        elif self.provider == "modelscope":
            resolved_api_key = api_key or os.getenv("MODELSCOPE_API_KEY") or os.getenv("LLM_API_KEY") or ""
            resolved_base_url = base_url or os.getenv("LLM_BASE_URL") or "https://api-inference.modelscope.cn/v1/"
            return resolved_api_key, resolved_base_url
    
        # ... 其他服务商的逻辑

        # 默认返回环境变量或空字符串
        return api_key or os.getenv("LLM_API_KEY") or "", base_url or os.getenv("LLM_BASE_URL") or ""