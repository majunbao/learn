# Chapter 8: Patterns & Best Practices — Production-Grade Agent Design

Chapters 1–7 covered each SDK subsystem in isolation. This chapter is different: it shows how to **compose** those subsystems into production-ready applications. Every pattern here comes from the source code — we'll read `retry.py`, `run_error_handlers.py`, `run_config.py`, and `tool.py` to understand what the SDK already provides, then build patterns on top.

## How to Read This Chapter

**Pass 1 — Build intuition (20 min):** Read §8.1 (the pattern map) → §8.2 (error handling overview only) → §8.5 (retry table only) → §8.7 (orchestration comparison only) → §8.10 (checklist only). Skip all 🔥 source code walkthroughs and deep subsections.

**Pass 2 — Dive into source code (40 min):** Read the three 🔥 walkthroughs: §8.3 (RunErrorHandlers pipeline), §8.6 (RetryPolicy system), §8.9 (tool_use_behavior + reset_tool_choice source). Also read §8.2 (error handling layers) and §8.4 (tool failure error function).

**Pass 3 — Fill gaps.** Itemized list:
- Error handling: all 4 layers + exception catch map? → §8.2 (4-layer diagram + catch table)
- MaxTurnsExceeded handler pipeline? → §8.3 (🔥 source code walkthrough + RunErrorData fields)
- Tool failure_error_function: 3 levels of customization? → §8.4 (source code + 3-level table + example)
- Model retry: backoff, policies, RewindCallable? → §8.5 (retry flow diagram) + §8.6 (🔥 source walkthrough + 6 built-in policies table)
- RunConfig production knobs? → §8.7 (14-field table + when-to-use)
- Multi-agent orchestration: agents-as-tools vs handoffs vs code? → §8.8 (3-pattern comparison + when to choose)
- tool_use_behavior: 4 modes + loop prevention? → §8.9 (🔥 source walkthrough + 4-mode table + reset_tool_choice source)
- Human-in-the-loop: durable approvals? → §8.10 (flow diagram + serialization options + versioning)
- Observability: tracing, hooks, usage? → §8.11 (3-layer stack + usage monitoring example)
- Production checklist? → §8.12 (28-item checklist organized by deployment phase)
- Putting it together: full production example? → §8.13 (multi-agent system + 4-scenario post-run analysis)
- Key takeaways? → §8.14

---

## 8.1 The Pattern Map

Production agent systems need patterns across five dimensions:

```
┌─────────────────────────────────────────────────────────────────┐
│                   PRODUCTION PATTERN MAP                        │
├─────────────┬─────────────┬──────────────┬─────────────────────┤
│  RELIABILITY │  CONTROL    │  SAFETY      │  OBSERVABILITY      │
│             │             │              │                     │
│  Error      │  Retry      │  Guardrails  │  Tracing            │
│  handling   │  policies   │  (Ch7)       │  Hooks              │
│  §8.2-8.4   │  §8.5-8.6   │              │  Usage monitoring   │
│             │             │  HITL        │  §8.11              │
│  MaxTurns   │  tool_use   │  §8.10       │                     │
│  handlers   │  _behavior  │              │                     │
│             │  §8.9       │              │                     │
├─────────────┼─────────────┴──────────────┴─────────────────────┤
│  ORCHESTRATION                                                 │
│  Agents-as-tools vs Handoffs vs Code   §8.8                   │
│  RunConfig production knobs            §8.7                   │
└────────────────────────────────────────────────────────────────┘
```

Each section in this chapter covers one cell. By the end, you'll have a complete mental model for building agents that don't break, don't loop, don't exceed budgets, and can be debugged when they do.

---

## 8.2 Error Handling: The Four Layers

The SDK provides error handling at four distinct layers. Understanding which layer catches which error is the single most important production skill:

```
Layer 1: TOOL LEVEL          ← failure_error_function (per-tool error message)
         "Tool X failed: try again"                          

Layer 2: RUN LEVEL           ← RunErrorHandlers (max_turns recovery)
         "You hit max turns, but here's a partial answer"    

Layer 3: EXCEPTION LEVEL     ← try/except around Runner.run()
         "Guardrail tripped, model misbehaved, timeout"      

Layer 4: INFRASTRUCTURE      ← RetryPolicy (transient API failures)
         "429 rate limit → wait 2s → retry"                  
```

### Exception Catch Map

| Exception | Where to catch | Typical recovery |
|---|---|---|
| `MaxTurnsExceeded` | RunErrorHandlers (Layer 2) or try/except | Return partial result or re-run with higher max_turns |
| `InputGuardrailTripwireTriggered` | try/except around `Runner.run()` | Log violation, reject user input |
| `OutputGuardrailTripwireTriggered` | try/except around `Runner.run()` | Log violation, return fallback message |
| `ToolInputGuardrailTripwireTriggered` | try/except around `Runner.run()` | Log violation, return error to user |
| `ToolOutputGuardrailTripwireTriggered` | try/except around `Runner.run()` | Log violation, return error to user |
| `ModelBehaviorError` | try/except | Log and retry or return error |
| `ToolTimeoutError` | try/except or `failure_error_function` | Return timeout message to LLM |
| `UserError` | try/except (bug in your code) | Fix your code |
| `APIConnectionError` / `APITimeoutError` | RetryPolicy (Layer 4) | Auto-retry with backoff |

### The Catch-All Pattern

```python
from agents import Runner
from agents.exceptions import (
    AgentsException,
    InputGuardrailTripwireTriggered,
    MaxTurnsExceeded,
    ModelBehaviorError,
)

try:
    result = await Runner.run(agent, user_input, run_config=config)
except InputGuardrailTripwireTriggered as e:
    guardrail_name = e.guardrail_result.guardrail.get_name()
    print(f"Safety violation by {guardrail_name}: {e.guardrail_result.output.output_info}")
except MaxTurnsExceeded:
    result = await Runner.run(agent, user_input, run_config=RunConfig(max_turns=30))
except ModelBehaviorError as e:
    print(f"Model misbehaved: {e.message}")
except AgentsException as e:
    if e.run_data is not None:
        print(f"Last agent: {e.run_data.last_agent.name}")
        print(f"Items generated before failure: {len(e.run_data.new_items)}")
    raise
```

**Key insight:** Every `AgentsException` may carry a `run_data: RunErrorDetails | None` field that gives you the full audit trail up to the point of failure — input, items, raw responses, and last agent. Always check it when debugging.

---

## 8.3 🔥 RunErrorHandlers: The MaxTurnsExceeded Recovery Pipeline

When `max_turns` is hit, the default behavior is to raise `MaxTurnsExceeded`. But the SDK provides a **recovery pipeline** that lets you return a partial result instead. Here's the source code:

```python
# src/agents/run_error_handlers.py (simplified)

@dataclass
class RunErrorData:
    """Snapshot of run data passed to error handlers."""
    input: str | list[TResponseInputItem]
    new_items: list[RunItem]
    history: list[TResponseInputItem]
    output: list[TResponseInputItem]
    raw_responses: list[ModelResponse]
    last_agent: Agent[Any]

@dataclass
class RunErrorHandlerInput(Generic[TContext]):
    error: MaxTurnsExceeded
    context: RunContextWrapper[TContext]
    run_data: RunErrorData

@dataclass
class RunErrorHandlerResult:
    """Result returned by an error handler."""
    final_output: Any
    include_in_history: bool = True

RunErrorHandler = Callable[
    [RunErrorHandlerInput[TContext]],
    MaybeAwaitable[RunErrorHandlerResult | dict[str, Any] | Any | None],
]

class RunErrorHandlers(TypedDict, Generic[TContext], total=False):
    max_turns: RunErrorHandler[TContext]
```

### How the Resolution Pipeline Works

```
MaxTurnsExceeded raised
        │
        ▼
┌─ resolve_run_error_handler_result() ──────────────────────┐
│                                                           │
│  1. Check RunConfig.error_handlers["max_turns"]           │
│     If None → return None → exception propagates          │
│                                                           │
│  2. Call handler(error, context, run_data)                 │
│                                                           │
│  3. Normalize result:                                     │
│     ┌────────────────────────┬──────────────────────────┐ │
│     │ Handler returns...     │ SDK converts to...        │ │
│     ├────────────────────────┼──────────────────────────┤ │
│     │ None                   │ None (exception raises)   │ │
│     │ RunErrorHandlerResult  │ Used as-is                │ │
│     │ dict with final_output │ RunErrorHandlerResult(**) │ │
│     │ Any other value        │ RunErrorHandlerResult(    │ │
│     │                        │   final_output=value)     │ │
│     └────────────────────────┴──────────────────────────┘ │
│                                                           │
│  4. If result is not None:                                │
│     → validate_handler_final_output(agent, final_output)  │
│     → If structured output, validates against schema      │
│     → create_message_output_item(agent, output_text)      │
│     → Return RunResult with handler's final_output        │
└───────────────────────────────────────────────────────────┘
```

### Field-by-Field: RunErrorData

| Field | Type | What it gives you |
|---|---|---|
| `input` | `str \| list[TResponseInputItem]` | The original input you passed to `Runner.run()` |
| `new_items` | `list[RunItem]` | All items generated before the max_turns limit |
| `history` | `list[TResponseInputItem]` | Full conversation history including new items |
| `output` | `list[TResponseInputItem]` | `new_items` converted to input-item format |
| `raw_responses` | `list[ModelResponse]` | Raw API responses from every LLM call |
| `last_agent` | `Agent[Any]` | The agent that was active when max_turns was hit |

### Practical Example: Graceful Degradation

```python
from agents import Runner, RunConfig
from agents.run_error_handlers import (
    RunErrorData,
    RunErrorHandlerInput,
    RunErrorHandlerResult,
    RunErrorHandlers,
)

async def handle_max_turns(
    handler_input: RunErrorHandlerInput[None],
) -> RunErrorHandlerResult:
    data = handler_input.run_data

    last_text = ""
    for item in reversed(data.new_items):
        if hasattr(item, "raw_item") and hasattr(item.raw_item, "content"):
            for content in item.raw_item.content:
                if hasattr(content, "text"):
                    last_text = content.text
                    break
        if last_text:
            break

    if last_text:
        return RunErrorHandlerResult(
            final_output=f"(Partial result — max turns reached)\n\n{last_text}",
            include_in_history=True,
        )
    return RunErrorHandlerResult(
        final_output="I need more turns to complete this task. Please ask me to continue.",
        include_in_history=True,
    )

config = RunConfig(
    max_turns=10,
    error_handlers=RunErrorHandlers(max_turns=handle_max_turns),
)

result = await Runner.run(agent, user_input, run_config=config)
print(result.final_output)
```

**Key insights from the source code:**

1. **The handler can return `None`** to let the exception propagate — useful if you only want to handle certain `MaxTurnsExceeded` cases.
2. **`include_in_history=True`** means the handler's output is added to conversation history. Set to `False` if you're returning an error message that shouldn't influence future turns.
3. **Structured output validation applies** — if your agent has `output_type=CalendarEvent`, your handler must return something compatible with that schema. The SDK calls `validate_handler_final_output()` which runs the same `output_schema.validate_json()` check.
4. **The handler receives `RunContextWrapper`**, so you can check `handler_input.context.usage` to log how many tokens were consumed before hitting the limit.

---

## 8.4 Tool Error Handling: Three Levels of Customization

When a `function_tool` raises an exception, the SDK doesn't crash the run. Instead, it sends an error message back to the LLM so it can try a different approach. You control this at three levels:

```
┌─────────────────────────────────────────────────────────┐
│  Level 1: @function_tool(failure_error_function=...)    │
│  → Per-tool error message formatter                     │
│  → Overrides the SDK default for THIS tool only         │
├─────────────────────────────────────────────────────────┤
│  Level 2: RunConfig(tool_error_formatter=...)           │
│  → Run-wide error message formatter                     │
│  → Currently only fires for approval rejections         │
│  → Falls back to SDK default for tool exceptions        │
├─────────────────────────────────────────────────────────┤
│  Level 3: default_tool_error_function                   │
│  → SDK default (used when Levels 1 & 2 are not set)    │
│  → Returns: "An error occurred while running the tool." │
└─────────────────────────────────────────────────────────┘
```

### 🔥 Source Code: `default_tool_error_function`

```python
# src/agents/tool.py (simplified)

def default_tool_error_function(ctx: RunContextWrapper[Any], error: Exception) -> str:
    """The default tool error function, which just returns a generic error message."""
    json_decode_error = _extract_tool_argument_json_error(error)
    if json_decode_error is not None:
        return (
            "An error occurred while parsing tool arguments. "
            "Please try again with valid JSON. "
            f"Error: {json_decode_error}"
        )
    return f"An error occurred while running the tool. Please try again. Error: {str(error)}"
```

**Non-obvious behavior:** The default function distinguishes JSON parse errors (when the LLM sends malformed arguments) from general errors. For JSON errors, it gives the model specific guidance ("Please try again with valid JSON"). For other errors, it includes the error string so the model can adapt.

### Level 1: Per-Tool Customization

```python
from agents import function_tool, RunContextWrapper

async def db_error_handler(ctx: RunContextWrapper[None], error: Exception) -> str:
    if "connection" in str(error).lower():
        return "The database is temporarily unavailable. Try again in a moment."
    if "timeout" in str(error).lower():
        return "The query took too long. Try a simpler query."
    return f"Database error: {error}"

@function_tool(failure_error_function=db_error_handler)
async def query_database(sql: str) -> str:
    result = await db.execute(sql)
    return str(result)
```

### Level 2: Run-Wide Approval Rejection Formatter

```python
from agents import RunConfig, ToolErrorFormatterArgs

def format_rejection(args: ToolErrorFormatterArgs[None]) -> str | None:
    if args.kind != "approval_rejected":
        return None
    return f"The action '{args.tool_name}' was not approved. Reason: requires manager sign-off."

config = RunConfig(tool_error_formatter=format_rejection)
```

**`ToolErrorFormatterArgs` field reference:**

| Field | Type | Purpose |
|---|---|---|
| `kind` | `Literal["approval_rejected"]` | Error category (currently only one kind) |
| `tool_type` | `Literal["function", "computer", "shell", "apply_patch", "custom"]` | Which tool runtime produced the error |
| `tool_name` | `str` | Name of the tool that was rejected |
| `call_id` | `str` | Unique tool call identifier |
| `default_message` | `str` | What the SDK would say by default |
| `run_context` | `RunContextWrapper[TContext]` | Active run context (for accessing usage, context data, etc.) |

Returning `None` from the formatter falls back to the SDK default message.

### Level 3: Disabling Error Recovery Entirely

Set `failure_error_function=None` to make tool errors **raise exceptions** instead of returning error messages:

```python
@function_tool(failure_error_function=None)
async def critical_payment_tool(amount: float) -> str:
    ...
```

With `None`, if this tool raises, the entire run crashes with the original exception. Use this only for tools where partial recovery is worse than failing fast.

---

## 8.5 Model Retry: When the API Fails

When the OpenAI API (or any model provider) returns a transient error — rate limit (429), server error (500/503), connection timeout — the SDK can automatically retry. This is powered by `ModelRetrySettings` in `RunConfig.model_settings`.

```
LLM Call Failed
       │
       ▼
┌─ get_response_with_retry() ─────────────────────────────┐
│                                                         │
│  1. Call the LLM API                                    │
│                                                         │
│  2. If error:                                           │
│     a. Normalize error → ModelRetryNormalizedError      │
│        (status_code, error_code, is_network_error,      │
│         is_timeout, retry_after, is_abort)              │
│                                                         │
│     b. Get provider_advice from model adapter           │
│        (some providers say "retry after X seconds")     │
│                                                         │
│     c. Evaluate RetryPolicy(context) → RetryDecision    │
│        ├── retry=True, delay=2.0  → sleep, then retry  │
│        ├── retry=True, delay=None → use backoff delay   │
│        └── retry=False            → raise exception     │
│                                                         │
│  3. If retry:                                           │
│     a. Rewind conversation state (if needed)            │
│     b. Wait delay seconds                               │
│     c. Increment attempt counter                        │
│     d. Go to step 1                                     │
│                                                         │
│  4. If max_retries exhausted: raise original exception  │
└─────────────────────────────────────────────────────────┘
```

### Retry Configuration in ModelSettings

```python
from agents import Agent, ModelSettings
from agents.retry import ModelRetrySettings, ModelRetryBackoffSettings

agent = Agent(
    name="Resilient Agent",
    model_settings=ModelSettings(
        retry_settings=ModelRetrySettings(
            max_retries=3,
            backoff=ModelRetryBackoffSettings(
                initial_delay=0.5,
                max_delay=8.0,
                multiplier=2.0,
                jitter=True,
            ),
        ),
    ),
)
```

**Backoff default values (from source):**

| Parameter | Default | Purpose |
|---|---|---|
| `initial_delay` | 0.25s | Wait before first retry |
| `max_delay` | 2.0s | Cap on any single delay |
| `multiplier` | 2.0 | Each delay = previous × multiplier |
| `jitter` | True | Randomize delay ±12.5% to avoid thundering herd |

With defaults: retry 1 waits ~0.25s, retry 2 waits ~0.5s, retry 3 waits ~1.0s (capped at 2.0s).

---

## 8.6 🔥 RetryPolicy: Controlling What Gets Retried

By default, if you set `max_retries`, the SDK retries nothing — you must also provide a `policy`. The SDK ships with 6 built-in policies in `retry_policies`:

```python
# src/agents/retry.py (simplified)

class _RetryPolicies:
    def never(self) -> RetryPolicy: ...
    def provider_suggested(self) -> RetryPolicy: ...
    def network_error(self) -> RetryPolicy: ...
    def retry_after(self) -> RetryPolicy: ...
    def http_status(self, statuses: Iterable[int]) -> RetryPolicy: ...
    def all(self, *policies: RetryPolicy) -> RetryPolicy: ...
    def any(self, *policies: RetryPolicy) -> RetryPolicy: ...

retry_policies = _RetryPolicies()
```

### Built-in Policy Reference

| Policy | Retries when | `safe_transport` | `all_transient` | Use case |
|---|---|---|---|---|
| `retry_policies.never()` | Never | No | No | Explicitly disable retries |
| `retry_policies.provider_suggested()` | Provider returns `advice.suggested=True` | Yes | No | Respect server guidance (429 with Retry-After) |
| `retry_policies.network_error()` | `is_network_error` or `is_timeout` | Yes | No | Connection failures, DNS errors, timeouts |
| `retry_policies.retry_after()` | `retry_after` header present | No | No | Servers that send `Retry-After` headers |
| `retry_policies.http_status({429, 503})` | Status code matches | No | No | Specific HTTP errors you want to retry |
| `retry_policies.all(p1, p2)` | ALL policies agree to retry | AND of both | AND of both | Require multiple conditions |
| `retry_policies.any(p1, p2)` | ANY policy agrees to retry | OR of both | OR of both | Broaden retry surface |

### 🔥 Source Code: `RetryPolicyContext` and `RetryDecision`

```python
# src/agents/retry.py

@dataclass
class RetryPolicyContext:
    """Context passed to runtime retry policy callbacks."""
    error: Exception
    attempt: int
    max_retries: int
    stream: bool
    normalized: ModelRetryNormalizedError
    provider_advice: ModelRetryAdvice | None = None

@dataclass
class RetryDecision:
    """Explicit retry decision returned by retry policies."""
    retry: bool
    delay: float | None = None
    reason: str | None = None
    _hard_veto: bool = field(default=False, init=False, repr=False, compare=False)
    _approves_replay: bool = field(default=False, init=False, repr=False, compare=False)
```

**Key insights:**

1. **`_hard_veto`** — If any policy returns a `RetryDecision` with `_hard_veto=True`, the combined `any()` / `all()` policy immediately stops trying other policies. `provider_suggested()` uses this when the provider explicitly says "do not retry" (`advice.suggested=False`).

2. **`_approves_replay`** — Used for conversation-locked retries. When the API says the conversation is temporarily locked (e.g., another request is in flight), the SDK may need to "rewind" the conversation state and replay. A policy that `_approves_replay` signals that replaying is safe.

3. **Your custom policy can return `bool` or `RetryDecision`** — Returning `True` is shorthand for `RetryDecision(retry=True)` with default delay. Returning a `RetryDecision` gives you explicit control over delay and reason.

### Practical Example: Custom Retry Policy

```python
from agents.retry import RetryPolicyContext, RetryDecision, retry_policies
from agents import Agent, ModelSettings
from agents.retry import ModelRetrySettings

async def smart_retry(ctx: RetryPolicyContext) -> bool | RetryDecision:
    if ctx.normalized.status_code == 429:
        delay = ctx.normalized.retry_after or 2.0
        return RetryDecision(retry=True, delay=delay, reason="Rate limited")
    if ctx.normalized.is_network_error:
        return RetryDecision(retry=True, delay=1.0)
    if ctx.normalized.status_code in (500, 502, 503):
        return True
    return False

agent = Agent(
    name="Production Agent",
    model_settings=ModelSettings(
        retry_settings=ModelRetrySettings(
            max_retries=5,
            policy=smart_retry,
        ),
    ),
)
```

### Composing Policies

```python
from agents.retry import retry_policies, ModelRetrySettings, ModelRetryBackoffSettings
from agents import ModelSettings

settings = ModelSettings(
    retry_settings=ModelRetrySettings(
        max_retries=4,
        backoff=ModelRetryBackoffSettings(
            initial_delay=1.0,
            max_delay=30.0,
            multiplier=3.0,
        ),
        policy=retry_policies.any(
            retry_policies.provider_suggested(),
            retry_policies.network_error(),
            retry_policies.http_status({429, 502, 503}),
        ),
    ),
)
```

This combination means: retry if the provider suggests it, OR if it's a network error, OR if the status is 429/502/503. The first retry waits ~1s, the second ~3s, the third ~9s, the fourth ~27s (capped at 30s).

---

## 8.7 RunConfig: The Production Knobs

`RunConfig` is the central place to configure a run's behavior. Here's a production-focused field reference:

| Field | Default | Production recommendation | Chapter reference |
|---|---|---|---|
| `model` | `None` (use agent's) | Override for A/B testing | Ch2 §2.3 |
| `model_provider` | `MultiProvider()` | Set if using non-OpenAI | Ch2 §2.10 |
| `model_settings` | `None` | Set `temperature`, `retry_settings` here | Ch2 §2.3 |
| `handoff_input_filter` | `None` | Use `remove_all_tools` in production | Ch7 §7.3 |
| `nest_handoff_history` | `False` | Enable for long multi-agent chains | Ch7 §7.3 |
| `input_guardrails` | `None` | Add safety guardrails at run level | Ch7 §7.5 |
| `output_guardrails` | `None` | Add output validation at run level | Ch7 §7.5 |
| `tracing_disabled` | `False` | Keep `False` in production! | Ch7 §7.9 |
| `workflow_name` | `"Agent workflow"` | Set meaningful name for trace UI | Ch7 §7.9 |
| `trace_include_sensitive_data` | env var | Set `False` if logs are shared | Ch7 §7.9 |
| `call_model_input_filter` | `None` | Token budget enforcement | §8.11 below |
| `tool_error_formatter` | `None` | Custom rejection messages | §8.4 |
| `error_handlers` | `None` | Handle `MaxTurnsExceeded` gracefully | §8.3 |
| `max_turns` | 10 | Always set explicitly! Never leave at default in production | §8.3 |

### Token Budget with `call_model_input_filter`

```python
from agents import RunConfig, CallModelData, ModelInputData

TOKEN_BUDGET = 100_000

async def enforce_token_budget(data: CallModelData[None]) -> ModelInputData:
    estimated_tokens = sum(
        len(str(item)) // 4 for item in data.model_data.input
    )
    if estimated_tokens > TOKEN_BUDGET:
        trimmed = data.model_data.input[-50:]
        return ModelInputData(input=trimmed, instructions=data.model_data.instructions)
    return data.model_data

config = RunConfig(call_model_input_filter=enforce_token_budget)
```

---

## 8.8 Multi-Agent Orchestration Patterns

There are three fundamental orchestration patterns. The choice depends on your control requirements:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Pattern 1: Agents as Tools (Manager/Worker)                        │
│                                                                     │
│  User → Manager Agent ──calls──→ Worker A (as tool)                 │
│                        ──calls──→ Worker B (as tool)                 │
│  Manager retains control, combines results, handles conversation    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Pattern 2: Handoffs (Triage/Specialist)                            │
│                                                                     │
│  User → Triage Agent ──hands off──→ Specialist Agent                │
│  Specialist takes over conversation directly                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Pattern 3: Code Orchestration (Deterministic Pipeline)             │
│                                                                     │
│  Code calls Agent A → transforms output → calls Agent B → ...       │
│  You control the flow in Python, the LLM controls within each step  │
└─────────────────────────────────────────────────────────────────────┘
```

### Comparison Table

| Aspect | Agents as Tools | Handoffs | Code Orchestration |
|---|---|---|---|
| Who controls flow | Manager LLM | Triage LLM | Your Python code |
| Conversation owner | Manager (always) | Specialist (after handoff) | Each agent independently |
| Use when | Combining multiple results, shared context | Routing to domain expert | Deterministic steps, parallel tasks |
| Cost per turn | Higher (manager re-processes) | Lower (one agent per turn) | Controlled (you decide) |
| Guardrails | Centralized on manager | Per-agent | Per-agent + your code |
| Context sharing | Automatic (same run) | Via HandoffInputData | You pass explicitly |
| Error isolation | Worker errors return to manager | Specialist errors propagate | You handle in code |
| Best for | Research → synthesis, multi-perspective | Customer support routing, specialization | ETL, classification, review loops |

### Pattern 1: Agents as Tools

```python
from agents import Agent, Runner

researcher = Agent(
    name="Researcher",
    instructions="Find relevant information. Return concise findings.",
    tools=[web_search_tool],
)

writer = Agent(
    name="Writer",
    instructions="Write a polished article based on the research findings.",
)

manager = Agent(
    name="Manager",
    instructions="Research the topic, then write an article. Combine both results.",
    tools=[
        researcher.as_tool(tool_name="research", tool_description="Research a topic"),
        writer.as_tool(tool_name="write", tool_description="Write an article from findings"),
    ],
)

result = await Runner.run(manager, "Write about quantum computing")
```

### Pattern 2: Handoffs

```python
from agents import Agent, handoff, RunContextWrapper
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

billing_agent = Agent(
    name="Billing",
    instructions=prompt_with_handoff_instructions("Handle billing questions only."),
)

tech_agent = Agent(
    name="Tech Support",
    instructions=prompt_with_handoff_instructions("Handle technical issues only."),
)

triage = Agent(
    name="Triage",
    instructions="Route to the right specialist.",
    handoffs=[billing_agent, tech_agent],
)
```

### Pattern 3: Code Orchestration

```python
import asyncio
from agents import Agent, Runner

classifier = Agent(name="Classifier", output_type=Literal["billing", "tech", "general"], ...)
billing = Agent(name="Billing", ...)
tech = Agent(name="Tech Support", ...)
general = Agent(name="General", ...)

agents_map = {"billing": billing, "tech": tech, "general": general}

async def orchestrate(user_input: str):
    classified = await Runner.run(classifier, user_input)
    specialist = agents_map[classified.final_output]
    result = await Runner.run(specialist, user_input)
    return result.final_output
```

### Pattern 3b: Parallel Code Orchestration

```python
async def parallel_research(topics: list[str]) -> list[str]:
    researcher = Agent(name="Researcher", instructions="Research the given topic briefly.")

    tasks = [Runner.run(researcher, f"Research: {topic}") for topic in topics]
    results = await asyncio.gather(*tasks)

    return [r.final_output for r in results]

async def review_loop(draft: str, max_iterations: int = 3) -> str:
    writer = Agent(name="Writer", instructions="Improve the draft based on feedback.")
    reviewer = Agent(name="Reviewer", output_type=Literal["approve", "reject"], 
                     instructions="Approve if quality is high, reject otherwise.")

    current = draft
    for _ in range(max_iterations):
        review = await Runner.run(reviewer, current)
        if review.final_output == "approve":
            break
        improved = await Runner.run(writer, f"Improve this based on review:\n\n{current}")
        current = improved.final_output
    return current
```

---

## 8.9 🔥 Tool Use Behavior: Controlling the Tool Loop

By default, after a tool runs, the LLM sees the result and gets to respond. But sometimes you want the tool's output to be the final answer. The `tool_use_behavior` field on `Agent` controls this:

```python
# src/agents/agent.py (simplified)

tool_use_behavior: (
    Literal["run_llm_again", "stop_on_first_tool"]
    | StopAtTools
    | ToolsToFinalOutputFunction
) = "run_llm_again"
```

### Four Modes

| Mode | Value | After tool call | LLM sees result? | Use case |
|---|---|---|---|---|
| **Loop back** | `"run_llm_again"` (default) | LLM processes result, may call more tools | Yes | General agents |
| **Stop on first** | `"stop_on_first_tool"` | First tool output = final output | No | Simple API wrappers, data retrieval |
| **Stop on named** | `StopAtTools(stop_at_tool_names=[...])` | Stop if tool name matches | No (for matching), Yes (others) | Mixed tools where some are "terminal" |
| **Custom function** | `callable(context, results)` | Your function decides | Your choice | Complex logic (e.g., "stop if JSON, loop if error") |

### 🔥 Source Code: `StopAtTools` and `reset_tool_choice`

```python
# src/agents/agent.py

class StopAtTools(TypedDict):
    stop_at_tool_names: list[str]
    """A list of tool names, any of which will stop the agent from running further."""

# ...

reset_tool_choice: bool = True
"""Whether to reset the tool choice to the default value after a tool has been called.
Defaults to True. This ensures that the agent doesn't enter an infinite loop of tool usage."""
```

**Why `reset_tool_choice=True` matters:** When you set `tool_choice="required"` (forcing the LLM to call a tool), the LLM will keep calling tools forever unless something resets the choice. `reset_tool_choice=True` automatically clears `tool_choice` after the first tool call, allowing the LLM to produce a final text response.

```
tool_choice="required"
        │
        ▼
┌─ Turn 1 ─────────────────────────────┐
│  LLM calls tool → result returned    │
│  reset_tool_choice=True:             │
│    tool_choice → None (reset!)       │
│    Next turn: LLM can output text    │
└──────────────────────────────────────┘

tool_choice="required" + reset_tool_choice=False:
        │
        ▼
┌─ Turn 1 ──→ Tool call ──→ Turn 2 ──→ Tool call ──→ ... INFINITE LOOP!
│  tool_choice stays "required" forever │
└───────────────────────────────────────┘
```

### Custom `ToolsToFinalOutputFunction`

```python
from agents import Agent, RunContextWrapper, ToolsToFinalOutputResult, FunctionToolResult

async def should_stop(
    ctx: RunContextWrapper[None],
    results: list[FunctionToolResult],
) -> ToolsToFinalOutputResult:
    for result in results:
        if "error" in str(result.output).lower():
            return ToolsToFinalOutputResult(is_final_output=False)
    return ToolsToFinalOutputResult(is_final_output=True)

agent = Agent(
    name="API Agent",
    tools=[api_call_tool, fallback_tool],
    tool_use_behavior=should_stop,
)
```

When `is_final_output=True`, the tool outputs become the final result (no LLM processing). When `False`, they go back to the LLM for further processing — identical to `"run_llm_again"`.

**Note:** `ToolsToFinalOutputFunction` receives `RunContextWrapper[TContext]` (the full run context) and `list[FunctionToolResult]` (tool results with `.output` and `.tool_name`), not `ToolContext` or `ToolCallOutputItem`.

---

## 8.10 Human-in-the-Loop: Durable Approval Patterns

Chapter 5 covered the `RunState` serialization mechanism. Here we focus on the **production patterns** for durable approvals:

```
┌──────────────────────────────────────────────────────────────────┐
│  HITL Production Flow                                            │
│                                                                  │
│  1. Runner.run() → result with result.interruptions              │
│                                                                  │
│  2. result.to_state() → RunState                                 │
│                                                                  │
│  3. Serialize and persist:                                       │
│     ├─ state.to_string() → JSON string → database                │
│     ├─ state.to_json()   → dict → database                      │
│     └─ Include tracing API key if resuming in another process    │
│                                                                  │
│  4. (Hours/days later...)                                        │
│                                                                  │
│  5. Deserialize:                                                  │
│     ├─ RunState.from_string(agent, json_str)                     │
│     └─ RunState.from_json(agent, json_dict)                      │
│                                                                  │
│  6. state.approve(item) or state.reject(item, rejection_message) │
│                                                                  │
│  7. Runner.run(agent, state) → resumed execution                 │
└──────────────────────────────────────────────────────────────────┘
```

### Serialization Options for `RunState`

| Option | Method | Purpose |
|---|---|---|
| `context_serializer` | `to_json()` / `from_json()` | Serialize non-mapping context objects |
| `context_deserializer` | `from_json()` / `from_string()` | Rebuild context objects on load |
| `strict_context=True` | Both | Fail unless context is a mapping or serializer provided |
| `context_override` | `from_json()` / `from_string()` | Replace context when loading (don't restore original) |
| `include_tracing_api_key=True` | `to_json()` / `to_string()` | Keep trace export working after resume |

### Sticky Decisions

```python
state.approve(item, always_approve=True)
state.reject(item, always_reject=True)
```

**Sticky decisions persist for the rest of the run.** They survive serialization/deserialization, so if you approve `cancel_order` with `always_approve=True`, the LLM can call it again without pausing. Use this for tools that need one-time approval per session.

### Versioning Pending Tasks

If approvals may sit for a while (hours or days), the agent definition or SDK version may have changed. Store a version marker alongside the serialized state:

```python
import json
from datetime import datetime

state_json = state.to_json()
state_json["_version"] = "2.1.0"
state_json["_agent_schema"] = "customer_service_v3"
state_json["_created_at"] = datetime.now().isoformat()

stored = json.dumps(state_json)

later_state_json = json.loads(stored)
version = later_state_json.pop("_version")
schema = later_state_json.pop("_agent_schema")

if version != CURRENT_VERSION:
    state = await RunState.from_json(current_agent, later_state_json)
else:
    state = await RunState.from_json(original_agent, later_state_json)
```

---

## 8.11 Observability: Tracing, Hooks, and Usage Monitoring

Production agents need three layers of observability:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Tracing (request-level)                           │
│  • Trace → Span → SpanData hierarchy                        │
│  • See every LLM call, tool invocation, handoff             │
│  • Export to OpenAI dashboard or custom processor            │
│  → Covered in Ch7 §7.9-7.11                                │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Hooks (event-level)                               │
│  • RunHooks / AgentHooks fire at lifecycle moments           │
│  • Log agent starts/ends, tool calls, handoffs              │
│  → Covered in Ch7 §7.12                                    │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Usage (token-level)                               │
│  • Per-request token counts                                 │
│  • Cumulative totals across the run                         │
│  • Cached tokens, reasoning tokens                          │
│  → This section                                             │
└─────────────────────────────────────────────────────────────┘
```

### Usage Monitoring Example

```python
from agents import Agent, Runner, RunContextWrapper
from agents import RunHooks

class UsageMonitor(RunHooks):
    async def on_agent_end(self, context, agent, output):
        u = context.usage
        cached = u.input_tokens_details.cached_tokens
        reasoning = u.output_tokens_details.reasoning_tokens
        print(
            f"[{agent.name}] "
            f"{u.requests} requests, "
            f"{u.input_tokens} in ({cached} cached), "
            f"{u.output_tokens} out ({reasoning} reasoning), "
            f"{u.total_tokens} total"
        )
        for i, entry in enumerate(u.request_usage_entries):
            print(
                f"  Request {i+1}: "
                f"{entry.input_tokens} in, {entry.output_tokens} out"
            )

result = await Runner.run(
    agent,
    "Analyze the quarterly report",
    hooks=UsageMonitor(),
)
```

### Token Budget Enforcement with Hooks

```python
MAX_TOKENS_PER_RUN = 50_000

class TokenBudgetGuard(RunHooks):
    async def on_llm_end(self, context, agent, response):
        if context.usage.total_tokens > MAX_TOKENS_PER_RUN:
            raise MaxTurnsExceeded(
                f"Token budget exceeded: {context.usage.total_tokens} > {MAX_TOKENS_PER_RUN}"
            )
```

---

## 8.12 Production Checklist

Organized by deployment phase:

### Pre-Deployment

- [ ] Set `max_turns` explicitly (never rely on default 10)
- [ ] Add `RunErrorHandlers` for `MaxTurnsExceeded`
- [ ] Configure `failure_error_function` on every tool that calls external APIs
- [ ] Set `ModelRetrySettings` with `policy` for transient API failures
- [ ] Add `input_guardrails` for user input validation
- [ ] Add `output_guardrails` for output safety checks
- [ ] Set `tool_use_behavior` if any tools should terminate the run
- [ ] Verify `reset_tool_choice=True` (default, but confirm)
- [ ] Set `workflow_name` in `RunConfig` for trace identification
- [ ] Configure `trace_include_sensitive_data` appropriately

### Runtime Safety

- [ ] Set `needs_approval=True` on destructive/sensitive tools
- [ ] Implement HITL flow with `RunState` serialization for long-running approvals
- [ ] Add `call_model_input_filter` for token budget enforcement
- [ ] Use `handoff_input_filter=remove_all_tools` to prevent tool leakage across agents
- [ ] Add `tool_error_formatter` for custom approval rejection messages
- [ ] Set `reasoning_item_id_policy="omit"` if reasoning items cause token bloat

### Observability

- [ ] Enable tracing (default, but confirm `tracing_disabled=False`)
- [ ] Add `RunHooks` for agent-level logging
- [ ] Monitor `result.context_wrapper.usage` for cost tracking
- [ ] Set `group_id` in `RunConfig` to link traces from same conversation
- [ ] Add `trace_metadata` for custom searchable fields

### Testing

- [ ] Write unit tests for every `function_tool` (pure functions, mock external APIs)
- [ ] Write guardrail tests (verify tripwire triggers on bad input/output)
- [ ] Write integration tests for multi-agent flows (handoffs, agents-as-tools)
- [ ] Test `MaxTurnsExceeded` recovery (verify handler output is valid)
- [ ] Test HITL serialization round-trip (`to_json` → `from_json` → `approve` → resume)
- [ ] Test retry policy with simulated failures
- [ ] Test `tool_use_behavior` modes (verify stop conditions work)

### Versioning & Deployment

- [ ] Version your agent definitions (factory functions with version in name)
- [ ] Store SDK version alongside serialized `RunState`
- [ ] Use feature flags for agent version rollouts
- [ ] Plan for `Agent` schema changes (add fields with defaults)
- [ ] Set `context_serializer`/`context_deserializer` for non-mapping context objects

---

## 8.13 Putting It Together: A Production Support System

This example combines error handling, retry, HITL, guardrails, and orchestration:

```python
import asyncio
from dataclasses import dataclass
from typing import Literal

from agents import (
    Agent, Runner, RunConfig, RunContextWrapper, ModelSettings,
    function_tool, input_guardrail, output_guardrail,
    GuardrailFunctionOutput, RunHooks,
)
from agents.exceptions import InputGuardrailTripwireTriggered
from agents.retry import (
    ModelRetrySettings, ModelRetryBackoffSettings, retry_policies,
)
from agents.run_error_handlers import (
    RunErrorHandlers, RunErrorHandlerInput, RunErrorHandlerResult,
)
from agents.extensions.handoff_filters import remove_all_tools
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

# ── Context ──────────────────────────────────────────────

@dataclass
class SupportContext:
    user_id: str
    is_premium: bool
    session_id: str

# ── Tools ────────────────────────────────────────────────

async def db_error_handler(ctx, error) -> str:
    if "connection" in str(error).lower():
        return "Database temporarily unavailable. Please retry."
    return f"Error: {error}"

@function_tool(failure_error_function=db_error_handler)
async def lookup_order(order_id: str) -> str:
    return f"Order {order_id}: shipped, arrives tomorrow"

@function_tool(needs_approval=True)
async def cancel_order(order_id: str) -> str:
    return f"Order {order_id} cancelled"

@function_tool
async def escalate_to_human(reason: str) -> str:
    return "Escalated. A human agent will follow up within 1 hour."

# ── Guardrails ───────────────────────────────────────────

@input_guardrail
async def no_profanity(ctx, agent, input_data) -> GuardrailFunctionOutput:
    text = str(input_data).lower()
    bad_words = {"spam", "hack", "exploit"}
    found = any(word in text for word in bad_words)
    return GuardrailFunctionOutput(
        tripwire_triggered=found,
        output_info={"reason": "Profanity detected"} if found else None,
    )

# ── Error Handlers ───────────────────────────────────────

async def handle_max_turns(handler_input: RunErrorHandlerInput[SupportContext]) -> RunErrorHandlerResult:
    return RunErrorHandlerResult(
        final_output="I need more time to resolve this. Please rephrase your request and try again.",
        include_in_history=True,
    )

# ── Hooks ────────────────────────────────────────────────

class SupportHooks(RunHooks[SupportContext]):
    async def on_agent_end(self, context, agent, output):
        u = context.usage
        ctx = context.context
        print(
            f"[{ctx.session_id}] {agent.name}: "
            f"{u.total_tokens} tokens, {u.requests} requests"
        )

# ── Agents ───────────────────────────────────────────────

billing_agent = Agent[SupportContext](
    name="Billing",
    instructions=prompt_with_handoff_instructions("Handle billing questions. Use lookup_order and cancel_order."),
    tools=[lookup_order, cancel_order],
)

tech_agent = Agent[SupportContext](
    name="Tech Support",
    instructions=prompt_with_handoff_instructions("Handle technical issues. Use escalate_to_human for complex problems."),
    tools=[escalate_to_human],
)

triage = Agent[SupportContext](
    name="Triage",
    instructions="Route to billing or tech support. For anything else, respond directly.",
    handoffs=[billing_agent, tech_agent],
    input_guardrails=[no_profanity],
)

# ── Run Configuration ───────────────────────────────────

config = RunConfig(
    max_turns=15,
    handoff_input_filter=remove_all_tools,
    workflow_name="Customer Support",
    model_settings=ModelSettings(
        retry_settings=ModelRetrySettings(
            max_retries=3,
            backoff=ModelRetryBackoffSettings(initial_delay=1.0, max_delay=10.0),
            policy=retry_policies.any(
                retry_policies.provider_suggested(),
                retry_policies.network_error(),
            ),
        ),
    ),
    error_handlers=RunErrorHandlers(max_turns=handle_max_turns),
)

# ── Run ──────────────────────────────────────────────────

async def handle_request(user_input: str, user_id: str, is_premium: bool):
    ctx = SupportContext(user_id=user_id, is_premium=is_premium, session_id=f"sess-{user_id}")

    try:
        result = await Runner.run(
            triage,
            user_input,
            context=ctx,
            run_config=config,
            hooks=SupportHooks(),
        )
        return result.final_output

    except InputGuardrailTripwireTriggered as e:
        guardrail_name = e.guardrail_result.guardrail.get_name()
        return f"Request rejected by {guardrail_name}. Please rephrase."

    except Exception as e:
        return f"An unexpected error occurred. Reference: {ctx.session_id}"
```

### Post-Run Analysis: Four Scenarios

**Scenario 1: Normal billing query** — `"What's the status of order ORD-123?"`

```
Triage → handoff to Billing → lookup_order("ORD-123") → "Order shipped, arrives tomorrow"
→ LLM formats response → final_output

result.last_agent.name = "Billing"
result.context_wrapper.usage.requests = 2    (triage + billing)
result.context_wrapper.usage.total_tokens ≈ 1500
result.new_items: [HandoffOutputItem, ToolCallOutputItem, MessageOutputItem]
```

**Scenario 2: Cancellation requiring approval** — `"Cancel order ORD-456"`

```
Triage → handoff to Billing → cancel_order("ORD-456")
→ needs_approval=True → result.interruptions = [ToolApprovalItem]

result.interruptions[0].tool_name = "cancel_order"
result.interruptions[0].agent.name = "Billing"
result.interruptions[0].arguments (contains order_id)

state = result.to_state()
state.approve(result.interruptions[0])
result = await Runner.run(triage, state, context=ctx, run_config=config)
```

**Scenario 3: Profanity detected** — `"How do I hack your system"`

```
InputGuardrailTripwireTriggered raised
→ e.guardrail_result.guardrail.get_name() = "no_profanity"
→ e.guardrail_result.output.output_info = {"reason": "Profanity detected"}

Never reaches the LLM. Zero tokens consumed.
```

**Scenario 4: Max turns reached** — Complex multi-step request

```
After 15 turns, MaxTurnsExceeded raised
→ handle_max_turns fires
→ Returns RunErrorHandlerResult(final_output="I need more time...")
→ result.final_output = "I need more time to resolve this..."

result.context_wrapper.usage.requests ≈ 15
result.context_wrapper.usage.total_tokens could be 30,000+
```

---

## 8.14 Key Takeaways

1. **Error handling has four layers** — tool-level, run-level, exception-level, infrastructure-level. Know which layer handles which error.

2. **`RunErrorHandlers` recovers from `MaxTurnsExceeded`** — Return a `RunErrorHandlerResult` with partial output instead of crashing. Remember structured output validation applies.

3. **Tool errors are recoverable by default** — The SDK sends error messages back to the LLM. Customize with `failure_error_function` (per-tool) or `tool_error_formatter` (run-wide for approvals). Set to `None` to fail fast.

4. **Retry requires a policy** — Setting `max_retries` alone does nothing. Combine it with a `policy` from `retry_policies` or a custom function. Use `retry_policies.any()` to compose multiple conditions.

5. **`reset_tool_choice=True` prevents infinite tool loops** — It's the default for good reason. Only set to `False` if you explicitly want forced tool use across multiple turns.

6. **Three orchestration patterns** — Agents-as-tools (manager retains control), handoffs (specialist takes over), code orchestration (you control flow). Combine them freely.

7. **HITL approvals are durable** — `RunState` survives serialization. Use `always_approve`/`always_reject` for sticky decisions. Version your state alongside your agents.

8. **Observability is three layers** — Tracing (request-level), Hooks (event-level), Usage (token-level). Combine all three for full production visibility.
