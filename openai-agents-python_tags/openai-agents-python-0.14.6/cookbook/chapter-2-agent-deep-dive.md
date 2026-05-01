# Chapter 2: Agent Deep Dive — Inside the Dataclass That Powers Everything

In Chapter 1 you used `Agent` as a configuration bag: set `name`, `instructions`, `tools`, and hand it to `Runner.run()`. This chapter goes deeper — we'll read the actual `src/agents/agent.py` source code to understand *why* it's a dataclass, *how* validation works, *what* each method does internally, and *how* the `AgentBase` → `Agent` hierarchy is designed.

## How to Read This Chapter

**Pass 1 — Build intuition (~20 min):** Read 2.1 → 2.3 → 2.5 → 2.6 in order. Skip source code walkthroughs and deep-dive subsections. Focus on diagrams, field tables, and the "Configuration vs State" insight.

**Pass 2 — Dive into source code (~40 min):** Go back and read the four 🔥 Source Code Walkthroughs in 2.2 → 2.4 → 2.7 → 2.9. By now you know the big picture, so the code reads easier.

**Pass 3 — Fill in the gaps:** Read selectively based on your needs:
- Agent validation details (all `__post_init__` checks)? → 2.4 (full walkthrough with GPT-5 compatibility)
- `clone()` and shallow copy gotchas? → 2.6
- `as_tool()` for multi-agent manager pattern? → 2.7 (includes streaming, structured input, approval propagation)
- Instructions vs Prompt — which to use? → 2.8 (includes `get_system_prompt()` + `get_prompt()` + comparison table)
- Hook system — RunHooks vs AgentHooks? → 2.9 (includes context type differences)
- MCP tool integration? → 2.10 (includes `mcp_config` options and lifecycle)
- `tool_use_behavior` and `reset_tool_choice`? → 2.11 (all four modes + loop prevention)
- Complete working example? → 2.12 (with post-run analysis)

**Key marker:** Sections marked with 🔥 are the highlights of this chapter — prioritize them.

## 2.1 Why a Dataclass, Not a Regular Class?

Look at `src/agents/agent.py`. The first thing you notice:

```python
@dataclass
class Agent(AgentBase, Generic[TContext]):
    """An agent is an AI model configured with instructions, tools, guardrails, handoffs and more."""
```

**Why `@dataclass` instead of a regular class?** Three reasons:

1. **Boilerplate elimination.** `Agent` has 16+ fields. A regular class would require a 16-parameter `__init__`, 16 `self.x = x` assignments, plus `__repr__` and `__eq__`. The dataclass generates all of that automatically.

2. **`dataclasses.replace()` for `clone()`.** This is the killer feature. The `clone()` method is a one-liner that creates a shallow copy with any number of fields overridden. Without dataclasses, you'd need `copy.deepcopy` plus manual overrides — fragile and error-prone.

3. **Design statement: Agent is data, not behavior.** A dataclass makes it explicit that `Agent` is a *configuration object* — it holds parameters, not runtime state. The mutable execution state lives separately in `RunState` (covered in Chapter 5).

Here's the contrast:

```
┌──────────────────────────────────────────┐
│  Regular class: 30+ lines of boilerplate │
│  • Manual __init__ with 16 parameters    │
│  • Manual __eq__ comparing 16 fields     │
│  • Manual __repr__ printing 16 fields    │
│  • clone() requires copy + manual merge  │
└──────────────────────────────────────────┘
                    vs.
┌──────────────────────────────────────────┐
│  Dataclass: fields only, auto-generated  │
│  • __init__: automatic                   │
│  • __eq__: automatic                     │
│  • __repr__: automatic                   │
│  • clone(): dataclasses.replace(self,…)  │
└──────────────────────────────────────────┘
```

## 2.2 The AgentBase → Agent Hierarchy

Before we read source code, let's see the inheritance structure at a glance:

```
AgentBase (dataclass)
│   Fields shared with RealtimeAgent:
│   • name: str
│   • handoff_description: str | None
│   • tools: list[Tool]
│   • mcp_servers: list[MCPServer]
│   • mcp_config: MCPConfig
│
│   Methods:
│   • get_mcp_tools() → fetches tools from MCP servers
│   • get_all_tools() → MCP tools + enabled function tools
│
└─── Agent (dataclass)
     Fields specific to text-based agents:
     • instructions, prompt, handoffs
     • model, model_settings
     • input_guardrails, output_guardrails
     • output_type, hooks
     • tool_use_behavior, reset_tool_choice
     
     Methods:
     • __post_init__() → validates all fields
     • clone() → shallow copy with overrides
     • as_tool() → convert agent to a callable tool
     • get_system_prompt() → resolve instructions to string
     • get_prompt() → resolve prompt for OpenAI Responses API
```

**Why split `AgentBase` and `Agent`?** Because `RealtimeAgent` (for voice/realtime use cases) shares the same base fields (`name`, `tools`, `mcp_servers`) but has different execution fields. The split avoids duplication. Note that `Agent` **inherits all `AgentBase` fields** — when you create an `Agent`, you get both `name`/`tools`/`mcp_servers` (from `AgentBase`) *and* `instructions`/`model`/`handoffs` (from `Agent`).

### 🔥 Source Code Walkthrough: AgentBase.get_all_tools()

One of the most important methods on `AgentBase` is `get_all_tools()` — it determines what tools the LLM actually sees. Let's read the real source:

```python
# src/agents/agent.py — the real code
async def get_all_tools(self, run_context: RunContextWrapper[TContext]) -> list[Tool]:
    """All agent tools, including MCP tools and function tools."""
    mcp_tools = await self.get_mcp_tools(run_context)

    async def _check_tool_enabled(tool: Tool) -> bool:
        if not isinstance(tool, FunctionTool):
            return True
        attr = tool.is_enabled
        if isinstance(attr, bool):
            return attr
        res = attr(run_context, self)
        if inspect.isawaitable(res):
            return bool(await res)
        return bool(res)

    results = await asyncio.gather(*(_check_tool_enabled(t) for t in self.tools))
    enabled: list[Tool] = [t for t, ok in zip(self.tools, results, strict=False) if ok]

    all_tools: list[Tool] = prune_orphaned_tool_search_tools([*mcp_tools, *enabled])
    _validate_codex_tool_name_collisions(all_tools)
    return all_tools
```

Key insights:

1. **MCP tools are fetched dynamically** — `get_mcp_tools()` calls out to MCP servers every time the agent runs. This means tools from MCP can change between runs without modifying the agent.
2. **`is_enabled` can be a callable** — a tool can be conditionally enabled based on the run context (e.g., only show admin tools to admin users). The callable can even be async.
3. **Orphaned tool-search tools are pruned** — if a tool references a tool-search tool that no longer exists, it's automatically removed. This prevents the LLM from seeing broken tool references.
4. **Codex tool name collisions are validated** — duplicate names among Codex tools cause a `UserError` before the run starts, not a confusing LLM failure later.

## 2.3 Field Overview: What's on Agent, and When Do You Need It?

Rather than listing all fields at once, here they are organized by when you'll actually use them:

**Fields you set from day one:**

| Field | Type | Default | What it does |
|-------|------|---------|-------------|
| `name` | `str` | *(required)* | Agent identity — shown in logs, traces, and handoff menus |
| `instructions` | `str \| Callable \| None` | `None` | System prompt, or a function `(ctx, agent) → str` |
| `model` | `str \| Model \| None` | `None` | Which LLM to use (default: `gpt-4.1`) |
| `tools` | `list[Tool]` | `[]` | Tools the agent can call |

**Fields you'll need as your agent grows:**

| Field | Type | Default | What it does |
|-------|------|---------|-------------|
| `output_type` | `type \| AgentOutputSchemaBase \| None` | `None` | Parse output into a structured type (Chapter 1 §1.7) |
| `handoffs` | `list[Agent \| Handoff]` | `[]` | Delegate to other agents (Chapter 7) |
| `tool_use_behavior` | `Literal[...] \| StopAtTools \| Callable` | `"run_llm_again"` | What happens after a tool call (§2.11) |
| `model_settings` | `ModelSettings` | *default settings* | Per-agent temperature, top_p, tool_choice, etc. |
| `prompt` | `Prompt \| DynamicPromptFunction \| None` | `None` | OpenAI Responses API prompt configuration (§2.8) |

**Fields for production hardening:**

| Field | Type | Default | What it does |
|-------|------|---------|-------------|
| `hooks` | `AgentHooks \| None` | `None` | Lifecycle callbacks for this specific agent (§2.9) |
| `input_guardrails` | `list[InputGuardrail]` | `[]` | Validate input before the agent runs |
| `output_guardrails` | `list[OutputGuardrail]` | `[]` | Validate output before returning |
| `reset_tool_choice` | `bool` | `True` | Reset `tool_choice` after each tool call to prevent loops (§2.11) |

**Fields inherited from AgentBase:**

| Field | Type | Default | What it does |
|-------|------|---------|-------------|
| `handoff_description` | `str \| None` | `None` | Description shown when this agent is a handoff target |
| `mcp_servers` | `list[MCPServer]` | `[]` | MCP servers providing tools (§2.10) |
| `mcp_config` | `MCPConfig` | `{}` | Configuration for MCP tool schemas and error handling (§2.10) |

## 2.4 Validation: The `__post_init__` Method

Dataclasses auto-generate `__init__`, but what about validation? The answer is `__post_init__` — a special method the dataclass calls automatically right after `__init__` finishes. It's the perfect place to catch configuration errors early.

### 🔥 Source Code Walkthrough: Agent.__post_init__()

Let's read the actual validation logic from `src/agents/agent.py`:

```python
# src/agents/agent.py — simplified from the real source
def __post_init__(self):
    from typing import get_origin

    # 1. Name must be a string (required field)
    if not isinstance(self.name, str):
        raise TypeError(f"Agent name must be a string, got {type(self.name).__name__}")

    # 2. handoff_description must be string or None
    if self.handoff_description is not None and not isinstance(self.handoff_description, str):
        raise TypeError(
            f"Agent handoff_description must be a string or None, "
            f"got {type(self.handoff_description).__name__}"
        )

    # 3. instructions must be str, callable, or None
    if (
        self.instructions is not None
        and not isinstance(self.instructions, str)
        and not callable(self.instructions)
    ):
        raise TypeError(
            f"Agent instructions must be a string, callable, or None, "
            f"got {type(self.instructions).__name__}"
        )

    # 4. prompt must be Prompt, DynamicPromptFunction, or None
    if self.prompt is not None and not callable(self.prompt) and not hasattr(self.prompt, "get"):
        raise TypeError(
            f"Agent prompt must be a Prompt, DynamicPromptFunction, or None, "
            f"got {type(self.prompt).__name__}"
        )

    # 5. model must be str, Model instance, or None
    if self.model is not None and not isinstance(self.model, str):
        if not isinstance(self.model, Model):
            raise TypeError(
                f"Agent model must be a string, Model, or None, got {type(self.model).__name__}"
            )

    # 6. model_settings must be a ModelSettings instance (not a dict!)
    if not isinstance(self.model_settings, ModelSettings):
        raise TypeError(
            f"Agent model_settings must be a ModelSettings instance, "
            f"got {type(self.model_settings).__name__}"
        )

    # 7. output_type must be a type, AgentOutputSchemaBase, or None
    if self.output_type is not None:
        if not (
            isinstance(self.output_type, type | AgentOutputSchemaBase)
            or get_origin(self.output_type) is not None
        ):
            raise TypeError(
                f"Agent output_type must be a type, AgentOutputSchemaBase, or None, "
                f"got {type(self.output_type).__name__}"
            )

    # 8. hooks must be an AgentHooksBase instance or None
    if self.hooks is not None:
        if not isinstance(self.hooks, AgentHooksBase):
            raise TypeError(
                f"Agent hooks must be an AgentHooks instance or None, "
                f"got {type(self.hooks).__name__}"
            )

    # 9. tool_use_behavior must be one of: string literal, dict (StopAtTools), or callable
    if (
        not (
            isinstance(self.tool_use_behavior, str)
            and self.tool_use_behavior in ["run_llm_again", "stop_on_first_tool"]
        )
        and not isinstance(self.tool_use_behavior, dict)
        and not callable(self.tool_use_behavior)
    ):
        raise TypeError(
            f"Agent tool_use_behavior must be 'run_llm_again', 'stop_on_first_tool', "
            f"StopAtTools dict, or callable, got {type(self.tool_use_behavior).__name__}"
        )

    # 10. GPT-5 default model settings compatibility check
    if (
        self.model is not None
        and is_gpt_5_default() is True
        and (
            isinstance(self.model, str) is False
            or gpt_5_reasoning_settings_required(self.model) is False
        )
        and self.model_settings == get_default_model_settings()
    ):
        self.model_settings = ModelSettings()
```

Key insights:

1. **Fail fast, not fail later.** Every field is validated at construction time, not when `Runner.run()` is called. If you pass `model_settings={"temperature": 0.7}` (a dict instead of `ModelSettings`), you get a `TypeError` immediately — not a cryptic LLM API error 10 seconds later.
2. **`get_origin()` handles generic types.** The `output_type` check uses `get_origin(self.output_type) is not None` to allow parameterized generics like `list[CityInfo]` — these aren't `type` instances, but `get_origin()` returns a non-None value for them.
3. **GPT-5 compatibility is handled silently.** If the default model is GPT-5 but you specify a non-GPT-5 model, the `model_settings` are automatically reset to generic defaults. This prevents confusing "incompatible settings" errors. This is the only `__post_init__` check that *mutates* the agent rather than raising an error.
4. **`tool_use_behavior` accepts three forms.** A string literal, a `StopAtTools` dict (TypedDict with `stop_at_tool_names`), or a custom callable. All three are validated.
5. **`prompt` is validated with `hasattr(prompt, "get")`.** The `Prompt` type is a `TypedDict`, and `TypedDict` instances are dicts — so the check uses `hasattr(prompt, "get")` to verify it's dict-like. Callables are also accepted (for `DynamicPromptFunction`).

## 2.5 Configuration vs State: The Core Design Split

The single most important concept in this chapter:

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Instance                            │
│  (Immutable Configuration — you create this once)           │
│                                                             │
│  name: "Travel Planner"                                     │
│  instructions: "You help users plan trips."                 │
│  tools: [search_flights, check_visa]                        │
│  output_type: TravelRecommendation                          │
│  model_settings: ModelSettings(temperature=0.3)             │
│                                                             │
│  This does NOT change during execution!                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ passed to Runner.run()
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    RunState                                  │
│  (Mutable Execution State — the SDK manages this)           │
│                                                             │
│  _current_turn: 3                                           │
│  _current_agent: <Agent "Travel Planner">                   │
│  _model_responses: [response1, response2, response3]        │
│  _generated_items: [msg, tool_call, tool_output, msg]       │
│  _context: RunContextWrapper(context=UserContext(...))       │
│                                                             │
│  This changes on every turn of the loop!                    │
└─────────────────────────────────────────────────────────────┘
```

**The Agent is not the conversation.** The Agent defines *how* the conversation should happen; `RunState` tracks *what actually happened*. This means:

- The same `Agent` instance can be reused across multiple runs
- You can pass the same `Agent` to `Runner.run()` twice with different inputs, and they're independent
- The agent's `tools` list is static — tools don't get added or removed mid-run (but `is_enabled` can hide them dynamically)

The `RunState` is covered in depth in Chapter 5 — it can be serialized to JSON and resumed later, which is the foundation for human-in-the-loop tool approval flows.

## 2.6 The `clone()` Method: Immutable Pattern for Variations

Agents come with a `clone()` method for creating variations without modifying the original:

```python
def clone(self, **kwargs: Any) -> Agent[TContext]:
    """Make a copy of the agent, with the given arguments changed."""
    return dataclasses.replace(self, **kwargs)
```

Under the hood, it's just `dataclasses.replace()` — a shallow copy with overrides. Here's a practical pattern:

```python
from agents import Agent, function_tool

@function_tool
def search_flights(destination: str) -> str:
    """Search for flights to a destination."""
    return f"Flights to {destination}: $450 round trip"

@function_tool
def search_hotels(destination: str) -> str:
    """Search for hotels in a destination."""
    return f"Hotels in {destination}: from $120/night"

@function_tool
def execute_python(code: str) -> str:
    """Execute Python code and return the output."""
    return "executed"

base_agent = Agent(
    name="Assistant",
    instructions="You are helpful.",
    tools=[search_flights],
)

travel_agent = base_agent.clone(
    name="Travel Planner",
    instructions="You help users plan trips. Use the search tools.",
    tools=[search_flights, search_hotels],
)

code_agent = base_agent.clone(
    name="Code Assistant",
    instructions="You write and run Python code.",
    tools=[search_flights, execute_python],
)

debug_agent = base_agent.clone(
    name="Debug Assistant",
    instructions="You debug Python code.",
    tools=[search_flights, execute_python],
    model_settings=ModelSettings(temperature=0.1),
)
```

This produces a clean family tree:

```
base_agent (tools: [search_flights])
    ├─→ clone() → travel_agent (tools: [search_flights, search_hotels])
    ├─→ clone() → code_agent (tools: [search_flights, execute_python])
    └─→ clone() → debug_agent (tools: [search_flights, execute_python], temp=0.1)
```

**Important: `clone()` is a shallow copy.** Mutable attributes like `tools` and `handoffs` are shared between the original and the clone unless you explicitly override them. If you need independent lists, pass new lists:

```python
# WRONG: both agents share the same list object
agent_a = base_agent.clone()
agent_a.tools.append(new_tool)  # This also modifies base_agent.tools!

# RIGHT: pass a new list to the clone
agent_a = base_agent.clone(tools=[*base_agent.tools, new_tool])
```

The shallow copy behavior also means that immutable fields (strings, numbers, `None`) are completely independent — you can change `name` or `instructions` on a clone without affecting the original. The danger is only with mutable container types (`list`, `dict`, and objects with internal state).

## 2.7 The `as_tool()` Method: Agents as Tools

One of the most powerful features: convert any agent into a tool that another agent can call. This is the foundation of the **manager pattern** in multi-agent systems.

### How `as_tool()` Differs from Handoffs

| Aspect | Handoff | `as_tool()` |
|--------|---------|-------------|
| Control | New agent takes over the conversation | Calling agent stays in control |
| Input | Full conversation history | Generated input (not history) |
| Result | New agent produces final output | Result returned to calling agent as tool output |
| Analogy | Transferring a phone call | Calling a consultant and coming back with the answer |
| When to use | Specialist should own the conversation | Specialist provides input, caller synthesizes |

### Example: Manager Pattern

```python
from agents import Agent, Runner

booking_agent = Agent(
    name="Booking Expert",
    instructions="You handle flight and hotel bookings. Return a concise summary.",
)

refund_agent = Agent(
    name="Refund Expert",
    instructions="You handle refund requests. Return a concise summary.",
)

manager_agent = Agent(
    name="Customer Service Manager",
    instructions=(
        "You are the primary contact for customers. "
        "When they need booking help, call the booking expert tool. "
        "When they need refund help, call the refund expert tool. "
        "Synthesize the results into a helpful response."
    ),
    tools=[
        booking_agent.as_tool(
            tool_name="booking_expert",
            tool_description="Handles booking questions and requests.",
        ),
        refund_agent.as_tool(
            tool_name="refund_expert",
            tool_description="Handles refund questions and requests.",
        ),
    ],
)

result = await Runner.run(manager_agent, "I need to book a flight to Tokyo")
```

### 🔥 Source Code Walkthrough: as_tool() Internals

Let's trace what happens when you call `agent.as_tool()`:

```
agent.as_tool(tool_name="expert", tool_description="...")
       │
       ▼
1. Build JSON schema for tool input (AgentAsToolInput by default,
   or custom Pydantic/dataclass type if `parameters` is provided)
       │
       ▼
2. Define _run_agent_impl(context, input_json) — the actual tool function:
   a. Parse and validate input_json via TypeAdapter
   b. Resolve the agent's input (from structured params or plain text)
   c. Call Runner.run(starting_agent=self, input=resolved_input, ...)
   d. Extract output: custom_output_extractor, or last message, or final_output
       │
       ▼
3. Wrap _run_agent_impl in a FunctionTool via _build_wrapped_function_tool()
       │
       ▼
4. Set _is_agent_tool = True and _agent_instance = self on the tool
       │
       ▼
5. Return the FunctionTool — it can be added to any other agent's tools list
```

The key code (simplified):

```python
# src/agents/agent.py — simplified
def as_tool(self, tool_name, tool_description, ...) -> FunctionTool:
    # Step 1: Build the schema
    if parameters is None:
        params_adapter = TypeAdapter(AgentAsToolInput)
        params_schema = ensure_strict_json_schema(params_adapter.json_schema())
    else:
        if not _is_supported_parameters(parameters):
            raise TypeError("Agent tool parameters must be a dataclass or Pydantic model type.")
        params_adapter = TypeAdapter(parameters)
        params_schema = ensure_strict_json_schema(params_adapter.json_schema())

    # Step 2: The implementation that runs when the LLM "calls" this tool
    async def _run_agent_impl(context: ToolContext, input_json: str) -> Any:
        json_data = _parse_function_tool_json_input(tool_name=..., input_json=input_json)
        parsed_params = params_adapter.validate_python(json_data)
        params_data = _normalize_tool_input(parsed_params, tool_name)
        resolved_input = await resolve_agent_tool_input(params=params_data, ...)

        # Run the nested agent
        run_result = await Runner.run(
            starting_agent=cast(Agent[Any], self),
            input=resolved_input,
            context=nested_context,
            run_config=resolved_run_config,
            max_turns=resolved_max_turns,
        )

        # Extract output
        if custom_output_extractor:
            return await custom_output_extractor(run_result)
        # Default: return the last text message or final_output
        for item in reversed(run_result.new_items):
            if isinstance(item, MessageOutputItem):
                text_output = ItemHelpers.text_message_output(item)
                if text_output:
                    return text_output
        return run_result.final_output

    # Step 3-5: Wrap in FunctionTool and return
    run_agent_tool = _build_wrapped_function_tool(
        name=tool_name_resolved,
        description=tool_description_resolved,
        params_json_schema=params_schema,
        invoke_tool_impl=_run_agent_impl,
        ...
    )
    run_agent_tool._is_agent_tool = True
    run_agent_tool._agent_instance = self
    return run_agent_tool
```

Key insights:

1. **The nested agent runs as a full `Runner.run()` call** — it gets its own agent loop, its own turn counter, its own guardrails. It's a complete sub-run, not just a function call.
2. **Input is parsed and validated** — the LLM's JSON arguments are validated against `AgentAsToolInput` (which has a single `input` string field) or your custom `parameters` type.
3. **Output extraction is smart by default** — it walks `new_items` in reverse and returns the last text message. This usually gives the most useful response. Use `custom_output_extractor` if you need something different.
4. **`_is_agent_tool = True`** — this metadata flag lets other parts of the SDK (tracing, debugging) identify that this tool is actually a nested agent, not a regular function tool.
5. **A fresh `ToolContext` is created** — the nested agent gets its own context to avoid sharing approval state with the parent run. This prevents unintended approval propagation.

### as_tool() Parameters — The Full Surface

The `as_tool()` method has many optional parameters for fine-grained control:

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `tool_name` | `str \| None` | Agent's name | Tool name shown to the LLM |
| `tool_description` | `str \| None` | `""` | Tool description shown to the LLM |
| `custom_output_extractor` | `Callable \| None` | `None` | Custom function to extract output from `RunResult` |
| `is_enabled` | `bool \| Callable` | `True` | Dynamically enable/disable this agent tool |
| `on_stream` | `Callable \| None` | `None` | Receive streaming events from nested agent |
| `run_config` | `RunConfig \| None` | `None` | RunConfig for the nested agent run |
| `max_turns` | `int \| None` | `10` | Max turns for the nested agent run |
| `hooks` | `RunHooks \| None` | `None` | Run hooks for the nested agent run |
| `previous_response_id` | `str \| None` | `None` | For server-managed conversation chaining |
| `conversation_id` | `str \| None` | `None` | For OpenAI conversation grouping |
| `session` | `Session \| None` | `None` | Session for the nested agent run |
| `failure_error_function` | `ToolErrorFunction \| None` | `default_tool_error_function` | How to handle nested agent failures |
| `needs_approval` | `bool \| Callable` | `False` | Require human approval before nested run |
| `parameters` | `type \| None` | `None` | Custom input type (Pydantic/dataclass) |
| `input_builder` | `StructuredToolInputBuilder \| None` | `None` | Custom function to build nested agent input |
| `include_input_schema` | `bool` | `False` | Include JSON schema in structured input |

### Structured Input for Agent-as-Tool

By default, the LLM provides a simple string as input to the nested agent. But you can define structured input with `parameters`:

```python
from pydantic import BaseModel

class BookingRequest(BaseModel):
    destination: str
    dates: str
    budget: str

booking_tool = booking_agent.as_tool(
    tool_name="booking_expert",
    tool_description="Handles booking questions with specific details.",
    parameters=BookingRequest,
    include_input_schema=True,
)
```

When `parameters` is provided, the LLM must provide a JSON object matching your schema. The SDK then converts it to a prompt for the nested agent. With `include_input_schema=True`, the schema is included in the prompt so the nested agent understands the structured data.

### Streaming from Nested Agents

When you provide `on_stream`, the nested agent runs in streaming mode and events are dispatched to your callback:

```python
async def handle_stream_event(event: AgentToolStreamEvent):
    print(f"[{event['agent'].name}] {type(event['event']).__name__}")

booking_tool = booking_agent.as_tool(
    tool_name="booking_expert",
    tool_description="Handles bookings.",
    on_stream=handle_stream_event,
)
```

The `AgentToolStreamEvent` is a `TypedDict` with three fields:

| Field | Type | What it contains |
|-------|------|-----------------|
| `event` | `StreamEvent` | The streaming event from the nested agent |
| `agent` | `Agent[Any]` | The nested agent that emitted the event |
| `tool_call` | `ResponseFunctionToolCall \| None` | The originating tool call, if available |

Internally, events are dispatched via an `asyncio.Queue` — a background task reads from the queue and calls your handler. This ensures slow handlers don't block event consumption.

## 2.8 Instructions vs Prompt: Two Ways to Configure System Behavior

The `Agent` class has two fields for configuring what the agent knows: `instructions` and `prompt`. They serve different purposes and come from different paradigms.

### `instructions` — The Classic System Prompt

As we saw in Chapter 1 §1.9, `instructions` is the system prompt. It can be a static string, a callable, or `None`. The callable form is called **every turn** via `get_system_prompt()` (see Chapter 1 §1.9 for the full source code walkthrough).

### `prompt` — OpenAI Responses API Prompt Templates

The `prompt` field is specific to the OpenAI Responses API. It references a prompt template created on the OpenAI platform:

```python
from agents import Agent

agent = Agent(
    name="Prompted Assistant",
    prompt={
        "id": "pmpt_123",
        "version": "1",
        "variables": {"poem_style": "haiku"},
    },
)
```

You can also make it dynamic with a `DynamicPromptFunction`:

```python
from agents import Agent, GenerateDynamicPromptData

async def build_prompt(data: GenerateDynamicPromptData):
    ctx = data.context.context
    return {
        "id": ctx.prompt_id,
        "version": "1",
        "variables": {"poem_style": ctx.poem_style},
    }

agent = Agent(name="Prompted Assistant", prompt=build_prompt)
```

### `get_prompt()` — How Prompts Are Resolved

The `get_prompt()` method on `Agent` resolves the `prompt` field to a `ResponsePromptParam`:

```python
# src/agents/agent.py — the real code
async def get_prompt(
    self, run_context: RunContextWrapper[TContext]
) -> ResponsePromptParam | None:
    """Get the prompt for the agent."""
    from ._public_agent import get_public_agent
    return await PromptUtil.to_model_input(
        self.prompt,
        run_context,
        cast(Agent[TContext], get_public_agent(self)),
    )
```

Internally, `PromptUtil.to_model_input()` handles both static `Prompt` dicts and `DynamicPromptFunction` callables, much like `get_system_prompt()` handles both string and callable instructions.

### Instructions vs Prompt — When to Use Which

| Aspect | `instructions` | `prompt` |
|--------|---------------|----------|
| Type | `str \| Callable \| None` | `Prompt \| DynamicPromptFunction \| None` |
| Paradigm | Classic system prompt | OpenAI Platform prompt templates |
| Provider | Any LLM provider | OpenAI only (Responses API) |
| Source | Defined in code | Defined on OpenAI Platform, referenced by ID |
| Dynamic | Yes, via callable | Yes, via `DynamicPromptFunction` |
| Versioning | Manual (code changes) | Platform-managed (version field) |
| Variables | No built-in variable system | Built-in template variables |
| Use case | Custom, provider-agnostic | Teams using OpenAI Platform prompt management |

**Can you use both?** Yes. The SDK calls `get_system_prompt()` and `get_prompt()` **concurrently** (via `asyncio.gather`) at the start of each turn, and passes both results to the LLM API. The `instructions` becomes the system prompt text, while `prompt` becomes the `prompt` parameter in the Responses API call. In practice, you typically use one or the other, not both.

**Important:** When `prompt` is set and `model` is not explicitly specified on the agent, the `model` parameter is omitted from the API call — the platform's prompt template determines which model to use. This is because prompt templates on the OpenAI Platform are associated with a specific model.

## 2.9 Lifecycle Hooks: RunHooks vs AgentHooks

The SDK provides two hook scopes for observing agent lifecycle events. They have the same callbacks, but different scopes:

```
┌─────────────────────────────────────────────────────────────────┐
│  RunHooks (passed to Runner.run)                                │
│  • Observes the ENTIRE run — all agents, all turns              │
│  • Good for: logging, metrics, tracing                          │
│                                                                 │
│  on_llm_start(ctx, agent, system_prompt, input_items)           │
│  on_llm_end(ctx, agent, response)                               │
│  on_agent_start(AgentHookContext, agent)                         │
│  on_agent_end(AgentHookContext, agent, output)                   │
│  on_tool_start(ctx, agent, tool)                                │
│  on_tool_end(ctx, agent, tool, result)                          │
│  on_handoff(ctx, from_agent, to_agent)                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  AgentHooks (set on agent.hooks)                                │
│  • Observes ONE specific agent only                             │
│  • Good for: agent-specific side effects (prefetch, notify)     │
│                                                                 │
│  on_start(AgentHookContext, agent)                               │
│  on_end(AgentHookContext, agent, output)                         │
│  on_llm_start(ctx, agent, system_prompt, input_items)           │
│  on_llm_end(ctx, agent, response)                               │
│  on_tool_start(ctx, agent, tool)                                │
│  on_tool_end(ctx, agent, tool, result)                          │
│  on_handoff(ctx, agent, source)  ← source = who handed off     │
└─────────────────────────────────────────────────────────────────┘
```

### 🔥 Source Code Walkthrough: Hook Callback Signatures

Let's read the actual callback signatures from `src/agents/lifecycle.py`:

```python
# src/agents/lifecycle.py — the real code

class RunHooksBase(Generic[TContext, TAgent]):
    """Run-wide lifecycle callbacks."""

    async def on_llm_start(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent[TContext],
        system_prompt: str | None,
        input_items: list[TResponseInputItem],
    ) -> None: ...

    async def on_llm_end(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent[TContext],
        response: ModelResponse,
    ) -> None: ...

    async def on_agent_start(
        self, context: AgentHookContext[TContext], agent: TAgent
    ) -> None: ...

    async def on_agent_end(
        self, context: AgentHookContext[TContext], agent: TAgent, output: Any
    ) -> None: ...

    async def on_handoff(
        self,
        context: RunContextWrapper[TContext],
        from_agent: TAgent,
        to_agent: TAgent,
    ) -> None: ...

    async def on_tool_start(
        self, context: RunContextWrapper[TContext], agent: TAgent, tool: Tool
    ) -> None: ...

    async def on_tool_end(
        self, context: RunContextWrapper[TContext], agent: TAgent, tool: Tool, result: str
    ) -> None: ...


class AgentHooksBase(Generic[TContext, TAgent]):
    """Agent-scoped lifecycle callbacks."""

    async def on_start(
        self, context: AgentHookContext[TContext], agent: TAgent
    ) -> None: ...

    async def on_end(
        self, context: AgentHookContext[TContext], agent: TAgent, output: Any
    ) -> None: ...

    async def on_handoff(
        self,
        context: RunContextWrapper[TContext],
        agent: TAgent,
        source: TAgent,
    ) -> None: ...

    async def on_tool_start(
        self, context: RunContextWrapper[TContext], agent: TAgent, tool: Tool
    ) -> None: ...

    async def on_tool_end(
        self, context: RunContextWrapper[TContext], agent: TAgent, tool: Tool, result: str
    ) -> None: ...

    async def on_llm_start(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent[TContext],
        system_prompt: str | None,
        input_items: list[TResponseInputItem],
    ) -> None: ...

    async def on_llm_end(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent[TContext],
        response: ModelResponse,
    ) -> None: ...
```

Key insights:

1. **Context types differ by event.** `on_agent_start`/`on_agent_end` receive `AgentHookContext` (which wraps your context + shared usage state), while `on_tool_start`/`on_tool_end` and `on_llm_start`/`on_llm_end` receive `RunContextWrapper` (or `ToolContext` for function tools, which adds `tool_call_id`, `tool_name`). See Chapter 1 §1.8 for the `RunContextWrapper` vs `AgentHookContext` comparison.
2. **`on_handoff` has different parameter order.** `RunHooks.on_handoff(ctx, from_agent, to_agent)` tells you who handed off and who received. `AgentHooks.on_handoff(ctx, agent, source)` tells you *this* agent received a handoff from `source`.
3. **All callbacks are async.** Even if your implementation is synchronous, the SDK always `await`s them. This is because the SDK's run loop is fully async.
4. **You don't have to implement all callbacks.** Both base classes define all methods as no-ops (`pass`). You only override the ones you need.

### Practical Example: Combined RunHooks + AgentHooks

```python
from agents import Agent, RunHooks, Runner, AgentHooksBase

class LoggingHooks(RunHooks):
    async def on_llm_end(self, context, agent, response):
        print(f"[Run] {agent.name} produced {len(response.output)} items")

    async def on_tool_start(self, context, agent, tool):
        print(f"[Run] {agent.name} calling tool: {tool.name}")

class TravelAgentHooks(AgentHooksBase):
    async def on_start(self, context, agent):
        print(f"[Travel Agent] Starting {agent.name}")

    async def on_tool_start(self, context, agent, tool):
        print(f"[Travel Agent] This agent is calling: {tool.name}")

travel_agent = Agent(
    name="Travel Planner",
    instructions="Help with travel.",
    tools=[search_flights],
    hooks=TravelAgentHooks(),
)

result = await Runner.run(
    travel_agent,
    "Book a flight to Tokyo",
    hooks=LoggingHooks(),
)
```

In this setup, both `LoggingHooks` and `TravelAgentHooks` fire for the same events — the `RunHooks` observe globally, and the `AgentHooks` observe only for `travel_agent`.

## 2.10 MCP Integration: `mcp_servers` and `mcp_config`

The `mcp_servers` field lets you attach Model Context Protocol servers to an agent. Every time the agent runs, the SDK fetches available tools from these servers and merges them with the agent's `tools` list.

```python
from agents import Agent
from agents.mcp import MCPServerStdio

server = MCPServerStdio(
    name="filesystem",
    params={"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]},
)

await server.connect()

agent = Agent(
    name="File Assistant",
    instructions="Help users with files.",
    mcp_servers=[server],
)

# When the agent runs, it will include tools from the MCP server
result = await Runner.run(agent, "List files in /tmp")

# Don't forget to clean up
await server.cleanup()
```

### MCP Tool Lifecycle

```
Agent starts a run
       │
       ▼
get_mcp_tools(run_context) → calls each MCP server's list_tools()
       │
       ▼
MCP schemas are converted to FunctionTool objects
       │
       ▼
MCP tools are merged with the agent's static tools
       │
       ▼
Disabled tools are filtered out (is_enabled check)
       │
       ▼
The combined tool list is sent to the LLM
```

**Important:** You are responsible for managing the MCP server lifecycle — call `server.connect()` before passing it to the agent, and `server.cleanup()` when done. Consider using `MCPServerManager` from `agents.mcp` to keep connect/cleanup in the same task.

### `mcp_config` — Fine-Tuning MCP Behavior

The `MCPConfig` TypedDict has two options:

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `convert_schemas_to_strict` | `bool` | `False` | Attempt to convert MCP schemas to OpenAI strict mode |
| `failure_error_function` | `ToolErrorFunction \| None` | `default_tool_error_function` | How to handle MCP tool failures |

When `convert_schemas_to_strict` is `True`, the SDK attempts to make MCP tool schemas compatible with OpenAI's strict Structured Outputs mode. This is a best-effort conversion — some schemas may not be convertible.

When an MCP tool fails, `failure_error_function` determines what happens. The default (`default_tool_error_function`) returns an error message to the LLM so it can retry or adapt. If set to `None`, the exception propagates and the run fails.

## 2.11 Tool Use Behavior and Loop Prevention

### `tool_use_behavior` — Four Modes

The `tool_use_behavior` field controls what happens after the LLM calls a tool:

| Mode | Type | Behavior | When to Use |
|------|------|----------|-------------|
| `"run_llm_again"` | `str` | Loop back to LLM with tool results (default) | General purpose — LLM synthesizes the answer |
| `"stop_on_first_tool"` | `str` | First tool's output becomes `final_output` | Tools are the answer (e.g., lookups, calculations) |
| `StopAtTools` | `dict` | Stop if any of the named tools is called | Conditional: stop for some tools, continue for others |
| Custom function | `Callable` | Your logic decides per-turn | Maximum flexibility |

The `StopAtTools` mode:

```python
from agents.agent import StopAtTools

agent = Agent(
    name="Assistant",
    tools=[get_weather, get_population, search_database],
    tool_use_behavior=StopAtTools(stop_at_tool_names=["get_weather"]),
)
# If get_weather is called, its output is the final answer
# If get_population or search_database is called, the LLM loops back
```

The custom function mode (full signature with type hints):

```python
from agents import Agent, ToolsToFinalOutputResult, FunctionToolResult, RunContextWrapper

def should_stop(
    ctx: RunContextWrapper[Any],
    tool_results: list[FunctionToolResult],
) -> ToolsToFinalOutputResult:
    if any(r.tool_name == "get_weather" for r in tool_results):
        return ToolsToFinalOutputResult(
            is_final_output=True,
            final_output=tool_results[0].output,
        )
    return ToolsToFinalOutputResult(is_final_output=False)

agent = Agent(
    name="Assistant",
    tools=[get_weather, get_population],
    tool_use_behavior=should_stop,
)
```

### `reset_tool_choice` — Preventing Tool Loops

When `model_settings.tool_choice` is set to `"required"` or a specific tool name, the LLM is forced to call a tool. After the tool call, if `tool_choice` is still set, the LLM will call another tool, and another — creating an infinite loop.

The `reset_tool_choice` field (default: `True`) prevents this by automatically resetting `tool_choice` to `"auto"` after each tool call:

```python
# With reset_tool_choice=True (default):
# Turn 1: tool_choice="get_weather" → LLM calls get_weather
# Turn 2: tool_choice is reset to "auto" → LLM can decide to respond or call another tool

# With reset_tool_choice=False:
# Turn 1: tool_choice="get_weather" → LLM calls get_weather
# Turn 2: tool_choice is still "get_weather" → LLM calls get_weather again
# Turn 3: same → infinite loop until max_turns is reached
```

You should only set `reset_tool_choice=False` if you have a specific reason to force repeated tool calls — and you should always pair it with a low `max_turns` to prevent infinite loops.

## 2.12 Putting It All Together: A Complete Multi-Agent System

Here's a comprehensive example combining `clone()`, `as_tool()`, hooks, and tool use behavior:

```python
import asyncio
from typing import Any
from pydantic import BaseModel
from agents import (
    Agent, Runner, RunContextWrapper, RunHooks, AgentHooksBase,
    function_tool, ModelSettings, ToolsToFinalOutputResult,
)


class UserContext:
    def __init__(self, user_id: str, locale: str):
        self.user_id = user_id
        self.locale = locale


class TravelPlan(BaseModel):
    destination: str
    flights: str
    hotels: str
    budget_estimate: str
    tips: str


@function_tool
def search_flights(
    ctx: RunContextWrapper[UserContext],
    destination: str,
) -> str:
    return f"Flights to {destination} from user {ctx.context.user_id}: $450 round trip"


@function_tool
def search_hotels(
    ctx: RunContextWrapper[UserContext],
    destination: str,
) -> str:
    return f"Hotels in {destination}: from $120/night"


@function_tool
def check_visa(
    destination: str,
    passport_country: str,
) -> str:
    return f"Visa for {destination}: Not required for {passport_country} passport holders"


class TravelHooks(AgentHooksBase):
    async def on_start(self, context, agent):
        print(f"[Hook] Travel agent starting: {agent.name}")

    async def on_tool_end(self, context, agent, tool, result):
        print(f"[Hook] Tool completed: {tool.name} → {result[:50]}...")


base_agent = Agent[UserContext](
    name="Base Agent",
    instructions="You are a helpful assistant.",
    tools=[search_flights],
)

research_agent = base_agent.clone(
    name="Research Agent",
    instructions="You research destinations. Find flights, hotels, and visa requirements.",
    tools=[search_flights, search_hotels, check_visa],
    hooks=TravelHooks(),
)

planner_agent = Agent[UserContext](
    name="Travel Planner",
    instructions=(
        "You create travel plans. Call the research agent to gather information, "
        "then synthesize it into a structured travel plan."
    ),
    tools=[
        research_agent.as_tool(
            tool_name="research_destination",
            tool_description="Research a destination: flights, hotels, visa. Provide the destination name.",
        ),
    ],
    output_type=TravelPlan,
    model_settings=ModelSettings(temperature=0.3),
)


class LoggingHooks(RunHooks):
    async def on_agent_start(self, context, agent):
        print(f"[Run] Agent starting: {agent.name}")

    async def on_agent_end(self, context, agent, output):
        print(f"[Run] Agent finished: {agent.name}")


async def main():
    ctx = UserContext(user_id="u_456", locale="en-US")
    result = await Runner.run(
        planner_agent,
        "I want to visit Tokyo for a week. I have a US passport.",
        context=ctx,
        hooks=LoggingHooks(),
    )

    plan = result.final_output_as(TravelPlan)
    print(f"\n=== Travel Plan ===")
    print(f"Destination: {plan.destination}")
    print(f"Flights: {plan.flights}")
    print(f"Hotels: {plan.hotels}")
    print(f"Budget: {plan.budget_estimate}")
    print(f"Tips: {plan.tips}")

    print(f"\nTurns: {len(result.raw_responses)}")
    print(f"Items: {len(result.new_items)}")
    for item in result.new_items:
        print(f"  {type(item).__name__}")
    print(f"Tokens: {result.context_wrapper.usage.total_tokens}")


if __name__ == "__main__":
    asyncio.run(main())
```

### What Happens When You Run This

```
[Run] Agent starting: Travel Planner
[Hook] Travel agent starting: Research Agent
[Hook] Tool completed: search_flights → Flights to Tokyo from user u_456: $450...
[Hook] Tool completed: search_hotels → Hotels in Tokyo: from $120/night...
[Hook] Tool completed: check_visa → Visa for Tokyo: Not required for US...
[Run] Agent finished: Travel Planner
```

Inspecting the `RunResult`:

```python
# 1. The structured output
plan = result.final_output_as(TravelPlan)
# plan.destination → "Tokyo"
# plan.flights → "$450 round trip from US"
# plan.hotels → "From $120/night"
# plan.budget_estimate → "$2,500-4,000 for a one-week trip"
# plan.tips → "Best time to visit is spring for cherry blossoms..."

# 2. How many LLM calls were made?
print(len(result.raw_responses))
# 2: Turn 1 calls research_agent tool, Turn 2 produces TravelPlan

# 3. What items were generated?
for item in result.new_items:
    print(type(item).__name__)
# ToolCallItem          ← planner_agent called research_destination
# ToolCallOutputItem    ← research_agent returned results
# (nested items from research_agent are NOT in planner's new_items)

# 4. Which agent handled the request?
print(result.last_agent.name)
# "Travel Planner" — the manager agent, not the research agent

# 5. Token usage
print(result.context_wrapper.usage.total_tokens)
# Includes tokens from BOTH the planner and the nested research agent
```

Key insight: nested agent runs (via `as_tool()`) are **transparent to the parent's `RunResult`** — the parent only sees the tool call and its output, not the internal items of the nested run. However, the **token usage accumulates** across both levels, so you always get the true cost.

## 2.13 Field Reference: The Complete Agent Definition

Here's every field on `Agent` and `AgentBase`, with types, defaults, and cross-references:

| Field | Class | Type | Default | Reference |
|-------|-------|------|---------|-----------|
| `name` | AgentBase | `str` | *(required)* | §2.3 |
| `handoff_description` | AgentBase | `str \| None` | `None` | §2.3, Ch1 §1.3 |
| `tools` | AgentBase | `list[Tool]` | `[]` | §2.2, Ch3 |
| `mcp_servers` | AgentBase | `list[MCPServer]` | `[]` | §2.10 |
| `mcp_config` | AgentBase | `MCPConfig` | `{}` | §2.10 |
| `instructions` | Agent | `str \| Callable \| None` | `None` | §2.8, Ch1 §1.9 |
| `prompt` | Agent | `Prompt \| DynamicPromptFunction \| None` | `None` | §2.8 |
| `handoffs` | Agent | `list[Agent \| Handoff]` | `[]` | §2.3, Ch7 |
| `model` | Agent | `str \| Model \| None` | `None` | §2.3 |
| `model_settings` | Agent | `ModelSettings` | *defaults* | §2.3, Ch1 §1.12 |
| `input_guardrails` | Agent | `list[InputGuardrail]` | `[]` | §2.3, Ch7 |
| `output_guardrails` | Agent | `list[OutputGuardrail]` | `[]` | §2.3, Ch7 |
| `output_type` | Agent | `type \| AgentOutputSchemaBase \| None` | `None` | §2.3, Ch1 §1.7 |
| `hooks` | Agent | `AgentHooks \| None` | `None` | §2.9 |
| `tool_use_behavior` | Agent | `Literal \| StopAtTools \| Callable` | `"run_llm_again"` | §2.11 |
| `reset_tool_choice` | Agent | `bool` | `True` | §2.11 |

## 2.14 Key Takeaways

| Concept | Insight | Source Code |
|---------|---------|-------------|
| Why dataclass | Boilerplate elimination + `dataclasses.replace()` for `clone()` | `src/agents/agent.py` |
| AgentBase vs Agent | Base shared with RealtimeAgent; Agent adds text-specific fields | `src/agents/agent.py` |
| `__post_init__` | 10+ validation checks at construction time — fail fast | `src/agents/agent.py` |
| `get_all_tools()` | Dynamically merges MCP + enabled function tools | `src/agents/agent.py` |
| `clone()` | One-liner: `dataclasses.replace(self, **kwargs)` — shallow copy | `src/agents/agent.py` |
| `as_tool()` | Creates a `FunctionTool` that runs `Runner.run()` internally | `src/agents/agent.py` |
| `get_system_prompt()` | Resolves str/callable/None → string, called every turn | `src/agents/agent.py`, Ch1 §1.9 |
| `get_prompt()` | Resolves Prompt/DynamicPromptFunction → ResponsePromptParam | `src/agents/agent.py` |
| instructions vs prompt | System prompt (any provider) vs Platform prompt templates (OpenAI only) | `src/agents/agent.py`, `src/agents/prompts.py` |
| Configuration vs State | Agent = immutable config; RunState = mutable execution | `src/agents/run_state.py`, Ch5 |
| RunHooks vs AgentHooks | Run-wide vs agent-scoped lifecycle callbacks | `src/agents/lifecycle.py` |
| tool_use_behavior | Four modes: run_llm_again, stop_on_first_tool, StopAtTools, custom function | `src/agents/agent.py` |
| reset_tool_choice | Prevents infinite tool-call loops by resetting to "auto" | `src/agents/agent.py` |
| MCP integration | Dynamic tool fetching from MCP servers, with schema conversion and error handling | `src/agents/agent.py`, `src/agents/mcp/` |
