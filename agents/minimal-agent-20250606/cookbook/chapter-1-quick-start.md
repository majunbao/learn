# Chapter 1: Quick Start & Architecture Overview

This chapter gives you a running start with **minimal-agent** — a \~100-line Python code agent built from first principles. You'll learn what a code agent is, set up the project, run your first task, and see the big-picture architecture before diving into each component in later chapters.

**What you'll learn:** What a code agent is, how to install and run minimal-agent, and the ReAct loop at a high level.

**Prerequisites:** Python 3.12+, a valid LLM API key, basic Python familiarity.

***

## 1.1 What Is a Code Agent?

An LLM agent is a system where the model doesn't just *generate text* — it *takes actions* in a loop. A **code agent** is a specific flavor where those actions are expressed as Python code snippets, which are then executed in a sandbox.

The key insight: the LLM writes code, the system runs it, the result is fed back, and the loop repeats until the task is done.

```
┌─────────────────────────────────────────┐
│              Code Agent Loop            │
│                                         │
│   1. LLM generates Thought + Code       │
│              ↓                          │
│   2. System extracts code block         │
│              ↓                          │
│   3. Python executor runs the code      │
│              ↓                          │
│   4. Observation (output) fed back      │
│              ↓                          │
│   5. Repeat until final_answer()        │
│                                         │
└─────────────────────────────────────────┘
```

This is the [ReAct framework](https://arxiv.org/abs/2210.03629): the model alternates between **Reasoning** (thinking about what to do) and **Acting** (executing code), building up context over multiple steps.

### Why "Minimal"?

Production agent frameworks like LangChain, CrewAI, or even Smolagents itself add layers of abstraction: memory backends, tool registries, retry logic, streaming, guardrails, and more. These are valuable, but they obscure the core mechanism.

minimal-agent strips everything down to the essentials:

| Aspect            | Production Framework                | minimal-agent                    |
| ----------------- | ----------------------------------- | -------------------------------- |
| Agent loop        | Abstract runner class               | `while` loop in `run()`          |
| Tool calling      | Complex registry / decorator system | Dict lookup `self.tools[name]`   |
| Code execution    | Docker / E2B sandbox                | Smolagents `LocalPythonExecutor` |
| Prompt management | Template engine with many variables | Single Jinja2 template           |
| Error handling    | Retry + fallback strategies         | Direct error messages            |
| Memory            | Vector DB / conversation store      | Python list `self.history`       |
| Total core code   | Thousands of lines                  | \~100 lines                      |

The tradeoff is clear: minimal-agent won't handle every edge case. But you'll understand every line.

***

## 1.2 Install & Run

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) for Python packaging
- An LLM API key (see supported providers below)
- Python 3.12+

### Setup

```bash
git clone https://github.com/Antropath/minimal-agent.git
cd minimal-agent
```

Create a `.env` file with your model and credentials. The repo uses [LiteLLM](https://docs.litellm.ai/) to support all model providers through a unified interface.

**AWS Bedrock:**

```bash
AWS_ACCESS_KEY_ID=<YOUR-AWS-ACCESS-KEY-ID>
AWS_SECRET_ACCESS_KEY=<YOUR-AWS-SECRET-ACCESS-KEY>
AWS_REGION_NAME=<YOUR-AWS-REGION-NAME>
MODEL="bedrock/anthropic.claude-3-7-sonnet-20250219-v1:0"
```

**Google Gemini:**

```bash
GEMINI_API_KEY=<YOUR-API-KEY>
MODEL="gemini/gemini-2.0-flash"
```

**Volcengine Doubao (Coding Plan):**

[Doubao Seed](https://www.volcengine.com/activity/codingplan) is ByteDance's coding-optimized LLM, available through the Volcengine Ark platform. It supports OpenAI-compatible API, so LiteLLM can call it via the `openai/` prefix with a custom `api_base`.

```bash
ARK_API_KEY=<YOUR-ARK-API-KEY>
MODEL="openai/doubao-seed-2.0-pro"
```

You also need to pass the custom base URL to LiteLLM. Modify the `completion()` call in `agent.py`:

```python
import os

response = completion(
    model=self.model,
    messages=history,
    stream=False,
    stop="<end_code>",
    api_base=os.environ.get("ARK_API_BASE", None),
)
```

And add this to your `.env`:

```bash
ARK_API_BASE=https://ark.cn-beijing.volces.com/api/coding/v3
```

To get started:
1. Register at [Volcengine Ark](https://console.volcengine.com/ark) and complete identity verification
2. Subscribe to a [Coding Plan](https://www.volcengine.com/activity/codingplan) (Lite: ¥9.9/month for first purchase)
3. Create an API Key in the Ark console → API Key Management
4. Enable the `doubao-seed-2.0-pro` model in Model Management

> **Note:** The standard Ark API endpoint is `https://ark.cn-beijing.volces.com/api/v3`. The `/api/coding/v3` endpoint is specifically for Coding Plan subscribers and offers better pricing for coding tasks.

For other providers, refer to the [LiteLLM documentation](https://docs.litellm.ai/docs/providers). You may need to add extra dependencies with `uv add <package>` (e.g., Bedrock requires `boto3`, already included).

> **Model choice matters:** Code agents require powerful LLMs. Claude 3.7 Sonnet, Amazon Nova Pro, or Gemini 2.0 Flash are recommended. Weaker models may produce poor results.

### Run the Default Example

```bash
uv run run_agent.py
```

This runs the default task: *"What was the hottest day in 2024 and how much was the Dow Jones on that day?"* with DuckDuckGo search and webpage visiting tools.

### Customizing the Task

Edit `run_agent.py` to change the task:

```python
res = agent.run("<Your task here in natural language>")
```

> **Note:** The original `run_agent.py` is missing the import for `DuckDuckGoSearchTool`. It imports `TavilySearchTool` but uses `DuckDuckGoSearchTool` in the tools list. Add `from minimal_agent.tools import DuckDuckGoSearchTool` to fix this.

### Switching to Tavily Search

DuckDuckGo is rate-limited. For reliable results, switch to [Tavily](https://www.tavily.com/):

```bash
# Add to .env:
TAVILY_API_KEY=<YOUR-TAVILY-API-KEY>
```

```python
# In run_agent.py, replace:
# DuckDuckGoSearchTool(max_results=10),
# With:
TavilySearchTool(max_results=10),
```

***

## 1.3 Project Structure

```
minimal-agent-20250606/
├── pyproject.toml              # Project metadata & dependencies
├── run_agent.py                # Entry point — configure & run the agent
├── src/
│   └── minimal_agent/
│       ├── __init__.py         # Empty (package marker)
│       ├── agent.py            # Core Agent class (~157 lines)
│       ├── prompts.py          # System prompt template with Jinja2
│       └── tools.py            # Tool classes (FinalAnswer, Search, VisitWebpage)
├── media/
│   ├── architecture.drawio     # Editable architecture diagram
│   └── architecture.svg        # Rendered architecture diagram
├── .python-version             # Python 3.12
└── LICENSE                     # Apache 2.0
```

### File-by-File Roles

| File             | Role                              | Key Classes/Functions                                                             | Depends On                                                      |
| ---------------- | --------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `agent.py`       | Core agent loop and orchestration | `Agent.__init__`, `Agent.run`, `Agent.step`, `Agent._extract_python_code`         | `litellm`, `smolagents`, `prompts.py`, `tools.py`               |
| `prompts.py`     | System prompt template            | `SYSTEM_PROMPT` (Jinja2 template string)                                          | None (pure string)                                              |
| `tools.py`       | Tool implementations              | `FinalAnswerTool`, `DuckDuckGoSearchTool`, `TavilySearchTool`, `VisitWebpageTool` | `requests`, `markdownify`, `duckduckgo-search`, `tavily-python` |
| `run_agent.py`   | User-facing entry point           | Configures model, tools, and task                                                 | `agent.py`, `tools.py`, `dotenv`                                |
| `pyproject.toml` | Package config & dependencies     | `hatchling` build system, 9 runtime dependencies                                  | —                                                               |

The entire agent logic lives in **3 source files** totaling \~440 lines. The core [agent.py](../src/minimal_agent/agent.py) alone is only \~157 lines.

***

## 1.4 The ReAct Loop — Big Picture

Before diving into code in the next chapters, let's trace the full lifecycle of a single agent run. This diagram shows what happens when you call `agent.run("What was the hottest day in 2024?")`:

```
                    ┌──────────────────┐
                    │  agent.run(task) │
                    └────────┬─────────┘
                             │
                    ┌────────▼────────┐
                    │ Add task as     │
                    │ user message    │
                    │ to history      │
                    └────────┬────────┘
                             │
               ┌─────────────▼──────────────┐
               │  WHILE step < max_steps    │◄──────────────┐
               │                            │               │
               │  ┌──────────────────────┐  │               │
               │  │ 1. Call LLM with     │  │               │
               │  │    full history      │  │               │
               │  │    (system + user +  │  │               │
               │  │     assistant msgs)  │  │               │
               │  └──────────┬───────────┘  │               │
               │             │              │               │
               │  ┌──────────▼───────────┐  │               │
               │  │ 2. Extract Python    │  │               │
               │  │    code from LLM     │  │               │
               │  │    response (regex)  │  │               │
               │  └──────────┬───────────┘  │               │
               │             │              │               │
               │  ┌──────────▼───────────┐  │               │
               │  │ 3. Execute code in   │  │               │
               │  │    LocalPythonExec   │  │               │
               │  │    (sandboxed)       │  │               │
               │  └──────────┬───────────┘  │               │
               │             │              │               │
               │  ┌──────────▼───────────┐  │               │
               │  │ 4. Was final_answer  │  │               │
               │  │    called?           │  │               │
               │  └────┬────────────┬────┘  │               │
               │       │ YES        │ NO    │               │
               │  ┌────▼────┐  ┌────▼────┐  │               │
               │  │ Return  │  │ Append  │  │               │
               │  │ answer  │  │ observa-│  │               │
               │  │         │  │ tion to │──┘               │
               │  └─────────┘  │ history │                  │
               │               └─────────┘                  │
               └────────────────────────────────────────────┘
               (if max_steps exceeded → return error message)
```

Key observations:

- The **history list** is the agent's memory. It grows every step.
- The LLM sees the **entire history** on every call — it reads all prior thoughts, code, and observations.
- The loop terminates when the LLM's code calls `final_answer()` or when `max_steps` is reached.
- Observations are given `role: "user"` so the LLM treats them as external feedback.

***

## 1.5 End-to-End Walkthrough

Let's trace a complete agent run with the default example task to see the ReAct loop in action.

### Entry Point

[run\_agent.py](../run_agent.py) creates the agent and kicks off the run:

```python
from minimal_agent.agent import Agent
from minimal_agent.tools import VisitWebpageTool, TavilySearchTool, DuckDuckGoSearchTool

agent = Agent(
    model=os.environ.get("MODEL"),
    tools=[
        DuckDuckGoSearchTool(max_results=10),
        VisitWebpageTool(max_output_length=1000),
    ],
)

res = agent.run(
    "What was the hottest day in 2024 and how much was the Dow Jones on that day?"
)
```

### Step-by-Step Execution

**Step 1 — First LLM call + search:**

````
history = [system, "Task: What was the hottest day in 2024..."]
  ↓ LLM generates:
  "Thought: I need to search for the hottest day in 2024 first.
   Code:
   ```py
   result = web_search(query='hottest day in 2024 worldwide')
   print(result)
   ```<end_code>"

  ↓ Executor runs: web_search("hottest day in 2024 worldwide")
  ↓ Observation:
  "## Search Results
   [Hottest Day 2024](https://...) - July 22 was confirmed as..."
````

**Step 2 — Visit webpage:**

````
  ↓ LLM generates:
  "Thought: Let me visit that page to get more details.
   Code:
   ```py
   page = visit_webpage(url='https://...')
   print(page)
   ```<end_code>"

  ↓ Executor runs: visit_webpage("https://...")
  ↓ Observation:
  "July 22, 2024 was the hottest day ever recorded..."
````

**Step 3 — Search for Dow Jones:**

````
  ↓ LLM generates:
  "Thought: Now I need to find the Dow Jones value on July 22.
   Code:
   ```py
   dow = web_search(query='Dow Jones Industrial Average July 22 2024')
   print(dow)
   ```<end_code>"

  ↓ Observation: search results with Dow Jones value
````

**Step 4 — Final answer:**

````
  ↓ LLM generates:
  "Thought: I have both pieces of information now.
   Code:
   ```py
   final_answer('The hottest day in 2024 was July 22, and the Dow Jones was at 42,358 points on that day.')
   ```<end_code>"

  ↓ Executor runs: final_answer("The hottest day...")
  ↓ is_final_answer = True
  → Returns "The hottest day in 2024 was July 22, and the Dow Jones was at 42,358 points on that day."
````

### Inspecting the Result

The `run()` method returns a plain string:

```python
res = agent.run("What was the hottest day in 2024...")

print(res)
# "The hottest day in 2024 was July 22, and the Dow Jones was at 42,358 points on that day."
```

You can inspect the full conversation history after the run:

````
agent.history structure:
  [0] system    → "You are an expert assistant who can solve any task..."
  [1] user      → "Task: What was the hottest day in 2024..."
  [2] assistant → "Thought: I need to search for...\nCode:\n```py\nresult = web_search(...)\nprint(result)\n```"
  [3] user      → "Observation:\n## Search Results\n\n[Hottest Day 2024](https://...)..."
  [4] assistant → "Thought: Let me visit that page...\nCode:\n```py\npage = visit_webpage(...)\nprint(page)\n```"
  [5] user      → "Observation:\nJuly 22, 2024 was the hottest day..."
  [6] assistant → "Thought: Now I need to find the Dow Jones...\nCode:\n```py\ndow = web_search(...)\nprint(dow)\n```"
  [7] user      → "Observation:\n## Search Results\n\n[Dow Jones July 22](https://...)..."
  [8] assistant → "Thought: I have both pieces...\nCode:\n```py\nfinal_answer('July 22...')\n```"
  ← No observation for step 4 because run() returned immediately
````

Key observations from the history:

- Messages alternate: `assistant` (thought+code) → `user` (observation)
- Each observation is prefixed with `"Observation:\n"`
- The last assistant message contains `final_answer()` — this is the termination signal
- The history never gets the observation for the final step, because `run()` returns before appending it

Unlike production frameworks that return rich result objects (with token usage, timing, tool call counts, etc.), minimal-agent returns just the final answer string. For debugging, you can:

1. Set `logging.INFO` to see each step's thought and observation
2. Inspect `agent.history` after the run
3. Modify `step()` to print additional details

***

## 1.6 What's Next

Now that you've seen the agent in action, the following chapters dive into each component in depth:

| Chapter  | Topic                  | Core Question                                                            |
| -------- | ---------------------- | ------------------------------------------------------------------------ |
| **Ch 2** | Agent Core             | How does the `Agent` class orchestrate the ReAct loop?                   |
| **Ch 3** | System Prompt          | How does the Jinja2 template instruct the LLM to behave as a code agent? |
| **Ch 4** | Tool System            | How do tools work, and how do you create custom ones?                    |
| **Ch 5** | Execution & Extensions | How does the sandboxed executor work, and how can you extend the agent?  |

