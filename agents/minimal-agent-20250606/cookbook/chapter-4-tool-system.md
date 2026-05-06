# Chapter 4: Tool System — Making Python Functions Available to the Agent

Tools are the agent's "hands" — they let it interact with the outside world. In minimal-agent, a tool is simply a Python class with a specific interface. This chapter walks through every built-in tool, explains the tool protocol, and shows how to create custom tools.

**What you'll learn:** The 5-attribute tool protocol, how each built-in tool works (with source code walkthroughs), search tool tradeoffs, and step-by-step custom tool creation.

**Prerequisites:** Chapter 2 (you understand how tools are registered in `Agent.__init__`), Chapter 3 (you've seen how tools are rendered in the system prompt).

## How to Read This Chapter

**Pass 1 — Build intuition:**
4.1 → 4.2 → 4.3 (skip 🔥 walkthroughs) → 4.4 (skip 🔥 walkthrough) → 4.5 → 4.6

**Pass 2 — Dive into source code:**
- §4.3 🔥 FinalAnswerTool — the simplest tool (control signal, not computation)
- §4.3 🔥 VisitWebpageTool — web scraping with HTML→Markdown + error handling
- §4.4 🔥 DuckDuckGoSearchTool — search with eager initialization

**Pass 3 — Fill gaps:**
- Tool protocol details? → §4.1
- How `final_answer` terminates the loop? → §4.2 + §4.3
- Search tool comparison? → §4.5
- Custom tool creation? → §4.6

---

## 4.1 The Tool Protocol

Every tool must implement this interface:

| Attribute/Method | Type | Purpose | Example |
|------------------|------|---------|---------|
| `name` | `str` (class attribute) | Identifier used in code and system prompt | `"web_search"` |
| `description` | `str` (class attribute) | Human-readable description shown to LLM | `"Performs a web search..."` |
| `inputs` | `dict` (class attribute) | JSON-schema-style input specification | `{"query": {"type": "string", "description": "..."}}` |
| `output_type` | `str` (class attribute) | Return type description | `"string"` |
| `__call__` | method | The actual function logic | `def __call__(self, query: str) -> str` |

This is a plain Python convention — **no base class, no abstract methods, no decorator**. If it has these five things, it's a tool. The `LocalPythonExecutor` uses `send_tools()` to inject the `__call__` method into the execution namespace under the `name` attribute.

### How the Protocol Flows

```
Tool class                  System Prompt              Execution Sandbox
  │                              │                          │
  │  name = "web_search"         │                          │
  │  description = "..."    ────►│  Rendered in Jinja2      │
  │  inputs = {...}         ────►│  loop (§3.3)             │
  │  output_type = "string" ────►│                          │
  │                              │                          │
  │  __call__(query)        ──────────────────────────────►│  Available as
  │                              │                          │  web_search(query="...")
```

The `name` and `description` are for the LLM (it reads them in the prompt). The `__call__` method is for the executor (it runs the code). The `inputs` and `output_type` are for both — the LLM reads them to know how to call the tool, and they could theoretically be used for validation (though minimal-agent doesn't validate).

---

## 4.2 The FinalAnswerTool — Termination Signal

The `FinalAnswerTool` is special: it's the only tool that's always included, and it's the only one that affects the control flow of the agent loop.

### How It Works

When the LLM's code calls `final_answer("some answer")`, the execution flow is:

```
LLM code: final_answer("The answer is 42")
    │
    ├── 1. LocalPythonExecutor calls FinalAnswerTool.__call__("The answer is 42")
    │       returns "The answer is 42"
    │
    ├── 2. Executor detects final_answer was called
    │       sets is_final_answer = True
    │       sets output = "The answer is 42"
    │
    └── 3. Agent.step() returns (True, observation, "The answer is 42")
            Agent.run() sees is_final_answer=True, returns "The answer is 42"
```

The tool itself is trivial — it just returns its input. The magic is in the **executor's detection mechanism**: it knows that a call to a function named `final_answer` means the task is done.

---

## 4.3 Built-in Tools — Source Walkthroughs

### 🔥 Source Walkthrough: FinalAnswerTool

```python
class FinalAnswerTool:
    name = "final_answer"
    description = "Provides a final answer to the given problem."
    inputs = {
        "answer": {"type": "any", "description": "The final answer to the problem"}
    }
    output_type = "any"

    def __call__(self, answer):
        return answer
```

**Key Insights:**

1. **`type: "any"`** — The input accepts any type. The LLM can pass a string, number, list, or dict. This is important because some answers are naturally numeric (e.g., `final_answer(88 ** 0.36)`).

2. **`output_type = "any"`** — The return type is also "any". The tool doesn't transform the answer — it passes it through unchanged.

3. **No `__init__`** — This tool has no constructor. It's a stateless singleton. There's no configuration needed.

4. **Always appended** — As seen in Chapter 2, `tools + [FinalAnswerTool()]` ensures this tool is always present. Without it, the agent has no way to signal completion.

5. **The `final_answer` name is a convention** — The `LocalPythonExecutor` from Smolagents specifically looks for a function named `final_answer` to set the `is_final_answer` flag. If you renamed it to `submit_answer`, the executor wouldn't detect it.

### 🔥 Source Walkthrough: VisitWebpageTool

```python
class VisitWebpageTool:
    name = "visit_webpage"
    description = "Visits a webpage at the given url and reads its content as a markdown string."
    inputs = {
        "url": {
            "type": "string",
            "description": "The url of the webpage to visit.",
        }
    }
    output_type = "string"

    def __init__(self, max_output_length: int = 40000):
        super().__init__()
        self.max_output_length = max_output_length

    def __call__(self, url: str) -> str:
        try:
            import re
            import requests
            from markdownify import markdownify
            from requests.exceptions import RequestException
            from smolagents.utils import truncate_content
        except ImportError as e:
            raise ImportError("You must install packages...") from e
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            markdown_content = markdownify(response.text).strip()
            markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)
            return truncate_content(markdown_content, self.max_output_length)
        except requests.exceptions.Timeout:
            return "The request timed out. Please try again later or check the URL."
        except RequestException as e:
            return f"Error fetching the webpage: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"
```

**Key Insights:**

1. **HTML → Markdown conversion** — The `markdownify` library converts HTML to Markdown. This strips scripts, styles, and navigation elements, leaving clean text that's more efficient for the LLM to process.

2. **Truncation at 40,000 chars** — Web pages can be enormous. `truncate_content()` (from Smolagents) cuts the output to `max_output_length` characters. Without this, a single webpage visit could consume the entire context window. In `run_agent.py`, it's configured with `max_output_length=1000` for efficiency.

3. **Lazy imports inside `__call__`** — The imports for `requests`, `markdownify`, etc. are inside the method, not at module level. This means you can install minimal-agent without these packages and only get an error when you actually *use* the tool. The `__init__` doesn't validate dependencies.

4. **Error handling returns strings, not exceptions** — When a request fails, the tool returns a human-readable error string instead of raising an exception. This is by design: the error string becomes the "Observation" in the agent loop, and the LLM can read it and try a different approach. If it raised an exception, the agent would crash.

5. **Multiple whitespace collapse** — `re.sub(r"\n{3,}", "\n\n", ...)` reduces 3+ consecutive newlines to 2. This cleans up markdownified HTML which often has excessive line breaks.

6. **20-second timeout** — `requests.get(url, timeout=20)` sets a generous timeout. If the page takes longer, it returns a friendly error message. The LLM can then try a different URL or search again.

### Tool Error Handling Pattern

The error handling strategy in `VisitWebpageTool` is worth highlighting because it illustrates a key design principle for agent tools:

```
Error Occurs
    │
    ├── Option A: Raise Exception
    │   → Agent crashes (bad)
    │
    └── Option B: Return Error String  ← VisitWebpageTool uses this
        → Error becomes Observation
        → LLM reads it and tries something else
        → Agent continues (good)
```

**Always return error strings, never raise exceptions** — unless you want the agent to crash. This is the most important rule for tool design in minimal-agent.

---

## 4.4 Search Tools

### 🔥 Source Walkthrough: DuckDuckGoSearchTool

```python
class DuckDuckGoSearchTool:
    name = "web_search"
    description = """Performs a duckduckgo web search based on your query
    then returns the top search results."""
    inputs = {
        "query": {"type": "string", "description": "The search query to perform."}
    }
    output_type = "string"

    def __init__(self, max_results=10, **kwargs):
        super().__init__()
        self.max_results = max_results
        try:
            from duckduckgo_search import DDGS
        except ImportError as e:
            raise ImportError(
                "You must install package `duckduckgo_search`..."
            ) from e
        self.ddgs = DDGS(**kwargs)

    def __call__(self, query: str) -> str:
        results = self.ddgs.text(query, max_results=self.max_results)
        if len(results) == 0:
            raise Exception("No results found! Try a less restrictive/shorter query.")
        postprocessed_results = [
            f"[{result['title']}]({result['href']})\n{result['body']}"
            for result in results
        ]
        return "## Search Results\n\n" + "\n\n".join(postprocessed_results)
```

**Key Insights:**

1. **Eager initialization in `__init__`** — Unlike `VisitWebpageTool`, the `DDGS` client is created in `__init__`, not lazily in `__call__`. This means the import error happens immediately when the tool is instantiated, not when it's first called. This is a deliberate choice: you want to know right away if the dependency is missing.

2. **Raises exceptions, doesn't return strings** — When no results are found, it raises `Exception("No results found!")`. This is different from `VisitWebpageTool` which returns error strings. The inconsistency means a "no results" search would crash the agent unless the executor catches it. **This is arguably a bug** — it would be more consistent to return the error message as a string.

3. **Markdown-formatted output** — Results are formatted as `[Title](URL)\nBody` with a `## Search Results` header. This gives the LLM clickable links and descriptions in a format it can parse.

4. **`**kwargs` pass-through** — Extra keyword arguments are forwarded to the `DDGS` constructor, allowing configuration of proxies, headers, etc. without modifying the class.

---

## 4.5 Search Tool Comparison

| Feature | DuckDuckGoSearchTool | TavilySearchTool |
|---------|---------------------|------------------|
| API key required | No | Yes (`TAVILY_API_KEY`) |
| Rate limits | Aggressive (often hits limits) | Generous (paid tier) |
| Result quality | Basic titles + snippets | Titles + full content excerpts |
| Output format | `[Title](url)\nbody` | `[Title](url)\ncontent` |
| Package dependency | `duckduckgo-search` | `tavily-python` |
| Constructor param | `max_results` | `max_results` + `**kwargs` passed to `TavilyClient` |
| Error handling | **Raises exception** on no results | Similar pattern |
| When to use | Quick testing, no signup | Production use, reliable results |

Both tools share the same interface pattern: `name`, `description`, `inputs`, `output_type`, `__init__`, `__call__`. The LLM doesn't know which search backend is being used — it just calls `web_search(query=...)` or `tavily_search(query=...)` and processes the results.

### Tool Initialization Strategy Comparison

| Tool | When Dependencies Are Checked | Where Client Is Created |
|------|------------------------------|------------------------|
| `FinalAnswerTool` | Never (no dependencies) | N/A (stateless) |
| `VisitWebpageTool` | At first `__call__` (lazy) | N/A (stateless per call) |
| `DuckDuckGoSearchTool` | At `__init__` (eager) | In `__init__` |
| `TavilySearchTool` | At `__init__` (eager) | In `__init__` |

The lazy vs eager choice affects the user experience:
- **Eager** (DuckDuckGo, Tavily): You get an `ImportError` immediately when creating the agent. Fail fast.
- **Lazy** (VisitWebpage): The agent starts fine, but crashes when the tool is first used. Fail late.

For production, eager is better — you want to know about missing dependencies before you start a task.

---

## 4.6 Creating Custom Tools

The tool protocol is so simple that adding a new tool takes just a few lines. Here's a step-by-step guide.

### Step 1: Define the Tool Class

```python
class CalculatorTool:
    name = "calculator"
    description = "Evaluates a mathematical expression and returns the result."
    inputs = {
        "expression": {
            "type": "string",
            "description": "The mathematical expression to evaluate, e.g. '2 + 3 * 4'.",
        }
    }
    output_type = "string"

    def __call__(self, expression: str) -> str:
        try:
            result = eval(expression, {"__builtins__": {}}, {"math": __import__("math")})
            return str(result)
        except Exception as e:
            return f"Error evaluating expression: {e}"
```

> **Security Warning:** This example uses `eval()` with `__builtins__` set to `{}` to restrict access to built-in functions. This is a reasonable sandboxing measure for a demo, but it's **not truly safe** — Python's `eval()` can be exploited through attribute access on allowed objects (e.g., `"().__class__.__bases__[0].__subclasses__()"` to access dangerous classes). For production use, prefer `ast.literal_eval()` (for literal expressions only) or a dedicated expression parser like `simpleeval`.

### Step 2: Register the Tool

```python
agent = Agent(
    model="gemini/gemini-2.0-flash",
    tools=[
        CalculatorTool(),
        DuckDuckGoSearchTool(max_results=10),
        VisitWebpageTool(max_output_length=1000),
    ],
)
```

The tool will automatically appear in the system prompt (rendered by the Jinja2 template) and be available as `calculator(expression="...")` in the agent's code. No other registration is needed.

### Step 3: Verify in the System Prompt

After creating the agent, you can check that the tool was registered correctly:

```python
print(agent.system_prompt)
# Should include:
# - calculator: Evaluates a mathematical expression...
#     Takes inputs: {'expression': {'type': 'string', ...}}
#     Returns an output of type: string
```

### Design Guidelines for Custom Tools

| Guideline | Why | Example |
|-----------|-----|---------|
| Return strings, not complex objects | The LLM reads the output as text; complex objects may not serialize well | Return `str(result)` not `result` |
| Handle errors gracefully | Return error messages, don't raise exceptions — the agent loop doesn't catch them | `return f"Error: {e}"` |
| Keep output concise | Long outputs consume context window tokens | Truncate at a reasonable length |
| Use descriptive names and descriptions | The LLM chooses tools based on these | `"stock_price"` not `"tool1"` |
| Lazy-import dependencies | Avoid ImportError at module load time | Import inside `__call__` |
| Make tools idempotent when possible | The LLM might call the same tool twice | Cache results or handle duplicate calls |
| Use `__init__` for configuration | Allow users to customize behavior | `max_output_length`, `max_results` |

### Example: A File Reader Tool

```python
class FileReaderTool:
    name = "read_file"
    description = "Reads the content of a text file and returns it as a string."
    inputs = {
        "filepath": {
            "type": "string",
            "description": "The path to the file to read.",
        }
    }
    output_type = "string"

    def __init__(self, max_length: int = 10000):
        self.max_length = max_length

    def __call__(self, filepath: str) -> str:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read(self.max_length)
            if len(content) == self.max_length:
                content += "\n... [truncated]"
            return content
        except FileNotFoundError:
            return f"Error: File not found: {filepath}"
        except PermissionError:
            return f"Error: Permission denied: {filepath}"
        except Exception as e:
            return f"Error reading file: {e}"
```

Note the consistent error handling pattern: all errors are returned as strings, never raised. This ensures the agent can continue and try alternative approaches.
