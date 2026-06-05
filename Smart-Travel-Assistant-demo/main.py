import os
from llm import LLM
from tools.get_attraction import get_attraction
from tools.get_weather import get_weather
from prompt import AGENT_SYSTEM_PROMPT
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量中读取OpenAI API密钥、模型名称和基础URL
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("MODEL_NAME", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "")

#将所有工具函数注册到一个字典中，方便LLM调用
TOOLS = {
    "get_weather": get_weather,
    "get_attraction": get_attraction
}

def main():
    # 初始化语言模型
    llm = LLM(model_name=OPENAI_MODEL, api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

    # 用户输入
    user_input = input("请输入您的旅行需求（例如：我想去巴黎旅游，天气怎么样？）: ")
    user_prompt = f"用户输入: {user_input}\n请分析用户的需求，并使用可用工具一步步地解决问题。"

    # 使用消息列表管理对话历史
    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    # agent循环，直到生成Finish动作
    for i in range(5):  # 最多循环5次，防止死循环
        print(f"\n🔄 第{i+1}轮对话:")
        # 流式输出，实时检测Thought和Action
        full_response = ""
        has_thought = False
        has_action = False

        print("\n正在生成响应...", end="", flush=True)
        for chunk in llm.generate_response_stream(messages):
            full_response += chunk

            # 检测Thought关键词
            if not has_thought and "Thought:" in full_response:
                has_thought = True
                print(f"\r💭 思考: ", end="", flush=True)
                # 输出Thought:之后的内容
                thought_start = full_response.index("Thought:") + len("Thought:")
                print(full_response[thought_start:], end="", flush=True)
            elif has_thought and not has_action:
                # 检测Action关键词
                if "Action:" in full_response:
                    has_action = True
                    thought_end = full_response.index("Action:")
                    thought_start = full_response.index("Thought:") + len("Thought:")
                    # 打印完整的思考内容
                    print(f"\r💭 思考: {full_response[thought_start:thought_end].strip()}")
                    print(f"🔧 行动: ", end="", flush=True)
                    # 输出Action:之后的内容
                    action_start = thought_end + len("Action:")
                    print(full_response[action_start:], end="", flush=True)
                else:
                    # 继续输出思考内容
                    print(chunk, end="", flush=True)
            elif has_action:
                # 继续输出行动内容
                print(chunk, end="", flush=True)

        print()  # 换行

        # 将LLM的回复加入消息历史
        messages.append({"role": "assistant", "content": full_response})

        # 解析完整响应，提取Action
        if "Thought:" in full_response and "Action:" in full_response:
            action = full_response.split("Action:")[1].strip()

            if action.startswith("Finish[") and action.endswith("]"):
                final_answer = action[len("Finish["):-1]
                print(f"\n✅ 最终答案: {final_answer}")
                break
            elif "(" in action and ")" in action:
                func_name = action.split("(")[0]
                args_str = action.split("(")[1].rstrip(")")
                args = {}
                for arg in args_str.split(","):
                    if "=" in arg:
                        key, value = arg.split("=")
                        args[key.strip()] = value.strip().strip('"')

                if func_name in TOOLS:
                    tool_result = TOOLS[func_name](**args)
                    print(f"\n📊 工具结果: {tool_result}")
                    messages.append({"role": "user", "content": f"工具执行结果: {tool_result}"})
                else:
                    print(f"\n❌ 错误: 未知工具 {func_name}")
                    messages.append({"role": "user", "content": f"错误: 未知工具 {func_name}"})
            else:
                print("\n❌ 错误: 无效的Action格式")
                messages.append({"role": "user", "content": "错误: 无效的Action格式"})
        else:
            print("\n❌ 错误: LLM响应格式不正确，缺少Thought或Action")
            messages.append({"role": "user", "content": "错误: LLM响应格式不正确，缺少Thought或Action"})
   

if __name__ == "__main__":
    main()


