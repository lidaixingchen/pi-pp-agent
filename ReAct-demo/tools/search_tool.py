import os
from tavily import TavilyClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def search(query: str) -> str:
    """
    使用Tavily Search API执行搜索，并返回优化后的结果。
    """
    # 1. 从环境变量中读取API密钥
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "错误:未配置TAVILY_API_KEY环境变量。"

    # 2. 初始化Tavily客户端
    tavily = TavilyClient(api_key=api_key)
    
    try:
        # 3. 调用API，使用advanced搜索深度获取更准确的结果
        response = tavily.search(
            query=query,
            search_depth="advanced",  # 深度搜索，结果更准确
            include_answer=True,
            max_results=5  # 限制结果数量
        )

        # 4. Tavily返回的结果已经非常干净，可以直接使用
        # response['answer'] 是一个基于所有搜索结果的总结性回答
        if response.get("answer"):
            return response["answer"]

        # 如果没有综合性回答，则格式化原始结果
        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")

        if not formatted_results:
            return "抱歉，没有找到相关的信息。"

        return "根据搜索，为您找到以下信息:\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误:执行Tavily搜索时出现问题 - {e}"