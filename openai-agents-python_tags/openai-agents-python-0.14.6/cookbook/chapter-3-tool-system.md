# Chapter 3: Tool System — FunctionTool Internals & Calling Flow

The tool system is the reason agents can *act*, not just talk. When the LLM decides to call `get_weather(37.7749, -122.4194)`, a pipeline of validation, guardrails, approval, timeout, and error handling fires before your Python function ever runs — and another pipeline fires after it returns. This chapter walks through every step of that pipeline, from the `@function_tool` decorator to the final output sent back to the LLM.

**How to Read This Chapter**

- **Pass 1 — Build intuition (25 min).** Read §3.1 → §3.2 → §3.4 (parameter table + ToolContext comparison only, skip usage examples) → §3.6 (output type table only) → §3.7 (flow diagram only, skip exception hierarchy) → §3.9 (approval flow diagram only) → §3.10 (7-step ASCII pipeline only, skip source code). Skip all 🔥 source code walkthroughs and deep subsections on first pass.
- **Pass 2 — Dive into source code (50 min).** Read the four 🔥 walkthroughs: §3.3 (`_detect_docstring_style` + `ensure_strict_json_schema`), §3.5 (`_on_invoke_tool_impl` + `_FailureHandlingFunctionToolInvoker`), §3.8 (`invoke_function_tool`), §3.10 (guardrail execution functions + pipeline source). Also read the exception hierarchy in §3.7 and the `ToolApprovalItem` structure in §3.9.
- **Pass 3 — Fill gaps.** Itemized list:
  - Tool output types (text/image/file)? → §3.6 (3-row table + validation rules + examples)
  - Tool context (RunContextWrapper vs ToolContext)? → §3.4 (10-row comparison table)
  - Error handling & failure_error_function? → §3.7 (flow diagram + default function source + 3-row comparison table)
  - Tool-related exception hierarchy? → §3.7 (tree diagram + 4-row comparison table + catch example)
  - Timeout mechanism (error_as_result vs raise_exception)? → §3.8 (6 key insights + race condition)
  - Human-in-the-loop approval + ToolApprovalItem? → §3.9 (flow diagram + structure + inspect example)
  - Tool guardrails (input vs output, three behaviors)? → §3.10 (behavior table + Input vs Output comparison table)
  - Internal fields (_is_agent_tool, _SYNC_FUNCTION_TOOL_MARKER)? → §3.11 (7-row internal fields table)
  - The __copy__ mechanism? → §3.11 (source code + __post_init__)
  - ToolOrigin + is_enabled + defer_loading? → §3.12 (ToolOrigin source + is_enabled example + defer_loading workflow)
  - Putting it together + multi-turn? → §3.13 (complete example + 9-step analysis + 4-turn interaction + to_input_list output)

---

## 3.1 The Tool Family Tree

The SDK defines a `Tool` union type that covers every tool the LLM can invoke:

```
Tool (Union Type)
├── FunctionTool          ← Custom Python functions, Agent.as_tool(), MCP tools
├── FileSearchTool        ← Hosted: search OpenAI Vector Stores
├── WebSearchTool         ← Hosted: web search
├── CodeInterpreterTool   ← Hosted: sandboxed code execution
├── ImageGenerationTool   ← Hosted: DALL-E image generation
├── HostedMCPTool         ← Hosted: remote MCP server tools
├── ToolSearchTool        ← Hosted: deferred tool loading
├── ComputerTool          ← Local: GUI/browser automation
├── ShellTool             ← Local/Hosted: shell command execution
├── ApplyPatchTool        ← Local: file diff application
├── LocalShellTool        ← Local: legacy shell integration
└── CustomTool            ← Responses API custom tool passthrough
```

**`FunctionTool` is the one you'll use 90% of the time.** Every hosted tool (except `FunctionTool`) is a dataclass that configures an OpenAI-side capability — you pass parameters, and OpenAI handles the execution. `FunctionTool` is the only one that runs *your* Python code.

| Category | Tools | Where execution happens |
|---|---|---|
| **Hosted** | FileSearchTool, WebSearchTool, CodeInterpreterTool, ImageGenerationTool, HostedMCPTool, ToolSearchTool | OpenAI servers |
| **Local** | ComputerTool, ApplyPatchTool, LocalShellTool | Your process |
| **Hybrid** | ShellTool (local or hosted container) | Configurable |
| **Your code** | FunctionTool | Your process |
| **Passthrough** | CustomTool | OpenAI servers (you handle the response) |

Cross-reference: `Agent.as_tool()` produces a `FunctionTool` (see Chapter 2 §2.7). MCP tools are also converted to `FunctionTool` internally (see Chapter 2 §2.10).

---

## 3.2 From Python Function to Tool: The Transformation Pipeline

When you write `@function_tool`, the SDK transforms your plain Python function into a `FunctionTool` dataclass. Here's the complete pipeline:

```
Your Python Function
        │
        ▼
  ┌─────────────────────────────┐
  │ 1. function_schema()        │  Extract name, description, JSON schema
  │    (function_schema.py)     │  from type hints + docstring
  └─────────────────────────────┘
        │
        ▼
  ┌─────────────────────────────┐
  │ 2. _on_invoke_tool_impl()   │  Build the invoker:
  │    (tool.py)                │  Parse JSON → Pydantic validate → call func
  └─────────────────────────────┘
        │
        ▼
  ┌─────────────────────────────┐
  │ 3. _FailureHandling...      │  Wrap invoker with error handling:
  │    Invoker (tool.py)        │  catch Exception → failure_error_function
  └─────────────────────────────┘
        │
        ▼
  ┌─────────────────────────────┐
  │ 4. _build_wrapped_...       │  Assemble the full FunctionTool:
  │    function_tool (tool.py)  │  schema + invoker + guardrails + approval
  └─────────────────────────────┘
        │
        ▼
  FunctionTool! 🎉
```

The rest of this chapter walks through each step in detail.

---

## 3.3 🔥 Source Code Walkthrough: `function_schema()` — Python to JSON Schema

The first step is extracting a JSON schema from your Python function. This happens in `src/agents/function_schema.py`.

> **Note:** Chapter 1 §1.6 covers the full `function_schema()` source with all 5 key insights (description priority, context detection, `*args`/`**kwargs`, `create_model()`, `ensure_strict_json_schema()`). This section adds the details that Chapter 1 skips.

### Docstring auto-detection

The SDK auto-detects your docstring style (Google, NumPy, or Sphinx) using a scoring heuristic in `_detect_docstring_style()`:

```python
# src/agents/function_schema.py — simplified
def _detect_docstring_style(doc: str) -> DocstringStyle:
    scores: dict[DocstringStyle, int] = {"sphinx": 0, "numpy": 0, "google": 0}

    sphinx_patterns = [r"^:param\s", r"^:type\s", r"^:return:", r"^:rtype:"]
    numpy_patterns = [r"^Parameters\s*\n\s*-{3,}", r"^Returns\s*\n\s*-{3,}"]
    google_patterns = [r"^(Args|Arguments):", r"^(Returns):", r"^(Raises):"]

    for pattern in sphinx_patterns:
        if re.search(pattern, doc, re.MULTILINE): scores["sphinx"] += 1
    for pattern in numpy_patterns:
        if re.search(pattern, doc, re.MULTILINE): scores["numpy"] += 1
    for pattern in google_patterns:
        if re.search(pattern, doc, re.MULTILINE): scores["google"] += 1

    if max(scores.values()) == 0:
        return "google"
    # Tie-breaking priority: sphinx > numpy > google
    for style in ["sphinx", "numpy", "google"]:
        if scores[style] == max(scores.values()):
            return style
```

If no docstring patterns are detected, the default is **Google style**. You can override with `@function_tool(docstring_style="numpy")`.

### `ensure_strict_json_schema()` — The Strict Mode Enforcer

When `strict_json_schema=True` (the default), the generated schema is post-processed by `ensure_strict_json_schema()` in `src/agents/strict_schema.py`. Here's what it does:

| Transformation | Why | Example |
|---|---|---|
| Add `additionalProperties: false` to every object | OpenAI requires it for Structured Outputs | `{type: "object", properties: {...}}` → adds `additionalProperties: false` |
| Make all properties `required` | Strict mode: no optional fields | `required: ["a"]` → `required: ["a", "b"]` |
| Convert `oneOf` → `anyOf` | OpenAI doesn't support `oneOf` in nested contexts | `{"oneOf": [...]}` → `{"anyOf": [...]}` |
| Inline `$ref` references | Can't have `$ref` + other properties on same object | `{"$ref": "#/$defs/X", "description": "..."}` → inlined |
| Strip `None` defaults | No meaningful distinction in strict mode | `{"default": null}` → removed |

This transformation is **recursive** — it walks through the entire schema tree, applying these rules at every level.

**What the LLM sees:**

For `get_weather(latitude: float, longitude: float)`, the generated JSON schema is:

```json
{
  "type": "object",
  "properties": {
    "latitude": {
      "type": "number",
      "description": "Latitude of the location"
    },
    "longitude": {
      "type": "number",
      "description": "Longitude of the location"
    }
  },
  "required": ["latitude", "longitude"],
  "additionalProperties": false
}
```

Every parameter becomes `required` and `additionalProperties` is `false` — this is the strict mode guarantee.

---

## 3.4 The `@function_tool` Decorator: Full Parameter Surface

The decorator has two overloads — one for `@function_tool` (no parentheses) and one for `@function_tool(timeout=5.0)` (with parentheses):

| Parameter | Type | Default | Purpose |
|---|---|---|---|
| `name_override` | `str \| None` | `None` | Override the function name as seen by the LLM |
| `description_override` | `str \| None` | `None` | Override the docstring-derived description |
| `docstring_style` | `"google" \| "numpy" \| "sphinx" \| None` | Auto-detect | Force a docstring parsing style |
| `use_docstring_info` | `bool` | `True` | Set `False` to ignore docstring entirely |
| `failure_error_function` | `ToolErrorFunction \| None` | Default formatter | Custom error handler (see §3.7) |
| `strict_mode` | `bool` | `True` | Enable strict JSON schema (strongly recommended) |
| `is_enabled` | `bool \| Callable` | `True` | Dynamically enable/disable (see §3.12) |
| `needs_approval` | `bool \| Callable` | `False` | Human-in-the-loop (see §3.9) |
| `tool_input_guardrails` | `list[ToolInputGuardrail] \| None` | `None` | Pre-execution guardrails (see §3.10) |
| `tool_output_guardrails` | `list[ToolOutputGuardrail] \| None` | `None` | Post-execution guardrails (see §3.10) |
| `timeout` | `float \| None` | `None` | Per-call timeout in seconds (see §3.8) |
| `timeout_behavior` | `"error_as_result" \| "raise_exception"` | `"error_as_result"` | What happens on timeout (see §3.8) |
| `timeout_error_function` | `ToolErrorFunction \| None` | `None` | Custom timeout message formatter |
| `defer_loading` | `bool` | `False` | Hide tool from LLM until ToolSearchTool loads it |

**Usage patterns:**

```python
@function_tool
async def simple_tool(query: str) -> str:
    """A simple tool with no extra config."""
    return f"Result for {query}"

@function_tool(name_override="search", timeout=5.0, strict_mode=True)
async def search_database(
    ctx: ToolContext[MyContext],
    query: Annotated[str, "The search query"],
    limit: int = 10,
) -> str:
    """Search the database."""
    return f"Found {limit} results for {query}"
```

**Sync functions are supported.** If you pass a non-async function, the SDK wraps it with `asyncio.to_thread()` so it runs in a thread pool. However, `timeout_seconds` is **not supported** for sync functions — the SDK raises `ValueError` if you try. This is because `asyncio.wait_for()` cannot cancel a thread.

### Tool Context: `RunContextWrapper` vs `ToolContext`

Your tool function can have three different signatures:

```python
# Form 1: No context
async def get_weather(latitude: float, longitude: float) -> str: ...

# Form 2: With RunContextWrapper
async def get_weather(
    ctx: RunContextWrapper[MyContext],
    latitude: float,
    longitude: float,
) -> str: ...

# Form 3: With ToolContext (extends RunContextWrapper)
async def get_weather(
    ctx: ToolContext[MyContext],
    latitude: float,
    longitude: float,
) -> str: ...
```

The SDK automatically detects which signature you used and injects the right context. Here's what each provides:

| Field | `RunContextWrapper` | `ToolContext` |
|---|---|---|
| `context` | ✅ Your custom data | ✅ Your custom data |
| `usage` | ✅ Token usage tracking | ✅ Token usage tracking |
| `tool_name` | ❌ | ✅ Name of the current tool |
| `tool_call_id` | ❌ | ✅ ID of this specific tool call |
| `tool_arguments` | ❌ | ✅ Raw JSON arguments string |
| `tool_call` | ❌ | ✅ Full `ResponseFunctionToolCall` object |
| `tool_namespace` | ❌ | ✅ Namespace for grouped tools |
| `agent` | ❌ | ✅ The active `AgentBase` |
| `run_config` | ❌ | ✅ The active `RunConfig` |
| `qualified_tool_name` | ❌ | ✅ `namespace.tool_name` format |

**When to use each:**

- **No context** — simple tools that don't need any external state
- **`RunContextWrapper`** — tools that need your custom context (e.g., user ID, database connection)
- **`ToolContext`** — tools that need tool-call metadata (e.g., logging the `tool_call_id`, inspecting raw arguments, accessing `run_config`)

`ToolContext` is created via `ToolContext.from_agent_context()`, which copies all fields from the existing `RunContextWrapper` and adds the tool-specific fields. It also preserves the shared `_approvals` dict and `tool_input` from the parent context.

---

## 3.5 🔥 Source Code Walkthrough: The Invoker Chain

When the LLM calls a tool, it sends JSON arguments. The SDK must parse, validate, and invoke your function. Here's the invoker chain, from the inner `_on_invoke_tool_impl` to the outer `_FailureHandlingFunctionToolInvoker`:

### The Inner Invoker: `_on_invoke_tool_impl`

This is the function created inside `@function_tool` that actually calls your Python function:

```python
# src/agents/tool.py — _create_function_tool() inner function, simplified
async def _on_invoke_tool_impl(ctx: ToolContext[Any], input: str) -> Any:
    tool_name = ctx.tool_name
    json_data = _parse_function_tool_json_input(tool_name=tool_name, input_json=input)
    _log_function_tool_invocation(tool_name=tool_name, input_json=input)

    try:
        parsed = (
            schema.params_pydantic_model(**json_data)
            if json_data
            else schema.params_pydantic_model()
        )
    except ValidationError as e:
        raise ModelBehaviorError(
            f"Invalid JSON input for tool {tool_name}: {e}"
        ) from e

    args, kwargs_dict = schema.to_call_args(parsed)

    if not is_sync_function_tool:
        if schema.takes_context:
            result = await the_func(ctx, *args, **kwargs_dict)
        else:
            result = await the_func(*args, **kwargs_dict)
    else:
        if schema.takes_context:
            result = await asyncio.to_thread(the_func, ctx, *args, **kwargs_dict)
        else:
            result = await asyncio.to_thread(the_func, *args, **kwargs_dict)

    return result
```

**Key Insights:**

1. **JSON → Pydantic → Python args.** The LLM sends a JSON string. It's parsed, validated against the Pydantic model, then converted back to positional/keyword args via `schema.to_call_args(parsed)`. This round-trip ensures type safety.

2. **`ValidationError` becomes `ModelBehaviorError`.** If the LLM sends invalid JSON (e.g., a string where a number is expected), it's treated as the LLM's fault, not the user's. The run fails with `ModelBehaviorError`.

3. **Context is injected automatically.** If `takes_context` is `True`, the `ToolContext` is passed as the first argument. Your function never sees the raw JSON string.

4. **Sync functions use `asyncio.to_thread()`.** This avoids blocking the event loop. But it means timeout cancellation is not possible (threads can't be cancelled in Python).

### The Outer Invoker: `_FailureHandlingFunctionToolInvoker`

The inner invoker is wrapped by `_FailureHandlingFunctionToolInvoker`, which adds error handling:

```python
# src/agents/tool.py — simplified
class _FailureHandlingFunctionToolInvoker:
    def __init__(
        self,
        invoke_tool_impl: Callable[[ToolContext[Any], str], Awaitable[Any]],
        on_handled_error: Callable[[FunctionTool, Exception, str], None],
        *,
        function_tool: FunctionTool | None = None,
    ) -> None:
        self._invoke_tool_impl = invoke_tool_impl
        self._on_handled_error = on_handled_error
        self._function_tool = function_tool

    def __agents_bind_function_tool__(
        self, function_tool: FunctionTool
    ) -> _FailureHandlingFunctionToolInvoker:
        if self._function_tool is function_tool:
            return self
        bound_invoker = _FailureHandlingFunctionToolInvoker(
            self._invoke_tool_impl,
            self._on_handled_error,
            function_tool=function_tool,
        )
        return bound_invoker

    async def __call__(self, ctx: ToolContext[Any], input: str) -> Any:
        try:
            return await self._invoke_tool_impl(ctx, input)
        except Exception as e:
            assert self._function_tool is not None
            result = await maybe_invoke_function_tool_failure_error_function(
                function_tool=self._function_tool,
                context=ctx,
                error=e,
            )
            if result is None:
                raise
            self._on_handled_error(self._function_tool, e, input)
            return result
```

**Key Insights:**

5. **The `__agents_bind_function_tool__` protocol.** When a `FunctionTool` is copied (via `__copy__`), the invoker needs to be rebound to the *new* tool instance. The `__post_init__` method checks for this protocol and rebinds automatically. This is the Decorator pattern at work.

6. **Error handling is configurable.** If `failure_error_function` returns a string, the error is sent to the LLM as a tool result (the LLM can try again). If it returns `None`, the exception is re-raised and the run fails. See §3.7 for the full error handling flow.

---

## 3.6 Tool Output Types: More Than Just Strings

Your tool can return different types of outputs. The SDK converts them into the format the LLM expects:

| Return Type | What the LLM sees | When to use |
|---|---|---|
| `str` | Plain text | Most common: text results |
| `ToolOutputText` | Explicit text output | When you need the `type: "text"` marker |
| `ToolOutputImage` | Image (URL or file_id) | Charts, screenshots, diagrams |
| `ToolOutputFileContent` | File (base64, URL, or file_id) | CSV exports, PDFs, data files |
| `list[...]` | Multiple outputs | Combine text + image in one response |

### The three output models (from `src/agents/tool.py`)

```python
class ToolOutputText(BaseModel):
    type: Literal["text"] = "text"
    text: str

class ToolOutputImage(BaseModel):
    type: Literal["image"] = "image"
    image_url: str | None = None
    file_id: str | None = None
    detail: Literal["low", "high", "auto"] | None = None

class ToolOutputFileContent(BaseModel):
    type: Literal["file"] = "file"
    file_data: str | None = None
    file_url: str | None = None
    file_id: str | None = None
    filename: str | None = None
```

**Validation rules:**
- `ToolOutputImage`: at least one of `image_url` or `file_id` must be provided (enforced by `@model_validator`)
- `ToolOutputFileContent`: at least one of `file_data`, `file_url`, or `file_id` must be provided

**Practical examples:**

```python
@function_tool
async def generate_chart(metric: str) -> list:
    """Generate a chart and return it as an image alongside a summary."""
    chart_url = await create_chart(metric)
    return [
        ToolOutputText(text=f"Here is the {metric} chart:"),
        ToolOutputImage(image_url=chart_url),
    ]

@function_tool
async def export_data(query: str) -> ToolOutputFileContent:
    """Export query results as a CSV file."""
    csv_data = await run_query(query)
    return ToolOutputFileContent(
        file_data=base64.b64encode(csv_data.encode()).decode(),
        filename="results.csv",
    )
```

**What happens to plain strings?** If you return a `str`, the SDK calls `str()` on it and wraps it as text. If you return a non-string, non-model object, `str()` is called on it. This means returning `"sunny"` and returning `ToolOutputText(text="sunny")` are functionally equivalent for the LLM — the explicit model just gives you type safety.

---

## 3.7 Error Handling: The Safety Net

When your function raises an exception, the SDK doesn't let it crash the run by default. Instead, it converts the error into a message the LLM can see and potentially recover from.

### The error handling flow

```
Your function raises ValueError("Invalid coordinates")
        │
        ▼
  Captured by _FailureHandlingFunctionToolInvoker
        │
        ▼
  maybe_invoke_function_tool_failure_error_function()
        │
        ├── failure_error_function is set?
        │     ├── Yes → call it: failure_error_function(ctx, error)
        │     │         ├── Returns str → send to LLM as tool result ✅
        │     │         └── Returns None → re-raise exception 💥
        │     └── No (None) → re-raise exception 💥
        │
        └── _use_default_failure_error_function is True?
              └── Yes → call default_tool_error_function(ctx, error)
                        → Returns: "An error occurred while running the tool. Please try again. Error: ..."
```

### The default error function

```python
# src/agents/tool.py
def default_tool_error_function(ctx: RunContextWrapper[Any], error: Exception) -> str:
    json_decode_error = _extract_tool_argument_json_error(error)
    if json_decode_error is not None:
        return (
            "An error occurred while parsing tool arguments. "
            "Please try again with valid JSON. "
            f"Error: {json_decode_error}"
        )
    return f"An error occurred while running the tool. Please try again. Error: {str(error)}"
```

The default function distinguishes between two cases:
- **JSON parse errors** — the LLM sent malformed JSON. It gets a specific "please try again with valid JSON" message.
- **All other errors** — your code raised an exception. It gets a generic message with the error text.

### Custom error functions

You can customize the error message (or suppress it entirely):

```python
@function_tool(
    failure_error_function=lambda ctx, err: f"Database error: {err}. Please rephrase your query."
)
async def query_database(sql: str) -> str:
    ...

@function_tool(
    failure_error_function=None       # ← None means: re-raise, don't send to LLM
)
async def critical_operation(data: str) -> str:
    ...
```

| `failure_error_function` value | Behavior on exception |
|---|---|
| Not set (default) | `default_tool_error_function` sends error message to LLM |
| Custom callable | Your function receives `(ctx, error)` and returns `str` or `None` |
| `None` | Exception is re-raised; the run fails |

**Important:** When `failure_error_function` returns a string, the error is logged as "non-fatal" via `on_handled_error`, and the LLM sees the error as a tool result. This means the LLM can *retry the call with different arguments* — a powerful self-correction mechanism.

### Tool-Related Exception Hierarchy

When things go wrong, the SDK raises specific exceptions. All of them inherit from `AgentsException`, which carries a `run_data: RunErrorDetails | None` field that provides the full run context for debugging:

```
AgentsException                          ← Base class for ALL SDK exceptions
├── run_data: RunErrorDetails | None     ← input, new_items, raw_responses, last_agent, ...
│
├── ModelBehaviorError                   ← LLM sent invalid JSON or called non-existent tool
│   └── message: str
│
├── ToolTimeoutError                     ← Tool exceeded its timeout_seconds
│   ├── tool_name: str
│   └── timeout_seconds: float
│
├── ToolInputGuardrailTripwireTriggered  ← Input guardrail returned raise_exception
│   ├── guardrail: ToolInputGuardrail
│   └── output: ToolGuardrailFunctionOutput
│
├── ToolOutputGuardrailTripwireTriggered ← Output guardrail returned raise_exception
│   ├── guardrail: ToolOutputGuardrail
│   └── output: ToolGuardrailFunctionOutput
│
├── InputGuardrailTripwireTriggered      ← Agent-level input guardrail (Chapter 7)
│   └── guardrail_result: InputGuardrailResult
│
└── OutputGuardrailTripwireTriggered     ← Agent-level output guardrail (Chapter 7)
    └── guardrail_result: OutputGuardrailResult
```

**Key distinctions:**

| Exception | Trigger | When it fires | Can LLM recover? |
|---|---|---|---|
| `ModelBehaviorError` | Invalid JSON from LLM | Inside `_on_invoke_tool_impl` | No — run terminates |
| `ToolTimeoutError` | `timeout_behavior="raise_exception"` + timeout | Inside `invoke_function_tool` | No — run terminates |
| `ToolInputGuardrailTripwireTriggered` | Input guardrail returns `raise_exception` | Before your function runs | No — run terminates |
| `ToolOutputGuardrailTripwireTriggered` | Output guardrail returns `raise_exception` | After your function runs | No — run terminates |

**Usage example — catching tool exceptions:**

```python
from agents.exceptions import ToolTimeoutError, ToolInputGuardrailTripwireTriggered

try:
    result = await Runner.run(agent, "Delete all records", context=ctx)
except ToolInputGuardrailTripwireTriggered as e:
    print(f"Blocked by guardrail: {e.guardrail.get_name()}")
    print(f"Guardrail output: {e.output.output_info}")
except ToolTimeoutError as e:
    print(f"Tool {e.tool_name} timed out after {e.timeout_seconds}s")
except AgentsException as e:
    if e.run_data is not None:
        print(f"Run failed after {len(e.run_data.raw_responses)} turns")
        print(f"Last agent: {e.run_data.last_agent.name}")
```

**Note:** When `timeout_behavior="error_as_result"` or `failure_error_function` returns a string, *no exception is raised*. The error is silently sent to the LLM as a tool result. These exceptions only fire in the "hard stop" cases.

---

## 3.8 🔥 Source Code Walkthrough: `invoke_function_tool()` — The Timeout Mechanism

After the approval check (§3.9) and input guardrails (§3.10) pass, the engine calls `invoke_function_tool()`. This is where the timeout is enforced:

```python
# src/agents/tool.py — simplified
async def invoke_function_tool(
    *,
    function_tool: FunctionTool,
    context: ToolContext[Any],
    arguments: str,
) -> Any:
    invoke_context = _get_function_tool_invoke_context(function_tool, context)
    timeout_seconds = function_tool.timeout_seconds

    if timeout_seconds is None:
        return await function_tool.on_invoke_tool(cast(Any, invoke_context), arguments)

    tool_task: asyncio.Future[Any] = asyncio.ensure_future(
        function_tool.on_invoke_tool(cast(Any, invoke_context), arguments)
    )
    try:
        return await asyncio.wait_for(tool_task, timeout=timeout_seconds)
    except asyncio.TimeoutError as exc:
        if tool_task.done() and not tool_task.cancelled():
            tool_exception = tool_task.exception()
            if tool_exception is None:
                return tool_task.result()
            raise tool_exception from None

        timeout_error = ToolTimeoutError(
            tool_name=function_tool.name,
            timeout_seconds=timeout_seconds,
        )
        if function_tool.timeout_behavior == "raise_exception":
            raise timeout_error from exc

        timeout_error_function = function_tool.timeout_error_function
        if timeout_error_function is None:
            return default_tool_timeout_error_message(
                tool_name=function_tool.name,
                timeout_seconds=timeout_seconds,
            )

        timeout_result = timeout_error_function(context, timeout_error)
        if inspect.isawaitable(timeout_result):
            return await timeout_result
        return timeout_result
```

**Key Insights:**

1. **No timeout = direct await.** If `timeout_seconds` is `None`, the function is awaited directly with no wrapper. Zero overhead.

2. **Timeout uses `asyncio.wait_for()`.** This creates a task and cancels it if the deadline passes. The cancelled task gets `asyncio.CancelledError` injected into it.

3. **Race condition protection.** After `TimeoutError`, the code checks `tool_task.done() and not tool_task.cancelled()`. If the task finished *just* before the timeout fired, the result is returned normally. This prevents losing a valid result due to a timing edge.

4. **Two timeout behaviors:**

| `timeout_behavior` | What happens | LLM sees error? |
|---|---|---|
| `"error_as_result"` (default) | Returns a string message to the LLM | Yes — LLM can retry |
| `"raise_exception"` | Raises `ToolTimeoutError`, fails the run | No — run terminates |

5. **Custom timeout message.** If `timeout_error_function` is set, it's called with `(context, ToolTimeoutError)`. Otherwise, the default message is `"Tool 'name' timed out after 5 seconds."`

6. **Sync functions can't use timeouts.** The `__post_init__` validation in `FunctionTool` raises `ValueError` if `timeout_seconds` is set on a sync function tool. This is because `asyncio.wait_for()` cannot cancel a thread.

**Usage:**

```python
@function_tool(timeout=5.0, timeout_behavior="error_as_result")
async def slow_api_call(query: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://api.example.com/search?q={query}")
    return resp.text

@function_tool(
    timeout=30.0,
    timeout_behavior="raise_exception",
    timeout_error_function=lambda ctx, err: f"Data pipeline timed out: {err.timeout_seconds}s"
)
async def run_pipeline(config: str) -> str:
    ...
```

---

## 3.9 Human-in-the-Loop: Tool Approval

Some tools are dangerous — transferring money, deleting records, running shell commands. The SDK lets you require human approval before a tool call is executed.

### How approval works

```
LLM decides to call transfer_money(amount=1000, to="alice")
        │
        ▼
  Check needs_approval
        │
        ├── False → continue to execution
        │
        └── True → interrupt the run
              │
              ▼
        Return ToolApprovalItem (instead of executing)
              │
              ▼
        Runner returns RunState with pending interruption
              │
              ├── User calls state.approve("call_id") → re-run, tool executes
              └── User calls state.reject("call_id") → rejection message sent to LLM
```

### Two ways to configure approval

**Static (always require approval):**

```python
@function_tool(needs_approval=True)
async def transfer_money(amount: float, to: str) -> str:
    return f"Transferred ${amount} to {to}"
```

**Dynamic (conditional approval):**

```python
async def should_approve(
    ctx: RunContextWrapper[MyContext],
    args: dict[str, Any],
    tool_name: str,
) -> bool:
    return args["amount"] >= 100

@function_tool(needs_approval=should_approve)
async def transfer_money(amount: float, to: str) -> str:
    return f"Transferred ${amount} to {to}"
```

The dynamic function receives:
- `ctx`: `RunContextWrapper` with your custom context
- `args`: the parsed tool arguments as a `dict`
- `tool_name`: the name of the tool being called

If the approval function returns `True`, the run is interrupted. If `False`, execution continues normally.

Cross-reference: The approval state is stored in `RunContextWrapper._approvals` and shared across context forks. See Chapter 5 for the full `RunState` serialization and resumption flow.

### What `ToolApprovalItem` Looks Like

When a tool needs approval, the Runner produces a `ToolApprovalItem` instead of executing the tool. Here's its structure:

```python
class ToolApprovalItem(RunItemBase):
    raw_item: ToolApprovalRawItem      # The original tool call (function, shell, etc.)
    tool_name: str | None = None       # Tool name for tracking; falls back to raw_item.name
    type: Literal["tool_approval_item"] = "tool_approval_item"
    tool_namespace: str | None = None  # Namespace for grouped tools
    tool_origin: ToolOrigin | None = None  # Where this tool came from
```

**How to inspect and resolve pending approvals:**

```python
from agents import Runner

result = await Runner.run(agent, "Transfer $500 to Alice", context=AppContext(...))

if result.state and result.state.interruptions:
    for interruption in result.state.interruptions:
        if isinstance(interruption, ToolApprovalItem):
            print(f"Tool: {interruption.tool_name}")
            print(f"Call ID: {interruption.raw_item.call_id}")
            print(f"Arguments: {interruption.raw_item.arguments}")

    result.state.approve("call_id_here")
    result2 = await Runner.run(
        agent,
        result.state.to_input_list(),
        context=AppContext(...),
    )
```

---

## 3.10 🔥 Source Code Walkthrough: Tool Guardrails & The Full Execution Pipeline

Tool guardrails are separate from the agent-level guardrails (Chapter 7). They run *per-tool-call*, not per-agent. The SDK supports both input guardrails (before your function runs) and output guardrails (after your function returns).

### The guardrail data models

```python
# src/agents/tool_guardrails.py — simplified
class ToolInputGuardrailData:
    context: ToolContext[Any]     # The tool context
    agent: Agent[Any]             # The agent executing the tool

class ToolOutputGuardrailData(ToolInputGuardrailData):
    output: Any                   # The output produced by the tool function
```

### The three guardrail behaviors

```python
class AllowBehavior(TypedDict):
    type: Literal["allow"]

class RejectContentBehavior(TypedDict):
    type: Literal["reject_content"]
    message: str                  # Sent to the LLM instead of the real output

class RaiseExceptionBehavior(TypedDict):
    type: Literal["raise_exception"]
```

| Behavior | Effect | When to use |
|---|---|---|
| `allow` | Tool execution continues normally | Default — no concerns |
| `reject_content` | Returns `message` to the LLM instead of the real output | Content filtering, PII redaction |
| `raise_exception` | Raises `ToolInputGuardrailTripwireTriggered` or `ToolOutputGuardrailTripwireTriggered` | Hard stop — dangerous content detected |

### Input vs Output Guardrails: Comparison

| Aspect | Input Guardrail | Output Guardrail |
|---|---|---|
| **When it runs** | Before your function is called | After your function returns |
| **Data available** | `ToolInputGuardrailData` (context, agent) | `ToolOutputGuardrailData` (context, agent, **output**) |
| **Can inspect tool arguments** | Yes — via `data.context.tool_arguments` | Yes — via `data.context.tool_arguments` |
| **Can inspect tool result** | No — function hasn't run yet | Yes — via `data.output` |
| **`reject_content` effect** | Returns message to LLM; **function never runs** | Returns message to LLM; **real output is discarded** |
| **`raise_exception` exception** | `ToolInputGuardrailTripwireTriggered` | `ToolOutputGuardrailTripwireTriggered` |
| **Typical use case** | Validate inputs, block dangerous commands | Filter PII from outputs, limit response size |
| **Decorator** | `@tool_input_guardrail` | `@tool_output_guardrail` |
| **Applied on** | `tool_input_guardrails=[...]` | `tool_output_guardrails=[...]` |

### The full execution pipeline (from `tool_execution.py`)

This is the complete sequence that happens when the LLM calls a function tool. It's implemented in `_FunctionToolBatchExecutor._execute_single_tool_body()` and `_invoke_tool_and_run_post_invoke()`. But first, let's see the two guardrail execution functions that power the pipeline:

```python
# src/agents/run_internal/tool_execution.py — simplified
async def _execute_tool_input_guardrails(
    *,
    func_tool: FunctionTool,
    tool_context: ToolContext[Any],
    agent: Agent[Any],
    tool_input_guardrail_results: list[ToolInputGuardrailResult],
) -> str | None:
    if not func_tool.tool_input_guardrails:
        return None

    for guardrail in func_tool.tool_input_guardrails:
        gr_out = await guardrail.run(
            ToolInputGuardrailData(context=tool_context, agent=agent)
        )
        tool_input_guardrail_results.append(
            ToolInputGuardrailResult(guardrail=guardrail, output=gr_out)
        )
        if gr_out.behavior["type"] == "raise_exception":
            raise ToolInputGuardrailTripwireTriggered(guardrail=guardrail, output=gr_out)
        elif gr_out.behavior["type"] == "reject_content":
            return gr_out.behavior["message"]

    return None


async def _execute_tool_output_guardrails(
    *,
    func_tool: FunctionTool,
    tool_context: ToolContext[Any],
    agent: Agent[Any],
    real_result: Any,
    tool_output_guardrail_results: list[ToolOutputGuardrailResult],
) -> Any:
    if not func_tool.tool_output_guardrails:
        return real_result

    final_result = real_result
    for output_guardrail in func_tool.tool_output_guardrails:
        gr_out = await output_guardrail.run(
            ToolOutputGuardrailData(context=tool_context, agent=agent, output=real_result)
        )
        tool_output_guardrail_results.append(
            ToolOutputGuardrailResult(guardrail=output_guardrail, output=gr_out)
        )
        if gr_out.behavior["type"] == "raise_exception":
            raise ToolOutputGuardrailTripwireTriggered(guardrail=output_guardrail, output=gr_out)
        elif gr_out.behavior["type"] == "reject_content":
            final_result = gr_out.behavior["message"]
            break

    return final_result
```

Now here's the main execution pipeline:

```python
# src/agents/run_internal/tool_execution.py — simplified
async def _execute_single_tool_body(self, ...) -> Any:
    # ── PHASE 1: Input Guardrails ──
    rejected_message = await _execute_tool_input_guardrails(
        func_tool=func_tool,
        tool_context=tool_context,
        agent=self.public_agent,
        tool_input_guardrail_results=self.tool_input_guardrail_results,
    )
    if rejected_message is not None:
        return rejected_message                              # ← guardrail rejected

    # ── PHASE 2: Pre-invoke Hooks ──
    await asyncio.gather(
        self.hooks.on_tool_start(tool_context, self.public_agent, func_tool),
        (
            agent_hooks.on_tool_start(tool_context, self.public_agent, func_tool)
            if agent_hooks
            else _coro.noop_coroutine()
        ),
    )

    # ── PHASE 3: Invoke the tool (with timeout) ──
    invoke_task = asyncio.create_task(
        self._invoke_tool_and_run_post_invoke(...)
    )
    return await self._await_invoke_task(...)


async def _invoke_tool_and_run_post_invoke(self, ...) -> Any:
    # ── PHASE 3a: Call the function ──
    real_result = await invoke_function_tool(
        function_tool=func_tool,
        context=tool_context,
        arguments=tool_call.arguments,
    )

    # ── PHASE 4: Output Guardrails ──
    final_result = await _execute_tool_output_guardrails(
        func_tool=func_tool,
        tool_context=tool_context,
        agent=self.public_agent,
        real_result=real_result,
        tool_output_guardrail_results=self.tool_output_guardrail_results,
    )

    # ── PHASE 5: Post-invoke Hooks ──
    await asyncio.gather(
        self.hooks.on_tool_end(tool_context, self.public_agent, func_tool, final_result),
        (
            agent_hooks.on_tool_end(tool_context, self.public_agent, func_tool, final_result)
            if agent_hooks
            else _coro.noop_coroutine()
        ),
    )

    return final_result
```

### The complete flow, visualized

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Approval Check (see §3.9)                                   │
│     needs_approval? → Yes: interrupt, return ToolApprovalItem   │
│                       → No: continue                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. Input Guardrails                                            │
│     Run all tool_input_guardrails sequentially                  │
│     ├── allow → continue                                        │
│     ├── reject_content → return message to LLM (skip tool)      │
│     └── raise_exception → throw ToolInputGuardrailTripwire...   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. Pre-invoke Hooks                                            │
│     RunHooks.on_tool_start + AgentHooks.on_tool_start           │
│     (run concurrently via asyncio.gather)                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. Invoke the Function (see §3.8)                              │
│     _on_invoke_tool_impl:                                       │
│       Parse JSON → Pydantic validate → call your function       │
│     invoke_function_tool:                                       │
│       Apply timeout (asyncio.wait_for)                          │
│     _FailureHandlingFunctionToolInvoker:                        │
│       Catch exceptions → failure_error_function (see §3.7)      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. Output Guardrails                                           │
│     Run all tool_output_guardrails sequentially                 │
│     ├── allow → pass through real_result                        │
│     ├── reject_content → replace with message, stop checking    │
│     └── raise_exception → throw ToolOutputGuardrailTripwire...  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  6. Post-invoke Hooks                                           │
│     RunHooks.on_tool_end + AgentHooks.on_tool_end               │
│     (run concurrently via asyncio.gather)                       │
│     Receives the final_result (possibly modified by guardrails) │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  7. Return result to the Runner loop                            │
│     The result is sent back to the LLM as a tool output         │
└─────────────────────────────────────────────────────────────────┘
```

**Key Insights:**

1. **Guardrails run sequentially, not concurrently.** Each guardrail is `await`ed in order. If one returns `reject_content` or `raise_exception`, the remaining guardrails are skipped.

2. **Input guardrail rejection skips the tool entirely.** If an input guardrail rejects, your function never runs. The rejection message is returned to the LLM directly.

3. **Output guardrail rejection replaces the output.** If an output guardrail rejects, the real output is discarded and replaced with the rejection message. The `break` statement means subsequent output guardrails don't run.

4. **Hooks run concurrently.** `RunHooks.on_tool_start` and `AgentHooks.on_tool_start` are called via `asyncio.gather()` — they run in parallel. Same for `on_tool_end`.

5. **Parallel tool calls are supported.** The `_FunctionToolBatchExecutor` creates a separate `asyncio.Task` for each tool call and drains them with `asyncio.wait(FIRST_COMPLETED)`. If one tool fails with `raise_exception` behavior, sibling tasks in the pre-invoke phase are cancelled, but tasks in the post-invoke phase are allowed to complete.

### Guardrail example

```python
from agents import function_tool, tool_input_guardrail, tool_output_guardrail
from agents.tool_guardrails import ToolGuardrailFunctionOutput

@tool_input_guardrail
def check_pii(data) -> ToolGuardrailFunctionOutput:
    args = json.loads(data.context.tool_arguments)
    if any(k in str(args) for k in ["ssn", "social_security"]):
        return ToolGuardrailFunctionOutput(
            output_info="PII detected in input",
            behavior={"type": "reject_content", "message": "Please do not include SSN in queries."},
        )
    return ToolGuardrailFunctionOutput.allow()

@tool_output_guardrail
def check_output_length(data) -> ToolGuardrailFunctionOutput:
    if len(str(data.output)) > 5000:
        return ToolGuardrailFunctionOutput(
            output_info="Output too long",
            behavior={"type": "reject_content", "message": "Result too large. Please narrow your query."},
        )
    return ToolGuardrailFunctionOutput.allow()

@function_tool(
    tool_input_guardrails=[check_pii],
    tool_output_guardrails=[check_output_length],
)
async def query_database(sql: str) -> str:
    ...
```

---

## 3.11 The `__copy__` Mechanism and Internal Fields

### `__copy__`: Why It Exists

`FunctionTool` implements `__copy__` because it has two categories of fields:

1. **Dataclass fields** — serializable, handled by `dataclasses.replace()`
2. **Non-dataclass attributes** — set dynamically, stored in `__dict__` but not in `dataclasses.fields()`

```python
# src/agents/tool.py
def __copy__(self) -> FunctionTool:
    copied_tool = dataclasses.replace(self)
    dataclass_field_names = {tool_field.name for tool_field in dataclasses.fields(FunctionTool)}
    for tool_field in dataclasses.fields(FunctionTool):
        if tool_field.init:
            continue
        setattr(copied_tool, tool_field.name, getattr(self, tool_field.name))
    for attr_name, attr_value in self.__dict__.items():
        if attr_name not in dataclass_field_names:
            setattr(copied_tool, attr_name, attr_value)
    return copied_tool
```

The `__agents_bind_function_tool__` protocol (§3.5) is also part of this: when a tool is copied, the invoker's `_function_tool` reference must be rebound to the new copy. This happens automatically in `__post_init__`:

```python
def __post_init__(self):
    bind_to_function_tool = getattr(self.on_invoke_tool, "__agents_bind_function_tool__", None)
    if callable(bind_to_function_tool):
        self.on_invoke_tool = bind_to_function_tool(self)
    if self.strict_json_schema:
        self.params_json_schema = ensure_strict_json_schema(self.params_json_schema)
    _validate_function_tool_timeout_config(self)
```

When would you copy a tool? The most common case is when the same tool is added to multiple agents — each agent gets its own copy with its own invoker binding. This prevents one agent's error handling from affecting another's.

### Internal Fields Explained

`FunctionTool` has several `kw_only=True, repr=False` internal fields that control behavior behind the scenes:

| Field | Type | Default | Purpose |
|---|---|---|---|
| `_is_agent_tool` | `bool` | `False` | Set by `Agent.as_tool()`. Used during `RunState` serialization to find nested agent instances for approval restoration. Also marks the tool in tracing signatures with `agent_tool_target`. |
| `_agent_instance` | `Any` | `None` | Reference to the `Agent` that this tool wraps (only when `_is_agent_tool=True`). Used by `RunState` to traverse nested agents during serialization. |
| `_SYNC_FUNCTION_TOOL_MARKER` | (on `on_invoke_tool`) | — | A sentinel attribute `__agents_sync_function_tool__` set to `True` when the original function is sync. Used by `__post_init__` to reject `timeout_seconds` on sync tools, and by `_build_wrapped_function_tool` to propagate the marker across copies. |
| `_tool_namespace` | `str \| None` | `None` | The Responses API namespace for grouping related tools. Set by `tool_namespace()` helper. |
| `_tool_namespace_description` | `str \| None` | `None` | Human-readable description for the namespace group. |
| `_mcp_title` | `str \| None` | `None` | Display title for MCP-backed tools. Appears in `ToolCallItem` tracing metadata. |
| `_emit_tool_origin` | `bool` | `True` | Controls whether `get_function_tool_origin()` returns metadata. Set to `False` to suppress origin tracking for internal tools. |

**Why these are internal:** These fields are not part of the public API because they are set automatically by higher-level constructs (`Agent.as_tool()`, `tool_namespace()`, MCP integration). You shouldn't need to set them directly.

---

## 3.12 ToolOrigin, `is_enabled`, and `defer_loading`

### ToolOrigin

Every `FunctionTool` carries a `_tool_origin` field that records where it came from:

```python
class ToolOriginType(str, Enum):
    FUNCTION = "function"
    MCP = "mcp"
    AGENT_AS_TOOL = "agent_as_tool"

@dataclass(frozen=True)
class ToolOrigin:
    type: ToolOriginType
    mcp_server_name: str | None = None
    agent_name: str | None = None
    agent_tool_name: str | None = None
```

This is used for tracing and debugging. When you inspect `RunResult.new_items`, each `ToolCallItem` carries its origin, so you can tell whether a tool call came from a regular function, an MCP server, or a nested agent.

### `is_enabled`

The `is_enabled` field lets you dynamically show or hide tools based on runtime state:

```python
async def is_premium_tool(ctx: RunContextWrapper[UserContext], agent: AgentBase) -> bool:
    return ctx.context.is_pro_user

@function_tool(is_enabled=is_premium_tool)
async def advanced_search(query: str) -> str:
    ...
```

At the start of each turn, `resolve_enabled_function_tools()` checks all `is_enabled` callables concurrently via `asyncio.gather()`. Disabled tools are completely hidden from the LLM — they don't appear in the tool list at all.

### `defer_loading` and `ToolSearchTool`

When you have many tools, sending all tool schemas to the LLM every turn wastes tokens. `defer_loading=True` hides a tool from the initial tool list, and `ToolSearchTool` lets the LLM load it on demand:

```python
from agents import Agent, ToolSearchTool, function_tool, tool_namespace

@function_tool(defer_loading=True)
def get_customer_profile(customer_id: str) -> str:
    """Fetch a CRM customer profile."""
    return f"profile for {customer_id}"

@function_tool(defer_loading=True)
def list_open_orders(customer_id: str) -> str:
    """List open orders for a customer."""
    return f"orders for {customer_id}"

crm_tools = tool_namespace(
    name="crm",
    description="CRM tools for customer lookups.",
    tools=[get_customer_profile, list_open_orders],
)

agent = Agent(
    name="Operations assistant",
    instructions="Load the crm namespace before using CRM tools.",
    tools=[*crm_tools, ToolSearchTool()],
)
```

**How it works:**

1. On the first turn, the LLM only sees `ToolSearchTool` in its tool list (plus any non-deferred tools).
2. When the LLM needs a CRM tool, it calls `tool_search` with a query like "load crm namespace".
3. OpenAI's servers load the deferred tool schemas and make them available for subsequent calls.
4. The LLM can now call `get_customer_profile` or `list_open_orders`.

**Constraints:**
- `defer_loading` only works with OpenAI Responses models
- You must include exactly one `ToolSearchTool()` per agent
- `tool_choice` cannot target deferred-only tools by name — use `auto` or `required`
- Prefer `tool_namespace()` groups over many individually deferred tools

Cross-reference: See the official docs (`docs/tools.md`) for the complete `ToolSearchTool` configuration and `tool_namespace()` API.

---

## 3.13 Putting It All Together: A Complete Tool System

Let's build a realistic example that uses every feature covered in this chapter:

```python
import asyncio
import json
from dataclasses import dataclass
from typing import Annotated

from agents import Agent, Runner, RunContextWrapper, function_tool
from agents.tool_context import ToolContext
from agents.tool_guardrails import ToolGuardrailFunctionOutput, tool_input_guardrail, tool_output_guardrail
from agents.agent import ToolsToFinalOutputResult

@dataclass
class AppContext:
    user_id: str
    is_admin: bool
    api_base: str = "https://api.example.com"

@tool_input_guardrail
def validate_sql(data) -> ToolGuardrailFunctionOutput:
    args = json.loads(data.context.tool_arguments)
    sql = args.get("sql", "")
    forbidden = ["DROP", "DELETE", "TRUNCATE", "ALTER"]
    if any(word in sql.upper() for word in forbidden):
        return ToolGuardrailFunctionOutput(
            output_info="Destructive SQL detected",
            behavior={"type": "reject_content", "message": "Destructive SQL is not allowed."},
        )
    return ToolGuardrailFunctionOutput.allow()

@tool_output_guardrail
def redact_pii(data) -> ToolGuardrailFunctionOutput:
    output_str = str(data.output)
    import re
    if re.search(r"\b\d{3}-\d{2}-\d{4}\b", output_str):
        return ToolGuardrailFunctionOutput(
            output_info="SSN detected in output",
            behavior={"type": "reject_content", "message": "Output contains PII and was redacted."},
        )
    return ToolGuardrailFunctionOutput.allow()

async def needs_db_approval(ctx: RunContextWrapper[AppContext], args: dict, call_id: str) -> bool:
    return not ctx.context.is_admin

@function_tool(
    name_override="query_db",
    timeout=10.0,
    timeout_behavior="error_as_result",
    needs_approval=needs_db_approval,
    tool_input_guardrails=[validate_sql],
    tool_output_guardrails=[redact_pii],
    failure_error_function=lambda ctx, err: f"Database error: {err}. Please try a simpler query.",
)
async def query_database(
    ctx: ToolContext[AppContext],
    sql: Annotated[str, "The SQL query to execute"],
    limit: Annotated[int, "Max rows to return"] = 100,
) -> str:
    """Execute a read-only SQL query against the database."""
    await asyncio.sleep(0.1)
    return json.dumps([
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
    ])

@function_tool
async def get_schema(ctx: ToolContext[AppContext]) -> str:
    """Get the database schema."""
    return "users(id, name, email), orders(id, user_id, amount, date)"

agent = Agent[AppContext](
    name="Database Assistant",
    instructions="Help users query the database. Always check the schema first.",
    tools=[query_database, get_schema],
)

async def main():
    result = await Runner.run(
        agent,
        "Show me all users",
        context=AppContext(user_id="u1", is_admin=False),
    )
    print(result.final_output)
    print(f"Turns: {len(result.raw_responses)}")
    for item in result.new_items:
        print(f"  Item: {type(item).__name__}")

if __name__ == "__main__":
    asyncio.run(main())
```

### What Happens When You Run This

When the LLM decides to call `query_db`, here's what happens:

1. **Approval check**: `needs_db_approval` returns `True` (non-admin user). The run is interrupted, and a `ToolApprovalItem` is returned.

2. **After approval**: The run resumes.

3. **Input guardrail**: `validate_sql` checks the SQL. If it contains `DROP` or `DELETE`, the LLM gets "Destructive SQL is not allowed." and can try again.

4. **Pre-invoke hooks**: `RunHooks.on_tool_start` and `AgentHooks.on_tool_start` fire (if configured).

5. **Invocation**: `invoke_function_tool()` calls the function with a 10-second timeout. If the function takes too long, the LLM gets "Tool 'query_db' timed out after 10 seconds."

6. **Error handling**: If the function raises an exception, `failure_error_function` converts it to "Database error: ...". The LLM sees this and can retry.

7. **Output guardrail**: `redact_pii` checks the output for SSNs. If found, the output is replaced with "Output contains PII and was redacted."

8. **Post-invoke hooks**: `RunHooks.on_tool_end` and `AgentHooks.on_tool_end` fire.

9. **Result**: The final output (possibly modified by guardrails) is sent back to the LLM.

You can inspect the `RunResult` to verify:

```python
result = await Runner.run(agent, "Show me all users", context=AppContext(...))

print(result.final_output)
print(f"Turns: {len(result.raw_responses)}")
for item in result.new_items:
    print(f"  {type(item).__name__}: {getattr(item, 'raw_item', 'N/A')}")
print(f"Total tokens: {result.context_wrapper.usage.total_tokens}")
```

### Multi-Turn Tool Interactions: What the LLM Actually Sees

The most important thing to understand about tools is that **the LLM self-corrects across turns**. When a tool returns an error or a guardrail rejects, the LLM sees that result and tries again. Let's trace a realistic 4-turn interaction:

**Turn 1: LLM calls the wrong tool (destructive SQL)**

The user asks "Remove all inactive users". The LLM calls `query_db` with `DROP TABLE inactive_users`:

```
LLM output:  function_call(name="query_db", arguments='{"sql": "DROP TABLE inactive_users"}')
Tool result: "Destructive SQL is not allowed."     ← input guardrail rejected
```

**Turn 2: LLM tries again with safe SQL**

The LLM sees the rejection and reformulates:

```
LLM output:  function_call(name="query_db", arguments='{"sql": "SELECT * FROM users WHERE active = false"}')
Tool result: '[{"id": 3, "name": "Charlie", "active": false}]'
```

**Turn 3: LLM calls a second tool for context**

The LLM decides to check the schema to understand the data better:

```
LLM output:  function_call(name="get_schema", arguments='{}')
Tool result: "users(id, name, email), orders(id, user_id, amount, date)"
```

**Turn 4: LLM produces final output**

```
LLM output:  "I found 1 inactive user: Charlie (ID 3). I can't directly remove users due to
              safety rules, but you could update their status. Would you like me to help with that?"
```

**What `to_input_list()` looks like after 4 turns:**

```python
result.to_input_list()
# [
#   {"role": "user", "content": "Remove all inactive users"},
#   {"type": "function_call", "name": "query_db", "call_id": "call_1",
#    "arguments": '{"sql": "DROP TABLE inactive_users"}'},
#   {"type": "function_call_output", "call_id": "call_1",
#    "output": "Destructive SQL is not allowed."},
#   {"type": "function_call", "name": "query_db", "call_id": "call_2",
#    "arguments": '{"sql": "SELECT * FROM users WHERE active = false"}'},
#   {"type": "function_call_output", "call_id": "call_2",
#    "output": '[{"id": 3, "name": "Charlie", "active": false}]'},
#   {"type": "function_call", "name": "get_schema", "call_id": "call_3",
#    "arguments": '{}'},
#   {"type": "function_call_output", "call_id": "call_3",
#    "output": "users(id, name, email), orders(id, user_id, amount, date)"},
# ]
```

Every `function_call` and `function_call_output` pair is included — this is the complete conversation history that the LLM uses to understand what happened. The guardrail rejection in Turn 1 appears as a normal tool output, which is why the LLM can learn from it and try a different approach.

This is also why `error_as_result` and `reject_content` are so powerful: they give the LLM a chance to self-correct instead of crashing the entire run.

---

## 3.14 FunctionTool Field Reference

| Field | Type | Default | Category | Reference |
|---|---|---|---|---|
| `name` | `str` | (required) | Identity | LLM sees this |
| `description` | `str` | (required) | Identity | LLM sees this |
| `params_json_schema` | `dict[str, Any]` | (required) | Identity | Generated by `function_schema()` |
| `on_invoke_tool` | `Callable[[ToolContext, str], Awaitable[Any]]` | (required) | Execution | Wrapped by `_FailureHandling...Invoker` |
| `strict_json_schema` | `bool` | `True` | Schema | §3.3 Key Insight #5 |
| `is_enabled` | `bool \| Callable` | `True` | Control | §3.12 |
| `tool_input_guardrails` | `list[ToolInputGuardrail] \| None` | `None` | Safety | §3.10 |
| `tool_output_guardrails` | `list[ToolOutputGuardrail] \| None` | `None` | Safety | §3.10 |
| `needs_approval` | `bool \| Callable` | `False` | Safety | §3.9 |
| `timeout_seconds` | `float \| None` | `None` | Safety | §3.8 |
| `timeout_behavior` | `"error_as_result" \| "raise_exception"` | `"error_as_result"` | Safety | §3.8 |
| `timeout_error_function` | `ToolErrorFunction \| None` | `None` | Safety | §3.8 |
| `defer_loading` | `bool` | `False` | Discovery | ToolSearchTool loads it |
| `_failure_error_function` | `ToolErrorFunction \| None` | `None` | Internal | §3.7 |
| `_use_default_failure_error_function` | `bool` | `True` | Internal | §3.7 |
| `_is_agent_tool` | `bool` | `False` | Internal | Agent.as_tool() sets this |
| `_tool_origin` | `ToolOrigin \| None` | `None` | Internal | §3.12 |

---

## 3.15 Key Takeaways

1. **`FunctionTool` is the core tool type** — all custom Python functions, agent-as-tool, and MCP tools become `FunctionTool` internally
2. **`function_schema()` is the transformation engine** — Python type hints + docstrings → strict JSON schema via Pydantic
3. **The invoker chain has three layers** — inner invoker (JSON→Pydantic→call), timeout wrapper, error handler wrapper
4. **Error handling is LLM-friendly by default** — exceptions become messages the LLM can see and recover from
5. **Timeouts use `asyncio.wait_for()`** — only works for async functions; sync functions can't be timed out
6. **Human approval interrupts the run** — the runner returns `RunState` with a pending interruption
7. **Tool guardrails are per-tool-call** — separate from agent-level guardrails, with three behaviors (allow, reject, raise)
8. **The full pipeline is: approval → input guardrails → pre-hooks → invoke → output guardrails → post-hooks**
9. **`is_enabled` can dynamically hide tools** — evaluated at the start of each turn
10. **`ToolOrigin` tracks where tools came from** — useful for tracing and debugging
11. **`strict_json_schema` is on by default** — all properties become required, no additional properties allowed
12. **`__copy__` handles the non-dataclass attributes** — necessary because the invoker function is set dynamically
