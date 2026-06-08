import os
from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from tavily import TavilyClient

# 加载 .env 文件中的环境变量
load_dotenv()


# 验证必要的环境变量
def validate_env_vars() -> None:
    required_vars = ["LLM_API_KEY", "TAVILY_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"缺少必要的环境变量: {', '.join(missing_vars)}")


validate_env_vars()

# 初始化模型
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_NAME", "deepseek-chat"),
    api_key=SecretStr(os.getenv("LLM_API_KEY", "")),
    base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
    temperature=0.7
)

# 初始化Tavily客户端
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
