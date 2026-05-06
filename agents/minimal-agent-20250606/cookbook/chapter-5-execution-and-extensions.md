# Chapter 5: Execution Sandbox & Extensions

The `LocalPythonExecutor` from Smolagents is where the LLM's code actually runs. This chapter explains how the sandbox works, the security model, how `final_answer` detection operates, and directions for extending the agent beyond its minimal design.

**What you'll learn:** How the executor provides sandboxed execution, the two-layer import restriction model, security limitations, and practical extension ideas (memory, timeout, token tracking).

**Prerequisites:** Chapters 1–4 (you understand the agent loop, system prompt, and tools).

## How to Read This Chapter

**Pass 1 — Build intuition:**
5.1 → 5.2 → 5.3 → 5.4 → 5.5

**Pass 2 — Dive into source code:**
No 🔥 walkthroughs in this chapter — the executor is from Smolagents, not part of minimal-agent's source. Instead, focus on the flow diagrams and comparison tables.

**Pass 3 — Fill gaps:**
- How `final_answer` detection works? → §5.2
- Import restriction details? → §5.3
- Security limitations? → §5.4
- Extension ideas? → §5.5

---

## 5.1 How the Executor Fits into the Agent

The `LocalPythonExecutor` bridges the gap between the LLM's text output and actual code execution:

```
Agent                    LocalPythonExecutor
  │                              │
  │  self.python_executor(       │
  │      code_action=code        │
  │  )                           │
  │ ──────────────────────────►  │
  │                              │  1. Parse code_action as Python
  │                              │  2. Check tool calls against self.tools
  │                              │  3. Execute in restricted namespace
  │                              │  4. Capture stdout → execution_logs
  │                              │  5. Detect final_answer() → is_final_answer
  │  ◄────────────────────────── │
  │  (output, logs, is_final)    │
```

### What the Executor Provides

| Feature | How It Works | Configured By |
|---------|-------------|---------------|
| **Tool access** | `send_tools(self.tools)` injects each tool as a callable function in the execution namespace | `Agent.__init__` |
| **Import restrictions** | `additional_authorized_imports` controls which modules can be imported | `Agent.__init__` |
| **State persistence** | Variables defined in one `code_action` persist to the next call | Automatic (namespace lives across calls) |
| **Output capture** | `print()` outputs are captured and returned as `execution_logs` | Automatic (stdout redirect) |
| **Final answer detection** | When `final_answer()` is called, the executor sets `is_final_answer = True` | Convention (tool named `final_answer`) |

### Initialization in Agent.__init__

```python
self.python_executor = LocalPythonExecutor(
    additional_authorized_imports=[],
)
self.python_executor.send_tools(self.tools)
```

Two things happen:
1. The executor is created with no *additional* authorized imports (it has its own defaults)
2. `send_tools()` injects the tool dict into the executor's namespace

---

## 5.2 How `final_answer` Detection Works

The `LocalPythonExecutor` doesn't have special knowledge of `final_answer`. Instead, it uses a convention-based mechanism:

```
1. send_tools({                       Executor Namespace:
     "web_search": DuckDuckGo...,       web_search = <callable>
     "visit_webpage": VisitWeb...,      visit_webpage = <callable>
     "final_answer": FinalAnswer...     final_answer = <callable>
   })

2. LLM code executes:                  final_answer("July 22")
   → calls FinalAnswerTool.__call__("July 22")
   → returns "July 22"

3. Executor detects:                   is_final_answer = True
   tool named "final_answer"           output = "July 22"
   was called with a return value

4. Returns:                            ("July 22", logs, True)
```

The key design insight: **the tool itself is trivial** (just `return answer`), but the **executor's awareness of it** is what makes the agent loop terminate. This is a convention established by Smolagents' `LocalPythonExecutor`.

### Executor Call Flow

Here's what happens inside the executor when it receives a `code_action`:

```
LocalPythonExecutor(code_action=code)
  │
  ├── 1. Parse code_action as Python AST
  │
  ├── 2. Execute in restricted namespace
  │     ├── Namespace includes: tool functions, authorized imports,
  │     │   and variables from previous executions
  │     ├── print() outputs → captured to stdout buffer
  │     └── final_answer() call → detected, return value stored
  │
  ├── 3. Collect results
  │     ├── execution_logs = captured stdout (everything printed)
  │     ├── is_final_answer = True if final_answer was called
  │     └── output = the value passed to final_answer (or None)
  │
  └── 4. Return (output, execution_logs, is_final_answer)
```

### State Persistence Across Steps

One of the most powerful features of the executor is that variables persist across steps. When the LLM writes:

```python
# Step 1:
search_result = web_search(query="hottest day 2024")
print(search_result)

# Step 2 (search_result is still accessible!):
visit_result = visit_webpage(url="https://...")
print(visit_result)
```

The `search_result` variable from step 1 is still in the namespace when step 2 executes. This is because the `LocalPythonExecutor` maintains a persistent state dictionary across `__call__` invocations.

This has important implications:
- **Pro:** The LLM can build up state incrementally — no need to re-fetch data
- **Con:** The namespace can get cluttered, and the LLM might accidentally reference stale variables from earlier steps
- **Con:** Memory usage grows over time as more variables accumulate

---

## 5.3 Two-Layer Import Restriction

There are **two separate** import control mechanisms, and they work independently:

### Layer 1: System Prompt (Soft Constraint)

`self.authorized_imports` is rendered into the prompt text:

```
you can use imports in your code, but only from the following list of modules:
['collections', 'datetime', 'itertools', 'math', 'queue', 'random', 're',
 'stat', 'statistics', 'time', 'unicodedata']
```

This tells the LLM "you can only import from these modules." But the LLM could ignore this rule and write `import os` anyway.

### Layer 2: Executor (Hard Constraint)

The `LocalPythonExecutor` has its own import whitelist. Even if the LLM writes `import os`, the executor will block it if `os` isn't in the allowed list.

### Comparison

| Aspect | Prompt Level | Executor Level |
|---------|-------------|----------------|
| Mechanism | Text instruction in system prompt | Import hook in Python runtime |
| Enforcement | Soft (LLM *should* comply) | Hard (code *cannot* import) |
| Configured by | `authorized_imports` parameter | `additional_authorized_imports` parameter |
| Default modules | `BASE_BUILTIN_MODULES` (11 modules) | Executor's own default set |
| Can be bypassed? | Yes (LLM can ignore instructions) | Harder (requires Python introspection tricks) |

In minimal-agent's default configuration, both layers are set to the same list (`BASE_BUILTIN_MODULES`), but they're enforced differently. This two-layer defense is important for security — the prompt is the first line of defense, and the executor is the second.

### The `authorized_imports` vs `additional_authorized_imports` Disconnect

There's a subtle disconnect: the Agent's `authorized_imports` is rendered into the prompt, but the executor is initialized with `additional_authorized_imports=[]`. These are **different parameters**:

- `Agent.authorized_imports` → rendered into the system prompt (tells the LLM what's allowed)
- `LocalPythonExecutor(additional_authorized_imports=[])` → controls what the executor actually permits

If you pass `authorized_imports=["pandas"]` to the Agent, the prompt will tell the LLM it can import `pandas`, but the executor won't allow it because `additional_authorized_imports` is still `[]`. To fix this, you'd need to also pass `additional_authorized_imports=["pandas"]` to the executor.

This is arguably a bug — the Agent doesn't propagate `authorized_imports` to the executor's `additional_authorized_imports`.

---

## 5.4 Security Considerations

The `LocalPythonExecutor` is **not** a full sandbox. It restricts imports and provides a limited namespace, but:

### Known Limitations

| Limitation | Risk | Mitigation |
|------------|------|------------|
| Same Python process | No OS-level isolation | Use `DockerPythonExecutor` or E2B |
| `__import__` bypass | LLM could write `__import__("os")` | Executor blocks some dunder methods, but not all |
| `eval()` / `exec()` | LLM could use these to bypass restrictions | Block them in the namespace |
| No CPU limit | LLM could write infinite loops | Add a timeout (see §5.5) |
| No memory limit | LLM could allocate huge data structures | Use resource limits or containerization |
| File system access | LLM can read/write files if `open` is in namespace | Ensure `open` is not in the default namespace |

### Production Sandboxing Options

| Option | Isolation Level | Setup Complexity | Cost |
|--------|----------------|------------------|------|
| `LocalPythonExecutor` | Low (same process) | None | Free |
| `DockerPythonExecutor` | Medium (container) | Docker required | Free |
| E2B Cloud Sandbox | High (cloud VM) | API key + E2B account | Per-execution |
| Modal / AWS Lambda | High (serverless) | Cloud account | Per-execution |

For learning and development, `LocalPythonExecutor` is fine. For production use with untrusted tasks, always use containerized or cloud-based execution.

---

## 5.5 Extending the Agent

minimal-agent is a starting point, not a finished product. Here are practical directions you could take it.

### Adding a Memory System

The current agent has no persistent memory between runs. Here's how to add session persistence:

```python
import json
import os

class Agent:
    def __init__(self, ..., session_file="session.json"):
        self.session_file = session_file
        self.system_prompt = self.initialize_system_prompt(SYSTEM_PROMPT)
        self.history = self._load_session()

    def _load_session(self):
        if os.path.exists(self.session_file):
            with open(self.session_file) as f:
                return json.load(f)
        return [{"role": "system", "content": self.system_prompt}]

    def _save_session(self):
        with open(self.session_file, "w") as f:
            json.dump(self.history, f)
```

Call `_save_session()` at the end of `run()` or after each step. This lets you resume conversations across multiple runs.

**Consideration:** Long sessions will have long histories that consume tokens. Add a history truncation mechanism that summarizes old messages.

### Adding Token Usage Tracking

LiteLLM's `completion()` response includes token usage data. Track it across steps:

```python
def run(self, task: str) -> str:
    self.total_prompt_tokens = 0
    self.total_completion_tokens = 0
    # ... existing run code ...

def step(self, history: list):
    response = completion(model=self.model, messages=history, stream=False, stop="<end_code>")
    usage = response.usage
    self.total_prompt_tokens += usage.prompt_tokens
    self.total_completion_tokens += usage.completion_tokens
    logger.info(f"Tokens — prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens}")
    # ... existing step code ...
```

After the run, you can inspect total usage:

```python
res = agent.run("What was the hottest day in 2024?")
print(f"Total tokens: {agent.total_prompt_tokens + agent.total_completion_tokens}")
```

### Adding a Timeout Per Step

The original `signal.SIGALRM` approach (Unix-only) doesn't work on Windows. Here's a cross-platform solution using threading:

```python
import threading

def step(self, history, timeout=30):
    result = {}
    def run_with_timeout():
        try:
            output, execution_logs, is_final_answer = self.python_executor(
                code_action=code_action
            )
            result["output"] = output
            result["logs"] = execution_logs
            result["is_final"] = is_final_answer
        except Exception as e:
            result["error"] = str(e)

    thread = threading.Thread(target=run_with_timeout)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        execution_logs = f"Code execution timed out after {timeout} seconds."
        is_final_answer = False
        output = None
    elif "error" in result:
        execution_logs = f"Error during execution: {result['error']}"
        is_final_answer = False
        output = None
    else:
        output = result["output"]
        execution_logs = result["logs"]
        is_final_answer = result["is_final"]

    observation = {"role": "user", "content": "Observation:\n" + execution_logs}
    return is_final_answer, observation, output
```

> **Note:** The threading approach can't forcibly kill the thread — it just stops waiting. The Python code might continue running in the background. For true cancellation, use `multiprocessing` with a separate process that can be terminated, or use Smolagents' `DockerPythonExecutor` which can kill the container.

### Adding History Truncation

For long tasks, the history can exceed the model's context window. A simple strategy:

```python
def _truncate_history(self, max_messages=20):
    if len(self.history) > max_messages:
        system_msg = self.history[0]
        recent = self.history[-max_messages + 1:]
        self.history = [system_msg] + recent
```

A more sophisticated approach would use the LLM to summarize old messages before truncating.

---

## 5.6 Comparison: minimal-agent vs. Smolagents CodeAgent

| Feature | minimal-agent | Smolagents CodeAgent |
|---------|--------------|---------------------|
| Core agent loop | Manual `while` loop | `AgentRunner` class with lifecycle hooks |
| Tool protocol | Plain class with attributes | `Tool` base class with `forward()` method |
| Code execution | `LocalPythonExecutor` | `LocalPythonExecutor` or `DockerPythonExecutor` |
| Error recovery | None (errors become observations) | Retry logic, error summarization |
| Memory | None (list only) | Various session backends |
| Streaming | Not supported | Supported |
| Logging | Basic `logging.info` | Structured logging with step tracking |
| Max steps | Hard limit, returns error string | Configurable with different behaviors |
| Planning | None | Optional planning step before action |
| Multi-agent | Not supported | Supported via `ManagedAgent` |
| Import authorization | Two-layer (prompt + executor), disconnected | Unified with `additional_authorized_imports` |

### When to Use What

| Scenario | Use minimal-agent | Use Smolagents |
|----------|-------------------|----------------|
| Learning how agents work | ✅ Perfect | ❌ Too much abstraction |
| Simple, well-defined tasks | ✅ Sufficient | Overkill |
| Production deployment | ❌ Too minimal | ✅ Better error handling |
| Need streaming | ❌ Not supported | ✅ Built-in |
| Need Docker sandboxing | ❌ Manual setup | ✅ Built-in `DockerPythonExecutor` |
| Multi-agent orchestration | ❌ Not supported | ✅ Built-in |
| Custom research / experiments | ✅ Easy to modify | May fight the framework |

The best approach is often: **learn with minimal-agent, then graduate to Smolagents** (or another framework) when you need production features. The core ReAct pattern is the same — you're just adding safety, robustness, and convenience layers.

---

## 5.7 Summary

The executor and extension possibilities complete the picture:

1. **The executor** provides sandboxed Python execution with tool access, import restrictions, state persistence, and `final_answer` detection.
2. **Two-layer import control** (prompt + executor) provides defense in depth, but the current implementation has a disconnect — `authorized_imports` is not propagated to the executor.
3. **Security is limited** — `LocalPythonExecutor` is not a full sandbox. Use Docker or E2B for production.
4. **Extensions are straightforward** — memory, timeout, token tracking, and history truncation can all be added in ~20 lines each.
5. **The ReAct pattern scales** — from 100-line minimal-agent to full Smolagents, the core loop is the same. You're just adding layers of robustness.

With all five chapters, you now understand every line of minimal-agent and the fundamental architecture that powers all LLM code agents.
