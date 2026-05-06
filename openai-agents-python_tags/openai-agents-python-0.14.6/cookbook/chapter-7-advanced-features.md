# Chapter 7: Advanced Features — Handoffs, Guardrails, Tracing & Hooks

You've seen agents run solo. But production systems need **delegation** (handoffs), **safety** (guardrails), **observability** (tracing), and **lifecycle control** (hooks). This chapter dives deep into all four — with real source code walkthroughs, flow diagrams, and practical examples you can run.

## How to Read This Chapter

**Pass 1 — Build intuition (~25 min):** Read 7.1 → 7.2 → 7.4 → 7.6 → 7.8 → 7.10 in order. Skip 🔥 source code walkthroughs and deep subsections. Focus on flow diagrams, comparison tables, and the "day one" tier in each section.

**Pass 2 — Dive into source code (~50 min):** Read the five 🔥 walkthroughs: 7.3 (Handoff `__init__.py`), 7.5 (Input/Output guardrail execution), 7.7 (Tool guardrails), 7.9 (Tracing processor interface), 7.11 (RunHooks vs AgentHooks). By now you have the mental models, so the code reads naturally.

**Pass 3 — Fill gaps:** Read selectively:
- Handoff input filters and `HandoffInputData` fields? → 7.3 (HandoffInputData deep dive, input_filter walkthrough)
- `nest_handoff_history` and conversation summarization? → 7.3 (Nested History subsection)
- `handoff_prompt` extension? → 7.3 (Recommended Prompt Prefix subsection)
- Guardrail execution modes (parallel vs blocking)? → 7.5 (run_in_parallel comparison)
- Guardrail exception hierarchy and catching? → 7.5 (Exception Tree + catch example)
- Tool guardrail three-way behavior (allow/reject/raise)? → 7.7 (ToolGuardrailFunctionOutput deep dive)
- Complete guardrail pipeline order? → 7.8 (full pipeline diagram)
- Tracing: Trace, Span, SpanData types? → 7.9 (Trace/Span architecture)
- Custom TracingProcessor? → 7.9 (🔥 processor interface walkthrough)
- Hook event map and context types? → 7.11 (RunHooks vs AgentHooks comparison table)
- Multi-agent handoff example with post-run analysis? → 7.12

---

## 7.1 Handoffs: The Big Picture

Handoffs let one agent delegate to another. The LLM doesn't "call a function" — it calls a **tool** that the SDK registers on its behalf. That tool is named `transfer_to_<agent_name>`.

```
User: "I need a refund for order #1234"
        │
        ▼
┌─── Triage Agent ──────────────────────────┐
│  LLM sees tools:                          │
│    • transfer_to_billing_agent             │
│    • transfer_to_refund_agent    ◄── picks │
│    • transfer_to_faq_agent                 │
│  LLM calls: transfer_to_refund_agent()    │
└────────────────────────────────────────────┘
        │
        ▼  SDK intercepts the tool call
┌─── Refund Agent ──────────────────────────┐
│  Receives conversation history            │
│  Processes the refund request             │
│  Returns final output                     │
└────────────────────────────────────────────┘
```

### Day One: Basic Handoff

```python
from agents import Agent, Runner

refund_agent = Agent(
    name="Refund Agent",
    instructions="You process refund requests.",
    handoff_description="Use for refund-related questions"
)

faq_agent = Agent(
    name="FAQ Agent",
    instructions="You answer general questions.",
    handoff_description="Use for general questions"
)

triage_agent = Agent(
    name="Triage Agent",
    instructions="Route to the right agent.",
    handoffs=[refund_agent, faq_agent]
)

result = await Runner.run(triage_agent, "I need a refund for order #1234")
print(result.final_output)
print(result.last_agent.name)
```

When you pass an `Agent` directly in `handoffs=[...]`, the SDK wraps it in a `Handoff` object automatically with default tool name `transfer_to_refund_agent` and description from `handoff_description`.

### As It Grows: Custom Handoff with `handoff()`

```python
from agents import Agent, handoff, RunContextWrapper

refund_agent = Agent(name="Refund Agent", instructions="Process refunds.")

async def on_handoff(ctx: RunContextWrapper[None]):
    print("Refund agent has been activated!")

refund_handoff = handoff(
    agent=refund_agent,
    on_handoff=on_handoff,
    tool_name_override="escalate_refund",
    tool_description_override="Escalate to the refund team for order issues"
)

triage_agent = Agent(
    name="Triage",
    instructions="Route questions.",
    handoffs=[refund_handoff]
)
```

### Production: Handoff with Structured Input

```python
from pydantic import BaseModel
from agents import Agent, handoff, RunContextWrapper

class EscalationData(BaseModel):
    reason: str
    urgency: str

async def on_handoff_with_input(ctx: RunContextWrapper[None], input_data: EscalationData):
    print(f"Escalation reason: {input_data.reason}, urgency: {input_data.urgency}")

escalation_handoff = handoff(
    agent=Agent(name="Escalation Agent", instructions="Handle escalated cases."),
    on_handoff=on_handoff_with_input,
    input_type=EscalationData,
)

manager = Agent(name="Manager", instructions="Manage requests.", handoffs=[escalation_handoff])
```

When `input_type` is set, the LLM generates JSON arguments that are validated against the Pydantic model and passed to `on_handoff`. **You must provide both `on_handoff` and `input_type` together, or neither.**

---

## 7.2 Handoff Flow: What Happens Inside the Runner

Before diving into source code, let's see the full lifecycle:

```
┌─ Turn N: Agent A is running ─────────────────────────────┐
│                                                          │
│  1. LLM produces a function_call with name               │
│     "transfer_to_agent_b" + arguments                    │
│                                                          │
│  2. process_model_response() classifies it:               │
│     → ToolRunHandoff(handoff, tool_call)                 │
│                                                          │
│  3. execute_handoffs() is called:                        │
│     a. Call handoff.on_invoke_handoff(ctx, args_json)    │
│        → returns the target Agent object                 │
│     b. Create HandoffOutputItem (source → target)        │
│     c. Fire hooks.on_handoff() and agent.hooks.on_handoff│
│     d. Apply input_filter if configured                  │
│     e. OR apply nest_handoff_history if configured       │
│                                                          │
│  4. Return SingleStepResult with:                        │
│     next_step = NextStepHandoff(new_agent)               │
│                                                          │
└──────────────────────────────────────────────────────────┘
        │
        ▼
┌─ Turn N+1: Agent B is running ───────────────────────────┐
│                                                          │
│  5. Agent B receives the (possibly filtered) input       │
│  6. Agent B runs normally, may produce final output      │
│     OR hand off to yet another agent                     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Key insight:** A handoff doesn't "return" to the original agent. Control transfers permanently. The new agent becomes `result.last_agent` and may itself hand off further, creating a chain.

---

## 7.3 🔥 Handoff Source Code Walkthrough

Let's read the actual `Handoff` dataclass from `src/agents/handoffs/__init__.py`:

```python
@dataclass
class Handoff(Generic[TContext, TAgent]):
    tool_name: str
    tool_description: str
    input_json_schema: dict[str, Any]
    on_invoke_handoff: Callable[[RunContextWrapper[Any], str], Awaitable[TAgent]]
    agent_name: str
    input_filter: HandoffInputFilter | None = None
    nest_handoff_history: bool | None = None
    strict_json_schema: bool = True
    is_enabled: bool | Callable[[RunContextWrapper[Any], AgentBase[Any]], MaybeAwaitable[bool]] = True
    _agent_ref: weakref.ReferenceType[AgentBase[Any]] | None = field(default=None, init=False, repr=False)
```

### Field-by-Field Deep Dive

| Field | Type | Purpose | Default |
|---|---|---|---|
| `tool_name` | `str` | The function name the LLM calls. Usually `transfer_to_<name>`. | Auto-generated |
| `tool_description` | `str` | Helps the LLM decide *when* to hand off. | Auto-generated from `handoff_description` |
| `input_json_schema` | `dict` | JSON Schema for handoff arguments. Empty `{}` if no `input_type`. | `{}` |
| `on_invoke_handoff` | `Callable` | **The core function.** Called by the Runner when the LLM invokes the handoff. Must return an `Agent`. | Created by `handoff()` |
| `agent_name` | `str` | Name of the target agent, used in tracing and `get_transfer_message()`. | From `agent.name` |
| `input_filter` | `HandoffInputFilter \| None` | Filters what the next agent sees. See §7.3.2. | `None` |
| `nest_handoff_history` | `bool \| None` | Per-handoff override for `RunConfig.nest_handoff_history`. | `None` (use RunConfig) |
| `strict_json_schema` | `bool` | Whether to enforce strict JSON Schema mode. **Always True** — the `handoff()` helper enforces this via `ensure_strict_json_schema()`. | `True` |
| `is_enabled` | `bool \| Callable` | Dynamic enable/disable. Disabled handoffs are **hidden from the LLM**. | `True` |
| `_agent_ref` | `weakref` | Weak reference to target agent. Prevents circular references in multi-agent graphs. | `None` |

**Key insights:**

1. **A Handoff IS a tool.** The LLM doesn't know about "handoffs" — it just sees a function called `transfer_to_refund_agent` with a description. The SDK intercepts the call and swaps the agent.

2. **`on_invoke_handoff` always returns the same agent** when created via `handoff()`. The `on_handoff` callback is for side effects only — logging, state changes, notifications. Dynamic destination selection should be done by registering multiple handoffs and letting the model choose.

3. **`_agent_ref` uses `weakref.ref()`** to avoid keeping agents alive in memory just because they appear in a handoff list. This matters in long-running processes with many agent definitions.

4. **`is_enabled` can be a callable** that receives `(RunContextWrapper, AgentBase)` and returns `bool`. This lets you disable handoffs dynamically based on user permissions, time of day, or feature flags — the LLM simply won't see the tool.

### HandoffInputData Deep Dive

When `input_filter` or `nest_handoff_history` is used, the SDK constructs a `HandoffInputData`:

```python
@dataclass(frozen=True)
class HandoffInputData:
    input_history: str | tuple[TResponseInputItem, ...]
    pre_handoff_items: tuple[RunItem, ...]
    new_items: tuple[RunItem, ...]
    run_context: RunContextWrapper[Any] | None = None
    input_items: tuple[RunItem, ...] | None = None
```

| Field | What it contains | Why it matters |
|---|---|---|
| `input_history` | The original `input` passed to `Runner.run()` — either a string or the full message list | The new agent needs the conversation start |
| `pre_handoff_items` | All `RunItem`s from *before* the current turn (previous turns' tool calls, messages, etc.) | Gives context of what happened earlier |
| `new_items` | Items from the *current turn*, including the `HandoffCallItem` and `HandoffOutputItem` | Shows what triggered the handoff |
| `run_context` | The active `RunContextWrapper` at handoff time | Access to user context, usage stats, approvals |
| `input_items` | **Override for model input.** When set, these items go to the next agent instead of `new_items`. `new_items` stays intact for session history. | Decouples "what the next agent sees" from "what gets saved" |

**The `input_items` field is critical for advanced filtering:** suppose you want the next agent to see a cleaned-up version of the conversation, but you still want the full history saved to the session. Set `input_items` to the filtered list and leave `new_items` untouched.

### The `handoff()` Helper Function

The `handoff()` function is the public API for creating `Handoff` objects. Here's the simplified flow:

```python
def handoff(
    agent: Agent[TContext],
    tool_name_override: str | None = None,
    tool_description_override: str | None = None,
    on_handoff: OnHandoffWithInput | OnHandoffWithoutInput | None = None,
    input_type: type[THandoffInput] | None = None,
    input_filter: HandoffInputFilter | None = None,
    nest_handoff_history: bool | None = None,
    is_enabled: bool | Callable = True,
) -> Handoff[TContext, Agent[TContext]]:
```

🔥 **Source Code Walkthrough: `handoff()` internal logic**

```python
async def _invoke_handoff(
    ctx: RunContextWrapper[Any], input_json: str | None = None
) -> Agent[TContext]:
    if input_type is not None and type_adapter is not None:
        validated_input = _json.validate_json(
            json_str=input_json,
            type_adapter=type_adapter,
            partial=False,
        )
        input_func = cast(OnHandoffWithInput[THandoffInput], on_handoff)
        if inspect.iscoroutinefunction(input_func):
            await input_func(ctx, validated_input)
        else:
            input_func(ctx, validated_input)
    elif on_handoff is not None:
        no_input_func = cast(OnHandoffWithoutInput, on_handoff)
        if inspect.iscoroutinefunction(no_input_func):
            await no_input_func(ctx)
        else:
            no_input_func(ctx)

    return agent
```

Key insights from this code:

1. **The function always returns `agent`** — the same agent passed to `handoff()`. The `on_handoff` callback runs for side effects only.
2. **`_json.validate_json()`** validates the LLM's JSON arguments against the `input_type` Pydantic model. If validation fails, a `ModelBehaviorError` is raised.
3. **Both sync and async `on_handoff` callbacks are supported.** The SDK checks `inspect.iscoroutinefunction()` and awaits if needed.
4. **`input_json` can be `None`** — if the LLM calls the handoff tool without arguments (no `input_type` was set), the JSON is empty.

### Built-in Input Filters: `remove_all_tools`

The SDK provides `remove_all_tools` in `agents.extensions.handoff_filters`:

```python
from agents import Agent, handoff
from agents.extensions.handoff_filters import remove_all_tools

billing_agent = Agent(name="Billing", instructions="Handle billing.")
triage_agent = Agent(
    name="Triage",
    instructions="Route requests.",
    handoffs=[
        handoff(billing_agent, input_filter=remove_all_tools)
    ]
)
```

This filter strips all `ToolCallItem`, `ToolCallOutputItem`, `HandoffCallItem`, `HandoffOutputItem`, `ReasoningItem`, and MCP-related items from the conversation history. The next agent sees a clean conversation without tool artifacts from previous agents.

### Nested Handoff History

When `nest_handoff_history=True` (set either in `RunConfig` or per-handoff), the SDK summarizes the previous conversation into a single assistant message before handing off. This reduces token usage and gives the new agent a concise summary instead of the full raw transcript.

```
Without nesting (default):
  Agent B sees: [user_msg, assistant_msg, tool_call, tool_output, handoff_call, handoff_output]

With nesting:
  Agent B sees: [assistant_msg("For context, here is the conversation so far:
    <CONVERSATION HISTORY>
    1. user: I need a refund
    2. assistant: Let me transfer you to the refund agent
    </CONVERSATION HISTORY>")]
```

The markers `<CONVERSATION HISTORY>` and `</CONVERSATION HISTORY>` are customizable via `set_conversation_history_wrappers()`.

### Recommended Prompt Prefix

The `handoff_prompt` extension provides a recommended system prompt prefix for agents that use handoffs:

```python
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

triage_agent = Agent(
    name="Triage",
    instructions=prompt_with_handoff_instructions("You route customer questions to the right agent."),
    handoffs=[billing_agent, refund_agent]
)
```

The prefix tells the LLM: "You are part of a multi-agent system. Transfers are handled seamlessly — don't mention or draw attention to these transfers." This prevents the model from saying things like "I'm now transferring you to another agent."

---

## 7.4 Guardrails: The Big Picture

Guardrails are safety checks that run at key boundaries in an agent's execution. The SDK provides four types:

```
┌──────────────────────────────────────────────────────────┐
│                    Agent Execution Flow                   │
│                                                          │
│  User Input ──→ [Input Guardrails] ──→ LLM Call          │
│                                          │               │
│                                     Tool Call?           │
│                                       ├── Yes ──→ [Tool Input Guardrails] → Execute Tool → [Tool Output Guardrails]
│                                       └── No ──→ Final Output                          │
│                                                    │     │
│                              [Output Guardrails] ◄─┘     │
│                                                    │     │
│                                              Return to   │
│                                               User       │
└──────────────────────────────────────────────────────────┘
```

### Workflow Boundary Rules

| Guardrail Type | When it Runs | Where Configured | Scope |
|---|---|---|---|
| Input guardrails | On initial user input, **first agent only** | `Agent.input_guardrails` or `RunConfig.input_guardrails` | Entire run |
| Output guardrails | On final output, **last agent only** | `Agent.output_guardrails` or `RunConfig.output_guardrails` | Entire run |
| Tool input guardrails | Before each function tool executes | `FunctionTool.input_guardrails` | Per tool call |
| Tool output guardrails | After each function tool executes | `FunctionTool.output_guardrails` | Per tool call |

**Critical rule:** Input guardrails only fire for the *first* agent in a handoff chain. Output guardrails only fire for the *last* agent. If you need checks around every tool call in a multi-agent workflow, use **tool guardrails** instead.

---

## 7.5 🔥 Input & Output Guardrails Source Code

### `GuardrailFunctionOutput`

```python
@dataclass
class GuardrailFunctionOutput:
    output_info: Any
    tripwire_triggered: bool
```

| Field | Type | Purpose |
|---|---|---|
| `output_info` | `Any` | Arbitrary metadata about what the guardrail checked (e.g., classification scores, flagged patterns). Not used by the SDK — for your logging. |
| `tripwire_triggered` | `bool` | **The only field the SDK cares about.** If `True`, execution halts immediately. |

### `InputGuardrail` Dataclass

```python
@dataclass
class InputGuardrail(Generic[TContext]):
    guardrail_function: Callable[
        [RunContextWrapper[TContext], Agent[Any], str | list[TResponseInputItem]],
        MaybeAwaitable[GuardrailFunctionOutput],
    ]
    name: str | None = None
    run_in_parallel: bool = True
```

| Field | Type | Purpose | Default |
|---|---|---|---|
| `guardrail_function` | `Callable` | Your check function. Receives `(context, agent, input)`. | Required |
| `name` | `str \| None` | Name for tracing. Falls back to function's `__name__`. | `None` |
| `run_in_parallel` | `bool` | `True` = run concurrently with the agent (lower latency but may waste tokens). `False` = run before the agent starts (saves tokens if tripwire triggers). | `True` |

### Input Guardrail Execution Modes

| Mode | `run_in_parallel` | Timing | Token cost | Use when |
|---|---|---|---|---|
| **Parallel** (default) | `True` | Guardrail + agent start simultaneously | May waste tokens if tripwire triggers | Latency matters, false positives are rare |
| **Blocking** | `False` | Guardrail completes before agent starts | Zero wasted tokens if tripwire triggers | Cost matters, guardrail is fast, high tripwire rate |

### The `@input_guardrail` Decorator

```python
from agents import Agent, input_guardrail, GuardrailFunctionOutput, Runner

@input_guardrail
async def check_homework(ctx, agent, input_data):
    prompt = input_data if isinstance(input_data, str) else str(input_data)
    result = await Runner.run(classifier_agent, prompt)
    if result.final_output.is_homework:
        return GuardrailFunctionOutput(
            output_info={"reason": "Homework detected"},
            tripwire_triggered=True
        )
    return GuardrailFunctionOutput(
        output_info={"reason": "OK"},
        tripwire_triggered=False
    )

agent = Agent(
    name="Assistant",
    instructions="Be helpful.",
    input_guardrails=[check_homework]
)
```

You can also use the decorator with arguments:

```python
@input_guardrail(name="homework_check", run_in_parallel=False)
async def check_homework(ctx, agent, input_data):
    ...
```

### `OutputGuardrail` Dataclass

```python
@dataclass
class OutputGuardrail(Generic[TContext]):
    guardrail_function: Callable[
        [RunContextWrapper[TContext], Agent[Any], Any],
        MaybeAwaitable[GuardrailFunctionOutput],
    ]
    name: str | None = None
```

Note: `OutputGuardrail` has **no `run_in_parallel`** option. It always runs after the agent finishes.

### `InputGuardrailResult` and `OutputGuardrailResult`

When a guardrail runs, the SDK wraps the output in a result object:

```python
@dataclass
class InputGuardrailResult:
    guardrail: InputGuardrail[Any]
    output: GuardrailFunctionOutput

@dataclass
class OutputGuardrailResult:
    guardrail: OutputGuardrail[Any]
    agent_output: Any
    agent: Agent[Any]
    output: GuardrailFunctionOutput
```

| Field | In `Input` | In `Output` | Purpose |
|---|---|---|---|
| `guardrail` | ✅ | ✅ | Reference to the guardrail that ran — call `.get_name()` for the name |
| `output` | ✅ | ✅ | The `GuardrailFunctionOutput` with `tripwire_triggered` and `output_info` |
| `agent_output` | — | ✅ | The raw agent output that was checked |
| `agent` | — | ✅ | The agent that produced the output |

These result objects are stored in `RunResult.input_guardrail_results` and `RunResult.output_guardrail_results` after a run completes, and are also attached to the exceptions when a tripwire triggers.

### Guardrail Exception Hierarchy

```
AgentsException
├── InputGuardrailTripwireTriggered
│   └── guardrail_result: InputGuardrailResult
├── OutputGuardrailTripwireTriggered
│   └── guardrail_result: OutputGuardrailResult
├── ToolInputGuardrailTripwireTriggered
│   ├── guardrail: ToolInputGuardrail
│   └── output: ToolGuardrailFunctionOutput
└── ToolOutputGuardrailTripwireTriggered
    ├── guardrail: ToolOutputGuardrail
    └── output: ToolGuardrailFunctionOutput
```

### Catching Guardrail Exceptions

```python
from agents import Agent, Runner, InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered

try:
    result = await Runner.run(agent, "Help me with my calculus homework")
except InputGuardrailTripwireTriggered as e:
    print(f"Input blocked by: {e.guardrail_result.guardrail.get_name()}")
    print(f"Reason: {e.guardrail_result.output.output_info}")
except OutputGuardrailTripwireTriggered as e:
    print(f"Output blocked by: {e.guardrail_result.guardrail.get_name()}")
    print(f"Agent that produced output: {e.guardrail_result.agent.name}")
```

Each exception carries the full `guardrail_result` (for agent guardrails) or `guardrail` + `output` (for tool guardrails), so you can inspect exactly what happened and respond accordingly.

---

## 7.6 Tool Guardrails: Three-Way Behavior

Tool guardrails are fundamentally different from agent guardrails. Instead of a simple tripwire, they support **three behaviors**:

```
┌─ Tool Call ──────────────────────────────────┐
│                                              │
│  [Tool Input Guardrails]                     │
│       │                                      │
│       ├── allow → Execute the tool           │
│       ├── reject_content → Skip execution,   │
│       │     send message back to model       │
│       └── raise_exception → Halt with error  │
│                                              │
│  [Tool Executes] (if allowed)                │
│       │                                      │
│  [Tool Output Guardrails]                    │
│       │                                      │
│       ├── allow → Return output to model     │
│       ├── reject_content → Replace output    │
│       │     with message to model            │
│       └── raise_exception → Halt with error  │
│                                              │
└──────────────────────────────────────────────┘
```

### Behavior Comparison Table

| Behavior | Tool executes? | Model gets | Execution continues? | Exception raised? |
|---|---|---|---|---|
| `allow` | Yes (input) / N/A (output) | Normal tool output | Yes | No |
| `reject_content` | **No** (input) / Yes (output) | Custom rejection message | Yes | No |
| `raise_exception` | **No** (input) / N/A (output) | Nothing | **No** | `ToolInputGuardrailTripwireTriggered` / `ToolOutputGuardrailTripwireTriggered` |

**Key insight:** `reject_content` is the most interesting behavior — it lets the model *try again* with a different approach, while `raise_exception` kills the entire run. Use `reject_content` when you want the model to self-correct; use `raise_exception` for hard safety boundaries.

---

## 7.7 🔥 Tool Guardrails Source Code

### `ToolGuardrailFunctionOutput`

```python
@dataclass
class ToolGuardrailFunctionOutput:
    output_info: Any
    behavior: RejectContentBehavior | RaiseExceptionBehavior | AllowBehavior = field(
        default_factory=lambda: AllowBehavior(type="allow")
    )
```

The SDK provides convenience class methods:

```python
@classmethod
def allow(cls, output_info: Any = None) -> ToolGuardrailFunctionOutput:
    return cls(output_info=output_info, behavior=AllowBehavior(type="allow"))

@classmethod
def reject_content(cls, message: str, output_info: Any = None) -> ToolGuardrailFunctionOutput:
    return cls(
        output_info=output_info,
        behavior=RejectContentBehavior(type="reject_content", message=message),
    )

@classmethod
def raise_exception(cls, output_info: Any = None) -> ToolGuardrailFunctionOutput:
    return cls(output_info=output_info, behavior=RaiseExceptionBehavior(type="raise_exception"))
```

### `ToolInputGuardrailData` and `ToolOutputGuardrailData`

```python
@dataclass
class ToolInputGuardrailData:
    context: ToolContext[Any]
    agent: Agent[Any]

@dataclass
class ToolOutputGuardrailData(ToolInputGuardrailData):
    output: Any
```

Note that `ToolOutputGuardrailData` extends `ToolInputGuardrailData` by adding the `output` field. Your guardrail function can inspect both the `agent` and the `context` (which includes `tool_call_id`, `tool_name`, `tool_arguments`).

### Practical Example: Transfer Amount Guardrail

```python
from agents import tool_input_guardrail, ToolGuardrailFunctionOutput, ToolInputGuardrailData, function_tool

@tool_input_guardrail
async def check_transfer_amount(data: ToolInputGuardrailData) -> ToolGuardrailFunctionOutput:
    args = data.context.tool_arguments
    if data.context.tool_name == "transfer_money":
        amount = args.get("amount", 0)
        if amount > 10000:
            return ToolGuardrailFunctionOutput.reject_content(
                message=f"Transfer of ${amount} exceeds the $10,000 limit. Please use the escalation process for large transfers.",
                output_info={"amount": amount, "limit": 10000}
            )
    return ToolGuardrailFunctionOutput.allow()

@function_tool(input_guardrails=[check_transfer_amount])
async def transfer_money(recipient: str, amount: float) -> str:
    return f"Transferred ${amount} to {recipient}"
```

When the model tries to call `transfer_money(amount=15000)`, the guardrail intercepts it and returns the rejection message instead. The model sees: "Transfer of $15000 exceeds the $10,000 limit..." and can try a different approach.

### Output Tool Guardrail with `reject_content`

Output tool guardrails work the same way but run *after* the tool executes. Use `reject_content` to replace the tool's output with a safer message:

```python
from agents import tool_output_guardrail, ToolGuardrailFunctionOutput, ToolOutputGuardrailData, function_tool

@tool_output_guardrail
async def mask_sensitive_data(data: ToolOutputGuardrailData) -> ToolGuardrailFunctionOutput:
    import re
    output_str = str(data.output)
    if re.search(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", output_str):
        masked = re.sub(r"\b(\d{4})[- ]?\d{4}[- ]?\d{4}[- ]?(\d{4})\b", r"\1-****-****-\2", output_str)
        return ToolGuardrailFunctionOutput.reject_content(
            message=masked,
            output_info={"reason": "Credit card number detected and masked"}
        )
    return ToolGuardrailFunctionOutput.allow()

@function_tool(output_guardrails=[mask_sensitive_data])
async def lookup_order(order_id: str) -> str:
    return "Order 1234 paid with card 4111-1111-1111-1234"
```

The model sees `"Order 1234 paid with card 4111-****-****-1234"` instead of the raw card number.

---

## 7.8 The Complete Guardrail Pipeline

Let's trace the full guardrail execution order for a multi-agent run with handoffs:

```
Runner.run(triage_agent, "I need a refund")
        │
        ▼
┌─ Turn 1: Triage Agent ────────────────────────┐
│                                               │
│  1. Input Guardrails (triage_agent's only,    │
│     because it's the FIRST agent)             │
│     ├── check_homework (parallel)             │
│     └── check_pii (parallel)                  │
│                                               │
│  2. LLM Call → decides to hand off            │
│                                               │
│  3. NO output guardrails (not the last agent) │
│                                               │
└───────────────────────────────────────────────┘
        │ Handoff
        ▼
┌─ Turn 2: Refund Agent ────────────────────────┐
│                                               │
│  4. NO input guardrails (not the first agent) │
│                                               │
│  5. LLM Call → decides to call tool           │
│                                               │
│  6. Tool Input Guardrails (per tool)          │
│     └── check_transfer_amount                 │
│                                               │
│  7. Tool executes                             │
│                                               │
│  8. Tool Output Guardrails (per tool)         │
│     └── check_output_safety                   │
│                                               │
│  9. LLM Call → produces final output          │
│                                               │
│  10. Output Guardrails (refund_agent's only,  │
│      because it's the LAST agent)             │
│      └── no_pii_in_output                     │
│                                               │
└───────────────────────────────────────────────┘
```

**Important scope limitation:** Tool guardrails apply only to `function_tool` (created with `@function_tool`). They do NOT apply to handoffs, hosted tools (`WebSearchTool`, `FileSearchTool`, `HostedMCPTool`, `CodeInterpreterTool`, `ImageGenerationTool`), or built-in execution tools (`ComputerTool`, `ShellTool`, `ApplyPatchTool`, `LocalShellTool`). `Agent.as_tool()` also does not currently expose tool-guardrail options.

**Key insight from the source code:** In `run_input_guardrails()` (from `src/agents/run_internal/guardrails.py`), guardrails run **concurrently** via `asyncio.as_completed()`. As soon as one tripwire triggers, all remaining guardrail tasks are **cancelled** and an exception is raised. This is a fast-fail design.

---

## 7.9 Tracing: The Big Picture

Tracing records everything that happens during a run: LLM calls, tool executions, guardrails, handoffs, and custom events. It's **enabled by default**.

```
Trace: "Agent workflow" (trace_abc123...)
├── Span: agent (Triage Agent)
│   ├── Span: guardrail (check_homework) → triggered: false
│   ├── Span: generation (gpt-4o, 150 tokens)
│   └── Span: handoff (Triage Agent → Refund Agent)
├── Span: agent (Refund Agent)
│   ├── Span: generation (gpt-4o, 200 tokens)
│   ├── Span: function (transfer_money)
│   │   ├── Span: guardrail (check_transfer_amount) → triggered: false
│   │   └── input: {"recipient": "Alice", "amount": 50}
│   ├── Span: generation (gpt-4o, 100 tokens)
│   └── Span: guardrail (no_pii) → triggered: false
└── [Trace complete]
```

### Three Ways to Disable Tracing

| Method | Scope | When to use |
|---|---|---|
| `OPENAI_AGENTS_DISABLE_TRACING=1` env var | Global | Production environments with ZDR policies |
| `set_tracing_disabled(True)` | Global | Programmatically disable in code |
| `RunConfig(tracing_disabled=True)` | Per run | Specific runs that don't need tracing |

### Day One: Default Tracing

You don't need to do anything. Every `Runner.run()` call is automatically wrapped in a trace. View traces at [platform.openai.com/traces](https://platform.openai.com/traces).

```python
from agents import Runner

result = await Runner.run(agent, "Hello!")
```

### As It Grows: Custom Trace Configuration

```python
from agents import Runner, RunConfig

result = await Runner.run(
    agent,
    "Hello!",
    run_config=RunConfig(
        workflow_name="Customer Support",
        group_id="chat_thread_123",
        trace_metadata={"customer_id": "user-456"},
    )
)
```

| `RunConfig` field | Type | Purpose |
|---|---|---|
| `workflow_name` | `str` | Logical name for the trace. Defaults to "Agent workflow". |
| `trace_id` | `str \| None` | Custom trace ID. Must match `trace_<32_alphanumeric>`. |
| `group_id` | `str \| None` | Links multiple traces from the same conversation. |
| `trace_metadata` | `dict \| None` | Arbitrary key-value pairs attached to the trace. |
| `tracing_disabled` | `bool` | Disable tracing for this specific run. |
| `trace_include_sensitive_data` | `bool` | Whether to include tool inputs/outputs in spans. Defaults to `True` (can be overridden by env var). |

---

## 7.10 🔥 Tracing Architecture: Trace, Span, and SpanData

The tracing system has three layers:

```
┌─ Trace ─────────────────────────────────────────────┐
│  workflow_name: "Customer Support"                  │
│  trace_id: "trace_abc123..."                        │
│  group_id: "chat_456"                               │
│                                                     │
│  ┌─ Span (agent) ─────────────────────────────┐    │
│  │  span_id: "span_def456..."                 │    │
│  │  parent_id: None                           │    │
│  │  span_data: AgentSpanData                  │    │
│  │    name: "Triage Agent"                    │    │
│  │    handoffs: ["Refund Agent"]              │    │
│  │    tools: ["transfer_money"]               │    │
│  │                                            │    │
│  │  ┌─ Span (generation) ──────────────┐     │    │
│  │  │  parent_id: "span_def456..."     │     │    │
│  │  │  span_data: GenerationSpanData   │     │    │
│  │  │    model: "gpt-4o"               │     │    │
│  │  │    usage: {input: 50, output: 80}│     │    │
│  │  └──────────────────────────────────┘     │    │
│  │                                            │    │
│  │  ┌─ Span (function) ────────────────┐     │    │
│  │  │  parent_id: "span_def456..."     │     │    │
│  │  │  span_data: FunctionSpanData     │     │    │
│  │  │    name: "transfer_money"        │     │    │
│  │  │    input: '{"amount": 50}'       │     │    │
│  │  │    output: "Transferred $50"     │     │    │
│  │  └──────────────────────────────────┘     │    │
│  └────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### SpanData Type Reference

| SpanData Type | `type` field | Key fields | Created by |
|---|---|---|---|
| `AgentSpanData` | `"agent"` | `name`, `handoffs`, `tools`, `output_type` | `agent_span()` |
| `GenerationSpanData` | `"generation"` | `input`, `output`, `model`, `model_config`, `usage` | `generation_span()` |
| `FunctionSpanData` | `"function"` | `name`, `input`, `output`, `mcp_data` | `function_span()` |
| `HandoffSpanData` | `"handoff"` | `from_agent`, `to_agent` | `handoff_span()` |
| `GuardrailSpanData` | `"guardrail"` | `name`, `triggered` | `guardrail_span()` |
| `ResponseSpanData` | `"response"` | `response_id`, `usage` | `response_span()` |
| `CustomSpanData` | `"custom"` | `name`, `data` | `custom_span()` |
| `TaskSpanData` | `"task"` (exported as custom) | `name`, `usage` | `task_span()` |
| `TurnSpanData` | `"turn"` (exported as custom) | `turn`, `agent_name`, `usage` | `turn_span()` |
| `MCPListToolsSpanData` | `"mcp_tools"` | `server`, `result` | `mcp_tools_span()` |

### Custom Spans

You can add your own spans to trace arbitrary operations:

```python
from agents import tracing

with tracing.custom_span("database_query", data={"operation": "SELECT", "table": "orders"}) as span:
    results = await db.query("SELECT * FROM orders WHERE user_id = ?", user_id)
    span.span_data.data["row_count"] = len(results)
```

---

## 7.11 🔥 Custom Tracing Processors

The `TracingProcessor` interface lets you send traces anywhere — your own backend, OpenTelemetry, log files, etc.

🔥 **Source Code Walkthrough: `TracingProcessor` interface**

```python
class TracingProcessor(abc.ABC):
    @abc.abstractmethod
    def on_trace_start(self, trace: Trace) -> None:
        pass

    @abc.abstractmethod
    def on_trace_end(self, trace: Trace) -> None:
        pass

    @abc.abstractmethod
    def on_span_start(self, span: Span[Any]) -> None:
        pass

    @abc.abstractmethod
    def on_span_end(self, span: Span[Any]) -> None:
        pass

    @abc.abstractmethod
    def shutdown(self) -> None:
        pass

    @abc.abstractmethod
    def force_flush(self) -> None:
        pass
```

Key insights:

1. **`on_trace_start` / `on_trace_end`** bracket the entire run. Use `on_trace_end` to batch-export all spans at once.
2. **`on_span_start` / `on_span_end`** fire for each individual operation. Spans nest automatically via `parent_id`.
3. **`shutdown()`** is called when the process exits. Clean up connections, flush queues.
4. **`force_flush()`** is called explicitly when immediate export is needed (e.g., Celery workers, Lambda functions).
5. **All methods must be thread-safe and non-blocking.** The SDK calls them synchronously from the event loop.

### Practical Example: Logging Processor

```python
from agents import tracing

class LoggingProcessor(tracing.TracingProcessor):
    def __init__(self):
        self.spans_by_trace: dict[str, list] = {}

    def on_trace_start(self, trace: tracing.Trace) -> None:
        self.spans_by_trace[trace.trace_id] = []
        print(f"Trace started: {trace.name} ({trace.trace_id})")

    def on_trace_end(self, trace: tracing.Trace) -> None:
        spans = self.spans_by_trace.pop(trace.trace_id, [])
        print(f"Trace ended: {trace.name} with {len(spans)} spans")

    def on_span_start(self, span: tracing.Span) -> None:
        pass

    def on_span_end(self, span: tracing.Span) -> None:
        data = span.span_data
        if data.type == "function":
            print(f"  Tool: {data.name}, output: {data.output}")
        elif data.type == "generation":
            print(f"  LLM: {data.model}, tokens: {data.usage}")
        elif data.type == "handoff":
            print(f"  Handoff: {data.from_agent} → {data.to_agent}")
        elif data.type == "guardrail":
            print(f"  Guardrail: {data.name}, triggered: {data.triggered}")

        trace_id = span.trace_id
        if trace_id in self.spans_by_trace:
            self.spans_by_trace[trace_id].append(span)

    def shutdown(self) -> None:
        self.spans_by_trace.clear()

    def force_flush(self) -> None:
        pass

tracing.add_trace_processor(LoggingProcessor())
```

### Long-Running Workers: `flush_traces()`

The default `BatchTraceProcessor` exports traces in the background every few seconds. For long-running workers (Celery, RQ, FastAPI background tasks), call `flush_traces()` at the end of your task:

```python
from agents import Runner, flush_traces, trace

@celery_app.task
def run_agent_task(prompt: str):
    try:
        with trace("celery_task"):
            result = Runner.run_sync(agent, prompt)
        return result.final_output
    finally:
        flush_traces()
```

---

## 7.12 Hooks: Lifecycle Events

Hooks let you run custom code at key lifecycle points. The SDK provides two hook systems:

### RunHooks vs AgentHooks

| Aspect | `RunHooks` (set on `Runner.run(hooks=...)`) | `AgentHooks` (set on `Agent(hooks=...)`) |
|---|---|---|
| Scope | Entire run (all agents) | Specific agent only |
| Fires on | Every agent change, every tool, every LLM call | Only when THIS agent is active |
| Context type | `RunContextWrapper` for most, `AgentHookContext` for start/end | `AgentHookContext` for start/end, `RunContextWrapper` for tools/LLM |
| Use case | Cross-cutting concerns: logging, metrics, auth | Agent-specific behavior: custom initialization, per-agent logging |

### 🔥 Source Code Walkthrough: `RunHooksBase` and `AgentHooksBase`

```python
class RunHooksBase(Generic[TContext, TAgent]):
    async def on_llm_start(self, context, agent, system_prompt, input_items): pass
    async def on_llm_end(self, context, agent, response): pass
    async def on_agent_start(self, context: AgentHookContext, agent): pass
    async def on_agent_end(self, context: AgentHookContext, agent, output): pass
    async def on_handoff(self, context, from_agent, to_agent): pass
    async def on_tool_start(self, context, agent, tool): pass
    async def on_tool_end(self, context, agent, tool, result): pass

class AgentHooksBase(Generic[TContext, TAgent]):
    async def on_start(self, context: AgentHookContext, agent): pass
    async def on_end(self, context: AgentHookContext, agent, output): pass
    async def on_handoff(self, context, agent, source): pass
    async def on_tool_start(self, context, agent, tool): pass
    async def on_tool_end(self, context, agent, tool, result): pass
    async def on_llm_start(self, context, agent, system_prompt, input_items): pass
    async def on_llm_end(self, context, agent, response): pass
```

Key insights:

1. **`RunHooks.on_agent_start` and `AgentHooks.on_start`** both fire when an agent begins, but `RunHooks` fires for *every* agent in the run while `AgentHooks` fires only for its own agent.
2. **The `on_handoff` signatures differ.** `RunHooks.on_handoff(context, from_agent, to_agent)` gives you both sides. `AgentHooks.on_handoff(context, agent, source)` fires on the *receiving* agent, where `source` is who handed off *to* this agent.
3. **`AgentHookContext`** (used for start/end) includes `_approvals` and `turn_input`, while `RunContextWrapper` (used for tools/LLM) includes the full context state. The `context` parameter in `on_tool_start` is typically a `ToolContext` which adds `tool_call_id`, `tool_name`, and `tool_arguments`.
4. **For function-tool invocations**, the `context` in `on_tool_start`/`on_tool_end` is a `ToolContext` instance. For other tool types (computer, shell), it's a plain `RunContextWrapper`.

### `AgentHookContext` Explained

`AgentHookContext` is a thin subclass of `RunContextWrapper` — it has the same fields (`context`, `usage`, `_approvals`, `turn_input`) but serves as a **type marker** to distinguish agent-lifecycle hook contexts from tool/LLM hook contexts. It's used in `on_agent_start`/`on_agent_end` (RunHooks) and `on_start`/`on_end` (AgentHooks).

```python
@dataclass(eq=False)
class AgentHookContext(RunContextWrapper[TContext]):
    """Context passed to agent hooks (on_start, on_end)."""
```

The SDK constructs it internally by copying the relevant fields from the active `RunContextWrapper`:

```python
agent_hook_context = AgentHookContext(
    context=context_wrapper.context,
    usage=context_wrapper.usage,
    _approvals=context_wrapper._approvals,
    turn_input=context_wrapper.turn_input,
)
```

This means you can access `ctx.context` (your user context), `ctx.usage` (token counts), and `ctx.turn_input` (the current turn's input items) inside your hook — but you don't get `tool_call_id` or `tool_arguments` because those only exist in tool-specific contexts.

### Hook Event Map During a Run

```
Runner.run(triage_agent, "Refund request")
│
├── RunHooks.on_agent_start(triage_agent)       ◄── AgentHooks(triage).on_start()
│   RunHooks.on_llm_start(triage_agent)
│   [LLM call]
│   RunHooks.on_llm_end(triage_agent)
│
│   LLM decides to hand off:
│   RunHooks.on_handoff(triage → refund)
│   RunHooks.on_agent_start(refund_agent)       ◄── AgentHooks(refund).on_start()
│       AgentHooks(triage).on_handoff(source=triage)  ← if triage has hooks
│
│   RunHooks.on_llm_start(refund_agent)
│   [LLM call]
│   RunHooks.on_llm_end(refund_agent)
│   RunHooks.on_tool_start(refund_agent, tool)
│   [Tool executes]
│   RunHooks.on_tool_end(refund_agent, tool, result)
│
│   LLM produces final output:
│   RunHooks.on_agent_end(refund_agent, output)  ◄── AgentHooks(refund).on_end()
```

### Practical Example: Observability Hooks

```python
from agents import Agent, Runner, RunHooksBase, AgentHooksBase
import time

class TimingHooks(RunHooksBase):
    async def on_agent_start(self, ctx, agent):
        ctx._start_time = time.time()
        print(f"[{agent.name}] Starting...")

    async def on_agent_end(self, ctx, agent, output):
        elapsed = time.time() - ctx._start_time
        print(f"[{agent.name}] Done in {elapsed:.2f}s")

    async def on_tool_start(self, ctx, agent, tool):
        print(f"[{agent.name}] Calling tool: {tool.name}")

    async def on_tool_end(self, ctx, agent, tool, result):
        print(f"[{agent.name}] Tool {tool.name} returned: {result[:50]}...")

    async def on_handoff(self, ctx, from_agent, to_agent):
        print(f"[Handoff] {from_agent.name} → {to_agent.name}")

refund_agent = Agent(name="Refund", instructions="Process refunds.")
triage_agent = Agent(
    name="Triage",
    instructions="Route requests.",
    handoffs=[refund_agent]
)

result = await Runner.run(
    triage_agent,
    "I need a refund",
    hooks=TimingHooks()
)
```

---

## 7.13 Putting It Together: Multi-Agent Customer Support

Let's combine handoffs, guardrails, tool guardrails, and hooks into a complete example:

```python
from pydantic import BaseModel
from agents import (
    Agent, Runner, handoff, RunContextWrapper,
    input_guardrail, output_guardrail, GuardrailFunctionOutput,
    tool_input_guardrail, ToolGuardrailFunctionOutput, ToolInputGuardrailData,
    function_tool, RunHooksBase, InputGuardrailTripwireTriggered,
)

class HomeworkCheck(BaseModel):
    is_homework: bool
    reasoning: str

classifier_agent = Agent(
    name="Classifier",
    instructions="Determine if the user is asking for homework help.",
    output_type=HomeworkCheck,
)

@input_guardrail(name="no_homework", run_in_parallel=False)
async def check_homework(ctx, agent, input_data):
    prompt = input_data if isinstance(input_data, str) else str(input_data[-1].get("content", ""))
    result = await Runner.run(classifier_agent, f"Is this homework? {prompt}")
    return GuardrailFunctionOutput(
        output_info={"reasoning": result.final_output.reasoning},
        tripwire_triggered=result.final_output.is_homework,
    )

@output_guardrail(name="no_pii")
async def check_pii_output(ctx, agent, output):
    import re
    if re.search(r"\d{3}-\d{2}-\d{4}", str(output)):
        return GuardrailFunctionOutput(
            output_info={"reason": "SSN detected in output"},
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(output_info={}, tripwire_triggered=False)

@tool_input_guardrail
async def check_large_transfers(data: ToolInputGuardrailData) -> ToolGuardrailFunctionOutput:
    if data.context.tool_name == "process_refund":
        args = data.context.tool_arguments
        if args.get("amount", 0) > 500:
            return ToolGuardrailFunctionOutput.reject_content(
                message="Refunds over $500 require manager approval. Please escalate manually.",
                output_info={"amount": args.get("amount")}
            )
    return ToolGuardrailFunctionOutput.allow()

@function_tool(input_guardrails=[check_large_transfers])
async def process_refund(order_id: str, amount: float) -> str:
    return f"Refund of ${amount} processed for order {order_id}"

refund_agent = Agent(
    name="Refund Agent",
    instructions="Process refund requests using the process_refund tool.",
    tools=[process_refund],
    output_guardrails=[check_pii_output],
)

faq_agent = Agent(
    name="FAQ Agent",
    instructions="Answer general questions about the service.",
)

triage_agent = Agent(
    name="Triage",
    instructions="Route to the right agent based on the request.",
    input_guardrails=[check_homework],
    output_guardrails=[check_pii_output],
    handoffs=[
        handoff(refund_agent, tool_description_override="Transfer for refund requests"),
        handoff(faq_agent, tool_description_override="Transfer for general questions"),
    ],
)

class LoggingHooks(RunHooksBase):
    async def on_handoff(self, ctx, from_agent, to_agent):
        print(f"Handoff: {from_agent.name} → {to_agent.name}")

    async def on_tool_start(self, ctx, agent, tool):
        print(f"[{agent.name}] Tool call: {tool.name}")

try:
    result = await Runner.run(
        triage_agent,
        "I need a refund of $300 for order #ORD-456",
        hooks=LoggingHooks(),
    )
    print(f"Final output: {result.final_output}")
    print(f"Last agent: {result.last_agent.name}")
except InputGuardrailTripwireTriggered as e:
    print(f"Blocked: {e.guardrail_result.output.output_info}")
```

### What Happens When You Run This

```
1. Input guardrail runs (blocking mode): check_homework
   → "Is this homework?" → No → tripwire_triggered=False

2. Triage Agent LLM call
   → Decides to hand off to Refund Agent

3. Handoff: Triage → Refund Agent
   → LoggingHooks.on_handoff fires

4. Refund Agent LLM call
   → Decides to call process_refund(order_id="ORD-456", amount=300)

5. Tool input guardrail: check_large_transfers
   → $300 < $500 → allow

6. process_refund executes
   → "Refund of $300 processed for order ORD-456"

7. Refund Agent LLM call
   → Produces final output

8. Output guardrail: check_pii_output
   → No SSN detected → tripwire_triggered=False

9. Result returned:
   final_output: "Your refund of $300 for order ORD-456 has been processed."
   last_agent: "Refund Agent"
```

Now try with `$800`:
```
5'. Tool input guardrail: check_large_transfers
    → $800 > $500 → reject_content("Refunds over $500 require manager approval...")

6'. Model sees rejection message, tries different approach
    → Produces final output about escalation
```

And with a homework request:
```
1'. Input guardrail: check_homework
    → "Is this homework?" → Yes → tripwire_triggered=True

2'. InputGuardrailTripwireTriggered exception raised
    → Run halts immediately
```

---

## 7.14 Key Takeaways

1. **Handoffs = LLM tools.** The model calls `transfer_to_<agent>` like any other function. The SDK intercepts and swaps the active agent.

2. **Input filters control what the next agent sees.** Use `remove_all_tools` to strip tool artifacts, or write custom filters for fine-grained control. The `input_items` field decouples model input from session history.

3. **Guardrails have two execution modes.** Parallel (default) for low latency; blocking for cost savings. Only input guardrails support this choice.

4. **Tool guardrails are more nuanced than agent guardrails.** Three behaviors — `allow`, `reject_content`, `raise_exception` — let the model self-correct or halt completely.

5. **Tracing is on by default.** Customize with `RunConfig`, add processors with `add_trace_processor()`, flush explicitly in workers with `flush_traces()`.

6. **Hooks give you lifecycle control.** `RunHooks` for cross-cutting concerns, `AgentHooks` for agent-specific behavior. Both fire at the same events but with different scope.

7. **Guardrail boundary rules matter.** Input guardrails run only on the first agent; output guardrails only on the last. Tool guardrails fill the gap for multi-agent workflows.

8. **All features compose.** Handoffs + guardrails + tool guardrails + hooks + tracing work together. The full pipeline in §7.8 shows exactly where each check fires.
