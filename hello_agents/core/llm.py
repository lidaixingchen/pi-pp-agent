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
        temperature: float | None = None
    ) -> None:
        """初始化LLM实例，设置模型名称、API密钥、基础URL和超时时间。优先使用传入的参数，如果未传入则使用环境变量中的值。"""
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME", "")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "")
        self.time_out = time_out if time_out is not None else int(os.getenv("LLM_TIMEOUT", "60"))
        self.temperature = temperature if temperature is not None else float(os.getenv("LLM_TEMPERATURE", "0.7"))
        
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
      