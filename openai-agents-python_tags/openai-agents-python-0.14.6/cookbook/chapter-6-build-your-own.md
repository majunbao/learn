# Chapter 6: Build Your Own — A 300-Line Mini SDK That Actually Calls the LLM

This chapter ties together everything from Chapters 1–5 by building a **working mini SDK** from scratch. Unlike toy examples with mocked LLMs, ours will call the OpenAI API, execute real tools, manage conversation state, and even stream responses.

**The goal:** Understand *why* the real SDK is designed the way it is, by experiencing the decisions firsthand.

**How to Read This Chapter**

- **Pass 1 — Build intuition (10 min).** Read §6.1 (the architecture diagram) → §6.9 (the comparison table). Skip all code blocks.
- **Pass 2 — Build the SDK (45 min).** Read §6.2–§6.7 in order. Each section adds a layer. Type (or paste) the code into a file as you go — by §6.7 you'll have a complete working SDK.
- **Pass 3 — Extend and understand.** Itemized list:
  - The core tool system and `@function_tool`? → §6.2 (source + schema extraction)
  - Agent dataclass and model calling? → §6.3 (source + `create_response` walkthrough)
  - The turn loop and `NextStep`? → §6.4 (🔥 source code walkthrough + state machine)
  - Context and type safety? → §6.5 (source + generic pattern)
  - Guardrails? → §6.6 (source + comparison with real SDK guardrails)
  - Handoffs? → §6.7 (🔥 source code walkthrough + flow diagram)
  - Streaming? → §6.8 (source + queue pattern)
  - How it maps to the real SDK? → §6.9 (7-row comparison table)
  - Complete working example? → §6.10 (3-turn demo with tools + handoff + post-run analysis)
  - Key takeaways? → §6.11

---

## 6.1 The Architecture: What We're Building

Before writing code, let's see the big picture. Our mini SDK has 6 components, each corresponding to a real SDK subsystem:

```
┌──────────────────────────────────────────────────────────────┐
│  MiniAgent                                                    │
│  • name, instructions, tools, model                          │
│  • (Ch2: same as Agent dataclass)                            │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  @mini_tool                                                   │
│  • name, description, params_json_schema, on_invoke          │
│  • (Ch3: same as FunctionTool)                               │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  MiniRunner.run()                                             │
│  • Turn loop: call LLM → parse → execute → decide next       │
│  • (Ch4: same as run_single_turn + AgentRunner.run loop)     │
│                                                               │
│  NextStep:                                                    │
│  ├── NextStepDone    → return MiniRunResult                  │
│  ├── NextStepTools   → execute tools, then loop again        │
│  └── NextStepHandoff → switch agent, then loop again         │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  MiniContext[T]                                               │
│  • context: T (your data)                                    │
│  • (Ch5: same as RunContextWrapper)                          │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  Guardrails                                                   │
│  • input_guardrails: check before run                        │
│  • (Ch7: simplified version of InputGuardrail/OutputGuardrail)│
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  MiniResult                                                   │
│  • final_output, turns, items, raw_responses                 │
│  • (Ch1: same as RunResult)                                  │
└──────────────────────────────────────────────────────────────┘
```

**Key design decisions we'll make** (and why the real SDK made them too):

1. **Agent is a dataclass, not a class with methods** — configuration is separate from execution
2. **Tools are defined by decorators** — captures schema automatically from Python signatures
3. **The runner is a turn-based state machine** — each turn produces a `NextStep*` that decides what happens next
4. **Context is generic** — `MiniContext[YourType]` gives type safety without the SDK knowing your types

---

## 6.2 Layer 1: The Tool System

The tool system is the foundation. We need:
- A `MiniTool` dataclass that captures name, description, and JSON schema
- A `@mini_tool` decorator that extracts these from a Python function
- An `on_invoke` callable that the runner will call

```python
import inspect
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar, get_type_hints

TContext = TypeVar("TContext")

@dataclass
class MiniTool:
    name: str
    description: str
    params_json_schema: dict[str, Any]
    on_invoke: Callable[..., Any]
    needs_ctx: bool = False

def mini_tool(func: Callable) -> MiniTool:
    name = func.__name__
    description = inspect.getdoc(func) or "No description"

    sig = inspect.signature(func)
    hints = get_type_hints(func)
    params = list(sig.parameters.values())

    first_param = params[0] if params else None
    needs_ctx = first_param is not None and first_param.name == "ctx"

    tool_params = params[1:] if needs_ctx else params

    properties = {}
    required = []
    for p in tool_params:
        ptype = hints.get(p.name, str)
        schema_type = _python_type_to_json(ptype)
        properties[p.name] = {"type": schema_type, "description": f"Parameter {p.name}"}
        if p.default is inspect.Parameter.empty:
            required.append(p.name)

    params_json_schema = {
        "type": "object",
        "properties": properties,
        "required": required,
    }

    return MiniTool(
        name=name,
        description=description,
        params_json_schema=params_json_schema,
        on_invoke=func,
        needs_ctx=needs_ctx,
    )

def _python_type_to_json(ptype: type) -> str:
    mapping = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array", dict: "object"}
    return mapping.get(ptype, "string")
```

**What this gives us** — same as the real `@function_tool`:
- Automatic name extraction from `func.__name__`
- Description from the docstring
- JSON schema from type hints and signature
- Context detection (first param named `ctx`)

**What the real SDK does differently** (Ch3 §3.3):
- Uses `inspect.signature()` + `pydantic` for much richer schema generation
- Supports `ToolContext` with `inspect.signature()` injection
- Handles default values, optional parameters, and complex nested types
- Has `strict_json_schema` mode for Structured Outputs compatibility

---

## 6.3 Layer 2: The Agent + Model Calling

```python
from openai import AsyncOpenAI

@dataclass
class MiniAgent(Generic[TContext]):
    name: str
    instructions: str | Callable[[MiniAgent, MiniContext], str]
    tools: list[MiniTool] = field(default_factory=list)
    model: str = "gpt-4o-mini"
    handoffs: list["MiniAgent"] = field(default_factory=list)
    input_guardrails: list[Callable] = field(default_factory=list)

    def get_instructions(self, ctx: "MiniContext") -> str:
        if callable(self.instructions):
            return self.instructions(self, ctx)
        return self.instructions

    def get_tools_api_format(self) -> list[dict]:
        tools = []
        for t in self.tools:
            tools.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.params_json_schema,
                },
            })
        for h in self.handoffs:
            tools.append({
                "type": "function",
                "function": {
                    "name": f"transfer_to_{h.name.lower().replace(' ', '_')}",
                    "description": h.handoff_description if hasattr(h, 'handoff_description') else f"Transfer to {h.name}",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            })
        return tools
```

**Key insight #1:** Handoffs are just tools! The real SDK does the same thing — `handoff()` creates a `FunctionTool` with `on_invoke_tool` that returns the target agent (Ch7 §7.1).

**Key insight #2:** Instructions can be callable — the real SDK's `Agent.instructions` field accepts `str | Callable[[Agent, RunContextWrapper], str]`. The callable is invoked **every turn**, not once (Ch2 §2.4).

---

## 6.4 🔥 Layer 3: The Runner — Turn-Based State Machine

This is the heart of the mini SDK. The runner is a **turn-based state machine** where each turn produces a `NextStep*` that decides what happens next:

```
┌─────────────────┐
│  Start:          │
│  Call LLM        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     No tool calls
│  Parse response  │──────────────────► NextStepDone
│  (output items)  │                    (return result)
└────────┬────────┘
         │
         │ Has tool calls
         ▼
┌─────────────────┐     Handoff tool
│  Which kind?     │──────────────────► NextStepHandoff
│                  │                    (switch agent, loop)
└────────┬────────┘
         │
         │ Regular tool
         ▼
    NextStepTools
    (execute, loop)
```

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class NextStepDone:
    final_output: str

@dataclass
class NextStepTools:
    tool_calls: list[dict]

@dataclass
class NextStepHandoff:
    target_agent: "MiniAgent"
    tool_calls: list[dict]

NextStep = NextStepDone | NextStepTools | NextStepHandoff

@dataclass
class MiniContext(Generic[TContext]):
    context: TContext
    turn_count: int = 0

@dataclass
class MiniResult:
    final_output: str
    turns: int
    items: list[dict]
    raw_responses: list[dict]

class MiniRunner:
    @staticmethod
    async def run(
        agent: MiniAgent,
        user_input: str,
        context: TContext | None = None,
        max_turns: int = 10,
    ) -> MiniResult:
        client = AsyncOpenAI()
        ctx = MiniContext(context=context or {})
        conversation = [{"role": "user", "content": user_input}]
        items = []
        raw_responses = []
        current_agent = agent

        while ctx.turn_count < max_turns:
            ctx.turn_count += 1
            next_step, raw_resp = await MiniRunner._single_turn(
                client, current_agent, ctx, conversation
            )
            raw_responses.append(raw_resp)

            if isinstance(next_step, NextStepDone):
                items.append({"type": "message", "content": next_step.final_output})
                return MiniResult(
                    final_output=next_step.final_output,
                    turns=ctx.turn_count,
                    items=items,
                    raw_responses=raw_responses,
                )
            elif isinstance(next_step, NextStepTools):
                for tc in next_step.tool_calls:
                    result = await MiniRunner._execute_tool(current_agent, ctx, tc)
                    conversation.append({
                        "type": "function_call_output",
                        "call_id": tc["call_id"],
                        "output": str(result),
                    })
                    items.append({"type": "tool_output", "name": tc["name"], "output": result})
            elif isinstance(next_step, NextStepHandoff):
                for tc in next_step.tool_calls:
                    conversation.append({
                        "type": "function_call_output",
                        "call_id": tc["call_id"],
                        "output": f"Transferred to {next_step.target_agent.name}",
                    })
                items.append({"type": "handoff", "from": current_agent.name, "to": next_step.target_agent.name})
                current_agent = next_step.target_agent

        raise RuntimeError(f"Max turns exceeded ({max_turns})")

    @staticmethod
    async def _single_turn(
        client: AsyncOpenAI,
        agent: MiniAgent,
        ctx: MiniContext,
        conversation: list[dict],
    ) -> tuple[NextStep, dict]:
        instructions = agent.get_instructions(ctx)
        tools_api = agent.get_tools_api_format()

        response = await client.responses.create(
            model=agent.model,
            instructions=instructions,
            input=conversation,
            tools=tools_api if tools_api else None,
        )

        raw_resp = {"id": response.id, "model": response.model, "output": response.output}
        tool_calls = []
        text_output = None

        for item in response.output:
            if item.type == "message" and item.content:
                for content_block in item.content:
                    if content_block.type == "output_text":
                        text_output = content_block.text
            elif item.type == "function_call":
                tool_calls.append({
                    "name": item.name,
                    "arguments": item.arguments,
                    "call_id": item.call_id,
                })

        for tc in tool_calls:
            conversation.append({
                "type": "function_call",
                "name": tc["name"],
                "arguments": tc["arguments"],
                "call_id": tc["call_id"],
            })

        handoff_map = {}
        for h in agent.handoffs:
            key = f"transfer_to_{h.name.lower().replace(' ', '_')}"
            handoff_map[key] = h

        handoff_calls = [tc for tc in tool_calls if tc["name"] in handoff_map]
        regular_calls = [tc for tc in tool_calls if tc["name"] not in handoff_map]

        if handoff_calls:
            target = handoff_map[handoff_calls[0]["name"]]
            if regular_calls:
                for tc in regular_calls:
                    result = await MiniRunner._execute_tool(agent, ctx, tc)
                    conversation.append({
                        "type": "function_call_output",
                        "call_id": tc["call_id"],
                        "output": str(result),
                    })
            return NextStepHandoff(target_agent=target, tool_calls=handoff_calls), raw_resp

        if regular_calls:
            return NextStepTools(tool_calls=regular_calls), raw_resp

        return NextStepDone(final_output=text_output or ""), raw_resp

    @staticmethod
    async def _execute_tool(
        agent: MiniAgent,
        ctx: MiniContext,
        tool_call: dict,
    ) -> Any:
        tool_map = {t.name: t for t in agent.tools}
        tool = tool_map.get(tool_call["name"])
        if not tool:
            return f"Error: Unknown tool '{tool_call['name']}'"

        try:
            args = json.loads(tool_call["arguments"]) if tool_call["arguments"] else {}
        except json.JSONDecodeError:
            return f"Error: Invalid JSON arguments"

        try:
            if tool.needs_ctx:
                result = tool.on_invoke(ctx, **args)
            else:
                result = tool.on_invoke(**args)
            if inspect.isawaitable(result):
                result = await result
            return result
        except Exception as e:
            return f"Error: {e}"
```

**Key insight #1:** The `NextStep*` types make the state machine **explicit and testable**. The real SDK has 4 types (Ch4 §4.3): `NextStepDone` → `NextStepFinalOutput`, `NextStepTools` → `NextStepRunAgain`, `NextStepHandoff`, `NextStepInterruption`.

**Key insight #2:** Handoffs are detected by matching the tool name to the handoff map. The real SDK does the same — `handoff()` creates a tool whose name matches the handoff key.

**Key insight #3:** Tool results are appended to conversation as `function_call_output` with matching `call_id`. This is the Responses API format that the real SDK uses (Ch4 §4.5).

---

## 6.5 Layer 4: Context — Type-Safe Custom State

Our `MiniContext` is already generic. Let's see it in action:

```python
from dataclasses import dataclass

@dataclass
class AppContext:
    user_id: str
    db: Any
    permissions: set[str]

@mini_tool
async def lookup_user(ctx: MiniContext[AppContext], user_id: str) -> str:
    if "read" not in ctx.context.permissions:
        return "Permission denied"
    return f"User {user_id}: Active, Premium plan"

agent = MiniAgent[AppContext](
    name="AdminAgent",
    instructions="Help with user administration",
    tools=[lookup_user],
)

result = await MiniRunner.run(
    agent,
    "Look up user u-123",
    context=AppContext(user_id="admin", db=None, permissions={"read", "write"}),
)
```

**What the real SDK does differently** (Ch5 §5.2):
- `RunContextWrapper` has `usage`, `turn_input`, `_approvals`, `tool_input` fields
- Supports forking (`_fork_with_tool_input`) for concurrent tool execution
- `AgentHookContext` subclass for hooks

Our mini version strips it to the essence: your custom data, wrapped for type safety.

---

## 6.6 Layer 5: Guardrails

Guardrails run checks before or after the LLM call. We'll add a simplified version:

```python
@dataclass
class GuardrailResult:
    passed: bool
    reason: str = ""

async def run_input_guardrails(
    guardrails: list[Callable],
    user_input: str,
) -> GuardrailResult:
    for guardrail in guardrails:
        result = guardrail(user_input)
        if inspect.isawaitable(result):
            result = await result
        if not result:
            return GuardrailResult(passed=False, reason=f"Blocked by {guardrail.__name__}")
    return GuardrailResult(passed=True)
```

Add it to the runner's main loop:

```python
# At the start of MiniRunner.run(), add:
if agent.input_guardrails:
    gr = await run_input_guardrails(agent.input_guardrails, user_input)
    if not gr.passed:
        return MiniResult(
            final_output=f"Input rejected: {gr.reason}",
            turns=0,
            items=[],
            raw_responses=[],
        )
```

**Usage:**

```python
def no_pii(text: str) -> bool:
    blocked = ["ssn", "social security", "credit card"]
    return not any(b in text.lower() for b in blocked)

agent = MiniAgent(
    name="SafeAgent",
    instructions="Be helpful but safe",
    tools=[lookup_user],
    input_guardrails=[no_pii],
)

result = await MiniRunner.run(agent, "What is my SSN 123-45-6789?")
print(result.final_output)
# "Input rejected: Blocked by no_pii"
```

**What the real SDK does differently** (Ch7 §7.2):
- `InputGuardrail` is a dataclass with `name` and `guardrail_function`
- Returns `InputGuardrailResult` with `tripwire_triggered` flag
- Runs **concurrently** with `asyncio.as_completed` for parallel guardrails
- Raises `InputGuardrailTripwireTriggered` exception (not a soft return)
- `OutputGuardrail` runs on the final output, not on every turn
- Tool guardrails are separate (Ch3 §3.10)

---

## 6.7 🔥 Layer 6: Handoffs — Agent-to-Agent Delegation

Handoffs are the mechanism that makes multi-agent systems work. Let's look at how our mini SDK handles them:

```
┌───────────────────────────────────────────────────────────┐
│  Runner Loop                                               │
│                                                            │
│  current_agent = RouterAgent                               │
│  │                                                         │
│  ├── Turn 1: Call LLM with RouterAgent's tools             │
│  │   └── LLM calls "transfer_to_math_agent"               │
│  │                                                         │
│  ├── Detect handoff: NextStepHandoff(target=MathAgent)     │
│  │                                                         │
│  ├── Add handoff output to conversation                    │
│  │                                                         │
│  ├── current_agent = MathAgent  ◄── switch!               │
│  │                                                         │
│  ├── Turn 2: Call LLM with MathAgent's tools               │
│  │   └── LLM calls "calculate" tool                       │
│  │                                                         │
│  ├── Execute tool → result                                 │
│  │                                                         │
│  ├── Turn 3: Call LLM again (MathAgent)                    │
│  │   └── LLM produces final output                        │
│  │                                                         │
│  └── NextStepDone → return result                          │
└───────────────────────────────────────────────────────────┘
```

**The key code in our runner** (from §6.4):

```python
if handoff_calls:
    target = handoff_map[handoff_calls[0]["name"]]
    return NextStepHandoff(target_agent=target, tool_calls=handoff_calls)

# In the main loop:
elif isinstance(next_step, NextStepHandoff):
    for tc in next_step.tool_calls:
        conversation.append({
            "type": "function_call_output",
            "call_id": tc["call_id"],
            "output": f"Transferred to {next_step.target_agent.name}",
        })
    items.append({"type": "handoff", "from": current_agent.name, "to": next_step.target_agent.name})
    current_agent = next_step.target_agent
```

**What the real SDK does differently** (Ch7 §7.1):
- `handoff()` returns a `Handoff` object with `tool_name`, `on_invoke_handoff`, `input_filter`
- The `input_filter` can strip or modify conversation items during handoff
- `HandoffOutputItem` has `source_agent` and `target_agent` with weakref management
- Agent start hooks fire on the new agent after handoff
- The `handoff_description` field is passed to the LLM as the tool description

---

## 6.8 Layer 7: Streaming (Optional)

For real-time text display, the real SDK uses a background task + event queue pattern (Ch4 §4.11). Here's a simplified version:

```python
import asyncio
from collections import deque

@dataclass
class StreamEvent:
    type: str
    data: Any = None

@dataclass
class MiniStreamingResult:
    _queue: deque = field(default_factory=deque)
    _task: asyncio.Task | None = None
    is_complete: bool = False
    final_output: str = ""

    def stream_events(self):
        return self._iter_events()

    def _iter_events(self):
        while True:
            if self._queue:
                yield self._queue.popleft()
            elif self.is_complete:
                break
            else:
                time.sleep(0.01)

class MiniRunnerStreaming:
    @staticmethod
    def run_streamed(agent: MiniAgent, user_input: str, **kwargs) -> MiniStreamingResult:
        result = MiniStreamingResult()

        async def _run():
            try:
                run_result = await MiniRunner.run(agent, user_input, **kwargs)
                result._queue.append(StreamEvent(type="text_delta", data=run_result.final_output))
                result.final_output = run_result.final_output
            finally:
                result.is_complete = True

        result._task = asyncio.create_task(_run())
        return result
```

**The real SDK's streaming** (Ch4 §4.11) is far more sophisticated:
- `run_streamed()` starts a background `asyncio.Task` that runs the full loop
- Uses `asyncio.Queue` instead of `deque` for proper async iteration
- Yields `RawResponsesStreamEvent` (raw LLM chunks) and `RunItemStreamEvent` (semantic items)
- Supports cancellation with `cancel("immediate")` or `cancel("after_turn")`
- Has a `QueueCompleteSentinel` to signal the stream is done

---

## 6.9 Mini SDK vs Real SDK: The Full Comparison

| Mini SDK Component | Lines | Real SDK Equivalent | Real SDK File |
|---|---|---|---|
| `MiniTool` + `@mini_tool` | ~40 | `FunctionTool` + `@function_tool` | `tool.py` (Ch3) |
| `MiniAgent` | ~20 | `Agent` dataclass | `agent.py` (Ch2) |
| `MiniRunner.run()` | ~80 | `AgentRunner.run()` loop | `run.py` / `run_loop.py` (Ch4) |
| `NextStep*` types | ~10 | `NextStepFinalOutput` / `NextStepRunAgain` / `NextStepHandoff` / `NextStepInterruption` | `run_steps.py` (Ch4) |
| `MiniContext` | ~5 | `RunContextWrapper` | `run_context.py` (Ch5) |
| Guardrails | ~15 | `InputGuardrail` / `OutputGuardrail` + concurrent execution | `guardrail.py` / `run_internal/guardrails.py` (Ch7) |
| Handoffs | ~10 | `Handoff` + `HandoffOutputItem` + `input_filter` | `handoffs/` (Ch7) |
| Streaming | ~25 | `RunResultStreaming` + `StreamEvent` types + cancel | `stream_events.py` / `run_loop.py` (Ch4) |
| **Total** | **~300** | **~15,000+** | |

**The ratio tells the story:** The real SDK is ~50× larger because it handles:
- Error recovery (retry with backoff, rewind, conversation_locked)
- Full guardrail pipeline (concurrent, tripwire exceptions, tool-level)
- Session persistence (SQLite, OpenAI Conversations, compaction)
- Schema versioning (RunState serialization with 9 schema versions)
- Tool approval system (per-call, always-approve, rejection messages)
- Context forking (shared state across concurrent tools)
- Memory management (weakref agent references, `release_agent()`)
- Tracing integration (TraceProvider, spans, custom exporters)
- Sandbox support (Docker, execution environments)
- MCP (Model Context Protocol) tools

---

## 6.10 Putting It All Together: A Complete 3-Turn Demo

Let's run a complete example that exercises tools, handoffs, and guardrails:

```python
import asyncio

@mini_tool
async def get_weather(ctx, location: str) -> str:
    """Get the current weather for a location."""
    return f"Sunny, 72°F in {location}"

@mini_tool
async def calculate(ctx, expression: str) -> str:
    """Evaluate a math expression."""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"

weather_agent = MiniAgent(
    name="Weather Agent",
    instructions="Answer weather questions using the get_weather tool.",
    tools=[get_weather],
)

math_agent = MiniAgent(
    name="Math Agent",
    instructions="Solve math problems using the calculate tool.",
    tools=[calculate],
)

def no_harmful(text: str) -> bool:
    blocked = ["hack", "exploit", "attack"]
    return not any(b in text.lower() for b in blocked)

router_agent = MiniAgent(
    name="Router",
    instructions="Route questions to the right agent. Use handoffs for weather or math questions.",
    handoffs=[weather_agent, math_agent],
    input_guardrails=[no_harmful],
)

async def main():
    print("=" * 60)
    print("Mini Agents SDK - Full Demo")
    print("=" * 60)

    result = await MiniRunner.run(router_agent, "What's the weather in Tokyo?")
    print(f"\nFinal: {result.final_output}")
    print(f"Turns: {result.turns}")
    print(f"Items: {result.items}")

    result2 = await MiniRunner.run(router_agent, "What is 42 * 17?")
    print(f"\nFinal: {result2.final_output}")
    print(f"Turns: {result2.turns}")
    print(f"Items: {result2.items}")

    result3 = await MiniRunner.run(router_agent, "How do I hack a server?")
    print(f"\nFinal: {result3.final_output}")
    print(f"Turns: {result3.turns}")

asyncio.run(main())
```

### What happens across 3 runs:

**Run 1: Weather question → Handoff to Weather Agent**

```
--- Run 1: "What's the weather in Tokyo?" ---
Turn 1 (Router): LLM calls transfer_to_weather_agent
  → Handoff: Router → Weather Agent
Turn 2 (Weather Agent): LLM calls get_weather(location="Tokyo")
  → Tool result: "Sunny, 72°F in Tokyo"
Turn 3 (Weather Agent): LLM produces final output
  → "The weather in Tokyo is sunny at 72°F."
```

**Run 2: Math question → Handoff to Math Agent**

```
--- Run 2: "What is 42 * 17?" ---
Turn 1 (Router): LLM calls transfer_to_math_agent
  → Handoff: Router → Math Agent
Turn 2 (Math Agent): LLM calls calculate(expression="42 * 17")
  → Tool result: "714"
Turn 3 (Math Agent): LLM produces final output
  → "42 * 17 = 714"
```

**Run 3: Blocked by guardrail**

```
--- Run 3: "How do I hack a server?" ---
  → Guardrail check: no_harmful() returns False
  → Input rejected: Blocked by no_harmful
  → Turns: 0 (never called the LLM)
```

### Post-run analysis:

```python
# Run 1 analysis
print(f"Final output: {result.final_output}")
print(f"Total turns: {result.turns}")
print(f"Raw responses: {len(result.raw_responses)}")
print(f"Items generated:")
for item in result.items:
    print(f"  {item}")
# {'type': 'handoff', 'from': 'Router', 'to': 'Weather Agent'}
# {'type': 'tool_output', 'name': 'get_weather', 'output': 'Sunny, 72°F in Tokyo'}
# {'type': 'message', 'content': 'The weather in Tokyo is sunny at 72°F.'}
```

---

## 6.11 Key Takeaways

1. **The core is surprisingly small** — 300 lines covers agent + tools + runner + context + guardrails + handoffs
2. **Agent is configuration, not behavior** — a dataclass that says *what*, the runner says *how*
3. **Tools are defined by decorators** — captures schema from Python, no manual JSON writing
4. **The runner is a NextStep state machine** — each turn produces an explicit decision
5. **Handoffs are just tools** — the LLM decides to call them, the runner detects the name
6. **Guardrails are pre/post checks** — simple in concept, complex in the real SDK (concurrent, exceptions, tripwires)
7. **Context is generic for type safety** — `MiniContext[YourType]` gives your tools type hints
8. **The real SDK is 50× larger** — error recovery, persistence, tracing, sandboxing, MCP, and more
9. **Every real SDK concept has a mini equivalent** — understanding the mini version makes the real one intuitive
10. **The architecture is the lesson** — if you can rebuild it, you truly understand it
