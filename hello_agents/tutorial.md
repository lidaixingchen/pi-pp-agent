# HelloAgents 框架教程

> 从零理解一个轻量级 AI Agent 框架的设计与实现。

---

## 目录

1. [项目概览](#1-项目概览)
2. [核心概念](#2-核心概念)
3. [项目结构](#3-项目结构)
4. [模块详解：core（核心层）](#4-模块详解core核心层)
   - 4.1 [Message — 消息系统](#41-message--消息系统)
   - 4.2 [Config — 配置管理](#42-config--配置管理)
   - 4.3 [Exceptions — 异常体系](#43-exceptions--异常体系)
   - 4.4 [LLM — 大语言模型客户端](#44-llm--大语言模型客户端)
   - 4.5 [Agent — Agent 基类](#45-agent--agent-基类)
5. [模块详解：tools（工具层）](#5-模块详解tools工具层)
   - 5.1 [Tool & ToolParameter — 工具抽象](#51-tool--toolparameter--工具抽象)
   - 5.2 [ToolRegistry — 工具注册表](#52-toolregistry--工具注册表)
   - 5.3 [ToolChain — 工具链](#53-toolchain--工具链)
   - 5.4 [AsyncToolExecutor — 异步执行器](#54-asynctoolexecutor--异步执行器)
6. [模块详解：agents（Agent 实现层）](#6-模块详解agentsagent-实现层)
   - 6.1 [SimpleAgent — 完整实现](#61-simpleagent--完整实现)
7. [扩展点：MyLLM](#7-扩展点myllm)
8. [快速上手](#8-快速上手)
9. [设计模式与最佳实践](#9-设计模式与最佳实践)

---

## 1. 项目概览

**HelloAgents** 是一个教学用的轻量级 AI Agent 框架，帮助你理解以下核心问题：

- 什么是 Agent？Agent 和普通的 LLM 调用有什么区别？
- 如何让 LLM 不只是"聊天"，而是能"做事"（调用工具）？
- 如何设计一个可扩展的框架，让添加新工具、新 Agent 类型变得简单？

### Agent vs 普通 LLM 调用

```
普通 LLM 调用:
  用户 → LLM → 回答（一问一答，LLM 只能"说"）

Agent:
  用户 → Agent → 思考 → 调用工具 → 获取结果 → 继续思考 → ... → 最终回答
         （Agent 能"说"也能"做"，可以多轮迭代）
```

### 设计目标

| 目标 | 说明 |
|------|------|
| **简单** | 每个模块职责单一，代码量小，适合学习 |
| **可扩展** | 通过继承和注册机制，轻松添加新工具、新 Agent |
| **实用** | 支持流式输出、多轮对话、工具调用等实际功能 |

---

## 2. 核心概念

在深入代码之前，先理解框架中的几个核心概念：

### 消息（Message）

对话的基本单位。每条消息有一个**角色**（role）：

| 角色 | 含义 |
|------|------|
| `system` | 系统提示词，定义 Agent 的行为规则 |
| `user` | 用户输入 |
| `assistant` | LLM 的回复 |
| `tool` | 工具执行结果 |

### LLM 客户端（LLM）

封装了与大语言模型 API 的通信。本框架使用 OpenAI 兼容协议，因此支持 DeepSeek、OpenAI、ModelScope 等多种服务商。

### 工具（Tool）

Agent 可以调用的外部能力。例如搜索、计算、查询天气等。工具让 LLM 从"只能说"变成"能做事"。

### 工具注册表（ToolRegistry）

管理所有可用工具的中央仓库。Agent 通过它查找和执行工具。

### Agent

框架的核心。Agent = LLM + 工具 + 编排逻辑。它负责：
1. 接收用户输入
2. 构造提示词发给 LLM
3. 解析 LLM 的回复
4. 如果 LLM 想调用工具，执行工具并将结果反馈
5. 重复 2-4 直到得出最终答案

---

## 3. 项目结构

```
hello_agents/
├── __init__.py              # 包标识
├── my_llm.py                # 扩展 LLM（ModelScope 支持）
├── .env                     # 环境变量（API 密钥等）
│
├── core/                    # 核心层 — 框架的基础组件
│   ├── __init__.py
│   ├── agent.py             # Agent 抽象基类
│   ├── config.py            # 配置管理
│   ├── exceptions.py        # 自定义异常
│   ├── llm.py               # LLM 客户端基类
│   └── message.py           # 消息系统
│
├── tools/                   # 工具层 — 工具的定义与管理
│   ├── __init__.py
│   ├── async_executor.py    # 异步工具执行器
│   ├── base.py              # Tool 和 ToolParameter 基类
│   ├── chain.py             # 工具链（多工具编排）
│   └── registry.py          # 工具注册表
│
└── agents/                  # Agent 实现层 — 具体的 Agent 实现
    ├── __init__.py
    └── simple_agent.py      # 简单 Agent 实现
```

**分层架构**：`core` → `tools` → `agents`，上层依赖下层，职责清晰。

---

## 4. 模块详解：core（核心层）

### 4.1 Message — 消息系统

**文件**：`core/message.py`

消息是对话的基本单位。`Message` 类封装了一条对话消息的所有信息。

#### 设计思路

LLM API（如 OpenAI）要求消息以 `{"role": "xxx", "content": "xxx"}` 的字典格式传入。`Message` 类的作用是：

1. **类型安全**：用 `Literal` 限制 role 只能是 `"user" | "assistant" | "system" | "tool"`
2. **附加信息**：携带时间戳和元数据
3. **格式转换**：通过 `to_dict()` 转换为 API 需要的字典格式

#### 核心代码

```python
from typing import Literal
from pydantic import BaseModel

# 用 Literal 限定消息角色，防止拼写错误
MessageRole = Literal["user", "assistant", "system", "tool"]

class Message(BaseModel):
    content: str          # 消息内容
    role: MessageRole     # 消息角色
    timestamp: datetime   # 创建时间
    metadata: dict        # 附加元数据

    def to_dict(self) -> dict:
        """转换为 OpenAI API 格式"""
        return {"role": self.role, "content": self.content}
```

#### 使用示例

```python
from core.message import Message

# 创建消息
msg = Message(content="你好", role="user")
print(msg)              # [user] 你好
print(msg.to_dict())    # {"role": "user", "content": "你好"}
```

#### 为什么用 Pydantic？

Pydantic 提供了：
- 自动类型验证（传入错误类型会报错）
- 序列化/反序列化支持
- 清晰的字段定义语法

---

### 4.2 Config — 配置管理

**文件**：`core/config.py`

集中管理框架的所有配置项，避免硬编码。

#### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `default_model` | str | `"deepseek-v4-flash"` | 默认模型名称 |
| `default_provider` | str | `"deepseek"` | 默认服务商 |
| `temperature` | float | `0.7` | 生成温度（越高越随机） |
| `max_tokens` | int? | `None` | 最大生成 token 数 |
| `debug` | bool | `False` | 调试模式 |
| `log_level` | str | `"INFO"` | 日志级别 |
| `max_history_length` | int | `100` | 最大历史消息数 |

#### 使用方式

```python
from core.config import Config

# 方式 1：直接创建
config = Config(temperature=0.5, debug=True)

# 方式 2：从环境变量加载
config = Config.from_env()

# 转换为字典
print(config.to_dict())
```

#### 设计要点

- 继承 `pydantic.BaseModel`，自动获得类型验证
- `from_env()` 工厂方法支持从环境变量读取配置，适合部署场景
- 提供合理默认值，开箱即用

---

### 4.3 Exceptions — 异常体系

**文件**：`core/exceptions.py`

自定义异常层次结构，让错误处理更精确。

#### 异常层次

```
HelloAgentsError              # 基础异常
├── LLMError                  # LLM 调用异常
├── AgentError                # Agent 运行异常
├── ConfigError               # 配置异常
└── ToolError                 # 工具相关异常
    ├── ToolNotFoundError     # 工具不存在
    └── ToolExecutionError    # 工具执行失败
```

#### 为什么需要自定义异常？

```python
# 不好的做法：捕获所有 Exception，无法区分错误类型
try:
    agent.run("查询天气")
except Exception as e:
    print("出错了")  # 是 LLM 调用失败？还是工具不存在？

# 好的做法：精确捕获，针对性处理
try:
    agent.run("查询天气")
except ToolNotFoundError:
    print("工具未注册，请先注册工具")
except LLMError:
    print("LLM 服务不可用，请检查网络和 API 密钥")
```

#### 使用示例

```python
from core.exceptions import ToolNotFoundError, ToolExecutionError

# 工具未找到
raise ToolNotFoundError("weather")
# → "未找到工具: weather"

# 工具执行失败
raise ToolExecutionError("weather", "网络超时")
# → "工具 'weather' 执行失败: 网络超时"
```

---

### 4.4 LLM — 大语言模型客户端

**文件**：`core/llm.py`

封装与 LLM API 的通信，是整个框架的"大脑"。

#### 设计思路

```
用户代码
   ↓
LLM.generate_response(messages)
   ↓
OpenAI SDK → HTTP 请求 → LLM API
   ↓
流式返回 → 逐块打印 + 拼接完整响应
   ↓
返回完整文本
```

#### 初始化流程

```python
LLM.__init__()
   │
   ├─ 1. 自动检测 provider（_auto_detect_provider）
   │     根据环境变量、base_url、api_key 格式判断服务商
   │
   ├─ 2. 解析凭证（_resolve_credentials）
   │     根据 provider 选择正确的 api_key 和 base_url
   │
   ├─ 3. 创建 OpenAI 客户端
   │
   └─ 4. 验证必要参数（model_name, api_key, base_url 都不能为空）
```

#### Provider 自动检测逻辑

`_auto_detect_provider` 按优先级依次检查：

1. **特定环境变量**：`MODELSCOPE_API_KEY` → modelscope，`DEEPSEEK_API_KEY` → deepseek
2. **base_url 特征**：`api.deepseek.com` → deepseek，`api-inference.modelscope.cn` → modelscope
3. **api_key 前缀**：`ms-` → modelscope，`sk-` → openai
4. **兜底**：返回 `"auto"`

#### 核心方法

```python
def generate_response(
    self,
    messages: list[dict[str, str]],   # 消息列表
    temperature: float = 0.7,         # 生成温度
    stream: bool = True,              # 是否流式输出
) -> str:
    """
    根据消息列表生成响应。

    流式模式（默认）：逐块打印到终端，同时拼接完整响应返回。
    非流式模式：等待完整响应后一次性返回。
    """
```

#### 使用示例

```python
from core.llm import LLM
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件中的环境变量

# 创建 LLM 实例（自动从 .env 读取配置）
llm = LLM()

# 生成响应
messages = [
    {"role": "system", "content": "你是一个友好的助手。"},
    {"role": "user", "content": "用一句话解释什么是 Agent。"},
]
response = llm.generate_response(messages)
print(response)
```

#### 流式输出的工作原理

```python
# stream=True 时
response = self.client.chat.completions.create(..., stream=True)

# response 是一个迭代器，每次返回一小块（chunk）
for chunk in response:
    delta = chunk.choices[0].delta
    if delta.content:
        print(delta.content, end="", flush=True)  # 实时打印
        full_response += delta.content             # 拼接完整响应
```

这就像 ChatGPT 网页版的打字效果——文字一个个出现，而不是等全部生成完再显示。

---

### 4.5 Agent — Agent 基类

**文件**：`core/agent.py`

定义了 Agent 的抽象接口，所有具体 Agent 都必须继承它。

#### 核心设计

```python
class Agent(ABC):
    def __init__(self, name, llm, system_prompt=None, config=None):
        self.name = name              # Agent 名称
        self.llm = llm                # LLM 客户端
        self.system_prompt = system_prompt  # 系统提示词
        self.config = config          # 配置
        self._history = []            # 对话历史

    @abstractmethod
    def run(self, input_text: str, **kwargs) -> str:
        """运行 Agent — 子类必须实现"""
        pass

    def add_message(self, message):    # 添加到历史
    def clear_history(self):           # 清空历史
    def get_history(self):             # 获取历史副本
```

#### 设计要点

- **ABC（抽象基类）**：强制子类实现 `run` 方法
- **历史管理**：基类提供统一的历史记录管理，子类不需要重复实现
- **组合模式**：Agent 持有 LLM 实例（has-a 关系），而非继承 LLM

#### 为什么用组合而非继承？

```
继承:   class Agent(LLM)     → Agent "是一个" LLM（语义不对）
组合:   class Agent 持有 LLM  → Agent "有一个" LLM（语义正确）
```

Agent 的职责是**编排**（协调 LLM 和工具），而不是**成为** LLM。

---

## 5. 模块详解：tools（工具层）

### 5.1 Tool & ToolParameter — 工具抽象

**文件**：`tools/base.py`

定义了工具的抽象接口。

#### ToolParameter — 参数定义

```python
class ToolParameter(BaseModel):
    name: str           # 参数名
    type: str           # 参数类型（如 "string", "int"）
    description: str    # 参数描述
    required: bool      # 是否必填
    default: Any        # 默认值
```

#### Tool — 工具基类

```python
class Tool(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, parameters: Dict[str, Any]) -> str:
        """执行工具 — 子类必须实现"""
        pass

    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        """返回参数定义 — 子类必须实现"""
        pass
```

#### 自定义工具示例

```python
from tools.base import Tool, ToolParameter

class WeatherTool(Tool):
    def __init__(self):
        super().__init__(
            name="weather",
            description="查询指定城市的天气信息"
        )

    def get_parameters(self):
        return [
            ToolParameter(
                name="city",
                type="string",
                description="城市名称",
                required=True,
            )
        ]

    def run(self, parameters):
        city = parameters.get("city", "")
        # 这里可以调用真实的天气 API
        return f"{city}今天晴天，气温 25°C"
```

---

### 5.2 ToolRegistry — 工具注册表

**文件**：`tools/registry.py`

工具注册表是工具的"中央仓库"，负责注册、查找和执行工具。

#### 两种注册方式

```python
registry = ToolRegistry()

# 方式 1：注册 Tool 对象（适合复杂工具）
weather_tool = WeatherTool()
registry.register_tool(weather_tool)

# 方式 2：注册普通函数（适合简单工具，更快捷）
def search(query: str) -> str:
    return f"搜索结果: {query}"

registry.register_function(
    name="search",
    description="搜索互联网信息",
    func=search,
)
```

#### 核心方法

| 方法 | 说明 |
|------|------|
| `register_tool(tool)` | 注册 Tool 对象 |
| `register_function(name, desc, func)` | 注册函数作为工具 |
| `get_tool(name)` | 获取 Tool 对象 |
| `get_tool_descriptions()` | 获取所有工具的描述文本（注入到提示词） |
| `execute_tool(name, params)` | 执行工具并返回结果 |
| `list_tools()` | 列出所有已注册的工具名 |

#### 工作流程

```
注册阶段:
  WeatherTool → registry.register_tool() → 存入 _tools 字典
  search 函数 → registry.register_function() → 存入 _functions 字典

执行阶段:
  registry.execute_tool("weather", "北京")
    → 查找 _tools → 找到 WeatherTool → 调用 tool.run({"input": "北京"})

  registry.execute_tool("search", "Python教程")
    → 查找 _tools 没有 → 查找 _functions → 找到 → 调用 func("Python教程")
```

#### 工具描述注入提示词

`get_tool_descriptions()` 生成的文本会被注入到 Agent 的系统提示词中，让 LLM 知道有哪些工具可用：

```
- weather: 查询指定城市的天气信息
- search: 搜索互联网信息
```

---

### 5.3 ToolChain — 工具链

**文件**：`tools/chain.py`

支持多个工具按顺序执行，前一步的输出可以作为后一步的输入。

#### 设计思路

有些任务需要多步完成，例如：

```
用户: "北京今天适合去哪玩？"

步骤 1: weather("北京")     → "晴天，25°C"
步骤 2: search("北京 晴天 25°C 推荐景点")  → "推荐故宫、颐和园..."
```

#### 使用示例

```python
from tools.chain import ToolChain, ToolChainManager

# 创建工具链
chain = ToolChain(name="weather_search", description="查天气后推荐景点")

# 添加步骤（{input} 会被替换为初始输入，{step_0_result} 会被替换为第一步的结果）
chain.add_step(tool_name="weather", input_template="{input}", output_key="weather_result")
chain.add_step(tool_name="search", input_template="{input} {weather_result} 推荐景点", output_key="search_result")

# 注册并执行
manager = ToolChainManager(registry)
manager.register_chain(chain)
result = manager.execute_chain("weather_search", "北京")
```

#### 模板变量机制

```
context = {"input": "北京"}

步骤 1: input_template = "{input}"
        → format(**context) → "北京"
        → 执行 weather("北京") → "晴天，25°C"
        → context["weather_result"] = "晴天，25°C"

步骤 2: input_template = "{input} {weather_result} 推荐景点"
        → format(**context) → "北京 晴天，25°C 推荐景点"
        → 执行 search("北京 晴天，25°C 推荐景点") → "推荐故宫..."
        → context["search_result"] = "推荐故宫..."
```

---

### 5.4 AsyncToolExecutor — 异步执行器

**文件**：`tools/async_executor.py`

当需要同时执行多个工具时，串行执行太慢。异步执行器利用线程池实现并发。

#### 使用场景

```
串行（慢）:
  weather("北京")  → 等待 2 秒 → 完成
  search("北京")   → 等待 3 秒 → 完成
  总耗时: 5 秒

并发（快）:
  weather("北京")  ─┐
  search("北京")   ─┤→ 同时执行
  总耗时: 3 秒（取最慢的那个）
```

#### 使用示例

```python
import asyncio
from tools.async_executor import AsyncToolExecutor

executor = AsyncToolExecutor(registry, max_workers=4)

async def main():
    # 并发执行多个工具
    results = await executor.execute_tools_parallel([
        ("weather", "北京"),
        ("search", "北京旅游攻略"),
        ("weather", "上海"),
    ])
    print(results)  # [北京天气结果, 搜索结果, 上海天气结果]

    executor.shutdown()

asyncio.run(main())
```

---

## 6. 模块详解：agents（Agent 实现层）

### 6.1 SimpleAgent — 完整实现

**文件**：`agents/simple_agent.py`

`SimpleAgent` 是框架中唯一的具体 Agent 实现，展示了如何将 LLM 和工具组合成一个完整的 Agent。

#### 整体流程

```
用户输入
    │
    ▼
构建消息列表（系统提示 + 历史 + 用户输入）
    │
    ▼
┌─ 工具调用已启用？──┐
│                    │
否                    是
│                    │
▼                    ▼
直接调用 LLM      进入工具调用循环
│                    │
▼                    ▼
返回响应          ┌─ 迭代开始 ──────────┐
                  │  调用 LLM 生成响应    │
                  │  检测工具调用标记      │
                  │  ┌─ 有工具调用？─┐    │
                  │  否              是   │
                  │  │               │    │
                  │  ▼               ▼    │
                  │  结束循环     执行工具  │
                  │               结果反馈 │
                  │               继续迭代 │
                  └───────────────────────┘
                        │
                        ▼
                  记录历史，返回最终响应
```

#### 工具调用协议

SimpleAgent 使用文本标记协议与 LLM 协作：

**LLM 输出格式**：
```
[TOLL_CALL:工具名:参数]
```

**示例**：
```
[TOLL_CALL:weather:北京]
[TOLL_CALL:search:query=Python教程,limit=3]
```

**Agent 反馈格式**：
```
[TOLL_RESULT:工具名:执行结果]
```

#### 提示词注入

`_get_enhanced_system_prompt` 将工具信息注入系统提示词：

```
你是一个智能助手，帮助用户解答问题。

你可以使用以下工具：
- weather: 查询指定城市的天气信息
- search: 搜索互联网信息

当需要使用工具时，请按照格式调用：
`[TOLL_CALL:工具名:参数]`
例如:`[TOLL_CALL:search:Python编程]`
```

这样 LLM 就知道有哪些工具可用、如何调用。

#### 参数解析

`_parse_tool_parameters` 支持多种参数格式：

| 格式 | 示例 | 解析结果 |
|------|------|----------|
| 直接值 | `北京` | `{"input": "北京"}` |
| 单个键值 | `city=北京` | `{"city": "北京"}` |
| 多个键值 | `query=Python,limit=3` | `{"query": "Python", "limit": "3"}` |
| 特殊工具 | search 工具传 `Python` | `{"query": "Python"}` |

#### 多轮迭代

`max_tool_iterations` 参数控制最大迭代次数（默认 3），防止 Agent 陷入无限循环：

```
迭代 1: LLM 说 "我需要查天气" → 调用 weather 工具
迭代 2: LLM 说 "天气不错，我需要查景点" → 调用 search 工具
迭代 3: LLM 说 "根据天气和景点信息，我推荐..." → 无工具调用 → 结束
```

---

## 7. 扩展点：MyLLM

**文件**：`my_llm.py`

展示了如何通过继承扩展框架功能。

#### 设计模式：模板方法

```python
class MyLLM(LLM):
    def __init__(self, ..., provider="auto"):
        if provider == "modelscope":
            # 处理 ModelScope 特殊逻辑
            self._init_modelscope(...)
        else:
            # 其他情况交给父类处理
            super().__init__(...)
```

#### 属性一致性

扩展类必须保持与父类一致的属性命名：

| 属性 | 父类 LLM | MyLLM（必须一致） |
|------|----------|-------------------|
| 模型名 | `self.model_name` | `self.model_name` ✓ |
| 客户端 | `self.client` | `self.client` ✓ |
| 超时 | `self.time_out` | `self.time_out` ✓ |

如果属性名不一致（如 `self.model` vs `self.model_name`），会导致父类方法访问不到正确的属性。

---

## 8. 快速上手

### 环境准备

```bash
# 1. 安装依赖
pip install openai pydantic python-dotenv

# 2. 配置 .env 文件
```

### .env 配置

```env
# DeepSeek（推荐，性价比高）
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL_NAME=deepseek-v4-flash

# 或者 OpenAI
# LLM_API_KEY=sk-your_key
# LLM_BASE_URL=https://api.openai.com/v1
# LLM_MODEL_NAME=gpt-4o-mini

# 超时和温度
LLM_TIMEOUT=60
LLM_TEMPERATURE=0.7
```

### 示例 1：纯对话（无工具）

```python
import sys
sys.path.insert(0, "hello_agents")

from dotenv import load_dotenv
load_dotenv("hello_agents/.env")

from core.llm import LLM
from agents.simple_agent import SimpleAgent

# 创建 LLM 和 Agent
llm = LLM()
agent = SimpleAgent(name="小助手", llm=llm, system_prompt="你是一个友好的助手。")

# 对话
response = agent.run("用一句话解释什么是 Agent")
print(response)
```

### 示例 2：带工具调用

```python
import sys
sys.path.insert(0, "hello_agents")

from dotenv import load_dotenv
load_dotenv("hello_agents/.env")

from core.llm import LLM
from agents.simple_agent import SimpleAgent
from tools.registry import ToolRegistry

# 创建工具注册表并注册工具
registry = ToolRegistry()

def get_weather(city: str) -> str:
    """模拟天气查询"""
    weather_data = {"北京": "晴天 25°C", "上海": "多云 22°C"}
    return weather_data.get(city, f"{city}天气数据暂无")

def search(query: str) -> str:
    """模拟搜索"""
    return f"关于'{query}'的搜索结果: 这是一些有用的信息..."

registry.register_function("weather", "查询城市天气", get_weather)
registry.register_function("search", "搜索互联网信息", search)

# 创建 Agent（传入工具注册表）
llm = LLM()
agent = SimpleAgent(
    name="旅行助手",
    llm=llm,
    system_prompt="你是一个旅行助手，帮助用户规划旅行。",
    tool_registry=registry,
)

# 对话
response = agent.run("我想去北京旅游，天气怎么样？有什么推荐的景点？")
print(response)
```

### 示例 3：多轮对话

```python
# 继续上面的代码，agent 已经创建好

# 第一轮
response1 = agent.run("北京天气怎么样？")

# 第二轮（Agent 会记住历史）
response2 = agent.run("那上海呢？")

# 查看对话历史
for msg in agent.get_history():
    print(msg)

# 清空历史重新开始
agent.clear_history()
```

---

## 9. 设计模式与最佳实践

### 9.1 分层架构

```
┌─────────────────────────────┐
│         agents/             │  实现层 — 具体的 Agent 逻辑
├─────────────────────────────┤
│         tools/              │  能力层 — 工具的定义与管理
├─────────────────────────────┤
│         core/               │  基础层 — LLM、消息、配置
└─────────────────────────────┘
```

**原则**：上层依赖下层，同层不互相依赖。

### 9.2 依赖注入

Agent 不自己创建 LLM，而是通过构造函数接收：

```python
# 好的做法：外部创建，注入进来
llm = LLM()
agent = SimpleAgent(llm=llm)

# 不好的做法：Agent 内部创建，难以测试和替换
class SimpleAgent:
    def __init__(self):
        self.llm = LLM()  # 耦合死了
```

好处：
- 可以轻松替换 LLM 实现（测试时用 Mock LLM）
- 可以多个 Agent 共享同一个 LLM 实例

### 9.3 注册表模式

工具通过注册表管理，而非硬编码在 Agent 中：

```python
# 好的做法：通过注册表管理
registry.register_function("weather", "查天气", get_weather)
agent = SimpleAgent(tool_registry=registry)

# 不好的做法：硬编码在 Agent 里
class SimpleAgent:
    def _execute_tool(self, name, params):
        if name == "weather":
            return get_weather(params)
        elif name == "search":
            return search(params)
        # 每次加工具都要改 Agent...
```

### 9.4 扩展建议

想要扩展这个框架？以下是几个方向：

| 扩展方向 | 做法 |
|----------|------|
| **添加新工具** | 继承 `Tool` 或直接用 `register_function` |
| **添加新 Agent 类型** | 继承 `Agent`，实现 `run` 方法（如 ReAct Agent） |
| **添加记忆功能** | 在 Agent 中实现向量存储，长期记忆 |
| **添加多 Agent 协作** | 创建 Orchestrator，协调多个 Agent |
| **支持更多 LLM** | 继承 `LLM`，添加新 provider 的逻辑 |

---

## 附录：常见问题

### Q: 为什么 LLM 不调用工具？

A: 检查以下几点：
1. 系统提示词是否正确注入了工具描述
2. 工具描述是否清晰（LLM 需要理解工具的用途）
3. `temperature` 是否过高（过高会导致格式不稳定）

### Q: 如何调试 Agent？

A: 设置 `config = Config(debug=True)`，框架会打印详细的执行日志。也可以直接看终端输出——每个步骤都有 emoji 标记。

### Q: 支持哪些 LLM 服务商？

A: 理论上支持所有兼容 OpenAI API 的服务商。已适配的有：
- DeepSeek
- OpenAI
- ModelScope
- 智谱（Zhipu）
- Ollama（本地）
- vLLM（本地）

### Q: `.env` 文件中的 API 密钥安全吗？

A: `.env` 文件已在 `.gitignore` 中，不会被提交到 Git。但请注意不要将 `.env` 文件分享给他人。
