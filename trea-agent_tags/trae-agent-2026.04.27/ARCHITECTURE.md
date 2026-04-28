
# Trae Agent 整体架构文档

## 目录
1. [项目概述](#项目概述)
2. [核心架构组件](#核心架构组件)
3. [主要模块详解](#主要模块详解)
4. [工作流程](#工作流程)
5. [扩展机制](#扩展机制)
6. [配置系统](#配置系统)

---

## 项目概述

Trae Agent 是一个基于大语言模型（LLM）的软件工程任务代理系统。它提供了强大的命令行接口，能够理解自然语言指令并使用各种工具执行复杂的软件工程工作流程。

### 主要特性
- 多LLM提供商支持（OpenAI、Anthropic、Doubao、Azure、OpenRouter、Ollama、Google Gemini）
- 丰富的工具生态系统
- 交互式模式
- 详细的轨迹记录
- 灵活的配置系统
- Docker环境支持
- MCP（Model Context Protocol）集成

---

## 核心架构组件

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   trae-cli   │  │  interactive │  │   show-config│           │
│  └──────┬───────┘  └───────┬──────┘  └──────────────┘           │
└─────────┼──────────────────┼────────────────────────────────────┘
          │                  │
          ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Layer                                │
│  ┌──────────────────┐                                           │
│  │   Agent Factory  │                                           │
│  └────────┬─────────┘                                           │
│           │                                                     │
│  ┌────────▼─────────┐  ┌──────────────────┐                     │
│  │   TraeAgent      │◄─┤   BaseAgent      │                     │
│  └──────────────────┘  └──────────────────┘                     │
└─────────┬───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Tool Layer                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Tools Registry                                           │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  • Bash Tool           • Str Replace Edit Tool            │  │
│  │  • JSON Edit Tool      • Sequential Thinking Tool         │  │
│  │  • Task Done Tool      • MCP Tools                        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────┬───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LLM Client Layer                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  LLMClient (Factory)                                      │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  • OpenAI Client      • Anthropic Client                  │  │
│  │  • Google Client      • Azure Client                      │  │
│  │  • Ollama Client      • Doubao Client                     │  │
│  │  • OpenRouter Client                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────┬───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Config & Utils Layer                         │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │   Config       │  │   Trajectory      │  │   CLI Console  │  │
│  └────────────────┘  └──────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 主要模块详解

### 1. CLI Layer (命令行界面层)

**位置**: `trae_agent/cli.py`

**主要功能**:
- 提供用户命令行接口
- 解析命令行参数
- 启动代理执行任务或进入交互模式
- 处理配置文件加载和解析
- 支持Docker模式

**核心命令**:
- `trae-cli run <task>`: 执行单个任务
- `trae-cli interactive`: 进入交互式会话
- `trae-cli show-config`: 显示当前配置

**关键类/函数**:
- `resolve_config_file()`: 解析配置文件，支持YAML和旧版JSON格式
- `check_docker()`: 检查Docker环境
- `build_with_pyinstaller()`: 构建Docker模式所需的工具
- `run()`: 执行单个任务的命令
- `interactive()`: 交互式模式命令

---

### 2. Agent Layer (代理层)

**位置**: `trae_agent/agent/`

**核心类**:

#### BaseAgent (基础代理类)
**位置**: `trae_agent/agent/base_agent.py`

`BaseAgent` 是所有代理的抽象基类，提供了代理执行的核心框架：

**主要职责**:
- 初始化LLM客户端
- 管理工具生命周期
- 执行任务主循环
- 处理工具调用
- 记录执行轨迹
- 管理Docker环境（可选）

**核心方法**:
- `new_task()`: 初始化新任务（抽象方法，由子类实现）
- `execute_task()`: 执行任务主循环
- `_run_llm_step()`: 执行单个LLM推理步骤
- `_tool_call_handler()`: 处理工具调用
- `_finalize_step()`: 完成当前步骤并记录

#### TraeAgent (Trae代理类)
**位置**: `trae_agent/agent/trae_agent.py`

`TraeAgent` 是 `BaseAgent` 的具体实现，专门用于软件工程任务：

**主要职责**:
- 初始化MCP（Model Context Protocol）工具
- 设置系统提示词
- 处理git diff生成
- 实现任务完成检测逻辑
- 管理MCP客户端清理

**核心方法**:
- `initialise_mcp()`: 初始化MCP工具
- `discover_mcp_tools()`: 发现MCP服务提供的工具
- `new_task()`: 为软件工程任务初始化
- `get_system_prompt()`: 获取系统提示词
- `get_git_diff()`: 获取git差异
- `llm_indicates_task_completed()`: 检测LLM是否认为任务完成
- `_is_task_completed()`: 检查任务是否实际完成
- `cleanup_mcp_clients()`: 清理MCP客户端

**核心工具集**:
```python
TraeAgentToolNames = [
    "str_replace_based_edit_tool",  # 字符串替换编辑工具
    "sequentialthinking",           # 顺序思考工具
    "json_edit_tool",               # JSON编辑工具
    "task_done",                    # 任务完成工具
    "bash",                         # Bash执行工具
]
```

#### 辅助类
**位置**: `trae_agent/agent/agent_basics.py`

定义了代理执行的基本数据结构：
- `AgentState`: 代理状态枚举（RUNNING, COMPLETED, ERROR）
- `AgentStepState`: 步骤状态枚举（THINKING, CALLING_TOOL, REFLECTING, COMPLETED, ERROR）
- `AgentStep`: 单个执行步骤的数据类
- `AgentExecution`: 完整执行结果的数据类

**位置**: `trae_agent/agent/docker_manager.py`

管理Docker环境，提供隔离的执行环境。

---

### 3. Tool Layer (工具层)

**位置**: `trae_agent/tools/`

#### 工具基类
**位置**: `trae_agent/tools/base.py`

定义了工具的基础接口：

**核心数据类**:
- `ToolError`: 工具错误异常
- `ToolExecResult`: 工具执行中间结果
- `ToolResult`: 工具执行最终结果
- `ToolCall`: 工具调用
- `ToolParameter`: 工具参数定义

**核心类**:
- `Tool`: 所有工具的抽象基类
  - `get_name()`: 获取工具名称
  - `get_description()`: 获取工具描述
  - `get_parameters()`: 获取工具参数
  - `execute()`: 执行工具
  - `json_definition()`: 获取JSON格式的工具定义
  - `get_input_schema()`: 获取工具输入schema（适配不同LLM提供商）

- `ToolExecutor`: 工具执行器
  - `execute_tool_call()`: 执行单个工具调用
  - `parallel_tool_call()`: 并行执行多个工具调用
  - `sequential_tool_call()`: 顺序执行多个工具调用
  - `close_tools()`: 关闭所有工具

#### 核心工具实现

**Bash Tool** (`bash_tool.py`)
- 执行Bash命令
- 管理子进程生命周期
- 支持长期运行的进程

**Str Replace Edit Tool** (`edit_tool.py`)
- 基于字符串替换的文件编辑
- 安全的编辑验证
- 支持查看文件内容

**JSON Edit Tool** (`json_edit_tool.py`)
- JSON路径编辑
- 支持增删改JSON字段
- 验证JSON格式

**Sequential Thinking Tool** (`sequential_thinking_tool.py`)
- 帮助LLM进行结构化思考
- 记录思考过程
- 分解复杂任务

**Task Done Tool** (`task_done_tool.py`)
- 标记任务完成
- 提供最终结果

**MCP Tool** (`mcp_tool.py`)
- 集成MCP（Model Context Protocol）服务
- 动态发现和注册MCP工具

**Docker Tool Executor** (`docker_tool_executor.py`)
- 在Docker容器中执行工具
- 文件同步
- 隔离执行环境

#### 工具注册机制
**位置**: `trae_agent/tools/__init__.py`

工具通过装饰器自动注册到 `tools_registry` 字典中，实现工具的动态发现和加载。

---

### 4. LLM Client Layer (LLM客户端层)

**位置**: `trae_agent/utils/llm_clients/`

#### 核心架构

**LLMClient** (`llm_client.py`)
- LLM客户端工厂
- 根据配置选择相应的提供商客户端
- 统一的聊天接口

**BaseClient** (`base_client.py`)
- 所有LLM客户端的抽象基类
- 定义了标准接口
- 重试逻辑
- 轨迹记录集成

#### 具体提供商客户端

| 客户端 | 文件 | 说明 |
|--------|------|------|
| OpenAI | `openai_client.py` | OpenAI API客户端 |
| Anthropic | `anthropic_client.py` | Anthropic Claude API客户端 |
| Google | `google_client.py` | Google Gemini API客户端 |
| Azure | `azure_client.py` | Azure OpenAI API客户端 |
| Ollama | `ollama_client.py` | 本地Ollama模型客户端 |
| Doubao | `doubao_client.py` | 字节跳动豆包API客户端 |
| OpenRouter | `openrouter_client.py` | OpenRouter多模型网关 |

#### 基础数据结构
**位置**: `trae_agent/utils/llm_clients/llm_basics.py`

- `LLMMessage`: LLM消息（role, content, tool_result）
- `LLMResponse`: LLM响应（content, tool_calls, usage）
- `ToolCallDefinition`: 工具调用定义
- `Provider`: 提供商枚举

#### 重试机制
**位置**: `trae_agent/utils/llm_clients/retry_utils.py`

提供了指数退避重试逻辑，处理API调用失败的情况。

---

### 5. Config & Utils Layer (配置和工具层)

#### 配置系统
**位置**: `trae_agent/utils/config.py`

配置系统采用YAML格式，支持层次化配置：

**核心配置类**:
- `ModelProvider`: 模型提供商配置（api_key, provider, base_url, api_version）
- `ModelConfig`: 模型配置（model, model_provider, temperature, top_p, max_tokens等）
- `MCPServerConfig`: MCP服务配置
- `AgentConfig`: 代理基础配置
- `TraeAgentConfig`: Trae代理配置（继承AgentConfig）
- `LakeviewConfig`: Lakeview配置
- `Config`: 主配置类，包含所有配置

**配置优先级**:
```
CLI参数 > 环境变量 > 配置文件 > 默认值
```

#### 轨迹记录系统
**位置**: `trae_agent/utils/trajectory_recorder.py`

记录代理执行的完整轨迹，用于调试、分析和复现：
- 记录每个步骤的状态
- 记录LLM消息和响应
- 记录工具调用和结果
- 记录token使用情况
- 保存为JSON格式

#### CLI控制台系统
**位置**: `trae_agent/utils/cli/`

提供两种控制台实现：

**Simple Console** (`simple_console.py`)
- 简洁的文本输出
- 适合批处理和日志

**Rich Console** (`rich_console.py`)
- 交互式富文本界面
- 基于Textual框架
- 实时状态显示
- Lakeview集成

#### MCP客户端
**位置**: `trae_agent/utils/mcp_client.py`

管理MCP（Model Context Protocol）服务连接：
- 连接MCP服务
- 发现MCP工具
- 转换MCP工具为内部Tool格式
- 处理MCP工具调用

---

### 6. Prompt Layer (提示词层)

**位置**: `trae_agent/prompt/agent_prompt.py`

定义了代理使用的系统提示词，指导LLM如何使用工具完成软件工程任务。

---

## 工作流程

### 单次任务执行流程

```
1. 用户输入任务
   ↓
2. CLI解析参数和配置
   ↓
3. 创建TraeAgent实例
   ↓
4. 初始化MCP工具（如配置）
   ↓
5. 调用agent.new_task()初始化任务
   ↓
6. 调用agent.execute_task()执行任务
   ↓
7. 任务执行循环：
   ├─ 7.1 调用LLM推理
   ├─ 7.2 解析LLM响应
   ├─ 7.3 检查任务是否完成
   ├─ 7.4 如未完成，执行工具调用
   ├─ 7.5 收集工具结果
   ├─ 7.6 反射（可选）
   └─ 7.7 记录步骤
   ↓
8. 任务完成或达到最大步数
   ↓
9. 生成git diff（如需要）
   ↓
10. 保存轨迹文件
    ↓
11. 清理资源（Docker, MCP等）
```

### 代理步骤内部流程

```
┌─────────────────────────────────────────────────────────────┐
│                    代理执行步骤                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   THINKING   │───▶│ CALLING_TOOL │───▶│  REFLECTING  │  │
│  │   (LLM推理)  │    │ (工具执行)    │    │  (可选)      │  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│         │                                       │           │
│         └───────────────────────────────────────┘           │
│                             │                               │
│                     ┌───────▼───────┐                       │
│                     │   COMPLETED   │                       │
│                     │   (步骤完成)   │                       │
│                     └───────────────┘                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 扩展机制

### 1. 添加新的LLM提供商

**步骤**:
1. 在 `trae_agent/utils/llm_clients/` 中创建新的客户端类，继承 `BaseClient`
2. 实现必要的抽象方法
3. 在 `LLMClient` 中注册新的提供商
4. 更新配置系统以支持新提供商

**关键接口**:
```python
class BaseClient(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        model_config: ModelConfig,
        tools: list[Tool] | None = None,
    ) -> LLMResponse:
        pass
```

### 2. 添加新工具

**步骤**:
1. 在 `trae_agent/tools/` 中创建新工具类，继承 `Tool`
2. 实现必要的抽象方法
3. 使用 `@tools_registry.register` 装饰器注册工具
4. 在配置中添加工具名称

**关键接口**:
```python
class Tool(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        pass
    
    @abstractmethod
    def get_parameters(self) -> list[ToolParameter]:
        pass
    
    @abstractmethod
    async def execute(self, arguments: ToolCallArguments) -> ToolExecResult:
        pass
```

### 3. 创建自定义代理

**步骤**:
1. 创建新类继承 `BaseAgent`
2. 实现抽象方法 `new_task()` 和 `cleanup_mcp_clients()`
3. 可选重写其他方法以定制行为
4. 在CLI中添加新代理类型的支持

**可重写的关键方法**:
- `new_task()`: 初始化任务
- `llm_indicates_task_completed()`: 检测任务完成
- `_is_task_completed()`: 验证任务完成
- `reflect_on_result()`: 结果反射
- `task_incomplete_message()`: 任务未完成消息

### 4. 集成MCP服务

MCP（Model Context Protocol）允许动态发现和使用外部工具：

**配置示例**:
```yaml
mcp_servers:
  playwright:
    command: npx
    args:
      - "@playwright/mcp@0.0.27"
allow_mcp_servers:
  - playwright
```

---

## 配置系统

### YAML配置文件结构

```yaml
# 模型提供商配置
model_providers:
  anthropic:
    api_key: your_anthropic_api_key
    provider: anthropic
  openai:
    api_key: your_openai_api_key
    provider: openai
    base_url: https://api.openai.com/v1

# 模型配置
models:
  trae_agent_model:
    model_provider: anthropic
    model: claude-sonnet-4-20250514
    max_tokens: 4096
    temperature: 0.5
    top_p: 1.0
    parallel_tool_calls: true
    max_retries: 3

# 代理配置
agents:
  trae_agent:
    enable_lakeview: true
    model: trae_agent_model
    max_steps: 200
    tools:
      - bash
      - str_replace_based_edit_tool
      - sequentialthinking
      - task_done

# MCP服务配置（可选）
mcp_servers:
  example_server:
    command: example_command
    args:
      - arg1

allow_mcp_servers:
  - example_server

# Lakeview配置（可选）
lakeview:
  model: trae_agent_model
```

### 环境变量

| 环境变量 | 说明 |
|---------|------|
| `OPENAI_API_KEY` | OpenAI API密钥 |
| `OPENAI_BASE_URL` | OpenAI基础URL |
| `ANTHROPIC_API_KEY` | Anthropic API密钥 |
| `ANTHROPIC_BASE_URL` | Anthropic基础URL |
| `GOOGLE_API_KEY` | Google API密钥 |
| `GOOGLE_BASE_URL` | Google基础URL |
| `OPENROUTER_API_KEY` | OpenRouter API密钥 |
| `OPENROUTER_BASE_URL` | OpenRouter基础URL |
| `DOUBAO_API_KEY` | Doubao API密钥 |
| `DOUBAO_BASE_URL` | Doubao基础URL |

---

## 目录结构

```
trae-agent/
├── trae_agent/                    # 主源代码目录
│   ├── __init__.py               # 包初始化，导出核心类
│   ├── cli.py                    # CLI入口
│   ├── agent/                    # 代理模块
│   │   ├── __init__.py
│   │   ├── base_agent.py         # 基础代理类
│   │   ├── trae_agent.py         # Trae代理类
│   │   ├── agent_basics.py       # 代理基础数据结构
│   │   └── docker_manager.py     # Docker管理
│   ├── tools/                    # 工具模块
│   │   ├── __init__.py           # 工具注册
│   │   ├── base.py               # 工具基类
│   │   ├── bash_tool.py          # Bash工具
│   │   ├── edit_tool.py          # 编辑工具
│   │   ├── json_edit_tool.py     # JSON编辑工具
│   │   ├── sequential_thinking_tool.py  # 顺序思考工具
│   │   ├── task_done_tool.py     # 任务完成工具
│   │   ├── mcp_tool.py           # MCP工具
│   │   ├── docker_tool_executor.py  # Docker工具执行器
│   │   └── ckg/                  # CKG工具（可选）
│   ├── prompt/                   # 提示词模块
│   │   ├── __init__.py
│   │   └── agent_prompt.py       # 代理提示词
│   └── utils/                    # 工具函数模块
│       ├── config.py             # 配置系统
│       ├── constants.py          # 常量定义
│       ├── trajectory_recorder.py  # 轨迹记录器
│       ├── mcp_client.py         # MCP客户端
│       ├── lake_view.py          # Lakeview功能
│       ├── legacy_config.py      # 旧版配置支持
│       ├── cli/                  # CLI控制台
│       │   ├── __init__.py
│       │   ├── cli_console.py    # CLI控制台接口
│       │   ├── console_factory.py  # 控制台工厂
│       │   ├── simple_console.py  # 简单控制台
│       │   └── rich_console.py   # 富文本控制台
│       └── llm_clients/          # LLM客户端
│           ├── __init__.py
│           ├── llm_client.py     # LLM客户端工厂
│           ├── llm_basics.py     # LLM基础数据结构
│           ├── base_client.py    # LLM客户端基类
│           ├── openai_client.py  # OpenAI客户端
│           ├── anthropic_client.py  # Anthropic客户端
│           ├── google_client.py  # Google客户端
│           ├── azure_client.py   # Azure客户端
│           ├── ollama_client.py  # Ollama客户端
│           ├── doubao_client.py  # Doubao客户端
│           ├── openrouter_client.py  # OpenRouter客户端
│           └── retry_utils.py    # 重试工具
├── tests/                        # 测试目录
│   ├── agent/                    # 代理测试
│   ├── tools/                    # 工具测试
│   └── utils/                    # 工具函数测试
├── evaluation/                   # 评估模块
├── docs/                         # 文档
├── pyproject.toml                # 项目配置
├── Makefile                      # 构建脚本
└── README.md                     # 项目说明
```

---

## 总结

Trae Agent 采用模块化、可扩展的架构设计：

1. **层次清晰**: CLI层 → Agent层 → Tool层 → LLM层 → Config层
2. **接口抽象**: 基类定义标准接口，子类实现具体逻辑
3. **易于扩展**: 支持添加新LLM提供商、新工具、新代理类型
4. **配置灵活**: 支持配置文件、环境变量、CLI参数多种配置方式
5. **研究友好**: 透明的架构，便于研究和实验新的代理设计

这种设计使得 Trae Agent 既可以作为实用的软件工程工具，也可以作为研究AI代理架构的平台。
