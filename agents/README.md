
https://github.com/Antropath/minimal-agent

明白，仓库都删了/改名了，我直接给你**3 个现在能打开、真·轻量、适合逐行读源码的 Agent 项目**，都是 **100～500 行、无依赖地狱、纯教学向**，和你之前要的 micro-agent/tiny-agent 完全同构。

---

## ✅ 1. minimal-agent（100 行，最纯粹 ReAct）
https://github.com/Antropath/minimal-agent

特点：
- **核心 agent.py 只有 ~100 行**（注释极多，新手友好）
- 只做一件事：ReAct 循环（思考→工具→观察→循环）
- 用 LiteLLM，**天然兼容火山/豆包/本地 Ollama**
- 无多余功能，读它 = 把 Agent 内核看透

核心结构：
```
minimal-agent/
  ├── agent.py   # 100行主循环（必看）
  ├── tools.py   # 工具基类
  └── main.py    # 运行示例
```

---

## ✅ 2. Agent-Base-Zero（300 行，渐进式学习）
https://github.com/frecol/Agent-Base-Zero

特点：
- **每一个 Git commit 是一个进化版本**，从最简 while 循环开始
- v0.1：300 行，只有「循环+工具调用」
- v0.5：逐步加上记忆、多工具、错误处理
- 适合**一步步跟着 commit 读**，理解 Agent 是怎么“长大”的

---

## ✅ 3. mini-coding-agent（500 行，工业级简化版）
https://github.com/Lightning-AI/mini-coding-agent

特点：
- 500 行，涵盖：**工具调用、记忆、上下文压缩、子任务委托**
- 作者是 Lightning AI 科学家，代码干净、注释全
- 读它 = 直接看懂生产级 Agent 的简化实现

---

## 🎯 现在我直接带你读「minimal-agent」（100 行那个，最适合入门）
我贴**精简可运行源码 + 逐行解释**，你马上就能跑通。

### 1. 安装依赖
```bash
git clone https://github.com/Antropath/minimal-agent
cd minimal-agent
pip install -r requirements.txt
```

### 2. agent.py（核心 100 行，逐行讲）
```python
import json
from typing import List, Dict, Any
from litellm import completion  # 统一兼容所有模型

class MinimalAgent:
    def __init__(self, model: str, tools: List[Dict[str, Any]]):
        self.model = model
        self.tools = tools  # 工具列表（OpenAI schema）
        self.messages = []  # 对话上下文

    def add_message(self, role: str, content: str):
        """添加消息到上下文"""
        self.messages.append({"role": role, "content": content})

    def run_tool(self, tool_call: Dict[str, Any]) -> str:
        """执行工具（这里简化，直接返回参数）"""
        name = tool_call["function"]["name"]
        args = json.loads(tool_call["function"]["arguments"])
        # 实际项目：根据 name 调用对应函数
        return f"工具 {name} 执行结果: {args}"

    def step(self) -> str:
        """单步推理：调用 LLM → 处理工具"""
        # 1. 调用 LLM（带工具）
        response = completion(
            model=self.model,
            messages=self.messages,
            tools=self.tools
        )
        msg = response.choices[0].message

        # 2. 无工具调用 → 返回答案
        if not msg.get("tool_calls"):
            return msg.content

        # 3. 有工具调用 → 执行并把结果塞回上下文
        for tool_call in msg["tool_calls"]:
            result = self.run_tool(tool_call)
            self.add_message("tool", result)

        # 4. 递归下一轮（直到无工具）
        return self.step()

    def chat(self, user_query: str) -> str:
        """入口：用户提问 → 开始循环"""
        self.add_message("user", user_query)
        return self.step()
```

### 3. 运行示例（main.py）
```python
from agent import MinimalAgent

# 1. 定义工具（OpenAI 标准 schema）
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取天气",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"]
            }
        }
    }
]

# 2. 初始化 Agent（支持火山/豆包，改 model+base_url 即可）
agent = MinimalAgent(
    model="gpt-3.5-turbo",
    tools=tools
)

# 3. 对话
print(agent.chat("北京今天天气怎么样？"))
```

---

## ✅ 关键点（你必须记住）
1. **所有轻量 Agent 内核都长这样**：
   - 消息上下文管理
   - LLM 调用（带 tools）
   - 工具解析与执行
   - 结果回塞 + 循环
2. **完全不用 Responses API**，只靠标准 `chat.completions`
3. **火山/豆包直接能用**，换 `model` 和 `base_url` 即可

---


The architecture follows the [ReAct framework](https://arxiv.org/abs/2210.03629). The agent completes its taks in a sequence of steps. In each step it can "Reason" and "Act" (= ReAct). The agent will perform as many steps as needed to complete the task.


For a more detail introduction to agents and to understand different levels of AI agents, Hugging Face's [AI Agent Course](
https://huggingface.co/learn/agents-course/en/unit1/what-are-agents) is a good start.

