import asyncio

from autogen import UserProxyAgent
from autogen.agentchat import a_run_group_chat
from autogen.agentchat.group.patterns import RoundRobinPattern
from llm import create_llm_config, create_product_manager, create_engineer, create_code_reviewer, create_user_proxy


async def run_team():
    """异步运行智能体团队进行协作开发任务"""
    # 1. 创建 LLM 配置
    llm_config = create_llm_config()

    # 2. 创建各个智能体
    product_manager = create_product_manager(llm_config)
    engineer = create_engineer(llm_config)
    code_reviewer = create_code_reviewer(llm_config)
    user_proxy = create_user_proxy()

    # 3. 定义团队协作模式
    pattern = RoundRobinPattern(
        initial_agent=product_manager,
        agents=[product_manager, engineer, code_reviewer],
        user_agent=user_proxy,
    )

    # 4. 定义任务描述
    task = """我们需要开发一个比特币价格显示应用，具体要求如下：
    核心功能：
    - 实时显示比特币当前价格（USD）
    - 显示24小时价格变化趋势（涨跌幅和涨跌额）
    - 提供价格刷新功能

    技术要求：
    - 使用 Streamlit 框架创建 Web 应用
    - 界面简洁美观，用户友好
    - 添加适当的错误处理和加载状态

    请团队协作完成这个任务，从需求分析到最终实现。"""

    # 5. 异步执行团队协作，流式输出对话过程
    print("=" * 50)
    print("🚀 启动智能体团队协作...")
    print("=" * 50)

    response = await a_run_group_chat(
        pattern=pattern,
        messages=task,
        max_rounds=20,
    )

    # 6. 流式处理事件
    print("\n📋 对话过程：")
    print("-" * 50)
    async for event in response.events:  # type: ignore
        print(event)

    # 7. 获取并打印结果摘要
    print("\n" + "=" * 50)
    print("✅ 对话完成！")

    summary = await response.summary
    last_speaker = await response.last_speaker

    if summary:
        print(f"📝 摘要: {summary}")
    if last_speaker:
        print(f"👤 最后发言者: {last_speaker}")
    print("=" * 50)

    return response


# 主程序入口
if __name__ == "__main__":
    result = asyncio.run(run_team())
