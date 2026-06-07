import os
from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from tavily import TavilyClient

# 加载 .env 文件中的环境变量
load_dotenv()

# 初始化模型
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_NAME", ""),
    api_key=SecretStr(os.getenv("LLM_API_KEY", "")) if os.getenv("LLM_API_KEY") else None,
    base_url=os.getenv("LLM_BASE_URL", ""),
    temperature=0.7
)

# 初始化Tavily客户端
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
