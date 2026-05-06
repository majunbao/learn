# Chapter 4: The Runner Engine — Inside `run_internal/`

You've used `Runner.run()` dozens of times. But what actually happens between your call and the `RunResult` you get back? This chapter goes line-by-line through the engine that orchestrates LLM calls, tool execution, handoffs, guardrails, retries, and streaming — all inside `src/agents/run_internal/`.

**How to Read This Chapter**

- **Pass 1 — Build intuition (20 min).** Read §4.1 → §4.2 (module map only) → §4.3 (NextStep table only) → §4.5 (ASCII flow only) → §4.7 (loop pseudocode only) → §4.10 (comparison table only). Skip all 🔥 source code walkthroughs and deep subsections.
- **Pass 2 — Dive into source code (45 min).** Read the three 🔥 walkthroughs: §4.4 (`run_single_turn`), §4.8 (`get_response_with_retry`), §4.11 (`run_single_turn_streamed`). Also read the guardrail execution in §4.6, the error handler pipeline in §4.9, and the exception hierarchy in §4.9.
- **Pass 3 — Fill gaps.** Itemized list:
  - Module map and which file does what? → §4.2 (21-file table)
  - NextStep state machine types and fields? → §4.3 (4-row type table + decision tree)
  - Single-step result structure? → §4.3 (SingleStepResult 7-row field table)
  - How does one turn work end-to-end? → §4.4 (🔥 source code walkthrough + call chain diagram)
  - ProcessedResponse: categorizing model output? → §4.5 (11-row field table + 8-row ToolRun type table + decision tree)
  - When do guardrails run? → §4.6 (Input vs Output comparison table + concurrent execution source)
  - The outer loop: `AgentRunner.run()`? → §4.7 (full lifecycle + pseudocode)
  - Model retry: backoff, rewind, conversation_locked? → §4.8 (🔥 retry walkthrough + 7-concept table)
  - Error handling: `MaxTurnsExceeded` handler pipeline? → §4.9 (3-stage pipeline + RunErrorHandlerResult source + example)
  - Runner exception hierarchy? → §4.9 (exception tree + 5-row recovery table)
  - `Runner.run()` vs `Runner.run_streamed()` vs `Runner.run_sync()`? → §4.10 (3-row comparison + RunResult vs Streaming 10-row table)
  - Streaming: queue, sentinel, events? → §4.11 (🔥 streaming walkthrough + real-time display example)
  - Turn preparation: tools, handoffs, model, schema? → §4.12 (4 resolver functions + maybe_reset_tool_choice + AgentToolUseTracker)
  - Session persistence within the loop? → §4.13 (5 save points diagram + compaction)
  - Putting it together + multi-turn? → §4.14 (3-turn handoff example + post-run analysis + to_input_list output)

---

## 4.1 The Big Picture: One Turn at a Time

The Runner is a **turn-based state machine**. Each turn does exactly one thing: call the LLM, process the response, and decide what to do next. The "what to do next" is encoded as a `NextStep` type:

```
Runner.run(agent, "Hello!")
        │
        ▼
┌─── Turn Loop ────────────────────────────────────────────┐
│                                                          │
│   1. Turn Preparation                                    │
│      • Resolve tools, handoffs, output schema, model     │
│      • Run agent start hooks                             │
│                                                          │
│   2. Input Guardrails (first turn only)                  │
│      • Sequential → then parallel (with model call)      │
│                                                          │
│   3. Call the LLM                                        │
│      • Build system prompt + input items                 │
│      • call_model_input_filter (if configured)           │
│      • get_response_with_retry (with backoff + rewind)   │
│                                                          │
│   4. Process Response → ProcessedResponse                │
│      • Categorize: handoffs, functions, computer, etc.   │
│                                                          │
│   5. Execute (if needed)                                 │
│      • Tool execution (parallel via _FunctionToolBatch)   │
│      • Handoff execution (switch agent)                  │
│      • Computer/Shell/MCP actions                        │
│                                                          │
│   6. Decide Next Step                                    │
│      ├── NextStepFinalOutput → break loop                │
│      ├── NextStepHandoff   → switch agent, continue      │
│      ├── NextStepRunAgain  → continue (tools executed)   │
│      └── NextStepInterruption → break (await approval)   │
│                                                          │
│   7. Save to Session (if configured)                     │
│      • Persist items, handle compaction                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
        │
        ▼
   Output Guardrails → RunResult
```

---

## 4.2 The Module Architecture: 21 Files, One Responsibility Each

| File | Lines | Responsibility |
|---|---|---|
| `run_loop.py` | ~1900 | Main orchestration: `run_single_turn`, `run_single_turn_streamed`, `start_streaming`, `get_new_response` |
| `run_steps.py` | ~207 | Data structures: `NextStep*`, `ProcessedResponse`, `SingleStepResult`, `QueueCompleteSentinel` |
| `turn_resolution.py` | ~1900 | Process model output: `process_model_response`, `execute_tools_and_side_effects`, `execute_handoffs`, `check_for_final_output_from_tools` |
| `turn_preparation.py` | ~132 | Pre-turn setup: `get_all_tools`, `get_handoffs`, `get_output_schema`, `get_model`, `maybe_filter_model_input` |
| `tool_execution.py` | ~2329 | Execute tools: `execute_function_tool_calls`, `invoke_function_tool`, parallel batch execution |
| `tool_planning.py` | ~600+ | MCP tool planning: approval requests, tool plan execution, deduplication |
| `tool_actions.py` | — | Computer/Shell/ApplyPatch action handling |
| `tool_use_tracker.py` | — | Track which tools have been used (prevents infinite tool_choice loops) |
| `guardrails.py` | ~191 | Input/output guardrail execution: `run_input_guardrails`, `run_output_guardrails`, concurrent execution |
| `error_handlers.py` | ~163 | `MaxTurnsExceeded` handler: format output, validate, synthesize message |
| `approvals.py` | — | Extract `ToolApprovalItem` from `NextStepInterruption` |
| `session_persistence.py` | ~630+ | Save/load session: `prepare_input_with_session`, `save_result_to_session`, `rewind_session_items` |
| `streaming.py` | — | Queue-based streaming: `stream_step_items_to_queue`, `stream_step_result_to_queue` |
| `model_retry.py` | ~724 | Retry logic: `get_response_with_retry`, `stream_response_with_retry`, backoff, conversation_locked |
| `oai_conversation.py` | — | OpenAI server-managed conversation tracking |
| `agent_bindings.py` | ~38 | `AgentBindings(public_agent, execution_agent)` — separates public vs sandbox agent |
| `agent_runner_helpers.py` | — | Utilities: `snapshot_usage`, `usage_delta`, `apply_resumed_conversation_settings` |
| `items.py` | — | Item normalization: deduplication, format conversion, orphan cleanup |
| `prompt_cache_key.py` | — | Prompt cache key resolution for API caching |
| `run_grouping.py` | — | Run grouping for trace correlation |
| `_asyncio_progress.py` | — | Asyncio progress tracking utilities |

**Key insight:** `run_loop.py` is the conductor. It calls into `turn_preparation.py` to set up, `turn_resolution.py` to process, `tool_execution.py` to execute, `guardrails.py` for safety, and `session_persistence.py` for durability. Each file is a specialist.

---

## 4.3 The NextStep State Machine: Four Ways to Leave a Turn

After every turn, the engine returns a `SingleStepResult` whose `next_step` field determines what happens next:

```python
@dataclass
class NextStepFinalOutput:
    output: Any

@dataclass
class NextStepHandoff:
    new_agent: Agent[Any]

@dataclass
class NextStepRunAgain:
    pass

@dataclass
class NextStepInterruption:
    interruptions: list[ToolApprovalItem]
```

| Type | When it fires | What the loop does | RunResult field |
|---|---|---|---|
| `NextStepFinalOutput` | LLM produces `output_type`-matching output, or `tool_use_behavior` returns `stop_on_first_tool` | Run output guardrails, return `RunResult` | `final_output` is set |
| `NextStepHandoff` | LLM calls a handoff tool (e.g., `transfer_to_billing`) | Switch `current_agent`, continue loop | No result yet — next turn uses new agent |
| `NextStepRunAgain` | LLM calls function tools that don't produce final output | Continue loop with tool results in history | No result yet — next turn includes tool outputs |
| `NextStepInterruption` | LLM calls a tool that needs approval (`needs_approval=True`) | Break loop, return partial `RunResult` with `interruptions` | `interruptions` list, resumable via `RunState` |

**The decision tree (from `turn_resolution.py`):**

```
ProcessedResponse
    │
    ├── has_interruptions()? → NextStepInterruption
    │
    ├── has handoffs? → execute_handoffs() → NextStepHandoff
    │
    ├── has functions/computer/shell/MCP?
    │   ├── execute all tools
    │   ├── check_for_final_output_from_tools()
    │   │   ├── is_final_output=True  → NextStepFinalOutput
    │   │   └── is_final_output=False → NextStepRunAgain
    │   └── (no tools) → NextStepRunAgain (shouldn't happen)
    │
    └── (none of the above) → NextStepFinalOutput (LLM produced text output)
```

### `SingleStepResult`: What One Turn Produces

```python
@dataclass
class SingleStepResult:
    original_input: str | list[TResponseInputItem]
    model_response: ModelResponse
    pre_step_items: list[RunItem]
    new_step_items: list[RunItem]
    next_step: NextStepHandoff | NextStepFinalOutput | NextStepRunAgain | NextStepInterruption
    tool_input_guardrail_results: list[ToolInputGuardrailResult]
    tool_output_guardrail_results: list[ToolOutputGuardrailResult]
    session_step_items: list[RunItem] | None = None
    output_guardrail_results: list[OutputGuardrailResult] = dataclasses.field(default_factory=list)
    processed_response: ProcessedResponse | None = None

    @property
    def generated_items(self) -> list[RunItem]:
        items = self.session_step_items if self.session_step_items is not None else self.new_step_items
        return self.pre_step_items + items
```

**Field-by-field:**

| Field | Purpose | Non-obvious behavior |
|---|---|---|
| `original_input` | The input items before `run()` was called | May be **mutated by handoff input filters** — the next agent may see a different history |
| `model_response` | The raw LLM response for this turn | Contains `usage` and `response_id` for tracing/debugging |
| `pre_step_items` | Items generated *before* this step | Cumulative across handoffs — grows as agents switch |
| `new_step_items` | Items generated *during* this step | Tool calls, tool outputs, handoff calls, etc. |
| `next_step` | What to do next | The 4-way state machine decision |
| `session_step_items` | Full unfiltered items for session persistence | When set, used instead of `new_step_items` for saving — needed when handoff input filters trim the model's view but the session should keep the full history |
| `processed_response` | The categorized model response | Only set when `NextStepInterruption` occurs — needed for resuming later |

---

## 4.4 🔥 Source Code Walkthrough: `run_single_turn` — The Non-Streaming Path

Before diving into the code, here's the complete call chain from `Runner.run()` down to the individual helper functions:

```
Runner.run(agent, input)
    └── AgentRunner.run()
        └── run_single_turn()                    ← This section
            ├── get_system_prompt() + get_prompt()     (concurrent)
            ├── get_output_schema()
            ├── get_handoffs()
            └── get_new_response()               ← §4.8 covers retry
                ├── maybe_filter_model_input()   ← §4.12
                ├── model_settings.resolve()
                ├── maybe_reset_tool_choice()
                └── get_response_with_retry()    ← §4.8
                    └── model.get_response()
            └── get_single_step_result_from_response()  ← §4.5
                ├── process_model_response()     → ProcessedResponse
                ├── execute_tools_and_side_effects()
                │   ├── execute_function_tool_calls()  ← Ch3 §3.8
                │   ├── execute_handoffs()             → NextStepHandoff
                │   └── execute_computer/shell/...
                └── check_for_final_output_from_tools()
```

This function is the core that executes exactly one turn. Let's walk through the actual source:

```python
async def run_single_turn(
    *,
    bindings: AgentBindings[TContext],
    all_tools: list[Tool],
    original_input: str | list[TResponseInputItem],
    generated_items: list[RunItem],
    hooks: RunHooks[TContext],
    context_wrapper: RunContextWrapper[TContext],
    run_config: RunConfig,
    should_run_agent_start_hooks: bool,
    tool_use_tracker: AgentToolUseTracker,
    server_conversation_tracker: OpenAIServerConversationTracker | None = None,
    session: Session | None = None,
    session_items_to_rewind: list[TResponseInputItem] | None = None,
    reasoning_item_id_policy: ReasoningItemIdPolicy | None = None,
    prompt_cache_key_resolver: PromptCacheKeyResolver | None = None,
) -> SingleStepResult:
```

### Step 1: Set turn input and run agent start hooks

```python
    public_agent = bindings.public_agent
    execution_agent = bindings.execution_agent
    try:
        turn_input = ItemHelpers.input_to_new_input_list(original_input)
    except Exception:
        turn_input = []
    context_wrapper.turn_input = list(turn_input)

    if should_run_agent_start_hooks:
        agent_hook_context = AgentHookContext(
            context=context_wrapper.context,
            usage=context_wrapper.usage,
            _approvals=context_wrapper._approvals,
            turn_input=turn_input,
        )
        await asyncio.gather(
            hooks.on_agent_start(agent_hook_context, public_agent),
            (
                public_agent.hooks.on_start(agent_hook_context, public_agent)
                if public_agent.hooks
                else _coro.noop_coroutine()
            ),
        )
```

**Key insight #1:** `bindings.public_agent` and `bindings.execution_agent` are usually the same object. They only differ when a **sandbox** is active — `execution_agent` is the sandbox-rewritten clone, while `public_agent` is the original agent the user created.

**Key insight #2:** `should_run_agent_start_hooks` is `True` only on the first turn for each agent. It resets to `True` after a handoff.

### Step 2: Resolve system prompt and prompt config concurrently

```python
    system_prompt, prompt_config = await asyncio.gather(
        execution_agent.get_system_prompt(context_wrapper),
        execution_agent.get_prompt(context_wrapper),
    )
```

**Key insight #3:** `get_system_prompt()` and `get_prompt()` are called concurrently via `asyncio.gather()`. Both can be callables, and both are called **every turn** — not just the first one. See Chapter 2 §2.8 for the full details.

### Step 3: Prepare input and call the model

```python
    output_schema = get_output_schema(execution_agent)
    handoffs = await get_handoffs(execution_agent, context_wrapper)
    if server_conversation_tracker is not None:
        input = server_conversation_tracker.prepare_input(original_input, generated_items)
    else:
        input = _prepare_turn_input_items(
            original_input, generated_items, reasoning_item_id_policy,
        )

    new_response = await get_new_response(
        bindings, system_prompt, input, output_schema, all_tools,
        handoffs, hooks, context_wrapper, run_config, tool_use_tracker,
        server_conversation_tracker, prompt_config,
        session=session,
        session_items_to_rewind=session_items_to_rewind,
        prompt_cache_key_resolver=prompt_cache_key_resolver,
    )
```

**Key insight #4:** `get_new_response()` is a wrapper that:
1. Calls `maybe_filter_model_input()` — the `call_model_input_filter` hook (see §4.12 for full source and use cases)
2. Deduplicates input items
3. Resolves model settings with `model_settings.resolve(run_config.model_settings)`
4. Resets `tool_choice` if the agent has already used tools (via `maybe_reset_tool_choice`)
5. Calls `get_response_with_retry()` (see §4.8 for the retry engine)
6. Updates `context_wrapper.usage` with the response usage

### Step 4: Process the response into a step result

```python
    return await get_single_step_result_from_response(
        bindings=bindings,
        original_input=original_input,
        pre_step_items=generated_items,
        new_response=new_response,
        output_schema=output_schema,
        all_tools=all_tools,
        handoffs=handoffs,
        hooks=hooks,
        context_wrapper=context_wrapper,
        run_config=run_config,
        tool_use_tracker=tool_use_tracker,
        server_manages_conversation=server_conversation_tracker is not None,
    )
```

This delegates to `turn_resolution.py` which:
1. Calls `process_model_response()` → `ProcessedResponse`
2. Checks for interruptions → `NextStepInterruption`
3. Calls `execute_tools_and_side_effects()` if there are tools
4. Returns a `SingleStepResult` with the appropriate `next_step`

**Key insight #5:** `run_single_turn` is intentionally thin — it's 40 lines of orchestration. The heavy lifting is in `get_new_response()` (model call + retry) and `get_single_step_result_from_response()` (tool execution + handoff + final output). This separation makes the streaming path (`run_single_turn_streamed`) parallel to the non-streaming path.

---

## 4.5 ProcessedResponse: Categorizing What the Model Said

After the LLM responds, `process_model_response()` (in `turn_resolution.py`) categorizes every output item into a `ProcessedResponse`:

```python
@dataclass
class ProcessedResponse:
    new_items: list[RunItem]
    handoffs: list[ToolRunHandoff]
    functions: list[ToolRunFunction]
    computer_actions: list[ToolRunComputerAction]
    local_shell_calls: list[ToolRunLocalShellCall]
    shell_calls: list[ToolRunShellCall]
    apply_patch_calls: list[ToolRunApplyPatchCall]
    tools_used: list[str]
    mcp_approval_requests: list[ToolRunMCPApprovalRequest]
    interruptions: list[ToolApprovalItem]
    custom_tool_calls: list[ToolRunCustom] = dataclasses.field(default_factory=list)
```

**ProcessedResponse field-by-field:**

| Field | Type | What it contains | When it's non-empty |
|---|---|---|---|
| `new_items` | `list[RunItem]` | All `RunItem` instances from this turn (tool calls, outputs, messages, reasoning) | Every response |
| `handoffs` | `list[ToolRunHandoff]` | Handoff calls paired with their `Handoff` definition | LLM called a handoff tool |
| `functions` | `list[ToolRunFunction]` | Function tool calls paired with their `FunctionTool` | LLM called a function tool |
| `computer_actions` | `list[ToolRunComputerAction]` | Computer use calls (click, type, screenshot) | LLM called a computer tool |
| `local_shell_calls` | `list[ToolRunLocalShellCall]` | Local shell command calls | LLM called a local shell tool |
| `shell_calls` | `list[ToolRunShellCall]` | Remote shell command calls | LLM called a remote shell tool |
| `apply_patch_calls` | `list[ToolRunApplyPatchCall]` | File patch calls | LLM called an apply_patch tool |
| `tools_used` | `list[str]` | Names of ALL tools used (including hosted tools) | Any tool was called |
| `mcp_approval_requests` | `list[ToolRunMCPApprovalRequest]` | MCP approval requests that have callbacks | LLM called an MCP tool needing approval |
| `interruptions` | `list[ToolApprovalItem]` | Tool calls awaiting user approval | LLM called a tool with `needs_approval` |
| `custom_tool_calls` | `list[ToolRunCustom]` | Custom tool calls | LLM called a `CustomTool` |

**Key distinction:** `tools_used` includes **hosted** tool names (file_search, web_search, code_interpreter, MCP hosted tools), while the typed lists (`functions`, `computer_actions`, etc.) only contain **local** tools that need SDK-side execution.

**Each `ToolRun*` type pairs a tool call with its tool definition:**

| ToolRun Type | Raw Call Type | Tool Type | Execution |
|---|---|---|---|
| `ToolRunHandoff` | `ResponseFunctionToolCall` | `Handoff` | Calls `handoff.on_invoke_handoff()` |
| `ToolRunFunction` | `ResponseFunctionToolCall` | `FunctionTool` | Calls `invoke_function_tool()` (see Ch3 §3.8) |
| `ToolRunComputerAction` | `ResponseComputerToolCall` | `ComputerTool` | Executes computer action (click, type, etc.) |
| `ToolRunLocalShellCall` | `LocalShellCall` | `LocalShellTool` | Runs local shell command |
| `ToolRunShellCall` | (varies) | `ShellTool` | Runs remote shell command |
| `ToolRunApplyPatchCall` | (varies) | `ApplyPatchTool` | Applies file patch |
| `ToolRunMCPApprovalRequest` | `McpApprovalRequest` | `HostedMCPTool` | Processes MCP approval |
| `ToolRunCustom` | (varies) | `CustomTool` | Calls custom tool handler |

### The `has_tools_or_approvals_to_run()` method

```python
def has_tools_or_approvals_to_run(self) -> bool:
    return any([
        self.handoffs,
        self.functions,
        self.computer_actions,
        self.custom_tool_calls,
        self.local_shell_calls,
        self.shell_calls,
        self.apply_patch_calls,
        self.mcp_approval_requests,
    ])
```

**Key insight:** "Hosted" tools (file_search, web_search, code_interpreter) are **not** in this list because they execute on OpenAI's servers — the SDK doesn't need to do anything locally. Only "local" tools (function, computer, shell, etc.) need execution.

### `check_for_final_output_from_tools()`: When Tools Become Final Output

The `tool_use_behavior` field on `Agent` controls whether tool results become the final output:

```python
async def check_for_final_output_from_tools(
    agent: Agent[TContext],
    tool_results: list[FunctionToolResult],
    context_wrapper: RunContextWrapper[TContext],
) -> ToolsToFinalOutputResult:
    if not tool_results:
        return NOT_FINAL_OUTPUT

    if agent.tool_use_behavior == "run_llm_again":
        return NOT_FINAL_OUTPUT
    elif agent.tool_use_behavior == "stop_on_first_tool":
        return ToolsToFinalOutputResult(is_final_output=True, final_output=tool_results[0].output)
    elif isinstance(agent.tool_use_behavior, dict):
        names = agent.tool_use_behavior.get("stop_at_tool_names", [])
        for tool_result in tool_results:
            if tool_result.tool.name in names or tool_result.tool.qualified_name in names:
                return ToolsToFinalOutputResult(is_final_output=True, final_output=tool_result.output)
        return ToolsToFinalOutputResult(is_final_output=False, final_output=None)
    elif callable(agent.tool_use_behavior):
        if inspect.iscoroutinefunction(agent.tool_use_behavior):
            return await cast(Awaitable[ToolsToFinalOutputResult], agent.tool_use_behavior(context_wrapper, tool_results))
        return cast(ToolsToFinalOutputResult, agent.tool_use_behavior(context_wrapper, tool_results))

    logger.error("Invalid tool_use_behavior: %s", agent.tool_use_behavior)
    raise UserError(f"Invalid tool_use_behavior: {agent.tool_use_behavior}")
```

| `tool_use_behavior` | Effect | When to use |
|---|---|---|
| `"run_llm_again"` (default) | Tool results go back to LLM for another response | General-purpose agents |
| `"stop_on_first_tool"` | First tool result becomes `final_output` | Tool-only agents (no LLM follow-up needed) |
| `{"stop_at_tool_names": [...]}` | Only specified tool results become `final_output` | Mixed agents where some tools are terminal |
| `callable` | Custom logic decides | Advanced use cases (e.g., stop only on specific conditions) |

Cross-reference: See Chapter 2 §2.11 for the `tool_use_behavior` field and loop prevention mechanism.

---

## 4.6 Guardrail Execution: When and How

### Input Guardrails: First Turn Only

Input guardrails only run on the **first turn** of the first agent (not after handoffs):

```python
all_input_guardrails = (
    starting_agent.input_guardrails + (run_config.input_guardrails or [])
    if current_turn == 0 and not resuming_turn
    else []
)
```

They are split into **sequential** and **parallel** groups based on `run_in_parallel`:

```python
sequential_guardrails = [g for g in all_input_guardrails if not g.run_in_parallel]
parallel_guardrails = [g for g in all_input_guardrails if g.run_in_parallel]
```

**On the first turn, the engine runs:**

1. **Sequential guardrails** — one at a time, blocking. Must complete before the model call starts. This is important for sandbox scenarios: a blocking guardrail can prevent sandbox creation.
2. **Parallel guardrails + model call** — run concurrently via `asyncio.gather()`. The model call starts immediately alongside parallel guardrails.

```python
parallel_results, turn_result = await asyncio.gather(
    run_input_guardrails(starting_agent, parallel_guardrails, copy_input_items(original_input), context_wrapper),
    model_task,
)
```

**Key insight:** If a parallel guardrail triggers a tripwire, the engine cancels the in-flight model task (if `should_cancel_parallel_model_task_on_input_guardrail_trip()` returns True). This saves tokens and latency.

### Output Guardrails: After Final Output

Output guardrails run only when the engine has determined a `NextStepFinalOutput`:

```python
output_guardrail_results = await run_output_guardrails(
    current_agent.output_guardrails + (run_config.output_guardrails or []),
    current_agent,
    turn_result.next_step.output,
    context_wrapper,
)
```

### Input vs Output Guardrails in the Runner: Comparison

| Aspect | Input Guardrails | Output Guardrails |
|---|---|---|
| **When they run** | First turn only | After every final output |
| **Scope** | Only `starting_agent`'s guardrails + `run_config` | Current `agent`'s guardrails + `run_config` |
| **Concurrency** | Sequential + parallel (with model call) | All parallel via `asyncio.gather()` |
| **On tripwire** | Cancel model task, raise `InputGuardrailTripwireTriggered` | Raise `OutputGuardrailTripwireTriggered` |
| **Session persistence** | Save input items before raising (so user input isn't lost) | No special handling (output never persisted) |
| **After handoff** | Never run again (even with new agent) | Run with whatever agent produced the output |

### Guardrail Execution Source: Concurrent with Cancellation

```python
async def run_input_guardrails(
    agent, guardrails, input, context,
) -> list[InputGuardrailResult]:
    if not guardrails:
        return []

    guardrail_tasks = [
        asyncio.create_task(run_single_input_guardrail(agent, guardrail, input, context))
        for guardrail in guardrails
    ]
    guardrail_results = []

    for done in asyncio.as_completed(guardrail_tasks):
        result = await done
        if result.output.tripwire_triggered:
            for t in guardrail_tasks:
                t.cancel()
            await asyncio.gather(*guardrail_tasks, return_exceptions=True)
            raise InputGuardrailTripwireTriggered(result)
        guardrail_results.append(result)

    return guardrail_results
```

**Key insight:** `asyncio.as_completed()` is used instead of `asyncio.gather()` because it allows **early termination** — as soon as any guardrail trips, all remaining guardrails are cancelled. With `gather()`, you'd have to wait for all guardrails to finish.

---

## 4.7 The Outer Loop: `AgentRunner.run()`

The public `Runner.run()` delegates to `AgentRunner.run()`, which contains the main `while True` loop. Here's the simplified pseudocode:

```python
async def run(self, starting_agent, input, **kwargs):
    # === INITIALIZATION ===
    is_resumed_state = isinstance(input, RunState)
    if is_resumed_state:
        run_state = input
        conversation_id, previous_response_id, auto_previous_response_id = apply_resumed_conversation_settings(...)
        context_wrapper = resolve_resumed_context(run_state)
        current_agent = run_state._current_agent or starting_agent
        current_turn = run_state._current_turn
    else:
        context_wrapper = ensure_context_wrapper(context)
        run_state = RunState(context=context_wrapper, original_input=..., starting_agent=starting_agent, max_turns=max_turns)
        current_agent = starting_agent
        current_turn = 0

    prepared_input, session_input_items_for_persistence = await prepare_input_with_session(...)
    server_conversation_tracker = OpenAIServerConversationTracker(...) if conversation_id or previous_response_id else None

    # === TRACE SETUP ===
    with TraceCtxManager(...):
        sandbox_runtime = SandboxRuntime(starting_agent=starting_agent, run_config=run_config)

        # === MAIN LOOP ===
        while True:
            current_turn += 1
            if current_turn > max_turns:
                # Try error handler, or raise MaxTurnsExceeded
                ...

            current_bindings = bind_public_agent(current_agent)
            prepared_sandbox = await sandbox_runtime.prepare_agent(current_agent, original_input, context_wrapper)
            current_bindings = prepared_sandbox.bindings

            # === RESUME FROM INTERRUPTION ===
            if run_state._current_step is not None and isinstance(run_state._current_step, NextStepInterruption):
                turn_result = await resolve_interrupted_turn(...)
                # Handle result same as normal turn
                ...

            # === INPUT GUARDRAILS (turn 1 only) ===
            all_input_guardrails = starting_agent.input_guardrails + (run_config.input_guardrails or []) if current_turn == 1 else []
            sequential_guardrails = [g for g in all_input_guardrails if not g.run_in_parallel]
            parallel_guardrails = [g for g in all_input_guardrails if g.run_in_parallel]

            # Sequential guardrails (blocking)
            if sequential_guardrails:
                sequential_results = await run_input_guardrails(starting_agent, sequential_guardrails, ...)

            # === RUN ONE TURN ===
            all_tools = await get_all_tools(execution_agent, context_wrapper)
            turn_result = await run_single_turn(
                bindings=current_bindings,
                all_tools=all_tools,
                original_input=original_input,
                generated_items=generated_items,
                hooks=hooks,
                context_wrapper=context_wrapper,
                run_config=run_config,
                ...
            )

            # If parallel guardrails, they ran concurrently with model_task above
            # (simplified here — actual code uses asyncio.gather)

            # === PROCESS NEXT STEP ===
            if isinstance(turn_result.next_step, NextStepFinalOutput):
                output_guardrail_results = await run_output_guardrails(...)
                result = RunResult(final_output=turn_result.next_step.output, ...)
                await save_result_to_session(session, ..., run_state)
                return result

            elif isinstance(turn_result.next_step, NextStepHandoff):
                current_agent = turn_result.next_step.new_agent
                original_input = turn_result.original_input
                should_run_agent_start_hooks = True
                continue

            elif isinstance(turn_result.next_step, NextStepRunAgain):
                original_input = turn_result.original_input
                generated_items = turn_result.generated_items
                session_items.extend(session_items_for_turn(turn_result))
                await save_result_to_session(session, ..., run_state)
                continue

            elif isinstance(turn_result.next_step, NextStepInterruption):
                # Save state for resumption
                update_run_state_for_interruption(run_state, ...)
                result = build_interruption_result(...)
                return result
```

### The Full Lifecycle: From `Runner.run()` to `RunResult`

```
Runner.run(agent, input)
    │
    ├── AgentRunner.run()
    │   │
    │   ├── Initialization
    │   │   ├── Create RunContextWrapper
    │   │   ├── Create RunState
    │   │   ├── Prepare input with session
    │   │   └── Set up tracing
    │   │
    │   ├── while True:
    │   │   ├── Increment current_turn
    │   │   ├── Check max_turns
    │   │   │   └── Try error_handlers.get("max_turns")
    │   │   │       ├── handler returns final_output → return synthesized RunResult
    │   │   │       └── no handler → raise MaxTurnsExceeded
    │   │   │
    │   │   ├── Prepare sandbox (if enabled)
    │   │   ├── Check for resumed interruption
    │   │   │   └── resolve_interrupted_turn()
    │   │   │
    │   │   ├── Input guardrails (turn 1)
    │   │   │   ├── Sequential (blocking)
    │   │   │   └── Parallel (concurrent with model)
    │   │   │
    │   │   ├── run_single_turn() or run_single_turn_streamed()
    │   │   │   ├── get_system_prompt() + get_prompt()
    │   │   │   ├── get_all_tools() + get_handoffs()
    │   │   │   ├── get_new_response()
    │   │   │   │   ├── maybe_filter_model_input()
    │   │   │   │   └── get_response_with_retry()
    │   │   │   └── get_single_step_result_from_response()
    │   │   │       ├── process_model_response()
    │   │   │       ├── execute_tools_and_side_effects()
    │   │   │       └── Return SingleStepResult
    │   │   │
    │   │   ├── Process next_step
    │   │   │   ├── NextStepFinalOutput → output guardrails → RunResult
    │   │   │   ├── NextStepHandoff → switch agent → continue
    │   │   │   ├── NextStepRunAgain → save session → continue
    │   │   │   └── NextStepInterruption → save state → partial RunResult
    │   │   │
    │   │   └── Save to session
    │   │
    │   └── Cleanup: dispose computers, finalize spans, finalize trace
    │
    └── Return RunResult or raise exception
```

---

## 4.8 🔥 Source Code Walkthrough: Model Retry — `get_response_with_retry()`

When the LLM call fails, the engine doesn't give up. It retries with exponential backoff, conversation rewind, and provider-managed retry coordination.

```python
async def get_response_with_retry(
    *,
    get_response: GetResponseCallable,
    rewind: RewindCallable,
    retry_settings: ModelRetrySettings | None,
    get_retry_advice: GetRetryAdviceCallable,
    previous_response_id: str | None,
    conversation_id: str | None,
) -> ModelResponse:
    request_attempt = 1
    policy_attempt = 1
    failed_policy_attempts = 0
    compatibility_retries_taken = 0
    stateful_request = _is_stateful_request(
        previous_response_id=previous_response_id,
        conversation_id=conversation_id,
    )

    while True:
        try:
            with (
                provider_managed_retries_disabled(
                    _should_disable_provider_managed_retries(retry_settings, attempt=request_attempt, stateful_request=stateful_request)
                ),
                websocket_pre_event_retries_disabled(
                    _should_disable_websocket_pre_event_retry(retry_settings)
                ),
            ):
                response = await get_response()
            response.usage = apply_retry_attempt_usage(response.usage, failed_policy_attempts + compatibility_retries_taken)
            return response
```

### The retry flow:

```
get_response()
    │
    ├── Success → return response (with retry usage baked in)
    │
    └── Exception
        │
        ├── conversation_locked error?
        │   ├── Yes → compatibility retry (up to 3 times, exponential backoff)
        │   │   ├── rewind session items
        │   │   ├── sleep 1s × 2^(n-1)
        │   │   └── retry
        │   └── No → continue to policy check
        │
        ├── Get provider retry advice
        │   └── model.get_retry_advice(error, attempt, stream, ...)
        │
        ├── Evaluate retry decision
        │   ├── attempt > max_retries? → give up (raise)
        │   ├── is_abort? → give up (CancelledError, etc.)
        │   ├── emitted_retry_unsafe_event? → give up (streaming already started)
        │   ├── no retry policy? → give up
        │   ├── RetryPolicy says no? → give up
        │   ├── stateful request but replay not approved? → give up
        │   └── All checks pass → retry with delay
        │
        └── Retry
            ├── delay = decision.delay or retry_after header or default backoff
            ├── await rewind_model_request() (rollback session items)
            └── await _sleep_for_retry(delay)
```

### Key retry concepts:

| Concept | What it means | Why it matters |
|---|---|---|
| `stateful_request` | Request uses `previous_response_id` or `conversation_id` | Stateful retries need rewind + replay-safety checks |
| `provider_managed_retries` | OpenAI's SDK has its own retry logic | The runner disables these on replay attempts to avoid double-retries |
| `conversation_locked` | OpenAI API returns code `conversation_locked` | Special compatibility path: retry up to 3 times with exponential backoff |
| `rewind_model_request()` | Roll back session items that were persisted before the failed call | Without rewind, retries would accumulate duplicate items in the session |
| `retry_after` header | HTTP `Retry-After` or `Retry-After-Ms` from the API | Takes priority over computed backoff delay |
| `replay_safety` | Provider marks replay as "safe" or "unsafe" | "unsafe" means the request can't be replayed (e.g., non-idempotent side effects) |
| `apply_retry_attempt_usage()` | Adds zero-usage entries for failed attempts | So `result.context_wrapper.usage.requests` reflects total attempts, not just successes |

### Default backoff parameters:

```python
DEFAULT_INITIAL_DELAY_SECONDS = 0.25
DEFAULT_MAX_DELAY_SECONDS = 2.0
DEFAULT_BACKOFF_MULTIPLIER = 2.0
DEFAULT_BACKOFF_JITTER = True
```

This gives delays of ~0.25s, ~0.5s, ~1.0s, ~2.0s (capped), with ±12.5% jitter to avoid thundering herd.

---

## 4.9 Error Handling: The `MaxTurnsExceeded` Pipeline

When `current_turn > max_turns`, the engine has a 3-stage pipeline before raising:

### Stage 1: Build error data

```python
run_error_data = build_run_error_data(
    input=original_input,
    new_items=session_items,
    raw_responses=model_responses,
    last_agent=current_agent,
)
```

This creates a `RunErrorData` with the full conversation history, all items, all raw responses, and the last agent — giving the error handler everything it needs to synthesize a response.

### Stage 2: Try the error handler

```python
handler_result = await resolve_run_error_handler_result(
    error_handlers=error_handlers,
    error=max_turns_error,
    context_wrapper=context_wrapper,
    run_data=run_error_data,
)
```

The handler can:
- Return `None` → let the exception propagate
- Return `RunErrorHandlerResult(final_output="...")` → synthesize a final output
- Return `RunErrorHandlerResult(final_output="...", include_in_history=True)` → also add to conversation

### The handler data structures:

```python
@dataclass
class RunErrorData:
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
    final_output: Any
    include_in_history: bool = True
```

**Handler return types are flexible** — you can return a `RunErrorHandlerResult`, a `dict` like `{"final_output": "..."}`, or just a raw value. `resolve_run_error_handler_result()` normalizes all three:

```python
from agents import Runner, RunErrorHandlers

async def handle_max_turns(input: RunErrorHandlerInput) -> RunErrorHandlerResult:
    last_response = input.run_data.raw_responses[-1]
    return RunErrorHandlerResult(
        final_output="I need more turns to complete this task. Here's what I have so far: ...",
        include_in_history=True,
    )

result = await Runner.run(
    agent,
    "Complex task...",
    error_handlers=RunErrorHandlers(max_turns=handle_max_turns),
)
print(result.final_output)
```

### Stage 3: Validate and format the synthesized output

```python
validated_output = validate_handler_final_output(current_agent, handler_result.final_output)
output_text = format_final_output_text(current_agent, validated_output)
synthesized_item = create_message_output_item(current_agent, output_text)
```

**Key insight:** `validate_handler_final_output()` checks that the synthesized output matches the agent's `output_type`. If the agent expects a Pydantic model but the handler returns a string, a `UserError` is raised. This prevents silent type mismatches.

If `include_in_history=True`:

```python
if include_in_history:
    generated_items.append(synthesized_item)
    session_items.append(synthesized_item)
```

The synthesized message is added to both the model's continuation items (so the LLM could see it if resumed) and the session (so it persists).

Then the engine runs `run_final_output_hooks()` and output guardrails on the synthesized output — the same as any normal final output. This ensures that even error-handler-synthesized outputs go through the full safety pipeline.

### Runner Exception Hierarchy

When the runner encounters errors, different exceptions have different termination behaviors:

```
AgentsException                              ← Base for ALL SDK exceptions
├── run_data: RunErrorDetails | None
│
├── MaxTurnsExceeded                         ← Turn limit reached
│   └── (no handler) → run terminates
│   └── (with handler) → handler may synthesize output
│
├── InputGuardrailTripwireTriggered          ← Input guardrail on first turn
│   └── guardrail_result: InputGuardrailResult
│   └── run terminates (session input persisted first)
│
├── OutputGuardrailTripwireTriggered         ← Output guardrail on final output
│   └── guardrail_result: OutputGuardrailResult
│   └── run terminates
│
├── ModelBehaviorError                       ← LLM sent invalid response
│   └── message: str
│   └── run terminates (caught in outer try/except)
│
├── UserError                                ← User misconfigured something
│   └── message: str
│   └── run terminates
│
└── ToolTimeoutError / Tool*GuardrailTripwireTriggered
    └── (see Ch3 §3.7 for tool-level exceptions)
```

| Exception | Can it be recovered? | How |
|---|---|---|
| `MaxTurnsExceeded` | ✅ Yes | `error_handlers={"max_turns": handler}` |
| `InputGuardrailTripwireTriggered` | ❌ No | Run terminates, but input is persisted in session |
| `OutputGuardrailTripwireTriggered` | ❌ No | Run terminates, final output rejected |
| `ModelBehaviorError` | ❌ No | Run terminates, but retries may have been attempted first |
| `UserError` | ❌ No | Configuration error, must fix code |

---

## 4.10 `Runner.run()` vs `Runner.run_streamed()` vs `Runner.run_sync()`

| Method | Returns | When to use |
|---|---|---|
| `Runner.run()` | `RunResult` (await) | Standard usage — wait for complete result |
| `Runner.run_streamed()` | `RunResultStreaming` (immediate) | Real-time UI — iterate events as they arrive |
| `Runner.run_sync()` | `RunResult` (blocking) | Scripts/no-async — wraps `run()` in `asyncio.run()` |

**Under the hood:**

- `run()` and `run_sync()` both use `run_single_turn()` — the non-streaming path
- `run_streamed()` uses `start_streaming()` → `run_single_turn_streamed()` — the streaming path
- `run_streamed()` starts a **background task** that feeds events into an `asyncio.Queue`
- The user iterates via `stream_events()` which yields from the queue until `QueueCompleteSentinel`

```python
class QueueCompleteSentinel:
    """Sentinel used to signal completion when streaming run loop results."""

QUEUE_COMPLETE_SENTINEL = QueueCompleteSentinel()
```

**Key constraint:** `run_sync()` will **not work** inside an existing event loop (e.g., Jupyter, FastAPI). For those, use `run()`.

### `RunResult` vs `RunResultStreaming`: Comparison

| Aspect | `RunResult` | `RunResultStreaming` |
|---|---|---|
| **How you get it** | `await Runner.run()` | `Runner.run_streamed()` (no await) |
| **`final_output`** | Available immediately | Available after `is_complete` is True |
| **`stream_events()`** | Not available | Async iterator yielding `StreamEvent` |
| **`is_complete`** | Always True | False until loop finishes |
| **`raw_responses`** | All responses at once | Grows as turns complete |
| **`new_items`** | All items at once | Grows as items are generated |
| **Cancel** | Not supported | `cancel("immediate")` or `cancel("after_turn")` |
| **Current agent** | Final agent | Changes as handoffs occur |
| **Usage** | Final usage | Updated incrementally |
| **Interruptions** | Available in result | Available when `is_complete` is True |

---

## 4.11 🔥 Source Code Walkthrough: The Streaming Path

`run_streamed()` is architecturally different from `run()`. Instead of awaiting the full result, it returns a `RunResultStreaming` immediately and runs the loop in a background task.

### The event queue architecture:

```
Background Task                    User Code
┌──────────────────┐              ┌──────────────────┐
│ start_streaming() │              │ for event in      │
│   │               │              │   result.         │
│   ├── turn 1      │              │   stream_events():│
│   │   ├── RawResp │──queue──→    │     yield event   │
│   │   ├── ToolCall│──queue──→    │     yield event   │
│   │   └── ...     │              │                    │
│   ├── turn 2      │              │                    │
│   │   └── ...     │──queue──→    │                    │
│   └── SENTINEL    │──queue──→    │   break (done!)   │
└──────────────────┘              └──────────────────┘
```

### `start_streaming()` — The streaming loop

The function is ~500 lines and mirrors the non-streaming `AgentRunner.run()` loop, but with key differences:

**Difference 1: Event queue instead of return values**

```python
streamed_result._event_queue.put_nowait(RawResponsesStreamEvent(data=event))
# ...
streamed_result._event_queue.put_nowait(RunItemStreamEvent(item=tool_item, name="tool_called"))
# ...
streamed_result._event_queue.put_nowait(QueueCompleteSentinel())
```

**Difference 2: Guardrail results stream into a queue**

```python
async def run_input_guardrails_with_queue(
    agent, guardrails, input, context, streamed_result, parent_span,
) -> None:
    queue = streamed_result._input_guardrail_queue
    guardrail_tasks = [
        asyncio.create_task(run_single_input_guardrail(agent, guardrail, input, context))
        for guardrail in guardrails
    ]
    for done in asyncio.as_completed(guardrail_tasks):
        result = await done
        if result.output.tripwire_triggered:
            for t in guardrail_tasks:
                t.cancel()
            # ... put result in queue, break
        queue.put_nowait(result)
```

**Difference 3: Output guardrails run as a background task**

```python
streamed_result._output_guardrails_task = asyncio.create_task(
    run_output_guardrails(agent.output_guardrails + ..., agent, output, context_wrapper)
)
```

This means the `RunResultStreaming` can be marked as complete (`is_complete = True`) while output guardrails are still running. The guardrail check happens in the `finally` block.

**Difference 4: Streaming uses `stream_response_with_retry()` instead of `get_response_with_retry()`**

```python
retry_stream = stream_response_with_retry(
    get_stream=lambda: model.stream_response(...),
    rewind=rewind_model_request,
    retry_settings=model_settings.retry,
    ...
)

async for event in retry_stream:
    streamed_result._event_queue.put_nowait(RawResponsesStreamEvent(data=event))
    # Process terminal_response, output_item_done events...
```

**Difference 5: Deduplication of already-emitted items**

Since streaming emits `ToolCallItem`, `ReasoningItem`, etc. as they arrive, the final `SingleStepResult` would contain duplicates. The engine filters them:

```python
if emitted_tool_call_ids:
    items_to_filter = [item for item in items_to_filter if not (
        isinstance(item, ToolCallItem)
        and (call_id := getattr(item.raw_item, "call_id", ...))
        and call_id in emitted_tool_call_ids
    )]
```

### `run_single_turn_streamed()` — One streamed turn

This function mirrors `run_single_turn()` but:
1. Uses `stream_response_with_retry()` instead of `get_response_with_retry()`
2. Emits events into the queue as they arrive
3. Checks for input guardrail tripwires between model response and tool execution
4. Returns a `SingleStepResult` (same as non-streaming) for the outer loop to process

### Real-time text display example

The most common streaming use case is displaying text as it arrives:

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are a helpful assistant.")
result = Runner.run_streamed(agent, "Explain how the Runner works in 3 sentences")

async for event in result.stream_events():
    if event.type == "raw_response_event":
        data = event.data
        if hasattr(data, 'delta') and hasattr(data.delta, 'content'):
            for text_block in data.delta.content or []:
                if hasattr(text_block, 'text') and text_block.text:
                    print(text_block.text, end="", flush=True)
    elif event.type == "run_item_stream_event":
        if event.name == "tool_called":
            print(f"\n[Tool: {event.item.raw_item.name}]")
        elif event.name == "agent_updated":
            print(f"\n[Agent: {event.new_agent.name}]")

print()  # newline after streaming
print(f"Final output: {result.final_output}")
print(f"Is complete: {result.is_complete}")
```

**Key insight:** `stream_events()` yields two main event types:
- `RawResponsesStreamEvent` — raw LLM chunks (text deltas, tool call deltas)
- `RunItemStreamEvent` — semantic items (tool calls, reasoning, agent switches)

The raw events let you display text in real-time. The semantic events let you show structured progress (tool names, agent changes).

---

## 4.12 Turn Preparation: Four Resolver Functions

Before calling the model, the engine resolves four things via `turn_preparation.py`:

### `get_all_tools(agent, context_wrapper)` → `list[Tool]`

```python
async def get_all_tools(agent: Agent[Any], context_wrapper: RunContextWrapper[Any]) -> list[Tool]:
    return await agent.get_all_tools(context_wrapper)
```

This delegates to `Agent.get_all_tools()` which resolves MCP tools, checks `is_enabled`, and returns the final tool list. Cross-reference: Chapter 3 §3.12 covers `resolve_enabled_function_tools()`.

### `get_handoffs(agent, context_wrapper)` → `list[Handoff]`

```python
async def get_handoffs(agent, context_wrapper) -> list[Handoff]:
    handoffs = []
    for handoff_item in agent.handoffs:
        if isinstance(handoff_item, Handoff):
            handoffs.append(handoff_item)
        elif isinstance(handoff_item, Agent):
            handoffs.append(handoff(handoff_item))

    async def check_handoff_enabled(handoff_obj: Handoff) -> bool:
        attr = handoff_obj.is_enabled
        if isinstance(attr, bool):
            return attr
        res = attr(context_wrapper, agent)
        if inspect.isawaitable(res):
            return bool(await res)
        return bool(res)

    results = await asyncio.gather(*(check_handoff_enabled(h) for h in handoffs))
    return [h for h, ok in zip(handoffs, results, strict=False) if ok]
```

**Key insight:** Handoffs support dynamic `is_enabled` (just like tools). All `is_enabled` checks run concurrently via `asyncio.gather()`. Also, if `agent.handoffs` contains an `Agent` instead of a `Handoff`, it's automatically wrapped with `handoff()`.

### `get_output_schema(agent)` → `AgentOutputSchemaBase | None`

```python
def get_output_schema(agent):
    if agent.output_type is None or agent.output_type is str:
        return None
    elif isinstance(agent.output_type, AgentOutputSchemaBase):
        return agent.output_type
    return AgentOutputSchema(agent.output_type)
```

Returns `None` for plain text agents (no structured output), the schema object otherwise.

### `get_model(agent, run_config)` → `Model`

```python
def get_model(agent, run_config):
    if isinstance(run_config.model, Model):
        return run_config.model
    elif isinstance(run_config.model, str):
        return run_config.model_provider.get_model(run_config.model)
    elif isinstance(agent.model, Model):
        return agent.model
    return run_config.model_provider.get_model(agent.model)
```

**Priority:** `run_config.model` > `agent.model`. `run_config` always wins.

### `maybe_filter_model_input()` — The `call_model_input_filter` Hook

```python
async def maybe_filter_model_input(*, agent, run_config, context_wrapper, input_items, system_instructions):
    if run_config.call_model_input_filter is None:
        return ModelInputData(input=input_items, instructions=system_instructions)

    model_input = ModelInputData(input=input_items.copy(), instructions=system_instructions)
    filter_payload = CallModelData(model_data=model_input, agent=agent, context=context_wrapper.context)
    maybe_updated = run_config.call_model_input_filter(filter_payload)
    updated = await maybe_updated if inspect.isawaitable(maybe_updated) else maybe_updated
    if not isinstance(updated, ModelInputData):
        raise UserError("call_model_input_filter must return a ModelInputData instance")
    return updated
```

This is a powerful hook: it lets you modify the system instructions and input items **right before they're sent to the model**. Common use cases:
- Removing sensitive items from history
- Injecting additional context (e.g., current time, user location)
- Truncating long conversations to fit context windows

Cross-reference: See Chapter 1 §1.12 (`RunConfig`) for the `call_model_input_filter` parameter.

### `maybe_reset_tool_choice()` — Preventing Infinite Tool Loops

When an agent has `tool_choice="required"` (forcing the LLM to always call a tool), the loop would never end — the LLM would keep calling tools forever. `maybe_reset_tool_choice()` prevents this:

```python
def maybe_reset_tool_choice(
    agent: Agent[Any],
    tool_use_tracker: AgentToolUseTracker,
    model_settings: ModelSettings,
) -> ModelSettings:
    if agent.reset_tool_choice is True and tool_use_tracker.has_used_tools(agent):
        return dataclasses.replace(model_settings, tool_choice=None)
    return model_settings
```

After the first tool is used, `AgentToolUseTracker` records it. On subsequent turns, if `agent.reset_tool_choice` is `True`, `tool_choice` is reset to `None` (auto mode), allowing the LLM to produce a final output instead of being forced to call another tool.

**`AgentToolUseTracker`** tracks which tools each agent has used:

```python
class AgentToolUseTracker:
    def __init__(self) -> None:
        self.agent_map: dict[str, set[str]] = {}
        self.agent_to_tools: list[tuple[Agent[Any], list[str]]] = []

    def record_used_tools(self, agent: Agent[Any], tools: list[ToolRunFunction]) -> None:
        tool_names = [get_function_tool_trace_name(tool.function_tool) or tool.function_tool.name for tool in tools]
        self.add_tool_use(agent, tool_names)
```

The tracker is serialized into `RunResult._tool_use_tracker_snapshot` and hydrated back when resuming from a `RunState`, so the reset logic works correctly across interruptions.

Cross-reference: See Chapter 2 §2.11 for the `reset_tool_choice` field and the complete loop prevention strategy.

---

## 4.13 Session Persistence Within the Loop

The engine saves to the session at **multiple points** during a run, not just at the end:

```
Session Save Points:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  1. INITIAL INPUT SAVE                                          │
│     Before the first turn: save the user's input items          │
│     so they're persisted even if a guardrail trips.             │
│                                                                 │
│  2. AFTER EACH TURN (NextStepRunAgain)                          │
│     Save new_step_items after tool execution.                   │
│     Uses _current_turn_persisted_item_count to avoid            │
│     duplicating items on streaming retries.                     │
│                                                                 │
│  3. AFTER FINAL OUTPUT (NextStepFinalOutput)                    │
│     Save the final turn's items.                                │
│     If using OpenAIConversationsSession, may trigger            │
│     compaction (replaces items with a server-side summary).     │
│                                                                 │
│  4. AFTER INTERRUPTION (NextStepInterruption)                   │
│     Save items so the interrupted state can be resumed.         │
│                                                                 │
│  5. ON GUARDRAIL TRIP                                           │
│     Save the user's input items so they aren't lost             │
│     when the run is aborted by a guardrail.                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Compaction: When Sessions Shrink

When using `OpenAIConversationsSession`, the engine may trigger **compaction** after a final output:

```python
if is_openai_responses_compaction_aware_session(session):
    has_local_tool_outputs = any(
        isinstance(item, ToolCallOutputItem | HandoffOutputItem) for item in new_items
    )
    if has_local_tool_outputs:
        defer_compaction(...)  # Can't compact yet — LLM needs these outputs
        return
    await session.run_compaction(compaction_args)
```

**Key insight:** Compaction is **deferred** if the turn produced local tool outputs or handoffs. These outputs are needed as conversation history for the next turn — compacting them away would break the LLM's context. The compaction runs on the *next* turn when those outputs have been incorporated into the server's conversation state.

Cross-reference: See Chapter 5 for full session management and RunState serialization.

---

## 4.14 Putting It All Together: A Multi-Turn Run with Handoff

Let's trace a complete 3-turn run that involves tool execution, a handoff, and final output:

```python
from agents import Agent, Runner, function_tool, handoff, RunContextWrapper
from pydantic import BaseModel

class BillingIssue(BaseModel):
    issue_type: str
    amount: float | None = None

@function_tool
async def lookup_account(account_id: str) -> str:
    return f"Account {account_id}: Premium plan, balance $49.99, last payment 2026-04-15"

@function_tool
async def create_refund(account_id: str, amount: float) -> str:
    return f"Refund of ${amount} created for account {account_id}. Refund ID: REF-789"

billing_agent = Agent[BillingIssue](
    name="Billing Agent",
    instructions="Handle billing inquiries. Use tools to look up accounts and create refunds.",
    tools=[lookup_account, create_refund],
    output_type=BillingIssue,
)

triage_agent = Agent(
    name="Triage Agent",
    instructions="Help users with their questions. Hand off to billing for payment issues.",
    handoffs=[handoff(billing_agent)],
)

result = await Runner.run(triage_agent, "I need a refund for my account acc-123, I was charged $49.99 incorrectly")
```

### What happens across 3 turns:

**Turn 1: Triage Agent decides to hand off**

```
Triage Agent receives: "I need a refund for my account acc-123..."
    │
    ├── LLM response: function_call(name="transfer_to_billing_agent", ...)
    │
    ├── process_model_response() → ProcessedResponse(handoffs=[ToolRunHandoff(...)])
    │
    ├── execute_handoffs()
    │   ├── handoff.on_invoke_handoff() → returns billing_agent
    │   ├── HandoffOutputItem added to new_step_items
    │   ├── hooks.on_handoff() fires
    │   └── Returns NextStepHandoff(new_agent=billing_agent)
    │
    └── current_agent = billing_agent, should_run_agent_start_hooks = True
```

**Turn 2: Billing Agent looks up the account**

```
Billing Agent receives: original input + handoff output
    │
    ├── Agent start hooks fire
    ├── get_all_tools() → [lookup_account, create_refund]
    ├── get_output_schema() → AgentOutputSchema(BillingIssue)
    │
    ├── LLM response: function_call(name="lookup_account", arguments='{"account_id": "acc-123"}')
    │
    ├── process_model_response() → ProcessedResponse(functions=[ToolRunFunction(...)])
    │
    ├── execute_tools_and_side_effects()
    │   ├── Input guardrails on lookup_account? → No (tool guardrails, not agent guardrails)
    │   ├── invoke_function_tool(lookup_account, ...) → "Account acc-123: Premium plan..."
    │   ├── ToolCallItem + ToolCallOutputItem added
    │   └── check_for_final_output_from_tools() → NOT_FINAL_OUTPUT (run_llm_again)
    │
    └── Returns NextStepRunAgain → continue loop
```

**Turn 3: Billing Agent creates refund and produces structured output**

```
Billing Agent receives: full history including tool result
    │
    ├── LLM response: function_call(name="create_refund", arguments='{"account_id": "acc-123", "amount": 49.99}')
    │
    ├── execute_tools_and_side_effects()
    │   ├── invoke_function_tool(create_refund, ...) → "Refund of $49.99 created..."
    │   └── check_for_final_output_from_tools() → NOT_FINAL_OUTPUT
    │
    ├── LLM response (turn 4 within this step): final output text
    │   └── Parsed as BillingIssue(issue_type="refund", amount=49.99)
    │
    └── Returns NextStepFinalOutput(output=BillingIssue(...))
```

### Post-run analysis:

```python
print(result.final_output)
# BillingIssue(issue_type='refund', amount=49.99)

print(f"Turns: {len(result.raw_responses)}")
# Turns: 3

print(f"Last agent: {result.last_agent.name}")
# Last agent: Billing Agent

for item in result.new_items:
    print(f"  {type(item).__name__}: {getattr(item, 'type', 'N/A')}")
#   HandoffOutputItem: handoff_output_item
#   ToolCallItem: tool_call_item
#   ToolCallOutputItem: tool_call_output_item
#   ToolCallItem: tool_call_item
#   ToolCallOutputItem: tool_call_output_item
#   MessageOutputItem: message_output_item

print(f"Total tokens: {result.context_wrapper.usage.total_tokens}")
# Total tokens: 1847

for resp in result.raw_responses:
    print(f"  Response {resp.response_id}: {resp.usage.input_tokens}in/{resp.usage.output_tokens}out")
#   Response resp_001: 412in/89out
#   Response resp_002: 523in/67out
#   Response resp_003: 598in/158out
```

### What `to_input_list()` looks like after 3 turns:

```python
result.to_input_list()
# [
#   {"role": "user", "content": "I need a refund for my account acc-123..."},
#   {"type": "function_call", "name": "transfer_to_billing_agent", "call_id": "call_1", ...},
#   {"type": "function_call_output", "call_id": "call_1", "output": "Transferring to Billing Agent"},
#   {"type": "function_call", "name": "lookup_account", "call_id": "call_2",
#    "arguments": '{"account_id": "acc-123"}'},
#   {"type": "function_call_output", "call_id": "call_2",
#    "output": "Account acc-123: Premium plan, balance $49.99..."},
#   {"type": "function_call", "name": "create_refund", "call_id": "call_3",
#    "arguments": '{"account_id": "acc-123", "amount": 49.99}'},
#   {"type": "function_call_output", "call_id": "call_3",
#    "output": "Refund of $49.99 created..."},
# ]
```

Every handoff, tool call, and tool output is included in the conversation history. This is the complete audit trail.

---

## 4.15 Key Takeaways

1. **The Runner is a turn-based state machine** — `NextStep*` types make decisions explicit and testable
2. **One turn = preparation → model call → process → execute → decide** — `run_single_turn()` orchestrates all five phases
3. **Input guardrails run once, output guardrails run per final output** — sequential guardrails block before model call; parallel guardrails run concurrently with it
4. **Model retries use exponential backoff + session rewind** — the `rewind_model_request()` function rolls back persisted items before retrying to prevent duplicates
5. **Streaming uses an async queue with a sentinel** — events are emitted as they arrive; `QueueCompleteSentinel` signals the end
6. **`AgentBindings` separates public agent from execution agent** — sandbox-prepared agents are clones with modified settings
7. **`tool_use_behavior` controls whether tools become final output** — `"run_llm_again"`, `"stop_on_first_tool"`, dict, or callable
8. **`call_model_input_filter` is the last-mile hook** — modify system instructions and input items right before the LLM call
9. **Session persistence happens at 5 save points** — not just at the end, but also after each turn, interruption, and guardrail trip
10. **`MaxTurnsExceeded` has a handler pipeline** — error handlers can synthesize a final output that goes through output guardrails before being returned
11. **Compaction is deferred when local tool outputs exist** — the server can't compact away items the LLM still needs as context
12. **`ProcessedResponse` categorizes all model output types** — hosted tools (file_search, web_search) don't need local execution; local tools (function, computer, shell) do
