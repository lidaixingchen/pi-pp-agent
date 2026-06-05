import os
from llm import LLM
from tools.get_attraction import get_attraction
from tools.get_weather import get_weather
from prompt import AGENT_SYSTEM_PROMPT
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量中读取OpenAI API密钥、模型名称和基础URL
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("MODEL_NAME")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")

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
    prompt_history = AGENT_SYSTEM_PROMPT + "\n" + user_prompt

    # agent循环，直到生成Finish动作
    for _ in range(5):  # 最多循环5次，防止死循环
        response = llm.generate_response(prompt_history, AGENT_SYSTEM_PROMPT)
        
        # 解析LLM的响应，提取Thought和Action
        if "Thought:" in response and "Action:" in response:
            thought = response.split("Thought:")[1].split("Action:")[0].strip()
            action = response.split("Action:")[1].strip()
            print(f"\nLLM思考: {thought}")
            print(f"LLM行动: {action}")

            if action.startswith("Finish[") and action.endswith("]"):
                final_answer = action[len("Finish["):-1]
                print(f"\n最终答案: {final_answer}")
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
                    print(f"\n工具执行结果: {tool_result}")
                    prompt_history += f"\n工具执行结果: {tool_result}"
                else:
                    print(f"\n错误: 未知工具 {func_name}")
                    prompt_history += f"\n错误: 未知工具 {func_name}"
            else:
                print("\n错误: 无效的Action格式")
                prompt_history += "\n错误: 无效的Action格式"
        else:
            print("\n错误: LLM响应格式不正确，缺少Thought或Action")
            prompt_history += "\n错误: LLM响应格式不正确，缺少Thought或Action"
   

if __name__ == "__main__":
    main()


