from openai import OpenAI
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

class LLM:
    """一个简单的语言模型类，用于与OpenAI API进行交互，生成响应,默认支持流式输出。"""
    
    def __init__(self, model_name: str, api_key: str, base_url: str,time_out: int) -> None:
        """初始化LLM实例，设置模型名称、API密钥、基础URL和超时时间。优先使用传入的参数，如果未传入则使用环境变量中的值。"""
        self.modulel_name = model_name or os.getenv("MODEL_NAME", "")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "")
        self.time_out = time_out or int(os.getenv("OPENAI_TIMEOUT", 60))
        if not all([self.modulel_name, self.api_key, self.base_url]):
            raise ValueError("模型名称、API密钥和基础URL必须提供。请检查环境变量或传入参数。")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.time_out)
    
    def generate_response(self, messages: list[dict[str, str]],temperature: float = 0.7,stream: bool = True) -> str:
        """根据消息列表生成响应。默认使用流式输出，逐块返回内容。"""
        print(f"{self.modulel_name}正在生成响应...")
        try:
            response = self.client.chat.completions.create(
                model=self.modulel_name,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                stream=stream
            )
            if stream:
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                return full_response
            else:
                return response.choices[0].message.content
        except Exception as e:
            print(f"生成响应时发生错误: {e}")
            return "抱歉，生成响应时发生了错误。"
      