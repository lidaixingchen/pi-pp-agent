import threading
from typing import List, Dict, Any, Optional

class Memory:
    """一个简单的短期记忆模块，用于存储智能体的行动与反思轨迹。"""
    def __init__(self):
        self.memory: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def add_entry(self, memory_type: str, content: str) -> None:
        """向记忆中添加一个新的条目"""
        with self._lock:
            self.memory.append({"type": memory_type, "content": content})

    def get_memory(self) -> List[Dict[str, Any]]:
        """获取当前的记忆内容"""
        with self._lock:
            return list(self.memory)
    
    def get_trajectory(self) -> str:
        """获取智能体的行动与反思轨迹，格式化为字符串"""
        trajectory = []
        with self._lock:
            entries = list(self.memory)
        for entry in entries:
            if entry["type"] == "action":
                trajectory.append(f"行动: {entry['content']}")
            elif entry["type"] == "reflection":
                trajectory.append(f"反思: {entry['content']}")
        return "\n".join(trajectory)
    
    def get_last_execution(self) -> Optional[str]:
        """获取最近一次执行的结果"""
        with self._lock:
            for i in range(len(self.memory) - 1, -1, -1):
                if self.memory[i]["type"] == "execution":
                    return self.memory[i]["content"]
        return None
    
    def clear_memory(self) -> None:
        """清空记忆内容"""
        with self._lock:
            self.memory.clear()
