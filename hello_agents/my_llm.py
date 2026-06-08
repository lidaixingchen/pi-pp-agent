"""自定义 LLM 客户端，扩展对 ModelScope 的支持"""
import os
from typing import Optional

from openai import OpenAI

from core.llm import LLM


class MyLLM(LLM):
    """一个自定义的 LLM 客户端，通过继承增加了对 ModelScope 的支持。"""

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        provider: Optional[str] = "auto",
        time_out: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        # 检查 provider 是否为我们想处理的 'modelscope'
        if provider == "modelscope":
            print("正在使用自定义的 ModelScope Provider")
            self.provider = "modelscope"

            # 解析 ModelScope 的凭证
            self.api_key = api_key or os.getenv("MODELSCOPE_API_KEY", "")
            self.base_url = base_url or "https://api-inference.modelscope.cn/v1/"

            # 验证凭证是否存在
            if not self.api_key:
                raise ValueError(
                    "ModelScope API key not found. "
                    "Please set MODELSCOPE_API_KEY environment variable."
                )

            # 设置模型和其他参数（与父类属性名保持一致）
            self.model_name = (
                model_name or os.getenv("LLM_MODEL_ID") or "Qwen/Qwen2.5-VL-72B-Instruct"
            )
            self.temperature = (
                temperature if temperature is not None else float(os.getenv("LLM_TEMPERATURE", "0.7"))
            )
            self.time_out = (
                time_out if time_out is not None else int(os.getenv("LLM_TIMEOUT", "60"))
            )

            # 使用获取的参数创建 OpenAI 客户端实例
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.time_out,
            )
        else:
            # 如果不是 modelscope，则完全使用父类的原始逻辑来处理
            super().__init__(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                time_out=time_out,
                temperature=temperature,
                provider=provider,
            )
