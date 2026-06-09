# 智能体架构详解

本文档详细解释了 Agent 101 的工作原理和架构设计。

## 目录

1. [概述](#概述)
2. [ReAct 框架](#react-框架)
3. [核心模块](#核心模块)
4. [工作流程详解](#工作流程详解)
5. [工具系统](#工具系统)

---

## 概述

Agent 101 是一个基于 **ReAct 框架** 的智能体实现。它的核心思想很简单：

> **思考 → 行动 → 观察 → 重复**

智能体通过调用大语言模型（LLM）来生成思考和代码，然后执行代码来调用工具或进行计算，最后根据观察结果继续下一步，直到完成任务。

---

## ReAct 框架

ReAct 是 "Reasoning + Acting" 的缩写，是一种将推理和行动结合起来的智能体框架。

### ReAct 的三个核心步骤

1. **Thought（思考）** - LLM 分析当前状态，决定下一步做什么
2. **Action（行动）** - 生成并执行代码，调用工具或进行计算
3. **Observation（观察）** - 获取执行结果，作为下一步的输入

### 为什么用 ReAct？

- **可解释性强** - 每一步都有清晰的思考过程
- **容错性好** - 可以根据观察结果纠正错误
- **灵活性高** - 可以处理各种复杂任务

---

## 核心模块

### 1. `src/agent/agent.py` - 智能体核心

这是整个系统的心脏，负责协调整个流程。

#### 主要方法

| 方法 | 作用 |
|------|------|
| `__init__()` | 初始化智能体，设置工具、API 等 |
| `run(task)` | 运行智能体完成任务（主入口） |
| `step()` | 执行单步操作 |
| `_call_llm()` | 调用大语言模型 |

#### 核心属性

- `history` - 对话历史记录
- `tools` - 可用工具字典
- `python_executor` - Python 代码执行器
- `client` - OpenAI 客户端

### 2. `src/agent/code_extractor.py` - 代码提取器

负责从 LLM 的响应中提取 Python 代码块。

```
LLM 响应 → 正则匹配 → 提取代码
```

### 3. `src/agent/prompts.py` - 提示词模块

定义和渲染系统提示词，告诉 LLM 如何工作。

### 4. `src/tools/` - 工具模块

包含智能体可以使用的各种工具。

---

## 工作流程详解

让我们通过一个具体例子来看智能体是如何工作的。

### 示例任务

> "上海和北京哪个城市人口更多？"

### 完整流程

#### 第 1 步：初始化

```python
# 创建智能体
agent = Agent(
    tools=[WebSearchTool(), VisitWebpageTool()],
    max_steps=10
)
```

智能体准备就绪，等待任务。

---

#### 第 2 步：接收任务

```python
result = agent.run("上海和北京哪个城市人口更多？")
```

智能体将任务添加到对话历史：

```
[
    {"role": "system", "content": "系统提示词..."},
    {"role": "user", "content": "Task: 上海和北京哪个城市人口更多？"}
]
```

---

#### 第 3 步：调用 LLM（第 1 轮）

智能体调用 LLM，传入对话历史。

**LLM 的响应：**
```
Thought: 我需要搜索上海和北京的人口数据来进行比较。我先搜索上海的人口。
Code:
```py
shanghai_pop = web_search(query="上海 人口 2024")
print("上海人口:", shanghai_pop)
```<end_code>
```

---

#### 第 4 步：提取代码

`CodeExtractor` 从响应中提取代码：

```python
code = """
shanghai_pop = web_search(query="上海 人口 2024")
print("上海人口:", shanghai_pop)
"""
```

---

#### 第 5 步：执行代码

`python_executor` 在沙箱中执行代码：

```
调用 web_search("上海 人口 2024")
→ 返回: "上海人口约 2489 万（2024年）"

执行 print("上海人口:", ...)
→ 输出: "上海人口: 上海人口约 2489 万（2024年）"
```

---

#### 第 6 步：构建观察结果

```python
observation = {
    "role": "user",
    "content": "Observation:\n上海人口: 上海人口约 2489 万（2024年）"
}
```

将观察结果添加到历史。

---

#### 第 7 步：调用 LLM（第 2 轮）

传入更新后的对话历史：

```
[
    ...前面的消息...,
    {"role": "assistant", "content": "Thought: 我需要搜索..."},
    {"role": "user", "content": "Observation:\n上海人口: ..."}
]
```

**LLM 的响应：**
```
Thought: 现在我知道了上海的人口，接下来搜索北京的人口。
Code:
```py
beijing_pop = web_search(query="北京 人口 2024")
print("北京人口:", beijing_pop)
```<end_code>
```

---

#### 第 8 步：执行第 2 轮代码（搜索北京人口）

同样的流程：提取代码 → 执行代码 → 构建观察结果。

**执行结果：**
```
调用 web_search("北京 人口 2024")
→ 返回: "北京人口约 2189 万（2024年）"

执行 print("北京人口:", ...)
→ 输出: "北京人口: 北京人口约 2189 万（2024年）"
```

**观察结果：**
```python
observation = {
    "role": "user",
    "content": "Observation:\n北京人口: 北京人口约 2189 万（2024年）"
}
```

将观察结果添加到历史。

---

#### 第 9 步：调用 LLM（第 3 轮，关键的比对步骤！）

现在对话历史包含了所有信息：

```
[
    {"role": "system", "content": "系统提示词..."},
    {"role": "user", "content": "Task: 上海和北京哪个城市人口更多？"},
    {"role": "assistant", "content": "Thought: 我需要搜索上海...（第1轮思考）"},
    {"role": "user", "content": "Observation:\n上海人口: 上海人口约 2489 万（2024年）"},
    {"role": "assistant", "content": "Thought: 现在我知道了上海...（第2轮思考）"},
    {"role": "user", "content": "Observation:\n北京人口: 北京人口约 2189 万（2024年）"}
]
```

**LLM 读取完整历史后进行推理：**

1. LLM 看到任务："上海和北京哪个城市人口更多？"
2. LLM 看到第 1 次观察："上海人口约 2489 万"
3. LLM 看到第 2 次观察："北京人口约 2189 万"
4. LLM 在脑海中比对这两个数字：
   - 上海：2489 万
   - 北京：2189 万
   - 2489 > 2189
   - 结论：上海人口更多
5. LLM 决定使用 final_answer() 返回结果

**LLM 的最终响应：**
```
Thought: 现在我有了两个城市的完整数据。根据搜索结果：
- 上海人口：约 2489 万（2024年）
- 北京人口：约 2189 万（2024年）

通过比较这两个数字，2489 万大于 2189 万，所以上海的人口更多。
Code:
```py
final_answer("上海人口更多，约 2489 万（2024年），北京约 2189 万")
```<end_code>
```

---

#### 第 10 步：检测最终答案

`python_executor` 检测到调用了 `final_answer()`，标记为最终答案。

---

#### 第 11 步：返回结果

智能体返回最终答案，任务完成！

---

## 工具系统

### 工具的结构

每个工具都是一个继承自 `BaseTool` 的类，必须定义：

```python
class MyTool(BaseTool):
    name = "my_tool"                    # 工具名称
    description = "工具描述"            # 工具描述
    inputs = {"param": {"type": "..."}} # 输入参数定义
    output_type = "string"              # 输出类型
    
    def __call__(self, param):          # 执行逻辑
        return result
```

### 内置工具

| 工具 | 作用 |
|------|------|
| `final_answer` | 返回最终答案 |
| `web_search` | 网络搜索 |
| `visit_webpage` | 访问网页 |

### 如何添加新工具

1. 在 `src/tools/` 下创建新文件
2. 继承 `BaseTool`
3. 实现 `__call__` 方法
4. 在 `src/tools/__init__.py` 中导出
5. 在创建智能体时传入

---

## 代码执行器

使用 `smolagents` 库的 `LocalPythonExecutor`，特点：

- ✅ 沙箱环境，安全执行
- ✅ 状态持久化，变量保留
- ✅ 自动检测 `final_answer()` 调用

---

## 总结

智能体的工作原理就是这么简单：

```
任务 → 思考 → 代码 → 执行 → 观察 → ... → 最终答案
     ↑_________________________________________|
```

希望这份文档能帮助你理解智能体的工作原理！
