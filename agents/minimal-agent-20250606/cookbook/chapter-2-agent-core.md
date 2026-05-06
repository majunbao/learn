# Chapter 2: Agent Core — The ReAct Loop in Code

This chapter dives into the `Agent` class in [agent.py](../src/minimal_agent/agent.py) — the ~157-line module that powers the entire agent. You'll see how the ReAct loop is implemented as a `while` loop, how each step works, and what bugs lurk in the simplicity.

**What you'll learn:** How `Agent.__init__` bootstraps the agent, how `step()` implements one ReAct iteration, how `run()` orchestrates the loop, and the subtle bugs in the current implementation.

**Prerequisites:** Chapter 1 (you've seen the big picture and run the agent).

## How to Read This Chapter

**Pass 1 — Build intuition:**
2.1 → 2.2 → 2.3 (skip 🔥 Source Walkthrough) → 2.4 (skip 🔥 Source Walkthrough) → 2.5

**Pass 2 — Dive into source code:**
- §2.3 🔥 `Agent.__init__` — bootstrapping the three subsystems
- §2.4 🔥 `Agent.step` — the heart of the ReAct loop

**Pass 3 — Fill gaps:**
- How code is extracted from LLM output? → §2.4 (Code Extraction Regex)
- How does the loop terminate? → §2.5 (Bug Alert + history growth)
- What are the constructor parameters? → §2.3 (Parameter Deep Dive)

---

## 2.1 Agent Architecture at a Glance

The `Agent` class has three responsibilities:

```
┌──────────────────────────────────────────────────┐
│                  Agent Class                      │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────┐ │
│  │  Subsystem 1  │  │  Subsystem 2  │  │ Sub 3  │ │
│  │  Python       │  │  System       │  │ History│ │
│  │  Executor     │  │  Prompt       │  │        │ │
│  │  + Tools      │  │  (Jinja2)     │  │ (list) │ │
│  └──────┬───────┘  └──────┬───────┘  └───┬────┘ │
│         │                 │               │      │
│         └─────────┬───────┘───────────────┘      │
│                   │                              │
│           ┌───────▼───────┐                      │
│           │  run() loop   │                      │
│           │  step() logic │                      │
│           └───────────────┘                      │
└──────────────────────────────────────────────────┘
```

| Subsystem | What It Does | Initialized In |
|-----------|-------------|----------------|
| **Python Executor + Tools** | Sandboxed code execution with tool access | `__init__` (lines 62–74) |
| **System Prompt** | Jinja2-rendered instructions for the LLM | `__init__` → `initialize_system_prompt()` |
| **History** | Growing list of messages (system, user, assistant) | `__init__` (starts with system prompt) |

The `run()` method is the orchestrator. The `step()` method is the workhorse.

---

## 2.2 The Three Subsystems in Brief

Before the source walkthrough, here's what each subsystem provides:

### Python Executor + Tools

The executor (from Smolagents' `LocalPythonExecutor`) provides sandboxed Python execution. Tools are injected via `send_tools()` so the LLM's code can call them like regular functions. The `FinalAnswerTool` is always appended — it's the termination signal.

### System Prompt

A Jinja2 template rendered with tool descriptions and authorized imports. It tells the LLM:
- What it is ("expert assistant")
- How to behave (Thought → Code → Observation cycle)
- What tools it has (dynamically listed)
- What rules to follow (10 rules)

The full prompt is covered in **Chapter 3**.

### History

A Python list of dicts with `role` and `content` keys. Starts with the system prompt, then grows as the agent runs. Each step adds an assistant message (thought+code) and a user message (observation).

---

## 2.3 Agent Initialization — Bootstrapping the Agent

### 🔥 Source Walkthrough: Agent.__init__

```python
class Agent:
    def __init__(
        self,
        model,                     # (A) LiteLLM model identifier, e.g. "gemini/gemini-2.0-flash"
        tools=None,                # (B) List of Tool objects the agent can use
        authorized_imports=None,   # (C) Python modules the agent is allowed to import
        max_steps=10,              # (D) Safety limit — stop after this many steps
    ):
        self.model = model
        self.max_steps = max_steps

        # ── Subsystem 1: Python Executor ──────────────────────────

        # 1.1 Always add FinalAnswerTool — this is how the agent
        #     signals "I'm done, here's the answer".
        #     Tools are stored as a dict keyed by name for O(1) lookup.
        self.tools = {tool.name: tool for tool in tools + [FinalAnswerTool()]}
        #                  ↑ dict comprehension          ↑ append mandatory tool

        # 1.2 Whitelist of Python modules the agent can import.
        #     Default: safe standard library modules only.
        self.authorized_imports = authorized_imports or BASE_BUILTIN_MODULES
        #  BASE_BUILTIN_MODULES = [
        #      "collections", "datetime", "itertools", "math",
        #      "queue", "random", "re", "stat", "statistics",
        #      "time", "unicodedata",
        #  ]

        # 1.3 Create the sandboxed Python executor from Smolagents.
        #     send_tools() makes our tool objects available as
        #     callable functions inside the sandbox.
        self.python_executor = LocalPythonExecutor(
            additional_authorized_imports=[],      # no extra imports beyond defaults
        )
        self.python_executor.send_tools(self.tools)  # inject tools into sandbox

        # ── Subsystem 2: System Prompt ────────────────────────────

        # Render the Jinja2 template with actual tool descriptions
        # and authorized imports. The prompt tells the LLM how to behave.
        self.system_prompt = self.initialize_system_prompt(SYSTEM_PROMPT)

        # ── Subsystem 3: Message History ──────────────────────────

        # Start with only the system prompt. User task and agent
        # interactions will be appended during run().
        self.history = [{"role": "system", "content": self.system_prompt}]
```

**Key Insights:**

1. **`tools + [FinalAnswerTool()]`** — The `FinalAnswerTool` is *always* appended, even if the user provides an empty tools list. Without it, the agent has no way to signal completion and would loop forever. **Bug alert:** the default value is `tools=None`, so calling `Agent(model="...")` without tools would crash on `None + [FinalAnswerTool()]`. The default in `run_agent.py` always passes a list, so this bug is latent but real. A fix would be `self.tools = {tool.name: tool for tool in (tools or []) + [FinalAnswerTool()]}`.

2. **Dict storage for tools** — Tools are stored as `{name: tool_object}` rather than a list. This is because the `LocalPythonExecutor.send_tools()` method expects a dict, and it enables O(1) lookup when the agent calls a tool by name inside code.

3. **`additional_authorized_imports=[]`** — The executor is initialized with no *additional* imports, but it has its own default allowed set. The `authorized_imports` field on the Agent is rendered into the system prompt as a *rule* for the LLM ("you can only import from these modules"), but it's the executor that actually enforces what can be imported.

4. **History starts with system prompt only** — The task hasn't been added yet. It's appended in `run()` when the user provides it. This design means you can call `run()` multiple times on the same agent (though the history from the first run would persist).

5. **`max_steps=10`** — This is the only safety valve. If the agent can't solve the task in 10 steps, it returns a hardcoded error string. There's no retry logic, no fallback model, no human-in-the-loop.

### Parameter Deep Dive

| Parameter | Type | Default | Purpose | Edge Cases |
|-----------|------|---------|---------|------------|
| `model` | `str` | (required) | LiteLLM model identifier passed directly to `litellm.completion()` | Must match a valid LiteLLM model name; invalid names raise `litellm` exceptions at runtime |
| `tools` | `list[Tool]` or `None` | `None` | Tool objects the agent can invoke in code | If `None`, crashes on `None + [FinalAnswerTool()]`. Fix: pass `tools=[]` or patch the code |
| `authorized_imports` | `list[str]` or `None` | `None` | Python modules the LLM is *told* it can import (rendered in prompt) | This is a prompt-level constraint, not an executor-level enforcement. The executor's own import whitelist is separate |
| `max_steps` | `int` | `10` | Maximum ReAct loop iterations before giving up | Setting too low (e.g., 1-2) will fail for most multi-step tasks; setting too high risks infinite loops with no timeout |

---

## 2.4 The Step Function — Heart of the ReAct Loop

The `step()` method implements one iteration: LLM call → code extraction → execution → observation. It's the smallest complete unit of agent reasoning.

### 🔥 Source Walkthrough: Agent.step

```python
def step(self, history: list) -> list:
    # ── Phase 1: LLM generates a thought ────────────────────────

    # Call LiteLLM's completion API with the full conversation history.
    # stop="<end_code>" tells the LLM to stop generating when it
    # writes this token — which is the end-of-code delimiter in our
    # prompt format.
    response = completion(
        model=self.model,
        messages=history,
        stream=False,
        stop="<end_code>"
    )
    # Extract the text content from the response object.
    thought = response.choices[0].message.content

    # Append the LLM's response to history as an "assistant" message.
    # Next time the LLM is called, it will see its own prior output.
    self.history.append({"role": "assistant", "content": thought})

    # ── Phase 2: Extract code from the thought ──────────────────

    # The LLM writes code inside ```py ... ``` blocks.
    # This regex finds the first such block.
    code_action = self._extract_python_code(thought)

    # ── Phase 3: Execute code in sandbox ────────────────────────

    # The executor runs the code and returns:
    #   output          — the return value (meaningful only if final_answer was called)
    #   execution_logs  — everything printed during execution (stdout)
    #   is_final_answer — True if the code called final_answer()
    output, execution_logs, is_final_answer = self.python_executor(
        code_action=code_action
    )

    # ── Phase 4: Create observation ─────────────────────────────

    # The observation is formatted as a user message so the LLM
    # treats it as external feedback. "Observation:\n" prefix
    # matches the format described in the system prompt.
    observation = {"role": "user", "content": "Observation:\n" + execution_logs}

    return is_final_answer, observation, output
```

**Key Insights:**

1. **`stop="<end_code>"`** — This is a crucial detail. The system prompt instructs the LLM to end each code block with `<end_code>`. By passing this as the `stop` parameter to the LLM API, the model stops generating *exactly* at that token. This prevents the LLM from hallucinating a fake "Observation:" after its code (which it would otherwise do, since the few-shot examples show observations following code).

2. **Observations have `role: "user"`** — This is a deliberate design choice. If the observation had `role: "assistant"`, the LLM would see it as its own output and might try to continue from there. By making it a `user` message, the LLM treats it as external input and generates a fresh response.

3. **`self._extract_python_code(thought)`** — The regex `r"```py([\s\S]*?)```"` extracts the first Python code block. If the LLM doesn't write any code (e.g., it just thinks without acting), `code_action` will be `None`, and the executor will handle that gracefully.

4. **Three return values** — The step function returns a tuple, not a result object. This is minimal-agent's style: no dataclasses, no type wrappers. `is_final_answer` is the control signal, `observation` goes into history, and `output` is the final answer string (or `None` if not final).

5. **`self.history` vs `history` parameter** — `step()` receives `history` as a parameter but also mutates `self.history`. The `history` parameter is the same list as `self.history` (Python passes lists by reference), so appending to `self.history` inside `step()` also updates the list that `run()` iterates over. This implicit coupling works but is fragile — a refactor that copies the list before passing would break the history tracking.

6. **History grows unboundedly** — There's no truncation, summarization, or token counting. For long tasks, the history can grow to exceed the model's context window, causing API errors. This is one of the tradeoffs of the minimal design.

### The Code Extraction Regex

The `_extract_python_code` method is simple but critical:

```python
def _extract_python_code(self, text: str) -> None | str:
    pattern = r"```py([\s\S]*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None
```

| Aspect | Detail |
|--------|--------|
| Pattern | `` ```py `` opening + captured content + `` ``` `` closing |
| `[\s\S]*?` | Non-greedy match for any character including newlines |
| `.strip()` | Removes leading/trailing whitespace from extracted code |
| Returns `None` | If no code block found — the executor will receive `None` as `code_action` |
| Only first match | `re.search` finds the first match; if the LLM writes multiple code blocks, only the first is executed |

The non-greedy `*?` is important — without it, the regex would match from the first `` ```py `` to the *last* `` ``` `` in the entire text, potentially spanning multiple code blocks.

### Step Execution Flow

```
step(history)
  │
  ├── 1. LLM completion(model, messages=history, stop="<end_code>")
  │     → returns full text: "Thought: ...\nCode:\n```py\n...\n```<end_code>"
  │
  ├── 2. _extract_python_code(text)
  │     → returns: Python code string (or None)
  │
  ├── 3. python_executor(code_action=code)
  │     → returns: (output, execution_logs, is_final_answer)
  │
  └── 4. Format observation as {"role": "user", "content": "Observation:\n" + logs}
        → returns: (is_final_answer, observation, output)
```

---

## 2.5 The Run Loop — Orchestration and Bugs

The `run()` method ties everything together into a while loop:

```python
def run(self, task: str) -> str:
    self.history.append({"role": "user", "content": f"Task: {task}"})

    task_completed = False
    nr_steps = 0
    while not task_completed or nr_steps <= self.max_steps:
        logger.info(f"!STEP!: {nr_steps}")
        is_final_answer, observation, output = self.step(self.history)
        logger.info(f"!Observation!: {observation['content']}")
        self.history.append(observation)
        nr_steps += 1
        if is_final_answer:
            return output
    return "Could not solve task: Maximum number of steps exceeded."
```

### Bug Alert: The Loop Condition

There's a subtle bug in the while condition: `while not task_completed or nr_steps <= self.max_steps`. With `or`, this loop will **always** run as long as `nr_steps <= self.max_steps`, regardless of `task_completed`. The intended logic was likely `and`:

```python
# Intended: loop while task is not done AND we haven't exceeded steps
while not task_completed and nr_steps < self.max_steps:
```

However, in practice, the bug is mitigated because `is_final_answer` causes an early `return`. The `task_completed` variable is never actually set to `True` — it's a **dead variable** that serves no purpose. The loop relies entirely on the `if is_final_answer: return` check and the `nr_steps` counter to terminate.

There's also an off-by-one issue: `nr_steps <= self.max_steps` should likely be `nr_steps < self.max_steps` (using `<` not `<=`), otherwise the agent runs `max_steps + 1` steps instead of `max_steps`.

### Bug Summary

| Bug | Location | Impact | Mitigation |
|-----|----------|--------|------------|
| `tools=None` crashes on list concat | `__init__` line 58 | `Agent(model="...")` without tools raises `TypeError` | Always pass `tools=[]` explicitly |
| `or` vs `and` in while condition | `run()` line 71 | `task_completed` is dead code; loop condition is wrong | `is_final_answer: return` catches it |
| Off-by-one: `<=` vs `<` | `run()` line 71 | Agent runs `max_steps + 1` steps instead of `max_steps` | Rarely matters in practice |
| `step()` mutates `self.history` via param | `step()` line 82 | Implicit coupling; fragile if refactored | Works by Python reference semantics |

### Message History Growth Pattern

Here's how the history grows across a 3-step run:

```
Step 0 (start):
  [0] system  → "You are an expert assistant..."
  [1] user    → "Task: What was the hottest day in 2024?"

Step 1 (after step 0):
  [2] assistant → "Thought: I'll search for...\nCode:\n```py\nresult = web_search(...)\nprint(result)\n```<end_code>"
  [3] user      → "Observation:\n## Search Results\n\n[Title](url)\nBody text..."

Step 2 (after step 1):
  [4] assistant → "Thought: Let me visit that page...\nCode:\n```py\npage = visit_webpage(...)\nprint(page)\n```<end_code>"
  [5] user      → "Observation:\nThe hottest day in 2024 was..."

Step 3 (after step 2, final answer):
  [6] assistant → "Thought: I now have the answer.\nCode:\n```py\nfinal_answer('July 22, 2024')\n```<end_code>"
  → Returns "July 22, 2024"
```

Each step adds exactly **2 messages** to history: the assistant's thought+code, and the user observation. This doubling is why the history can grow quickly — by step 10, the history contains 22 messages (1 system + 1 task + 20 step messages).

### Data Flow: step() → run() → history

```
run()                                step()
  │                                    │
  │── self.step(self.history) ────────►│
  │                                    │
  │   Inside step():                   │
  │   1. LLM call → thought            │
  │   2. self.history.append(thought)  │  ← mutates same list
  │   3. extract code                  │
  │   4. executor runs code            │
  │   5. create observation dict       │
  │                                    │
  │◄── (is_final, observation, output)─│
  │                                    │
  │   self.history.append(observation) │
  │   if is_final: return output       │
```

The key point: `self.history` is both read (passed to LLM) and written (appended to) in every step. The history *is* the agent's entire state.
