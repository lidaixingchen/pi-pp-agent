from search_assistant import create_search_assistant
from g_state import SearchState



def main():
    # 用户输入
    user_query = input("请输入您的问题: ")
    
    # 创建搜索助手
    search_assistant = create_search_assistant()
    
    # 启动搜索助手
    initial_state: SearchState = {
        "messages": [],
        "user_query": user_query,
        "search_query": "",
        "search_results": "",
        "final_answer": "",
        "step": "start"
    }
    
    try:
        result = search_assistant.invoke(initial_state, config={"configurable": {"thread_id": "1"}})  # type: ignore
    except Exception as e:
        print(f"\n❌ 搜索助手执行失败: {e}")
        return

    print("\n🔔 最终答案:")
    print(result.get("final_answer", "未生成答案"))

if __name__ == "__main__":
    main()
