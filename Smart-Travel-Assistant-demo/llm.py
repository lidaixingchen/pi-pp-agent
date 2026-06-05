from openai import OpenAI

class LLM:
    """
    一个简单的语言模型类，用于与OpenAI API进行交互，生成响应。
    """
    def __init__(self, model_name, api_key, base_url):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name

    def generate_response(self, prompt, system_prompt):
        """根据用户输入的提示和系统提示生成响应。"""
        print("正在生成响应...")
        try:
            response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
            # 遍历流，逐块拼接响应
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    print(chunk.choices[0].delta.content, end='', flush=True)  # 实时输出生成的内容
            # print(f"生成的响应: {full_response}")
            return full_response
        except Exception as e:
            print(f"生成响应时发生错误: {e}")
            return "抱歉，生成响应时发生了错误。"