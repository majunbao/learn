# Chapter 1: Quick Start - From Zero to Production-Ready Agent

This chapter walks you through the OpenAI Agents SDK from first principles. We'll build up to a real, multi-tool agent with structured output, streaming, context management, and multi-turn conversation — and when we say "source code", we actually mean it: we'll read the SDK's own Python code together.

## How to Read This Chapter

**Pass 1 — Build intuition (~30 min):** Read 1.1 → 1.2 (flow diagram only) → 1.3 (field lists only, skip deep-dive subsections) → 1.4 → 1.5 (skip Guardrail/ContextWrapper/Key Methods subsections) → 1.6 → 1.7 (example + pipeline diagram only, skip _is_wrapped/strict_json_schema) → 1.11 in order. Skip all "Source Code Walkthrough" subsections and deep-dive subsections. Focus on flow diagrams, field tables, and example code. The goal: understand the main thread — **Agent is configuration, Runner is execution, RunResult is the output**.

**Pass 2 — Dive into source code (~60 min):** Go back and read the four 🔥 Source Code Walkthroughs in 1.2 → 1.5 → 1.6 → 1.7. By now you know the big picture, so the code reads much easier. The goal: understand **how the SDK calls the LLM, executes tools, and parses structured output**.

**Pass 3 — Fill in the gaps:** Read selectively based on your needs:
- Agent field details (hooks, model_settings, handoff_description)? → 1.3 (deep-dive subsections)
- RunResult details (guardrails, context wrapper, methods)? → 1.5 (Guardrail Results, Context Wrapper, Key Methods subsections)
- Structured output internals (wrapping, strict schema, validation)? → 1.7 (_is_wrapped, strict_json_schema, validate_json subsections)
- Context system & dynamic instructions? → 1.8 + 1.9 (includes context forking, tool approval, get_system_prompt source)
- Streaming? → 1.10 (includes StreamEvent source code, cancel, practical examples, silent failure detection)
- Multi-turn strategies & session lifecycle? → 1.11 (includes session lifecycle diagram, auto_previous_response_id)
- RunConfig & ModelSettings overrides? → 1.12 (includes resolve() source code and advanced features)
- Complete working example with post-run analysis? → 1.13
- Debugging & error handling? → 1.14 (includes weakref pattern, RunErrorDetails, ToolTimeoutError)
- Full architecture overview? → 1.15

**Key marker:** Sections marked with 🔥 are the highlights of this chapter — prioritize them.

## 1.1 The Simplest Agent

Let's start with the minimal runnable example (see `examples/basic/hello_world.py`):

```python
import asyncio
from agents import Agent, Runner

async def main():
    agent = Agent(
        name="Assistant",
        instructions="You only respond in haikus.",
    )
    result = await Runner.run(agent, "Tell me about recursion in programming.")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

Two classes, one async call, done. But what actually happened? To answer that, we need to look inside the SDK.

## 1.2 What Happens When You Call Runner.run()

Before we read source code, let's build intuition with a simple picture. When you call `Runner.run(agent, "Hello!")`, the SDK runs a loop:

```
  Runner.run(agent, "Hello!")
         │
         ▼
  ┌─ Initialize ──────────────────────────────┐
  │  • Wrap your context in RunContextWrapper  │
  │  • Create RunState (tracks the whole run)  │
  │  • Set up tracing                         │
  └────────────────────────────────────────────┘
         │
         ▼
  ┌─ The Loop ──────────────────────────────────────────────────────┐
  │                                                                  │
  │   1. (first turn only) Run input guardrails                     │
  │   2. Call the LLM ──────▶ get back a response                  │
  │   3. What did the LLM return?                                   │
  │      ├─ Final answer? ──────▶ exit loop ✅                      │
  │      ├─ Tool calls? ───────▶ execute tools, then loop again 🔄  │
  │      └─ Handoff? ──────────▶ switch agent, then loop again 🔄  │
  │                                                                  │
  │   (repeat until final answer, or max_turns exceeded)            │
  └──────────────────────────────────────────────────────────────────┘
         │
         ▼
  ┌─ Cleanup ───────────────────────────────────┐
  │  • Run output guardrails                    │
  │  • Save to session (if provided)            │
  │  • Return RunResult                         │
  └─────────────────────────────────────────────┘
```

This is the "agent loop" — the core pattern in every agentic framework. The key insight: **an agent run is not a single LLM call.** It's a loop that may call the LLM multiple times, executing tools or switching agents between each call.

Now let's read the actual source code to see how this picture maps to real Python.

### 🔥 Source Code Walkthrough: AgentRunner.run()

Let's open `src/agents/run.py` and trace the path from your `Runner.run()` call to the LLM response. Here's the **simplified** core of `AgentRunner.run()` (the method that `Runner.run()` delegates to):

```python
# src/agents/run.py, simplified from the real source
async def run(self, starting_agent, input, **kwargs):
    context = kwargs.get("context")
    max_turns = kwargs.get("max_turns", DEFAULT_MAX_TURNS)  # default is 10
    hooks = validate_run_hooks(kwargs.get("hooks"))
    run_config = kwargs.get("run_config") or RunConfig()     # ← default config created here

    # Step 1: Prepare the input
    # If input is a string, it becomes [{"role": "user", "content": "..."}]
    # If input is a list, it's used as-is
    # If session is provided, session history is prepended
    prepared_input = await prepare_input_with_session(input, session, ...)

    # Step 2: Wrap your context object
    context_wrapper = ensure_context_wrapper(context)
    # This creates RunContextWrapper(context=your_context, usage=Usage())

    # Step 3: Create the RunState — the mutable state that tracks the entire run
    run_state = RunState(
        context=context_wrapper,
        original_input=original_input,
        starting_agent=starting_agent,
        max_turns=max_turns,
    )

    # Step 4: Set up tracing (visible in OpenAI Dashboard)
    with TraceCtxManager(workflow_name=..., tracing=...):

        # Step 5: THE MAIN LOOP — iterate until we get a final output
        current_turn = 0
        current_agent = starting_agent
        while current_turn < max_turns:

            # 5a. Run input guardrails (only on first turn)
            if current_turn == 0:
                await run_input_guardrails(current_agent, prepared_input, ...)

            # 5b. Call the LLM
            # run_single_turn: assembles system prompt + tools + input → calls LLM API → returns response
            response = await run_single_turn(current_agent, prepared_input, ...)

            # 5c. Process the LLM response
            # process_model_response: inspects the LLM response and decides what to do next
            # It returns a "NextStep" object — a dataclass that tells the loop what happened:
            #   NextStepFinalOutput → LLM produced a final answer → exit loop
            #   NextStepHandoff    → LLM wants to delegate to another agent → switch agent
            #   NextStepRunAgain   → LLM called tools, tools executed, results ready → loop again
            #   (defined in src/agents/run_internal/run_steps.py)
            step = process_model_response(response, ...)

            if isinstance(step, NextStepFinalOutput):
                break  # ← We got our answer!
            elif isinstance(step, NextStepHandoff):
                current_agent = step.new_agent  # Switch to new agent, loop again
            elif isinstance(step, NextStepRunAgain):
                # Tools were executed inside process_model_response,
                # their results are already appended to the conversation.
                # We just update the input and loop again.
                prepared_input = step.model_input

            current_turn += 1

        # Step 6: Run output guardrails
        await run_output_guardrails(current_agent, final_output, ...)

        # Step 7: Build and return the RunResult
        return RunResult(
            input=original_input,
            new_items=all_new_items,
            raw_responses=all_model_responses,
            final_output=final_output,
            ...
        )
```

Now you can see how the flow diagram maps to code. Let's highlight the key insights:

1. **The loop is explicit** — you can see `while current_turn < max_turns`. Each tool call or handoff creates another iteration.
2. **Your context is wrapped early** — `ensure_context_wrapper(context)` happens once, before the loop. The same wrapper is reused across all turns and all agents.
3. **Input guardrails run only once** — only on the first turn, for the starting agent.
4. **Output guardrails run at the end** — after the loop exits, not during.
5. **Handoffs switch the agent but keep the loop running** — the `current_agent` changes, but `current_turn` keeps counting.
6. **Tool execution happens inside `process_model_response`** — it doesn't just *inspect* the response; it also *executes* the tools the LLM requested and appends their results. By the time we get a `NextStepRunAgain`, the work is already done.

Two functions do the heavy lifting inside the loop:

- **`run_single_turn`** (`src/agents/run_internal/run_loop.py`): Assembles the system prompt, tools, handoffs, and output schema from the agent, then calls the LLM API and returns the raw response.
- **`process_model_response`** (`src/agents/run_internal/turn_resolution.py`): Inspects the LLM's response. If the LLM made tool calls, this function *executes* them (via `execute_function_tool_calls` and friends) and appends the results. Then it returns a `NextStep*` to tell the loop what to do.

Now when you see `Runner.run()` in your code, you know exactly what's happening inside.

## 1.3 The Agent: Core Fields You Need to Know

Looking at `src/agents/agent.py`, `Agent` inherits from `AgentBase` and is a `@dataclass` generic on `TContext`. Here are the fields organized by when you'll need them:

**Fields you use from day one:**

```python
@dataclass
class Agent(AgentBase[TContext], Generic[TContext]):
    name: str                                    # Required. Identifies the agent.
    instructions: str | Callable | None = None   # The system prompt (or a function that returns one)
    model: str | Model | None = None             # Which LLM to use (None = default)
    tools: list[Tool] = field(default_factory=list)  # What tools the agent can call
```

**Fields you'll need as your agent grows:**

```python
    output_type: type | AgentOutputSchemaBase | None = None
    handoffs: list[Agent | Handoff] = field(default_factory=list)
    tool_use_behavior: Literal["run_llm_again", "stop_on_first_tool"] | ToolsToFinalOutputFunction = "run_llm_again"
    hooks: AgentHooks[TContext] | None = None
    model_settings: ModelSettings | None = None
```

**Fields for production hardening:**

```python
    input_guardrails: list[InputGuardrail] = field(default_factory=list)
    output_guardrails: list[OutputGuardrail] = field(default_factory=list)
    handoff_description: str | None = None  # (from AgentBase)
```

### The "As It Grows" Fields — Deep Dive

#### `hooks: AgentHooks[TContext]` — Per-Agent Lifecycle Callbacks

`AgentHooks` fires callbacks for **this specific agent only**. This is different from `RunHooks` (which fires for all agents). The callbacks are defined in `src/agents/lifecycle.py`:

```python
# src/agents/lifecycle.py — the real interface
class AgentHooksBase(Generic[TContext, TAgent]):
    async def on_start(self, context: AgentHookContext[TContext], agent: TAgent) -> None:
        """Called before this agent is invoked."""

    async def on_end(self, context: AgentHookContext[TContext], agent: TAgent, output: Any) -> None:
        """Called when this agent produces a final output."""

    async def on_handoff(self, context: RunContextWrapper[TContext], agent: TAgent, source: TAgent) -> None:
        """Called when this agent is being handed off TO. source is the agent handing off."""

    async def on_tool_start(self, context: RunContextWrapper[TContext], agent: TAgent, tool: Tool) -> None:
        """Called immediately before a local tool is invoked."""

    async def on_tool_end(self, context: RunContextWrapper[TContext], agent: TAgent, tool: Tool, result: str) -> None:
        """Called immediately after a local tool is invoked."""

    async def on_llm_start(self, context: RunContextWrapper[TContext], agent: Agent[TContext],
                           system_prompt: str | None, input_items: list[TResponseInputItem]) -> None:
        """Called immediately before the agent issues an LLM call."""

    async def on_llm_end(self, context: RunContextWrapper[TContext], agent: Agent[TContext],
                         response: ModelResponse) -> None:
        """Called immediately after the agent receives the LLM response."""
```

| Hook | When It Fires | Common Use |
|---|---|---|
| `on_start` | Agent is about to run | Logging, initialization, input validation |
| `on_end` | Agent produces final output | Logging, output post-processing, metrics |
| `on_handoff` | Another agent hands off TO this agent | Transition logging, state reset |
| `on_tool_start` | Before a tool function is called | Input logging, rate limiting |
| `on_tool_end` | After a tool function returns | Result logging, caching |
| `on_llm_start` | Before the LLM API call | Prompt logging, token budgeting |
| `on_llm_end` | After the LLM API call returns | Response logging, usage tracking |

Example usage:

```python
from agents import AgentHooks, AgentHookContext

class MyHooks(AgentHooks[None]):
    async def on_start(self, context: AgentHookContext, agent: Agent) -> None:
        print(f"[{agent.name}] Starting...")

    async def on_tool_start(self, context, agent, tool) -> None:
        print(f"[{agent.name}] Calling tool: {tool.name}")

agent = Agent(name="Assistant", hooks=MyHooks())
```

#### `model_settings: ModelSettings` — Per-Agent LLM Configuration

Each agent can have its own model settings that override the global `RunConfig.model_settings`. The full `ModelSettings` class (from `src/agents/model_settings.py`) has these commonly used fields:

| Field | Type | What It Controls |
|---|---|---|
| `temperature` | `float \| None` | Randomness (0 = deterministic, 1 = creative) |
| `top_p` | `float \| None` | Nucleus sampling threshold |
| `max_tokens` | `int \| None` | Maximum output tokens |
| `tool_choice` | `ToolChoice \| None` | Force/auto/disable tool use |
| `parallel_tool_calls` | `bool \| None` | Allow multiple tool calls in one turn |
| `truncation` | `"auto" \| "disabled" \| None` | How to handle context overflow |
| `reasoning` | `Reasoning \| None` | Reasoning model configuration |
| `store` | `bool \| None` | Store response for later retrieval |

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Creative Writer",
    model_settings=ModelSettings(temperature=0.9, max_tokens=2000),
)

agent2 = Agent(
    name="Code Generator",
    model_settings=ModelSettings(temperature=0.0, tool_choice="required"),
)
```

The resolution chain: `Agent.model_settings` → `resolve(RunConfig.model_settings)` → final merged settings. See section 1.12 for the `resolve()` source code.

### The "Production Hardening" Fields — Deep Dive

#### `handoff_description: str | None` — When to Hand Off

This field (from `AgentBase`) is critical for multi-agent systems. When an agent has `handoffs` to other agents, the LLM needs to know *when* to delegate. The `handoff_description` tells the LLM what each target agent does:

```python
refund_agent = Agent(
    name="Refund Agent",
    handoff_description="Handles refund requests and return policy questions",
)

sales_agent = Agent(
    name="Sales Agent",
    handoff_description="Helps with product recommendations and pricing",
)

triage_agent = Agent(
    name="Triage Agent",
    instructions="Route the user to the right department.",
    handoffs=[refund_agent, sales_agent],
)
```

Without `handoff_description`, the LLM only sees the agent's `name` to decide when to hand off — which is often ambiguous. With it, the LLM gets a clear description of each target's capabilities.

We'll introduce each field with examples as we go. For now, remember: **Agent is configuration, not execution.** It's a data bag that describes what the agent *is*; the `Runner` is what makes it *do* things.

## 1.4 Three Ways to Run an Agent

The `Runner` class (in `src/agents/run.py`) provides three methods:

| Method | Return Type | When to Use |
|--------|-------------|-------------|
| `Runner.run()` | `RunResult` | Standard async execution — **use this by default** |
| `Runner.run_sync()` | `RunResult` | Sync wrapper around `run()`. Won't work inside async contexts (FastAPI, Jupyter). |
| `Runner.run_streamed()` | `RunResultStreaming` | Real-time streaming — you receive events as the LLM generates tokens |

All three share the same parameters. Let's walk through each one (defined in `src/agents/run.py` and `src/agents/run_config.py`):

```python
result = await Runner.run(
    starting_agent,          # The Agent to start with
    input,                   # str | list[TResponseInputItem]
    *,
    context=None,            # Your custom context object (TContext)
    max_turns=10,            # Safety limit for the agent loop (default: 10)
    run_config=None,         # RunConfig — global overrides
    session=None,            # Session for SDK-managed conversation history
    previous_response_id=None,  # OpenAI server-side conversation continuation
)
```

**`starting_agent`** — The `Agent` instance that begins the run. This is the agent the LLM talks to first. If handoffs occur during the run, the current agent changes, but `starting_agent` stays the same.

**`input`** — Can be either:
- A **string**: automatically converted to `[{"role": "user", "content": "..."}]` internally
- A **list of `TResponseInputItem`**: full control over the conversation history (multi-turn, system messages, etc.)
- A **`RunState`**: resume a previously interrupted run (see section 1.5's `to_state()`)

**`context`** — Your custom object (of type `TContext`). It's wrapped into a `RunContextWrapper` early in the run and shared across all turns, tools, hooks, and handoffs. **Never sent to the LLM.** See section 1.8 for details.

**`max_turns`** — Safety valve for the agent loop. Each LLM call counts as one turn. If the LLM keeps calling tools or handing off without producing a final answer, this limit prevents infinite loops. When exceeded, `MaxTurnsExceeded` is raised. Default is `DEFAULT_MAX_TURNS = 10` (defined in `src/agents/run_config.py`).

**`run_config`** — A `RunConfig` object for global overrides. This is how you set the model, temperature, tracing, guardrails, etc. without modifying each agent individually. See section 1.12 for the full breakdown.

**`session`** — A `Session` object for SDK-managed conversation history. When provided, the SDK automatically loads history before the run and saves new items after. Supports SQLite, encrypted, SQLAlchemy, Redis, and more backends. See section 1.11 for strategies.

**`previous_response_id`** — For OpenAI server-side conversation continuation. Instead of managing history locally, you pass the ID of the previous response, and OpenAI's servers reconstruct the conversation. Only works with OpenAI models and the Responses API. See section 1.11 for details.

**`hooks`** — `RunHooks` lifecycle callbacks (on_llm_start, on_tool_start, on_agent_start, etc.). These fire for **all** agents in the run. See section 1.14 and `src/agents/lifecycle.py` for the full hook interface.

**`error_handlers`** — `RunErrorHandlers` that let you gracefully handle errors like `MaxTurnsExceeded` by returning a fallback message instead of raising an exception. See section 1.14 for an example.

## 1.5 The RunResult: What You Get Back

After the loop finishes, you get a `RunResult`. Let's look at what's inside, directly from `src/agents/result.py`:

```python
@dataclass
class RunResultBase(abc.ABC):
    input: str | list[TResponseInputItem]
    new_items: list[RunItem]
    raw_responses: list[ModelResponse]
    final_output: Any
    input_guardrail_results: list[InputGuardrailResult]
    output_guardrail_results: list[OutputGuardrailResult]
    context_wrapper: RunContextWrapper[Any]
```

### Understanding Each Field

**`input`** — The original input you passed to `Runner.run()`. Note: this may be a *mutated* version if handoff input filters modified it during the run.

**`new_items`** — All items generated during the run: messages, tool calls, tool outputs, handoff events. This is the "paper trail" of everything that happened.

**`raw_responses`** — The raw LLM API responses, one per turn. So `len(raw_responses)` equals the number of turns the agent took.

**`final_output`** — The final text or structured output from the last agent. This is what you usually care about the most.

#### Guardrail Results

**`input_guardrail_results`** and **`output_guardrail_results`** store the results of safety guardrail checks. Let's look at the source (`src/agents/guardrail.py`):

```python
@dataclass
class GuardrailFunctionOutput:
    output_info: Any          # Optional details about what the guardrail checked
    tripwire_triggered: bool  # If True, execution is halted immediately

@dataclass
class InputGuardrailResult:
    guardrail: InputGuardrail[Any]   # Which guardrail was run
    output: GuardrailFunctionOutput  # What it found

@dataclass
class OutputGuardrailResult:
    guardrail: OutputGuardrail[Any]  # Which guardrail was run
    agent: Agent[Any]                # Which agent was checked
    agent_output: Any                # The output that was checked
    output: GuardrailFunctionOutput  # What it found
```

The key concept is the **tripwire**: if any guardrail sets `tripwire_triggered = True`, the agent's execution is immediately halted and an exception (`InputGuardrailTripwireTriggered` or `OutputGuardrailTripwireTriggered`) is raised. These result lists let you audit all guardrail checks after the run, even when no tripwire was triggered.

```
Input Guardrail flow:
  User Input ──→ InputGuardrail.run() ──→ InputGuardrailResult
                     │                         │
                     └─ tripwire_triggered?    ├─ guardrail: which check
                          ├─ True  → raise     └─ output: what was found
                          └─ False → continue

Output Guardrail flow:
  Agent Output ──→ OutputGuardrail.run() ──→ OutputGuardrailResult
                       │                          │
                       └─ tripwire_triggered?     ├─ guardrail: which check
                            ├─ True  → raise      ├─ agent: which agent
                            └─ False → continue   ├─ agent_output: what was checked
                                                   └─ output: what was found
```

Guardrails are defined with decorators and attached to agents:

```python
from agents import input_guardrail, output_guardrail, GuardrailFunctionOutput

@input_guardrail
def check_off_topic(context, agent, input_text):
    is_off_topic = "politics" in input_text.lower()
    return GuardrailFunctionOutput(
        output_info={"topic": "politics detected"} if is_off_topic else None,
        tripwire_triggered=is_off_topic
    )

agent = Agent(
    instructions="You are a helpful assistant.",
    input_guardrails=[check_off_topic]
)
```

#### Context Wrapper

**`context_wrapper`** is a `RunContextWrapper[Any]` — a runtime backpack that carries two things. Let's read the source (`src/agents/run_context.py`):

```python
@dataclass(eq=False)
class RunContextWrapper(Generic[TContext]):
    context: TContext    # Your custom context object (or None)
    usage: Usage         # Token usage statistics for the entire run
    # ... (tool approval methods omitted for now)
```

**`context`** — The custom object you passed to `Runner.run()`. Important: this is **never** sent to the LLM. It's purely for your code — tool functions, callbacks, hooks, etc.

**`usage`** — Token usage statistics. Let's look at `src/agents/usage.py`:

```python
@dataclass
class Usage:
    requests: int = 0               # Total LLM API calls made
    input_tokens: int = 0           # Total input tokens across all requests
    output_tokens: int = 0          # Total output tokens across all requests
    total_tokens: int = 0           # input_tokens + output_tokens
    input_tokens_details: InputTokensDetails   # e.g. cached_tokens
    output_tokens_details: OutputTokensDetails # e.g. reasoning_tokens
    request_usage_entries: list[RequestUsage]  # Per-request breakdown
```

This is your **cost dashboard**. After a run, you can check how much the agent spent:

```python
result = await Runner.run(agent, "Analyze this data", context=my_context)
usage = result.context_wrapper.usage
print(f"API calls: {usage.requests}")
print(f"Input tokens: {usage.input_tokens}")
print(f"Output tokens: {usage.output_tokens}")
print(f"Cached tokens: {usage.input_tokens_details.cached_tokens}")
print(f"Reasoning tokens: {usage.output_tokens_details.reasoning_tokens}")

# Per-request breakdown (useful for cost attribution)
for i, entry in enumerate(usage.request_usage_entries):
    print(f"  Request {i+1}: {entry.input_tokens} in / {entry.output_tokens} out")
```

### Key Methods on RunResult

#### final_output_as() — Type-Safe Structured Output Access

```python
answer: MyOutput = result.final_output_as(MyOutput, raise_if_incorrect_type=True)
```

Let's read the source (`src/agents/result.py:268-284`):

```python
def final_output_as(self, cls: type[T], raise_if_incorrect_type: bool = False) -> T:
    if raise_if_incorrect_type and not isinstance(self.final_output, cls):
        raise TypeError(f"Final output is not of type {cls.__name__}")
    return cast(T, self.final_output)
```

The behavior depends on `raise_if_incorrect_type`:

| `raise_if_incorrect_type` | What happens |
|---|---|
| `False` (default) | Only a type annotation hint for your IDE; no runtime check |
| `True` | Runs `isinstance()` at runtime; raises `TypeError` if mismatch |

**When to use `True`**: When your agent has `output_type` set to a Pydantic model and you want to fail fast if something goes wrong with structured output parsing.

#### last_agent — Who Handled the Request?

```python
print(result.last_agent.name)  # e.g. "refund_agent"
```

This seems trivial for a single-agent setup — it's always the same agent. But it becomes **critical with handoffs**: if Agent A hands off to Agent B, `last_agent` tells you that Agent B was the one that produced the final output.

Under the hood, `RunResult` uses a `weakref` to store the agent reference:

```python
@dataclass
class RunResult(RunResultBase):
    _last_agent: Agent[Any]
    _last_agent_ref: weakref.ReferenceType[Agent[Any]] | None = field(...)

    @property
    def last_agent(self) -> Agent[Any]:
        agent = self.__dict__.get("_last_agent")
        if agent is not None:
            return agent
        if self._last_agent_ref:
            agent = self._last_agent_ref()
            if agent is not None:
                return agent
        raise AgentsException("Last agent reference is no longer available.")
```

The weakref pattern is important: after `release_agents()` is called, the strong reference is dropped and only the weakref remains. If the agent gets garbage collected, accessing `last_agent` will raise `AgentsException`.

#### release_agents() — Memory Management

```python
result.release_agents()
```

Why does this exist? Agent graphs can be large (multiple agents connected via handoffs), and `RunResult` holds references to them through `new_items` and `last_agent`. Without explicit release, these agents stay in memory as long as the result object exists.

The implementation walks through all `new_items` and calls `release_agent()` on each, then converts the `last_agent` strong reference to a weakref:

```python
def release_agents(self, *, release_new_items: bool = True) -> None:
    if release_new_items:
        for item in self.new_items:
            release = getattr(item, "release_agent", None)
            if callable(release):
                release()
    self._release_last_agent_reference()
```

As a safety net, `__del__` also calls `release_agents(release_new_items=False)` automatically, so you don't *have* to call it explicitly — but calling it early lets the GC reclaim memory sooner.

#### to_state() — Resuming from Interruptions

```python
if result.interruptions:
    state = result.to_state()
    state.approve(result.interruptions[0])
    result = await Runner.run(agent, state)  # Resume from where we left off
```

`to_state()` serializes the entire run state (current agent, conversation history, turn count, guardrail results, etc.) into a `RunState` object. You can then approve/reject pending tool calls and pass the state back to `Runner.run()` to continue execution. This is the foundation for **human-in-the-loop** tool approval flows.

### 🔥 Source Code Walkthrough: to_input_list()

The most important method is `to_input_list()` — it's how you chain multi-turn conversations. Let's read the actual source:

```python
# src/agents/result.py — the real code
def to_input_list(self, *, mode: ToInputListMode = "preserve_all") -> list[TResponseInputItem]:
    """Create an input-item view of this run."""
    original_items: list[TResponseInputItem] = ItemHelpers.input_to_new_input_list(self.input)
    reasoning_item_id_policy = getattr(self, "_reasoning_item_id_policy", None)
    replay_items = _input_items_for_result(self, mode=mode, reasoning_item_id_policy=...)
    return original_items + replay_items
```

The logic is beautifully simple: **take the original input, append all the new items from this run, return the combined list.** This combined list is what you pass to the next `Runner.run()` call:

```python
result1 = await Runner.run(agent, "Hello!")
result2 = await Runner.run(agent, result1.to_input_list() + [
    {"role": "user", "content": "What did I just say?"}
])
result3 = await Runner.run(agent, result2.to_input_list() + [
    {"role": "user", "content": "Can you summarize our conversation?"}
])
result4 = await Runner.run(agent, result3.to_input_list() + [
    {"role": "user", "content": "Thanks, that's all!"}
])
```

What does `to_input_list()` actually produce? For a simple single-turn conversation, it looks like this:

```python
# After: result = await Runner.run(agent, "Hello!")
result.to_input_list()
# → [
#     {"role": "user", "content": "Hello!"},           # original input
#     {"role": "assistant", "content": "Hi there! ..."} # LLM's response (new_items)
#   ]
```

For a multi-turn conversation with tools, the list grows to include tool calls and tool outputs too — everything the LLM needs to reconstruct the full conversation history.

```python
# After: result = await Runner.run(
#     agent_with_tools, "What's the weather in Tokyo and London?"
# )
result.to_input_list()
# → [
#     {"role": "user", "content": "What's the weather in Tokyo and London?"},
#     {"type": "function_call", "name": "get_weather", "arguments": "{\"city\": \"Tokyo\"}", "call_id": "call_1"},
#     {"type": "function_call", "name": "get_weather", "arguments": "{\"city\": \"London\"}", "call_id": "call_2"},
#     {"type": "function_call_output", "call_id": "call_1", "output": "Weather in Tokyo: 68°F, cloudy"},
#     {"type": "function_call_output", "call_id": "call_2", "output": "Weather in London: 55°F, rainy"},
#     {"role": "assistant", "content": "Tokyo is 68°F and cloudy, while London is 55°F and rainy."}
#   ]
```

Notice how the list includes not just messages but also `function_call` entries (the LLM's tool requests) and `function_call_output` entries (the tool results). This is the full conversation history that the LLM needs to understand what happened — without it, the LLM wouldn't know what tools it called or what results it got.

### RunResult vs RunResultStreaming

| Feature | `RunResult` | `RunResultStreaming` |
|---|---|---|
| How to get it | `Runner.run()` / `Runner.run_sync()` | `Runner.run_streamed()` |
| Blocking | Yes, waits until complete | No, returns immediately |
| Event stream | None | `stream_events()` async iterator |
| Cancel | Not applicable | `cancel(mode="immediate"\|"after_turn")` |
| Completion | Always complete | Check `is_complete` property |
| `last_agent` | Available after return | Updates as run progresses; true value only after complete |

## 1.6 Adding Tools the Right Way

The SDK provides the `@function_tool` decorator as the primary way to define tools. Let's build a practical example:

```python
import asyncio
from typing import Annotated
from agents import Agent, Runner, function_tool


@function_tool
def get_weather(
    city: Annotated[str, "The city name, e.g. 'San Francisco'"],
) -> str:
    """Get the current weather for a city."""
    return f"Weather in {city}: 72°F, sunny"


@function_tool
def get_population(
    city: Annotated[str, "The city name, e.g. 'San Francisco'"],
) -> str:
    """Get the population of a city."""
    return f"Population of {city}: ~870,000"


agent = Agent(
    name="City Info Assistant",
    instructions="You help users learn about cities. Use the available tools to get real data.",
    tools=[get_weather, get_population],
)

async def main():
    result = await Runner.run(
        agent,
        "What's the weather and population of San Francisco?",
    )
    print(result.final_output)
    print(f"Turns: {len(result.raw_responses)}")
    for item in result.new_items:
        print(f"  Item: {type(item).__name__}")

if __name__ == "__main__":
    asyncio.run(main())
```

**`@function_tool` extracts the tool schema automatically from your function signature:**

- The **function name** becomes the tool name
- The **docstring** becomes the tool description (shown to the LLM when it decides which tool to use)
- **Parameter type hints** define the JSON schema types
- **`Annotated[type, description]`** provides per-parameter descriptions (the LLM sees these)
- **Default values** make parameters optional

### 🔥 Source Code Walkthrough: How `@function_tool` Generates the JSON Schema

The SDK uses `src/agents/function_schema.py` to convert your Python function signature into the strict JSON schema that the OpenAI API requires. Here's the core function, simplified from the real source:

```python
# src/agents/function_schema.py — simplified
def function_schema(
    func: Callable[..., Any],
    docstring_style: DocstringStyle | None = None,
    name_override: str | None = None,
    description_override: str | None = None,
    use_docstring_info: bool = True,
    strict_json_schema: bool = True,
) -> FuncSchema:
    # 1. Extract docstring info (description, param descriptions)
    doc_info = generate_func_documentation(func, docstring_style)
    param_descs = dict(doc_info.param_descriptions or {})

    # 2. Process type hints — strip Annotated, extract descriptions
    type_hints_with_extras = get_type_hints(func, include_extras=True)
    for name, annotation in type_hints_with_extras.items():
        stripped_ann, metadata = _strip_annotated(annotation)
        description = _extract_description_from_metadata(metadata)
        if description is not None:
            param_descs.setdefault(name, description)  # Annotated wins over docstring

    # 3. Check if first parameter is RunContextWrapper/ToolContext → takes_context
    sig = inspect.signature(func)
    # ... (skipped: detect context parameter, filter it out)

    # 4. Dynamically build a Pydantic model from the parameters
    fields: dict[str, Any] = {}
    for name, param in filtered_params:
        ann = type_hints.get(name, param.annotation)
        if ann == inspect._empty:
            ann = Any
        if param.default == inspect._empty:
            fields[name] = (ann, Field(..., description=param_descs.get(name)))
        else:
            fields[name] = (ann, Field(default=param.default, description=param_descs.get(name)))

    dynamic_model = create_model(f"{func_name}_args", __base__=BaseModel, **fields)

    # 5. Generate JSON schema from the Pydantic model
    json_schema = dynamic_model.model_json_schema()
    if strict_json_schema:
        json_schema = ensure_strict_json_schema(json_schema)

    return FuncSchema(
        name=func_name,
        description=description_override or doc_info.description,
        params_pydantic_model=dynamic_model,
        params_json_schema=json_schema,
        signature=sig,
        takes_context=takes_context,
        strict_json_schema=strict_json_schema,
    )
```

Key insights:

1. **`Annotated` descriptions override docstring descriptions.** If you write `city: Annotated[str, "The city name"]`, that description takes priority over a docstring `:param city: ...` section. This is useful when you want the LLM to see a different description than your code documentation.
2. **A Pydantic model is dynamically created.** The SDK doesn't just read type hints — it builds a full `create_model()` so that all Pydantic validation features (validators, custom types, etc.) work.
3. **`strict_json_schema=True` by default.** The generated schema is post-processed by `ensure_strict_json_schema()` to add `additionalProperties: false` and make all fields required. This matches OpenAI's Structured Outputs requirements.
4. **The `FuncSchema.takes_context` flag.** If the first parameter is `RunContextWrapper` or `ToolContext`, it's excluded from the JSON schema (the LLM doesn't see it) but stored so the SDK knows to inject it at call time.
5. **Docstring style is auto-detected.** The SDK supports Google, NumPy, and Sphinx docstring styles via the `griffe` library. You don't need to specify which style you're using.

What the LLM actually sees for our `get_weather` function:

```json
{
  "type": "function",
  "name": "get_weather",
  "description": "Get the current weather for a city.",
  "parameters": {
    "type": "object",
    "properties": {
      "city": {
        "type": "string",
        "description": "The city name, e.g. 'San Francisco'"
      }
    },
    "required": ["city"],
    "additionalProperties": false
  },
  "strict": true
}
```

### Async Tools and Error Handling

Tools can be `async def` — the SDK detects this automatically and `await`s the result:

```python
@function_tool
async def fetch_api_data(
    url: Annotated[str, "The URL to fetch data from"],
) -> str:
    """Fetch data from an external API."""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()
```

When a tool raises an exception, the SDK handles it differently depending on configuration:

```python
# Default behavior: the exception propagates and the run fails
# But you can configure per-tool timeout handling:
@function_tool
def slow_operation(
    data: Annotated[str, "Input data"],
) -> str:
    """A potentially slow operation."""
    import time
    time.sleep(30)
    return "done"
```

The `FunctionTool` class has several fields for error handling (see the table below). The key mechanism is in `invoke_function_tool()` from `src/agents/tool.py`:

```python
# src/agents/tool.py — simplified
async def invoke_function_tool(
    *,
    function_tool: FunctionTool,
    context: ToolContext[Any],
    arguments: str,
) -> Any:
    timeout_seconds = function_tool.timeout_seconds
    if timeout_seconds is None:
        return await function_tool.on_invoke_tool(context, arguments)

    tool_task = asyncio.ensure_future(function_tool.on_invoke_tool(context, arguments))
    try:
        return await asyncio.wait_for(tool_task, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        timeout_error = ToolTimeoutError(tool_name=function_tool.name, timeout_seconds=timeout_seconds)
        if function_tool.timeout_behavior == "raise_exception":
            raise timeout_error
        # "error_as_result" — return error message as tool output, LLM can retry
        return default_tool_timeout_error_message(function_tool.name, timeout_seconds)
```

With `timeout_behavior="error_as_result"` (the default), the timeout error becomes a string that the LLM sees as the tool output. The LLM can then decide to retry, use a different approach, or inform the user. With `timeout_behavior="raise_exception"`, the entire run fails.

### FunctionTool Key Fields

| Field | Type | Purpose |
|---|---|---|
| `name` | `str` | Tool name shown to the LLM (defaults to function name) |
| `description` | `str` | Tool description shown to the LLM (defaults to docstring) |
| `params_json_schema` | `dict` | JSON schema for parameters (auto-generated) |
| `on_invoke_tool` | `Callable` | The actual function to call (wrapped by `@function_tool`) |
| `strict_json_schema` | `bool` | Whether schema is strict mode (default: `True`) |
| `is_enabled` | `bool \| Callable` | Dynamically enable/disable the tool per run |
| `needs_approval` | `bool \| Callable` | Require human approval before execution |
| `timeout_seconds` | `float \| None` | Timeout per invocation (default: `None` = no timeout) |
| `timeout_behavior` | `"error_as_result" \| "raise_exception"` | What to do on timeout |
| `timeout_error_function` | `Callable \| None` | Custom timeout error message formatter |
| `tool_input_guardrails` | `list \| None` | Per-tool input guardrails (run before invocation) |
| `tool_output_guardrails` | `list \| None` | Per-tool output guardrails (run after invocation) |

The `is_enabled` field is particularly useful for conditional tools:

```python
@function_tool
def delete_database(ctx: RunContextWrapper[UserContext]) -> str:
    """Delete the entire database. Admin only."""
    return "Database deleted."

# Make it conditional:
delete_database.is_enabled = lambda ctx, agent: ctx.context.is_admin
```

When `is_enabled` returns `False`, the tool is completely hidden from the LLM — it won't even appear in the tool list.

### 🔥 Source Code Walkthrough: execute_function_tool_calls

Remember in section 1.2 we said that `process_model_response` executes tools? Here's how it works under the hood. When the LLM decides to call a tool, `process_model_response` calls `execute_function_tool_calls` from `src/agents/run_internal/tool_execution.py`:

```
process_model_response()
       │
       │ LLM response contains tool calls
       ▼
execute_function_tool_calls()         ← entry point
       │
       ▼
_FunctionToolBatchExecutor.execute()  ← handles parallel calls
       │
       ├─ 1. Run tool input guardrails (if configured)
       ├─ 2. Fire hooks.on_tool_start()
       ├─ 3. Call invoke_function_tool()  ← runs your actual Python function
       ├─ 4. Run tool output guardrails (if configured)
       ├─ 5. Fire hooks.on_tool_end()
       └─ 6. Return FunctionToolResult for each tool call
```

And here's the actual signature, simplified from the real source:

```python
# src/agents/run_internal/tool_execution.py — simplified
async def execute_function_tool_calls(
    *,
    bindings: AgentBindings,            # Contains the public + execution agent
    tool_runs: list[ToolRunFunction],   # One entry per tool call the LLM made
    hooks: RunHooks,                    # Lifecycle hooks
    context_wrapper: RunContextWrapper,  # Your context + usage info
    config: RunConfig,                  # Global run config
) -> tuple[list[FunctionToolResult], list[...], list[...]]:
    """Execute function tool calls with approvals, guardrails, and hooks."""
    return await _FunctionToolBatchExecutor(
        bindings=bindings,
        tool_runs=tool_runs,
        hooks=hooks,
        context_wrapper=context_wrapper,
        config=config,
    ).execute()
```

Key insights:

1. **Tool execution is a pipeline, not just a function call.** Guardrails, hooks, and approvals wrap your actual function.
2. **Parallel tool calls are handled by the BatchExecutor.** The LLM can request multiple tools in a single turn, and they're executed concurrently via `asyncio`.
3. **`tool_runs` is a list** — each entry corresponds to one tool call the LLM made. If the LLM called both `get_weather` and `get_population`, there would be two entries.
4. **The return value includes guardrail results** — the second and third elements of the tuple are tool input/output guardrail results, which may be empty if no tool guardrails are configured.

### Tool Use Behavior

By default, after executing tools, the SDK loops back to the LLM so it can process the tool results. You can change this with `tool_use_behavior`:

```python
agent = Agent(
    name="Assistant",
    tools=[get_weather],
    tool_use_behavior="stop_on_first_tool",
    # The tool's output becomes final_output directly, no second LLM call
)
```

Or use a custom function for fine-grained control:

```python
from agents import Agent, ToolsToFinalOutputResult

def should_stop(ctx: RunContextWrapper, agent: Agent, tool_results: list[FunctionToolResult]):
    if any(r.tool_name == "get_weather" for r in tool_results):
        return ToolsToFinalOutputResult(
            is_final_output=True,
            final_output=tool_results[0].output,  # Use the weather result as the final answer
        )
    return ToolsToFinalOutputResult(is_final_output=False)  # Continue to the LLM

agent = Agent(
    name="Assistant",
    tools=[get_weather, get_population],
    tool_use_behavior=should_stop,
)
```

The `ToolsToFinalOutputResult` has two fields:

| Field | Type | Meaning |
|---|---|---|
| `is_final_output` | `bool` | If `True`, stop the agent loop and return. If `False`, continue to the LLM. |
| `final_output` | `Any` | The value to use as `result.final_output` when `is_final_output=True` |

The three `tool_use_behavior` options compared:

| Option | Behavior | When to Use |
|---|---|---|
| `"run_llm_again"` (default) | Loop back to LLM with tool results | General purpose — LLM synthesizes the answer |
| `"stop_on_first_tool"` | First tool's output becomes `final_output` | Tools are the answer (e.g., lookups, calculations) |
| Custom function | Your logic decides per-turn | Conditional: stop for some tools, continue for others |

## 1.7 Structured Output with `output_type`

Most real applications don't want raw text — they want structured data. The SDK uses `output_type` to enforce this:

```python
from pydantic import BaseModel
from agents import Agent, Runner


class CityInfo(BaseModel):
    city: str
    weather: str
    population: str
    summary: str


agent = Agent(
    name="City Info Assistant",
    instructions="You help users learn about cities. Always return structured data.",
    tools=[get_weather, get_population],
    output_type=CityInfo,
)

async def main():
    result = await Runner.run(agent, "Tell me about San Francisco")
    info = result.final_output_as(CityInfo)
    print(f"City: {info.city}, Weather: {info.weather}")
```

### 🔥 Source Code Walkthrough: How output_type Works

Let's read `src/agents/agent_output.py` to understand the internal mechanism:

```python
# src/agents/agent_output.py — simplified
@dataclass(init=False)
class AgentOutputSchema(AgentOutputSchemaBase):
    output_type: type[Any]
    _type_adapter: TypeAdapter[Any]    # Pydantic adapter for validation
    _is_wrapped: bool                  # Whether the output is wrapped in a dict
    _output_schema: dict[str, Any]     # The JSON schema

    def __init__(self, output_type: type[Any], strict_json_schema: bool = True):
        self.output_type = output_type
        self._strict_json_schema = strict_json_schema

        if output_type is None or output_type is str:
            # Plain text output — no schema needed
            self._is_wrapped = False
            self._type_adapter = TypeAdapter(output_type)
            return

        # For complex types, we may need to wrap them
        self._is_wrapped = not _is_subclass_of_base_model_or_dict(output_type)

        if self._is_wrapped:
            # Some types can't be represented as JSON Schema objects directly,
            # so we wrap them: {"response": <your_type>}
            OutputType = TypedDict("OutputType", {"response": output_type})
            self._type_adapter = TypeAdapter(OutputType)
        else:
            self._type_adapter = TypeAdapter(output_type)

        # Generate and (optionally) strict-ify the JSON schema
        self._output_schema = self._type_adapter.json_schema()
        if self._strict_json_schema:
            self._output_schema = ensure_strict_json_schema(self._output_schema)
```

The full pipeline works like this:

```
Your output_type (e.g. CityInfo)
       │
       ▼
AgentOutputSchema.__init__() creates JSON schema + TypeAdapter
       │
       ▼
Converter.get_response_format() injects the schema as response_format
       │
       ▼
OpenAI API receives: response_format={format: {type: "json_schema", name: "final_output", schema: ...}}
       │
       ▼
The LLM is forced to produce JSON matching your schema
(It appears as a tool call named "json_tool_call" in the response)
       │
       ▼
AgentOutputSchema.validate_json() parses the LLM output via TypeAdapter
       │
       ▼
You get back a validated CityInfo instance
```

This is why structured output "just works" — the LLM doesn't know it's producing structured data; the OpenAI API enforces the schema at the model level. When the response comes back, the SDK recognizes the `json_tool_call` tool call and routes it to `validate_json()` instead of treating it as a regular tool.

What the LLM API actually receives (from `src/agents/models/openai_responses.py`):

```python
# Converter.get_response_format() produces this:
response_format = {
    "format": {
        "type": "json_schema",
        "name": "final_output",         # Internal name, not your class name
        "schema": output_schema.json_schema(),  # Your CityInfo's JSON schema
        "strict": output_schema.is_strict_json_schema(),  # True by default
    }
}
```

This is set as the `text.format` parameter in the OpenAI Responses API call. The LLM is then constrained to produce JSON that matches your schema — it cannot produce free-form text.

### output_type + tools: How They Coexist

Our example has both `tools` and `output_type`:

```python
agent = Agent(
    tools=[get_weather, get_population],  # The LLM can call these
    output_type=CityInfo,                  # But the final output must be CityInfo
)
```

What happens when you run this? The answer depends on the turn:

```
Turn 1:
  LLM sees: tools=[get_weather, get_population] + response_format=CityInfo
  LLM decides: "I need to call tools first to get data"
  → Produces: tool calls (get_weather, get_population)
  → NO structured output yet — tools take priority

Turn 2:
  Tool results are added to the conversation
  LLM sees: same tools + response_format + tool results
  LLM decides: "Now I have the data, I'll produce the structured output"
  → Produces: JSON matching CityInfo schema
  → Run ends — final_output is a CityInfo instance
```

Key insight: **tools and structured output are not mutually exclusive.** The LLM can call tools for multiple turns, then produce structured output when it's ready. The `response_format` constraint is always present, but the LLM can choose to call tools instead of producing the final output — it's only when the LLM produces non-tool-call output that the schema is enforced.

This means:
- If you have `output_type=CityInfo` and **no tools**, the LLM must produce `CityInfo` on the first turn
- If you have `output_type=CityInfo` and **tools**, the LLM can call tools first, then produce `CityInfo` on a later turn
- The `max_turns` limit still applies — if the LLM keeps calling tools and never produces structured output, you'll get a `MaxTurnsExceeded` exception

### The `_is_wrapped` Mechanism — Why Some Types Need Wrapping

Not all Python types can be represented as JSON Schema objects. The SDK handles this by wrapping unsupported types in a `TypedDict`:

```python
# src/agents/agent_output.py — the wrapping logic
self._is_wrapped = not _is_subclass_of_base_model_or_dict(output_type)

if self._is_wrapped:
    OutputType = TypedDict("OutputType", {"response": output_type})
    self._type_adapter = TypeAdapter(OutputType)
else:
    self._type_adapter = TypeAdapter(output_type)
```

| `output_type` | `_is_wrapped` | What the LLM sees |
|---|---|---|
| `str` or `None` | `False` | No schema (plain text mode) |
| Pydantic `BaseModel` subclass | `False` | The model's JSON schema directly |
| `dict` or `dict[str, Any]` | `False` | The dict's JSON schema directly |
| `list[str]`, `int`, `tuple`, etc. | `True` | Wrapped: `{"response": <your_type>}` |

When `_is_wrapped` is True, the LLM produces JSON like `{"response": ["a", "b", "c"]}` instead of `["a", "b", "c"]`. The `validate_json()` method automatically unwraps it:

```python
# src/agents/agent_output.py — the unwrapping logic
def validate_json(self, json_str: str) -> Any:
    validated = _json.validate_json(json_str, self._type_adapter, partial=False)
    if self._is_wrapped:
        if not isinstance(validated, dict):
            raise ModelBehaviorError(f"Expected a dict, got {type(validated)}")
        if _WRAPPER_DICT_KEY not in validated:  # _WRAPPER_DICT_KEY = "response"
            raise ModelBehaviorError(f"Could not find key 'response' in JSON")
        return validated["response"]  # Unwrap!
    return validated
```

### `strict_json_schema` — Why It Matters

The `AgentOutputSchema` constructor takes `strict_json_schema=True` by default. This enables OpenAI's [Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs) mode, which **guarantees** the LLM output matches the schema:

```python
# When strict_json_schema is True (default):
if self._strict_json_schema:
    self._output_schema = ensure_strict_json_schema(self._output_schema)
```

Strict mode restricts the JSON schema features (no optional fields without defaults, no `anyOf`, etc.) but guarantees valid JSON output. If your type isn't compatible with strict mode, you'll get a `UserError`:

```python
# This works — Pydantic model with required fields
class MyOutput(BaseModel):
    answer: str
    confidence: float

# This fails with strict_json_schema=True — list types aren't strict-compatible
agent = Agent(output_type=list[str])  # Works! SDK wraps it, but strict schema may fail

# If strict mode fails, you can disable it:
from agents import AgentOutputSchema
agent = Agent(
    output_type=AgentOutputSchema(list[str], strict_json_schema=False)
)
```

| `strict_json_schema` | Behavior | Trade-off |
|---|---|---|
| `True` (default) | Guarantees valid JSON output | Schema must follow strict rules |
| `False` | More flexible schema types | LLM may occasionally produce invalid JSON |

## 1.8 The Context System

The `TContext` generic parameter on `Agent[TContext]` is how you pass dependencies to tools, hooks, and guardrails without global state:

```python
from dataclasses import dataclass
from agents import Agent, Runner, RunContextWrapper, function_tool


@dataclass
class UserContext:
    user_id: str
    preferred_language: str
    api_token: str


@function_tool
def get_user_profile(
    ctx: RunContextWrapper[UserContext],
) -> str:
    """Get the current user's profile."""
    user_ctx = ctx.context
    return f"User {user_ctx.user_id}, language: {user_ctx.preferred_language}"


agent = Agent[UserContext](
    name="Profile Assistant",
    instructions="Help users with their profile. Use the user's preferred language.",
    tools=[get_user_profile],
)

async def main():
    ctx = UserContext(user_id="u_123", preferred_language="zh-CN", api_token="secret")
    result = await Runner.run(agent, "Show me my profile", context=ctx)
    print(result.final_output)
```

**Key points about context:**

1. The context is **never sent to the LLM** — it's purely for your code (tools, hooks, guardrails)
2. Tools can optionally take `RunContextWrapper` as their first parameter (the SDK detects this automatically via `inspect.signature`)
3. The same context object is shared across the entire run, including across handoffs

### RunContextWrapper vs AgentHookContext

We introduced `RunContextWrapper` in section 1.5. Now let's clarify the two context types you'll encounter. The SDK defines a subclass for agent hooks:

```python
# src/agents/run_context.py
@dataclass(eq=False)
class RunContextWrapper(Generic[TContext]):
    context: TContext                           # Your custom context object
    usage: Usage = field(default_factory=Usage) # Token counts, updated each turn
    turn_input: list[TResponseInputItem] = field(default_factory=list)

@dataclass(eq=False)
class AgentHookContext(RunContextWrapper[TContext]):
    """Context passed to agent hooks (on_start, on_end)."""
    pass  # Inherits everything from RunContextWrapper
```

| Context Type | Where It's Used | What It Carries |
|---|---|---|
| `RunContextWrapper[TContext]` | Tools, guardrails, `RunHooks.on_llm_start/end`, `RunHooks.on_tool_start/end` | Your context + usage + turn_input |
| `AgentHookContext[TContext]` | `RunHooks.on_agent_start/end`, `AgentHooks.on_start/end` | Same as above (it's a subclass) |

The distinction is deliberate: agent hooks (`on_agent_start`, `on_agent_end`) receive `AgentHookContext`, which is a marker type that tells you "an agent lifecycle event is happening." All other callbacks receive the base `RunContextWrapper`. In practice, they have the same fields — but the type distinction helps you reason about *when* your callback is firing.

### How Tools Receive Context

The SDK uses `inspect.signature()` to detect whether your tool function expects a context parameter. If the first parameter is annotated as `RunContextWrapper`, the SDK passes it automatically:

```python
# SDK detects ctx: RunContextWrapper and injects it
@function_tool
def my_tool(ctx: RunContextWrapper[UserContext], city: str) -> str:
    return ctx.context.user_id

# SDK sees no ctx parameter — no context is passed
@function_tool
def simple_tool(city: str) -> str:
    return city
```

This is handled in `src/agents/tool.py` — the `FunctionTool` class stores whether the function expects context, and `invoke_function_tool()` passes it accordingly.

### How Context Is Forked for Tool Calls

When a tool is called, the SDK creates a **forked** copy of the `RunContextWrapper` so that the tool can access additional metadata (like `tool_input`) without mutating the parent context. From `src/agents/run_context.py`:

```python
# src/agents/run_context.py
def _fork_with_tool_input(self, tool_input: Any) -> RunContextWrapper[TContext]:
    """Create a child context that shares approvals and usage with tool input set."""
    fork = RunContextWrapper(context=self.context)
    fork.usage = self.usage              # Shared reference — usage accumulates
    fork._approvals = self._approvals    # Shared reference — approvals persist
    fork.turn_input = self.turn_input    # Shared reference
    fork.tool_input = tool_input         # Tool-specific: only on the fork
    return fork

def _fork_without_tool_input(self) -> RunContextWrapper[TContext]:
    """Create a child context that shares approvals and usage without tool input."""
    fork = RunContextWrapper(context=self.context)
    fork.usage = self.usage
    fork._approvals = self._approvals
    fork.turn_input = self.turn_input
    return fork
```

Key insight: `usage` and `_approvals` are **shared references** across forks. This means:
- If a tool call updates `usage`, the parent context sees it too
- If a hook approves/rejects a tool, the approval persists across the entire run
- `tool_input` is the only thing that's different on the fork — it contains the structured tool arguments

### Tool Approval — Human-in-the-Loop

The `RunContextWrapper` also provides methods for approving or rejecting tool calls. This is the mechanism behind `result.interruptions` and `result.to_state()` that we saw in section 1.5:

```python
# Approve a tool call (optionally for all future calls to the same tool)
context_wrapper.approve_tool(approval_item, always_approve=True)

# Reject a tool call (optionally for all future calls)
context_wrapper.reject_tool(
    approval_item,
    always_reject=True,
    rejection_message="This tool is not allowed for this user."
)

# Check if a tool is already approved
is_approved = context_wrapper.is_tool_approved("delete_file", "call_abc123")
```

The approval state is tracked per-tool-name and per-call-id, stored in the `_approvals` dict. Since `_approvals` is shared across all context forks, an approval in one part of the run persists everywhere.

## 1.9 Dynamic Instructions

The `instructions` field can be a callable instead of a string. This is useful when the system prompt depends on runtime information that isn't known when you create the agent. Common scenarios:

- **User preferences**: adapt tone, language, or verbosity based on user settings
- **Authorization level**: include or exclude certain capabilities based on the user's role
- **Contextual awareness**: inject data retrieved by a previous tool call into the prompt

Here's an example that adapts based on user context:

```python
from agents import Agent, RunContextWrapper


def build_instructions(
    ctx: RunContextWrapper[UserContext],
    agent: Agent[UserContext],
) -> str:
    base = "You are a helpful assistant."
    if ctx.context.preferred_language == "zh-CN":
        base += "\nAlways respond in Simplified Chinese."
    return base


agent = Agent[UserContext](
    name="Assistant",
    instructions=build_instructions,
)
```

### How Dynamic Instructions Work Internally

The SDK resolves instructions at the beginning of **every turn** via `agent.get_system_prompt(context_wrapper)`. Let's look at the source (`src/agents/agent.py`):

```python
# src/agents/agent.py — simplified
def get_system_prompt(self, context_wrapper: RunContextWrapper[TContext]) -> str | None:
    if isinstance(self.instructions, str):
        return self.instructions
    if callable(self.instructions):
        return self.instructions(context_wrapper, self)
    return None
```

The logic is straightforward:
1. If `instructions` is a **string** → return it directly
2. If `instructions` is a **callable** → call it with `(context_wrapper, agent)` and return the result
3. If `instructions` is **None** → no system prompt

This has an important implication: **if a tool call mutates the context object, the next turn's instructions will automatically reflect that change.** For example:

```python
@function_tool
def set_language(ctx: RunContextWrapper[UserContext], lang: str) -> str:
    ctx.context.preferred_language = lang  # Mutate the context
    return f"Language set to {lang}"

# Next turn, build_instructions() sees the updated preferred_language
# No manual refresh needed — the SDK calls the function every turn
```

### When to Use Dynamic vs Static Instructions

| Pattern | When to Use | Example |
|---|---|---|
| Static string | Instructions never change | `"You are a helpful assistant."` |
| Callable | Instructions depend on context or runtime state | User language, role-based access, time-of-day |
| None | No system prompt needed (e.g., the agent is purely a tool router) | Agent with only `handoffs`, no conversation |

## 1.10 Streaming

For real-time applications, use `Runner.run_streamed()`. Note: unlike `Runner.run()`, this is **not** an async call — you don't `await` it. It returns a `RunResultStreaming` object immediately, and the LLM call happens in the background while you consume events:

```python
from agents import Agent, Runner

agent = Agent(name="Storyteller", instructions="You write creative short stories.")

async def main():
    # No await! run_streamed returns immediately.
    result = Runner.run_streamed(agent, "Write a short story about a robot learning to paint.")

    # Consume events as they arrive
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            continue
        elif event.type == "run_item_stream_event":
            print(f"  → {event.name}: {type(event.item).__name__}")

    # After the stream completes, the result has full data just like Runner.run()
    print(f"Final output length: {len(result.final_output)}")
    print(f"Turns: {len(result.raw_responses)}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Stream Event Types — Source Code Walkthrough

Let's read the actual event types from `src/agents/stream_events.py`:

```python
# src/agents/stream_events.py — the real source
@dataclass
class RawResponsesStreamEvent:
    """Streaming event from the LLM. Raw events passed through from the LLM API."""
    data: TResponseStreamEvent
    type: Literal["raw_response_event"] = "raw_response_event"

@dataclass
class RunItemStreamEvent:
    """Streaming events that wrap a RunItem — messages, tool calls, tool outputs, handoffs, etc."""
    name: Literal[
        "message_output_created",
        "handoff_requested",
        "handoff_occured",        # Historical misspelling, can't change (breaking change)
        "tool_called",
        "tool_search_called",
        "tool_search_output_created",
        "tool_output",
        "reasoning_item_created",
        "mcp_approval_requested",
        "mcp_approval_response",
        "mcp_list_tools",
    ]
    item: RunItem
    type: Literal["run_item_stream_event"] = "run_item_stream_event"

@dataclass
class AgentUpdatedStreamEvent:
    """Event that notifies that there is a new agent running (via handoff)."""
    new_agent: Agent[Any]
    type: Literal["agent_updated_stream_event"] = "agent_updated_stream_event"

StreamEvent: TypeAlias = RawResponsesStreamEvent | RunItemStreamEvent | AgentUpdatedStreamEvent
```

| Event Type | When It Fires | Typical Use |
|------------|--------------|-------------|
| `raw_response_event` | Every token/chunk from the LLM API | Real-time text display, typing indicators |
| `run_item_stream_event` | When a complete item is produced (message, tool call, tool output, handoff) | UI updates, progress tracking |
| `agent_updated_stream_event` | When the current agent changes (via handoff) | Showing which agent is active |

### Practical Streaming: Displaying Text in Real-Time

The most common streaming pattern is displaying LLM output token-by-token. Here's how:

```python
result = Runner.run_streamed(agent, "Tell me a story")

async for event in result.stream_events():
    if event.type == "raw_response_event":
        # Raw token events from the LLM API
        # The data field contains ResponseStreamEvent objects
        # For text output, look for "response.output_text.delta" events
        if hasattr(event.data, "delta"):
            print(event.data.delta, end="", flush=True)
    elif event.type == "run_item_stream_event":
        if event.name == "tool_called":
            print(f"\n[Calling tool: {type(event.item).__name__}]")
        elif event.name == "tool_output":
            print(f"\n[Tool result received]")
    elif event.type == "agent_updated_stream_event":
        print(f"\n[Agent changed to: {event.new_agent.name}]")

print()  # Final newline
```

### Canceling a Streaming Run

`RunResultStreaming` supports two cancellation strategies:

```python
result = Runner.run_streamed(agent, "Long task")

async for event in result.stream_events():
    if user_interrupted():
        result.cancel(mode="after_turn")  # Graceful: finish current turn, then stop
        # result.cancel()                 # Immediate: stop right now (default)
```

| Mode | Behavior |
|---|---|
| `"immediate"` (default) | Stop immediately, cancel all tasks, clear queues |
| `"after_turn"` | Complete current turn gracefully (finish LLM response, execute pending tools, save session state) then stop before next turn |

After `cancel()`, you should continue consuming `stream_events()` to allow the cancellation to complete properly.

### Checking for Silent Failures

Sometimes the background run loop fails before producing any stream events (e.g., sandbox initialization error). After consuming the stream, check `run_loop_exception`:

```python
result = Runner.run_streamed(agent, "hello")
async for event in result.stream_events():
    pass  # Process events...

if result.run_loop_exception:
    raise result.run_loop_exception  # Surface the error
```

The `RunResultStreaming` object is a superset of `RunResult` — after the stream completes, you can access `final_output`, `new_items`, `raw_responses`, etc., just like with `Runner.run()`. This means you don't need separate code paths for streaming vs. non-streaming results.

## 1.11 Multi-Turn Conversations

There are three strategies for continuing conversations across turns:

### Strategy 1: Manual — `to_input_list()`

```python
result1 = await Runner.run(agent, "Hello!")
result2 = await Runner.run(agent, result1.to_input_list() + [
    {"role": "user", "content": "What did I just say?"}
])
result3 = await Runner.run(agent, result2.to_input_list() + [
    {"role": "user", "content": "Can you go deeper on that?"}
])
```

Full control, works with any model provider, but you manage the history yourself.

### Strategy 2: SDK Session

```python
from agents.memory import SQLiteSession

session = SQLiteSession("conversation.db")
result1 = await Runner.run(agent, "Hello!", session=session)
result2 = await Runner.run(agent, "Follow up question", session=session)
result3 = await Runner.run(agent, "Can you elaborate on that?", session=session)
```

The SDK loads/saves history automatically. Available session backends:

| Backend | Import | Storage | Best For |
|---|---|---|---|
| `SQLiteSession` | `from agents.memory import SQLiteSession` | Local SQLite file | Local development, single-process apps |
| `InMemorySession` | `from agents.memory import InMemorySession` | In-memory dict | Testing, ephemeral conversations |
| `EncryptedSession` | `from agents.memory import EncryptedSession` | Encrypted SQLite | Sensitive data, local apps |
| `SQLAlchemySession` | `from agents.memory import SQLAlchemySession` | Any SQLAlchemy DB | Production with PostgreSQL, MySQL, etc. |
| `RedisSession` | `from agents.memory import RedisSession` | Redis | Distributed/ephemeral production |

### Strategy 3: OpenAI Server-Managed State

```python
result1 = await Runner.run(agent, "Hello!")
result2 = await Runner.run(
    agent,
    "Follow up",
    previous_response_id=result1.last_response_id,
)
result3 = await Runner.run(
    agent,
    "One more question",
    previous_response_id=result2.last_response_id,
)
```

Or with `auto_previous_response_id=True` for automatic chaining. The conversation lives on OpenAI's servers — no local history management needed.

How does this work? The `previous_response_id` is the ID of the last OpenAI API response. When you pass it, the OpenAI Responses API automatically includes the prior conversation context server-side, so you don't need to resend the full history. You can access it via `result.last_response_id` (defined in `src/agents/result.py`):

```python
# src/agents/result.py
@property
def last_response_id(self) -> str | None:
    """Convenience method to get the response ID of the last model response."""
    if not self.raw_responses:
        return None
    return self.raw_responses[-1].response_id
```

**Important**: This only works with OpenAI models and the Responses API. Other providers (LiteLLM, custom) don't support server-side conversation state.

| Strategy | Best For | Trade-off |
|----------|----------|-----------|
| `to_input_list()` | Full control, any provider | You manage history |
| Session | SDK-managed persistence | Storage backend needed |
| `previous_response_id` | OpenAI-only, simplest | Vendor lock-in |

### Session Lifecycle — How Sessions Work Internally

When you provide a `session` parameter, the SDK follows a specific lifecycle each time you call `Runner.run()`:

```
Runner.run(agent, "Hello", session=session)
       │
       ▼
1. session.get_items() → load previous conversation history
       │
       ▼
2. Prepend history to input → full conversation context
       │
       ▼
3. Run the agent loop (as usual)
       │
       ▼
4. session.add_items(new_items) → save new conversation items
       │
       ▼
5. Return RunResult
```

This means each `Runner.run()` call with a session:
- **Reads** the full history at the start
- **Appends** only the new items at the end
- The session backend handles persistence (file, DB, memory, etc.)

You can also configure session behavior with `RunConfig.session_settings`:

```python
from agents import RunConfig
from agents.memory import SessionSettings

result = await Runner.run(
    agent, "Hello", session=session,
    run_config=RunConfig(
        session_settings=SessionSettings(
            # Control how many items to retrieve, etc.
        )
    ),
)
```

### `auto_previous_response_id` — Automatic Conversation Chaining

Instead of manually passing `previous_response_id` each time, you can enable automatic chaining:

```python
# First call — no previous_response_id yet
result1 = await Runner.run(
    agent, "Hello",
    auto_previous_response_id=True,
)

# Subsequent calls — automatically chains to the previous response
result2 = await Runner.run(
    agent, "Follow up",
    auto_previous_response_id=True,
    # The SDK automatically uses result1.last_response_id
)
```

**Important caveats:**
- Only works with OpenAI models and the Responses API
- `auto_previous_response_id=True` on the first turn is a no-op (there's no previous response yet)
- Handoff input filters are **not** supported with server-managed conversations (`conversation_id`, `previous_response_id`, or `auto_previous_response_id`)

## 1.12 RunConfig: Global Overrides

`RunConfig` (from `src/agents/run_config.py`) lets you override settings for an entire run without modifying each agent:

```python
from agents import Agent, Runner, RunConfig, ModelSettings

agent = Agent(name="Assistant", instructions="Be helpful.")
result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(
        model="gpt-4o",
        model_settings=ModelSettings(temperature=0.7),
        workflow_name="my-app",
    ),
)
```

**Key RunConfig fields:**

| Field | Purpose |
|-------|---------|
| `model` | Override the model for all agents in this run |
| `model_provider` | Custom model provider (e.g., LiteLLM, custom endpoint) |
| `model_settings` | Override temperature, top_p, etc. globally (takes `ModelSettings`, not a dict) |
| `tracing_disabled` | Disable trace export |
| `workflow_name` | Name for the trace (visible in OpenAI Dashboard) |
| `trace_id` / `group_id` | Link traces across multiple runs |
| `handoff_input_filter` | Global input filter applied to all handoffs |
| `input_guardrails` / `output_guardrails` | Additional guardrails for all agents |

### ModelSettings.resolve() — How Overrides Work

A common question: "If I set `temperature` on both the Agent and the RunConfig, which wins?" The answer is in `ModelSettings.resolve()` (from `src/agents/model_settings.py`):

```python
# src/agents/model_settings.py — the real source
def resolve(self, override: ModelSettings | None) -> ModelSettings:
    """Produce a new ModelSettings by overlaying any non-None values
    from the override on top of this instance."""
    if override is None:
        return self

    changes = {
        field.name: getattr(override, field.name)
        for field in fields(self)
        if getattr(override, field.name) is not None
    }
    # Handle extra_args merging specially — merge dicts instead of replacing
    if self.extra_args is not None or override.extra_args is not None:
        merged_args = {}
        if self.extra_args:
            merged_args.update(self.extra_args)
        if override.extra_args:
            merged_args.update(override.extra_args)
        changes["extra_args"] = merged_args if merged_args else None

    return replace(self, **changes)
```

The resolution chain works like this:

```
Agent.model_settings (per-agent base)
       │
       ▼ resolve(RunConfig.model_settings)
       │
Merged ModelSettings (RunConfig non-None values override Agent values)
```

**Rule**: `RunConfig.model_settings` wins for any field that is not `None`. Only non-None values from the override are applied. This means you can set `temperature=0.7` globally in `RunConfig` while keeping per-agent `max_tokens` settings intact.

### Advanced RunConfig Features

**`call_model_input_filter`** — Intercept and modify model input before each LLM call:

```python
from agents import RunConfig, CallModelData, ModelInputData

async def limit_context(data: CallModelData) -> ModelInputData:
    # Trim input items if too long, add custom system prompt, etc.
    if len(data.model_data.input) > 50:
        data.model_data.input = data.model_data.input[-50:]
    return data.model_data

result = await Runner.run(
    agent, "Hello",
    run_config=RunConfig(call_model_input_filter=limit_context),
)
```

This is useful for staying within token limits or injecting dynamic context before each LLM call.

**`tool_error_formatter`** — Customize how tool errors are reported back to the LLM:

```python
from agents import RunConfig

async def format_tool_error(args) -> str | None:
    # Return None to use the SDK default message
    # Or return a custom message the LLM will see
    if args.kind == "approval_rejected":
        return f"The tool {args.tool_name} was rejected by the user."
    return None

result = await Runner.run(
    agent, "Hello",
    run_config=RunConfig(tool_error_formatter=format_tool_error),
)
```

**`trace_include_sensitive_data`** — Control what appears in traces:

```python
# Default: True (controlled by OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA env var)
result = await Runner.run(
    agent, "Hello",
    run_config=RunConfig(trace_include_sensitive_data=False),
    # Tool inputs/outputs and LLM generations will be redacted from traces
)
```

**`reasoning_item_id_policy`** — Control how reasoning items are preserved in multi-turn:

```python
# "preserve" (default): keep reasoning item IDs in conversation history
# "omit": strip reasoning item IDs to save tokens on next turn
result = await Runner.run(
    agent, "Complex reasoning task",
    run_config=RunConfig(reasoning_item_id_policy="omit"),
)
```

## 1.13 Putting It All Together: A Complete Agent

Here's a comprehensive example combining everything we've covered:

```python
import asyncio
from typing import Annotated
from pydantic import BaseModel
from agents import Agent, Runner, RunContextWrapper, function_tool, RunConfig, ModelSettings


class UserContext:
    def __init__(self, user_id: str, locale: str):
        self.user_id = user_id
        self.locale = locale


class TravelRecommendation(BaseModel):
    destination: str
    reason: str
    estimated_cost: str
    best_season: str


@function_tool
def search_flights(
    ctx: RunContextWrapper[UserContext],
    destination: Annotated[str, "The destination city"],
) -> str:
    """Search for available flights to a destination."""
    return f"Flights to {destination} from user {ctx.context.user_id}: $450 round trip"


@function_tool
def check_visa_requirements(
    destination: Annotated[str, "The destination country"],
    passport_country: Annotated[str, "The passport country code, e.g. 'US'"],
) -> str:
    """Check visa requirements for a destination."""
    return f"Visa for {destination}: Not required for {passport_country} passport holders"


def dynamic_instructions(
    ctx: RunContextWrapper[UserContext],
    agent: Agent[UserContext],
) -> str:
    instructions = "You are a travel assistant. Help users plan trips."
    if ctx.context.locale == "zh-CN":
        instructions += "\n请用中文回复。"
    return instructions


agent = Agent[UserContext](
    name="Travel Planner",
    instructions=dynamic_instructions,
    tools=[search_flights, check_visa_requirements],
    output_type=TravelRecommendation,
)


async def main():
    ctx = UserContext(user_id="u_456", locale="en-US")
    result = await Runner.run(
        agent,
        "I want to visit Tokyo. Can you check flights and visa requirements?",
        context=ctx,
        run_config=RunConfig(
            workflow_name="travel-planner",
            model_settings=ModelSettings(temperature=0.3),
        ),
    )
    rec = result.final_output_as(TravelRecommendation)
    print(f"Destination: {rec.destination}")
    print(f"Reason: {rec.reason}")
    print(f"Cost: {rec.estimated_cost}")
    print(f"Best Season: {rec.best_season}")
    print(f"Turns: {len(result.raw_responses)}")
    print(f"Items generated: {len(result.new_items)}")


if __name__ == "__main__":
    asyncio.run(main())
```

This agent demonstrates every concept from this chapter in a single runnable file:
- **Dynamic instructions** that adapt based on user context
- **Context-aware tools** that access `user_id` via `RunContextWrapper`
- **Structured output** enforced via Pydantic model
- **RunConfig** with tracing and model settings
- **Multi-turn execution** (the LLM will call both tools, then synthesize)

### What Happens When You Run This — A Walkthrough

When you run this agent, here's what you can observe from the `RunResult`:

```python
# After running the agent:
result = await Runner.run(agent, "I want to visit Tokyo...", context=ctx, ...)

# 1. The structured output
rec = result.final_output_as(TravelRecommendation)
# rec.destination → "Tokyo"
# rec.reason → "Rich cultural heritage, amazing food scene, and beautiful seasonal scenery"
# rec.estimated_cost → "$2,500-4,000 for a one-week trip"
# rec.best_season → "Spring (March-May) for cherry blossoms or Autumn (October-November)"

# 2. How many LLM calls were made?
print(f"Turns: {len(result.raw_responses)}")
# Likely 2: first turn calls both tools, second turn synthesizes the answer

# 3. What items were generated?
for item in result.new_items:
    print(f"  {type(item).__name__}")
# Likely:
#   ToolCallItem          ← LLM requested search_flights
#   ToolCallOutputItem    ← search_flights returned a result
#   ToolCallItem          ← LLM requested check_visa_requirements
#   ToolCallOutputItem    ← check_visa_requirements returned a result
#   MessageOutputItem     ← LLM produced the final structured output

# 4. How many tokens were used?
usage = result.context_wrapper.usage
print(f"API calls: {usage.requests}")
print(f"Input tokens: {usage.input_tokens}")
print(f"Output tokens: {usage.output_tokens}")

# 5. Which agent handled the request?
print(f"Agent: {result.last_agent.name}")
# "Travel Planner" (no handoffs, so it's the same agent)

# 6. Were any guardrails triggered?
print(f"Input guardrails: {len(result.input_guardrail_results)}")
print(f"Output guardrails: {len(result.output_guardrail_results)}")
# Both 0 — no guardrails configured on this agent
```

This is the debugging pattern you should internalize: after every run, you can inspect `result` to understand exactly what the agent did, how many turns it took, what tools it called, and how much it cost. The `RunResult` is your **complete audit trail**.

## 1.14 Debugging: Items System and Error Handling

### The Items System

Every run produces a list of `RunItem` objects in `result.new_items`. Understanding these is essential for debugging and building UIs:

```python
for item in result.new_items:
    match item:
        case MessageOutputItem():
            print(f"Message: {item.raw_item}")
        case ToolCallItem():
            print(f"Tool called: {item.raw_item.name}")
        case ToolCallOutputItem():
            print(f"Tool result: {item.raw_item.output}")
        case HandoffCallItem():
            print(f"Handoff to: {item.raw_item.name}")
        case HandoffOutputItem():
            print(f"Handoff from {item.source_agent.name} to {item.target_agent.name}")
        case ReasoningItem():
            print(f"Reasoning: {item.raw_item.summary}")
```

The item types (from `src/agents/items.py`):

| Item Type | What It Represents |
|-----------|-------------------|
| `MessageOutputItem` | A text message from the LLM |
| `ToolCallItem` | The LLM requesting a tool call |
| `ToolCallOutputItem` | The result of a tool execution |
| `HandoffCallItem` | The LLM requesting a handoff |
| `HandoffOutputItem` | The result of a handoff |
| `ReasoningItem` | Reasoning output from reasoning models |
| `ModelResponse` | A complete LLM response (wraps multiple items) |
| `ToolApprovalItem` | A tool call awaiting human approval |

### How Items Are Stored — The weakref Pattern

Every `RunItem` holds a reference to the `Agent` that produced it. But since agent graphs can be large, the SDK uses the same weakref pattern we saw in `RunResult.last_agent`:

```python
# src/agents/items.py — simplified
@dataclass
class RunItemBase(Generic[T], abc.ABC):
    agent: Agent[Any]       # Strong reference
    raw_item: T             # The raw Responses API item
    _agent_ref: weakref.ReferenceType[Agent[Any]] | None = field(...)

    def __post_init__(self) -> None:
        self._agent_ref = weakref.ref(self.agent)

    def release_agent(self) -> None:
        """Release the strong reference while keeping a weak reference."""
        agent = self.__dict__["agent"]
        # ... convert strong ref to weak ref
```

This is why `result.release_agents()` works — it walks through all items and calls `release_agent()` on each, converting strong references to weak references for garbage collection.

### Error Handling

The SDK defines a clear exception hierarchy (from `src/agents/exceptions.py`):

```
AgentsException              # Base for all SDK exceptions
├── MaxTurnsExceeded         # Agent loop exceeded max_turns
├── ModelBehaviorError       # LLM did something unexpected (e.g., invalid tool call)
├── UserError                # Misuse of the SDK API
├── InputGuardrailTripwireTriggered  # Input guardrail was triggered
├── OutputGuardrailTripwireTriggered # Output guardrail was triggered
├── ToolInputGuardrailTripwireTriggered  # Tool input guardrail triggered
├── ToolOutputGuardrailTripwireTriggered # Tool output guardrail triggered
├── ToolTimeoutError         # A tool execution timed out
└── MCPToolCancellationError # An MCP tool call was internally cancelled
```

Note the hierarchy is deeper than what you might initially expect — there are separate exception types for **tool guardrails** (`ToolInputGuardrailTripwireTriggered`, `ToolOutputGuardrailTripwireTriggered`) in addition to agent-level guardrails. This lets you catch tool-level and agent-level guardrail errors separately.

#### RunErrorDetails — Diagnostic Data on Errors

When an exception is raised during a run, the SDK attaches diagnostic data via `RunErrorDetails`:

```python
# src/agents/exceptions.py
@dataclass
class RunErrorDetails:
    """Data collected from an agent run when an exception occurs."""
    input: str | list[TResponseInputItem]
    new_items: list[RunItem]
    raw_responses: list[ModelResponse]
    last_agent: Agent[Any]
    context_wrapper: RunContextWrapper[Any]
    input_guardrail_results: list[InputGuardrailResult]
    output_guardrail_results: list[OutputGuardrailResult]
```

This is attached to `AgentsException` instances as `exception.run_data`. You can use it for logging, debugging, or building user-friendly error messages:

```python
from agents import AgentsException, MaxTurnsExceeded

try:
    result = await Runner.run(agent, "Complex task")
except MaxTurnsExceeded as e:
    details = e.run_data  # RunErrorDetails or None
    if details:
        print(f"Failed after {len(details.raw_responses)} turns")
        print(f"Last agent: {details.last_agent.name}")
        print(f"Items so far: {len(details.new_items)}")
```

#### ToolTimeoutError — Tool Execution Timeouts

When a function tool takes too long, the SDK raises `ToolTimeoutError`:

```python
# src/agents/exceptions.py
class ToolTimeoutError(AgentsException):
    tool_name: str
    timeout_seconds: float

    def __init__(self, tool_name: str, timeout_seconds: float):
        self.tool_name = tool_name
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Tool '{tool_name}' timed out after {timeout_seconds:g} seconds.")
```

You can set tool timeouts via `@function_tool(timeout_seconds=30)`:

```python
@function_tool(timeout_seconds=5)
def slow_api_call(query: str) -> str:
    """Call an external API with a 5-second timeout."""
    return requests.get(f"https://api.example.com/search?q={query}").text
```

You can handle `MaxTurnsExceeded` gracefully with error handlers:

```python
from agents import Runner, RunConfig, RunErrorHandlers

error_handlers = RunErrorHandlers(
    max_turns=lambda ctx, error: "I'm sorry, I couldn't complete that task in time."
)

result = await Runner.run(
    agent,
    "Complex task",
    run_config=RunConfig(max_turns=3),
    error_handlers=error_handlers,
)
```

## 1.15 The Full SDK Architecture (Reference)

Now that you've used the SDK, this architecture diagram will make much more sense. Come back to this whenever you need to remember how the pieces fit together:

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Your Application                              │
│                                                                      │
│   ┌──────────┐    ┌──────────┐    ┌──────────────┐                  │
│   │  Agent   │───▶│  Runner  │───▶│  RunResult   │                  │
│   └──────────┘    └────┬─────┘    └──────────────┘                  │
│                        │                                             │
│   ┌──────────┐    ┌────┴─────┐    ┌──────────────┐                  │
│   │  Tools   │    │ RunConfig│    │RunContextWrapper│                │
│   └──────────┘    └──────────┘    └──────────────┘                  │
│                                                                      │
│   ┌──────────┐    ┌──────────┐    ┌──────────────┐                  │
│   │Guardrails│    │ Handoffs │    │  Sessions    │                  │
│   └──────────┘    └──────────┘    └──────────────┘                  │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      SDK Core (run_internal/)                        │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐              │
│  │  run_loop.py │  │tool_execution│  │turn_resolution│              │
│  │  (orchestration)│  │  (call tools) │  │(process output)│           │
│  └──────────────┘  └──────────────┘  └───────────────┘              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐              │
│  │turn_preparation│ │  run_steps  │  │  guardrails   │              │
│  │(build prompts)│  │(next step)  │  │  (safety)     │              │
│  └──────────────┘  └──────────────┘  └───────────────┘              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐              │
│  │  streaming   │  │  approvals   │  │session_persist│              │
│  └──────────────┘  └──────────────┘  └───────────────┘              │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        Model Layer                                   │
│                                                                      │
│  ┌────────────────────┐  ┌─────────────────────────────────┐        │
│  │ OpenAI Responses   │  │ OpenAI Chat Completions         │        │
│  │ (default, primary) │  │ (legacy, via ChatCompletionsModel)│      │
│  └────────────────────┘  └─────────────────────────────────┘        │
│  ┌────────────────────┐  ┌─────────────────────────────────┐        │
│  │ LiteLLM Provider   │  │ Custom Model Provider           │        │
│  │ (multi-provider)   │  │ (implement Model interface)     │        │
│  └────────────────────┘  └─────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────────┘
```

## 1.16 Key Takeaways

| Concept | What It Is | Source Code | Where to Learn More |
|---------|-----------|------------|-------------------|
| `Agent` | Configuration dataclass | `src/agents/agent.py` | Chapter 2 |
| `Runner` | Execution engine (3 run modes) | `src/agents/run.py` | Chapter 4 |
| `RunResult` | Contains final_output, new_items, raw_responses | `src/agents/result.py` | Chapter 4 |
| `@function_tool` | Auto-generates tool schemas from Python signatures | `src/agents/tool.py`, `function_schema.py` | Chapter 3 |
| `TContext` | Generic context passed to tools/hooks (never to LLM) | `src/agents/run_context.py` | Chapter 5 |
| `output_type` | Enforce structured output via Pydantic/dataclass/TypedDict | `src/agents/agent_output.py` | Chapter 2 |
| `RunConfig` | Global overrides for model, tracing, guardrails | `src/agents/run_config.py` | Chapter 4 |
| `RunItem` | Typed objects for each event in a run | `src/agents/items.py` | Chapter 4 |
| Sessions | Three strategies: manual, SDK session, or server-managed | `src/agents/memory/` | Chapter 5 |
| Guardrails | Input/output safety checks that can halt execution | `src/agents/guardrail.py` | Chapter 7 |
| Handoffs | Agent-to-agent delegation within a single run | `src/agents/handoffs/` | Chapter 7 |

In the next chapter, we'll dive deep into the `Agent` dataclass — understanding every field, the `__post_init__` validation logic, the `clone()` method, and the design philosophy behind using a dataclass instead of a regular class.
