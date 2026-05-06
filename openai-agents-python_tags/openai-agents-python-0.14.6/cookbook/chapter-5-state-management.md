# Chapter 5: State Management — RunContext, Session & RunState

This chapter covers the three state subsystems that make the Agents SDK work across turns, tools, and interruptions:

1. **RunContextWrapper** — per-run mutable state (your data + usage + approvals)
2. **Session** — conversation persistence across `Runner.run()` calls
3. **RunState** — durable pause/resume for human-in-the-loop flows

Chapter 1 §1.11 introduced the three multi-turn strategies (`to_input_list`, Session, `previous_response_id`). This chapter goes deep into **how they're implemented** and **how to extend them**.

**How to Read This Chapter**

- **Pass 1 — Build intuition (15 min).** Read §5.1 (the big picture) → §5.2 (RunContextWrapper fields only) → §5.5 (Session protocol only) → §5.9 (RunState field tables only) → §5.14 (key takeaways only). Skip all 🔥 source code walkthroughs.
- **Pass 2 — Dive into source code (40 min).** Read the three 🔥 walkthroughs: §5.3 (Approval System), §5.9 (RunState serialization), §5.10 (Session persistence internals). Also read §5.7 (OpenAIConversationsSession) and §5.8 (CompactionSession).
- **Pass 3 — Fill gaps.** Itemized list:
  - RunContextWrapper fields and generics? → §5.2 (6-row field table + fork methods)
  - Approval system: per-call, always, rejection messages? → §5.3 (🔥 source code walkthrough + 3×3 decision table)
  - `_fork_with_tool_input` / `_fork_without_tool_input`? → §5.4 (source code + shared-state diagram)
  - AgentHookContext vs RunContextWrapper? → §5.4 (comparison table)
  - Session protocol: methods and backends? → §5.5 (Protocol source + 7-row comparison table)
  - SessionInputCallback? → §5.6 (source code + 3 example patterns)
  - OpenAIConversationsSession? → §5.7 (source code + lazy initialization)
  - OpenAIResponsesCompactionSession? → §5.8 (compaction flow diagram + 3 modes)
  - RunState fields and schema versioning? → §5.9 (🔥 30+ field table + schema policy)
  - RunState to_json/from_json? → §5.10 (🔥 serialization walkthrough + context serializer strategies)
  - Session persistence internals? → §5.11 (🔥 prepare_input_with_session + save_result_to_session + rewind)
  - RunItem type hierarchy? → §5.12 (full tree + 10-row type table + release_agent)
  - Putting it together + HITL flow? → §5.13 (complete 3-round HITL example + RunState JSON output)
  - Key takeaways? → §5.14

---

## 5.1 The Big Picture: Three State Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 1: RunContextWrapper                                         │
│  • Your custom data (TContext)                                      │
│  • Usage tracking (tokens per turn, cumulative)                     │
│  • Approval state (per-tool, per-call-id, always-approve/reject)    │
│  • Forked for concurrent tool execution                             │
│  → Lives ONLY during one run                                        │
│  → NOT serialized (you provide context on each run)                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│  Layer 2: Session                                                   │
│  • Conversation history (TResponseInputItem list)                   │
│  • Automatic load-before / save-after each Runner.run()             │
│  • Multiple backends (SQLite, Redis, OpenAI Conversations, etc.)    │
│  → Persists ACROSS runs                                             │
│  → Serialized by the backend (SQLite rows, Redis keys, etc.)        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│  Layer 3: RunState                                                  │
│  • Full run snapshot (agent, items, turn count, guardrail results)  │
│  • Pending interruptions (tool approvals)                           │
│  • Context (with custom serializer/deserializer)                    │
│  • Schema versioning (CURRENT_SCHEMA_VERSION = "1.9")               │
│  → Can be serialized to JSON and resumed later                      │
│  → For human-in-the-loop pause/resume                               │
└─────────────────────────────────────────────────────────────────────┘
```

**Key distinction:** RunContextWrapper is your *runtime* scratchpad. Session is your *conversation* memory. RunState is your *resume* checkpoint.

---

## 5.2 RunContextWrapper: Your Data + SDK Data

The `RunContextWrapper` (from `src/agents/run_context.py`) is the object that gets passed to every tool, hook, and guardrail during a run. It carries your custom context alongside SDK-managed state.

```python
@dataclass(eq=False)
class RunContextWrapper(Generic[TContext]):
    context: TContext
    usage: Usage = field(default_factory=Usage)
    turn_input: list[TResponseInputItem] = field(default_factory=list)
    _approvals: dict[str, _ApprovalRecord] = field(default_factory=dict)
    tool_input: Any | None = None
```

**Field-by-field:**

| Field | Type | What it stores | Who reads it |
|---|---|---|---|
| `context` | `TContext` (your type) | Your custom data — DB connections, user info, config | Your tools, hooks, guardrails |
| `usage` | `Usage` | Token counts: `input_tokens`, `output_tokens`, `total_tokens` (cumulative across all turns) | `result.context_wrapper.usage` after run |
| `turn_input` | `list[TResponseInputItem]` | The input items for the current turn (set by the runner before each turn) | Hooks that need to inspect current turn |
| `_approvals` | `dict[str, _ApprovalRecord]` | Approval/rejection state per tool name | `is_tool_approved()`, tool execution pipeline |
| `tool_input` | `Any | None` | Structured input for the current agent tool run (set when agent-as-tool is active) | Agent tool implementations |

### The Generic Pattern

```python
from dataclasses import dataclass
from agents import Agent, Runner, RunContextWrapper, function_tool

@dataclass
class AppContext:
    db_pool: Any
    user_id: str
    permissions: set[str]

@function_tool
async def query_orders(ctx: RunContextWrapper[AppContext], order_id: str) -> str:
    pool = ctx.context.db_pool
    user = ctx.context.user_id
    if "read_orders" not in ctx.context.permissions:
        return "Permission denied"
    return f"Order {order_id} for {user}: $49.99"

agent = Agent[AppContext](
    name="OrderAgent",
    instructions="Help with orders",
    tools=[query_orders],
)

ctx = AppContext(db_pool=my_pool, user_id="u-123", permissions={"read_orders"})
result = await Runner.run(agent, "Check order ORD-456", context=ctx)
```

The `Generic[TContext]` means your tool functions get **full type hints** — `ctx.context` is typed as `AppContext`, not `Any`.

---

## 5.3 🔥 Source Code Walkthrough: The Approval System

The approval system inside `RunContextWrapper` is one of the most complex subsystems. Let's walk through the source.

### The `_ApprovalRecord` data structure

```python
@dataclass(eq=False)
class _ApprovalRecord:
    approved: bool | list[str] = field(default_factory=list)
    rejected: bool | list[str] = field(default_factory=list)
    rejection_messages: dict[str, str] = field(default_factory=dict)
    sticky_rejection_message: str | None = None
```

**The `bool | list[str]` pattern is the key insight:**

| Value | Meaning |
|---|---|
| `approved = True` | ALL calls to this tool are approved (always-approve) |
| `approved = ["call_1", "call_3"]` | Only specific call IDs are approved |
| `approved = []` (default) | Nothing is approved yet |
| `rejected = True` | ALL calls to this tool are rejected (always-reject) |
| `rejected = ["call_2"]` | Only specific call IDs are rejected |

### The decision logic: `_get_approval_status_for_key()`

```python
def _get_approval_status_for_key(self, approval_key: str, call_id: str) -> bool | None:
    approval_entry = self._approvals.get(approval_key)
    if not approval_entry:
        return None

    if approval_entry.approved is True and approval_entry.rejected is True:
        return True  # Approval takes precedence

    if approval_entry.approved is True:
        return True

    if approval_entry.rejected is True:
        return False

    approved_ids = set(approval_entry.approved) if isinstance(approval_entry.approved, list) else set()
    rejected_ids = set(approval_entry.rejected) if isinstance(approval_entry.rejected, list) else set()

    if call_id in approved_ids:
        return True
    if call_id in rejected_ids:
        return False
    return None
```

**Decision matrix:**

| Scenario | `approved` | `rejected` | Result for `call_id` |
|---|---|---|---|
| No decision yet | `[]` | `[]` | `None` (ask user) |
| Always approved | `True` | `[]` | `True` |
| Always rejected | `[]` | `True` | `False` |
| Both True (edge) | `True` | `True` | `True` (approve wins) |
| Per-call approved | `["call_1"]` | `[]` | `True` for `call_1`, `None` for others |
| Per-call rejected | `[]` | `["call_2"]` | `False` for `call_2`, `None` for others |
| Mixed per-call | `["call_1"]` | `["call_2"]` | `True`/`False`/`None` depending on call_id |

### The public API

```python
ctx.approve_tool(approval_item, always_approve=False)
ctx.reject_tool(approval_item, always_reject=False, rejection_message="Not allowed!")
status = ctx.is_tool_approved(tool_name, call_id)
message = ctx.get_rejection_message(tool_name, call_id)
```

**Key insight #1:** `always_approve=True` sets `approved = True` (boolean, not a list), which means ALL future calls to this tool are automatically approved.

**Key insight #2:** `rejection_message` is stored per-call-id in `rejection_messages`, or as `sticky_rejection_message` when `always_reject=True`. When the run resumes, the rejection message is sent back to the model as the tool output.

**Key insight #3:** The approval key resolution is complex — it uses `get_function_tool_approval_keys()` which considers `tool_name`, `tool_namespace`, and `tool_lookup_key`. This means a namespaced MCP tool like `stripe.create_charge` can have a different approval record than a bare `create_charge`.

---

## 5.4 Forking: How RunContextWrapper Is Shared Across Tools

When multiple tools execute concurrently, each needs its own context but must share approval state and usage tracking. The SDK uses a **fork pattern**:

### 🔥 Source Code: `_fork_with_tool_input` and `_fork_without_tool_input`

```python
def _fork_with_tool_input(self, tool_input: Any) -> RunContextWrapper[TContext]:
    fork = RunContextWrapper(context=self.context)
    fork.usage = self.usage
    fork._approvals = self._approvals
    fork.turn_input = self.turn_input
    fork.tool_input = tool_input
    return fork

def _fork_without_tool_input(self) -> RunContextWrapper[TContext]:
    fork = RunContextWrapper(context=self.context)
    fork.usage = self.usage
    fork._approvals = self._approvals
    fork.turn_input = self.turn_input
    return fork
```

```
Original RunContextWrapper
├── context: AppContext       ← shared reference (not copied)
├── usage: Usage              ← shared reference (not copied)
├── _approvals: dict          ← shared reference (not copied)
├── turn_input: list          ← shared reference (not copied)
└── tool_input: None
        │
        ├── _fork_with_tool_input(ToolA_input)
        │   ├── context: AppContext   (same object)
        │   ├── usage: Usage          (same object)
        │   ├── _approvals: dict      (same object)
        │   └── tool_input: ToolA_input  ← unique per fork
        │
        ├── _fork_with_tool_input(ToolB_input)
        │   ├── context: AppContext   (same object)
        │   ├── usage: Usage          (same object)
        │   ├── _approvals: dict      (same object)
        │   └── tool_input: ToolB_input  ← unique per fork
        │
        └── _fork_without_tool_input()  (for hooks, guardrails)
            ├── context: AppContext   (same object)
            ├── usage: Usage          (same object)
            ├── _approvals: dict      (same object)
            └── tool_input: None
```

**Key insight:** The fork creates a NEW `RunContextWrapper` instance, but shares the underlying `context`, `usage`, and `_approvals` objects. This means:
- If Tool A approves a tool, Tool B (running concurrently) immediately sees the approval
- If Tool A updates `usage`, the cumulative count is visible to Tool B
- But `tool_input` is unique per fork, so each tool sees only its own input

### `AgentHookContext` — A Subclass for Hooks

```python
@dataclass(eq=False)
class AgentHookContext(RunContextWrapper[TContext]):
    """Context passed to agent hooks (on_start, on_end)."""
```

It's a simple subclass — no extra fields. The distinction is purely **type-level**:

| Aspect | `RunContextWrapper` | `AgentHookContext` |
|---|---|---|
| Passed to | Tools, guardrails, hooks | `on_agent_start`, `on_agent_end` hooks |
| Type | `RunContextWrapper[TContext]` | `AgentHookContext[TContext]` |
| Extra fields | None | None (just a type marker) |
| Why separate? | Type safety | Lets you write type-specific hook signatures |

---

## 5.5 The Session Protocol: What Every Backend Implements

The `Session` protocol (from `src/agents/memory/session.py`) defines the interface that all session backends must implement:

```python
@runtime_checkable
class Session(Protocol):
    session_id: str
    session_settings: SessionSettings | None = None

    async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]: ...
    async def add_items(self, items: list[TResponseInputItem]) -> None: ...
    async def pop_item(self) -> TResponseInputItem | None: ...
    async def clear_session(self) -> None: ...
```

**Method-by-method:**

| Method | Purpose | When called by the runner |
|---|---|---|
| `get_items(limit)` | Load history (latest N items, chronological order) | Before each `Runner.run()` — prepended to input |
| `add_items(items)` | Append new conversation items | After each turn — saves new `RunItem`s as `TResponseInputItem`s |
| `pop_item()` | Remove and return the most recent item | Used for rewinding after failed retries |
| `clear_session()` | Delete all items for this session | Used by compaction (replaces old items with compacted version) |

There's also `SessionABC` — an abstract base class for internal use. Third-party backends should implement the `Session` **protocol** instead (no inheritance required).

### Available Session Backends

| Backend | Import | Storage | Thread Safety | Best For |
|---|---|---|---|---|
| `SQLiteSession` | `from agents.memory import SQLiteSession` | SQLite file (`:memory:` or path) | Thread-local connections + file lock | Local dev, single-process apps |
| `OpenAIConversationsSession` | `from agents.memory import OpenAIConversationsSession` | OpenAI Conversations API | API-level | Server-managed history, no local DB |
| `OpenAIResponsesCompactionSession` | `from agents.memory import OpenAIResponsesCompactionSession` | Wraps another session + `responses.compact` API | Delegates to underlying | Long conversations that need compaction |
| Custom | Implement `Session` protocol | Any (Redis, PostgreSQL, etc.) | You implement | Production requirements |

**Note:** `InMemorySession`, `EncryptedSession`, `SQLAlchemySession`, and `RedisSession` are mentioned in docs but not in the current `memory/__init__.py`. Check your SDK version for availability.

### `SessionSettings` — Configuring Session Behavior

```python
@dataclass
class SessionSettings:
    limit: int | None = None

    def resolve(self, override: SessionSettings | None) -> SessionSettings:
        if override is None:
            return self
        changes = {
            field.name: getattr(override, field.name)
            for field in fields(self)
            if getattr(override, field.name) is not None
        }
        return replace(self, **changes)
```

Currently `SessionSettings` only has `limit` (max items to retrieve). The `resolve()` method follows the same pattern as `ModelSettings.resolve()` — non-None values from the override win.

---

## 5.6 `SessionInputCallback`: Custom History Merging

Before the runner sends input to the model, it needs to merge session history with the new turn input. The `SessionInputCallback` lets you customize this:

```python
SessionInputCallback = Callable[
    [list[TResponseInputItem], list[TResponseInputItem]],
    MaybeAwaitable[list[TResponseInputItem]],
]
```

The first argument is `history_items` (from `session.get_items()`), the second is `new_items` (the current turn input). You return the merged list.

### Three common patterns:

**Pattern 1: Trim old history (sliding window)**

```python
async def sliding_window(history: list, new_items: list) -> list:
    max_history = 20
    trimmed = history[-max_history:] if len(history) > max_history else history
    return trimmed + new_items

result = await Runner.run(
    agent, "Hello",
    session=session,
    run_config=RunConfig(session_input_callback=sliding_window),
)
```

**Pattern 2: Prioritize recent context**

```python
async def recent_first(history: list, new_items: list) -> list:
    system_items = [h for h in history if h.get("role") == "system"]
    other_items = [h for h in history if h.get("role") != "system"]
    return system_items + other_items[-10:] + new_items
```

**Pattern 3: Filter sensitive items**

```python
async def filter_secrets(history: list, new_items: list) -> list:
    def is_safe(item):
        content = str(item.get("content", ""))
        return "API_KEY" not in content and "password" not in content
    return [h for h in history if is_safe(h)] + new_items
```

**Key insight:** When `session_input_callback` is `None` (default), the SDK simply prepends all history to the new input. The callback gives you control over what the model actually sees, without changing what's stored in the session.

---

## 5.7 OpenAIConversationsSession: Server-Managed History

The `OpenAIConversationsSession` (from `src/agents/memory/openai_conversations_session.py`) uses the OpenAI Conversations API to store history on OpenAI's servers instead of locally:

```python
class OpenAIConversationsSession(SessionABC):
    def __init__(
        self,
        *,
        conversation_id: str | None = None,
        openai_client: AsyncOpenAI | None = None,
        session_settings: SessionSettings | None = None,
    ):
        self._session_id: str | None = conversation_id
        self.session_settings = session_settings or SessionSettings()
        _openai_client = openai_client
        if _openai_client is None:
            _openai_client = get_default_openai_client() or AsyncOpenAI()
        self._openai_client: AsyncOpenAI = _openai_client
```

**Key insight #1: Lazy initialization.** If you don't provide a `conversation_id`, the session creates one on the first API call:

```python
async def _get_session_id(self) -> str:
    if self._session_id is None:
        self._session_id = await start_openai_conversations_session(self._openai_client)
    return self._session_id
```

`start_openai_conversations_session()` calls `conversations.create(items=[])` to create an empty conversation on the server.

**Key insight #2: Accessing `session_id` before any API call raises `ValueError`:**

```python
@property
def session_id(self) -> str:
    if self._session_id is None:
        raise ValueError(
            "Session ID not yet available. The session is lazily initialized "
            "on first API call. Call get_items(), add_items(), or similar first."
        )
    return self._session_id
```

**Key insight #3: `clear_session()` deletes the conversation and resets the ID:**

```python
async def clear_session(self) -> None:
    session_id = await self._get_session_id()
    await self._openai_client.conversations.delete(conversation_id=session_id)
    await self._clear_session_id()  # sets _session_id = None
```

**Usage:**

```python
from agents import Agent, Runner
from agents.memory import OpenAIConversationsSession

session = OpenAIConversationsSession()
result1 = await Runner.run(agent, "Hello!", session=session)
print(f"Conversation ID: {session.session_id}")

result2 = await Runner.run(agent, "Follow up", session=session)
result3 = await Runner.run(agent, "One more", session=session)
```

---

## 5.8 OpenAIResponsesCompactionSession: Automatic History Compaction

Long conversations eventually exceed the model's context window. The `OpenAIResponsesCompactionSession` wraps another session and automatically calls the `responses.compact` API when history grows too large.

### The compaction flow:

```
Runner.run() completes a turn
    │
    ▼
save_result_to_session() adds new items to underlying session
    │
    ▼
OpenAIResponsesCompactionSession.add_items()
    ├── delegates to underlying.add_items(items)
    ├── updates _compaction_candidate_items (incremental)
    └── updates _session_items (incremental)
    │
    ▼
run_compaction() is called (by the runner or manually)
    │
    ├── _ensure_compaction_candidates() → count candidates
    │
    ├── should_trigger_compaction()?
    │   └── Default: candidates >= 10
    │
    ├── Yes → call responses.compact(model, input=items or previous_response_id)
    │   ├── underlying.clear_session()
    │   └── underlying.add_items(compacted_items)
    │
    └── No → skip, history stays as-is
```

### The three compaction modes:

| Mode | How history is provided | When to use |
|---|---|---|
| `"auto"` (default) | Uses `previous_response_id` if available and stored; falls back to `input` | Most cases |
| `"previous_response_id"` | Sends the last response ID to the server | When the last response was stored (`store=True`) |
| `"input"` | Sends the full session items as input | When responses weren't stored, or non-OpenAI models |

**Key insight:** The `should_trigger_compaction` hook is customizable:

```python
from agents.memory import OpenAIResponsesCompactionSession, SQLiteSession

def my_compaction_hook(context: dict) -> bool:
    candidates = context["compaction_candidate_items"]
    mode = context["compaction_mode"]
    if mode == "previous_response_id":
        return len(candidates) >= 20
    return len(candidates) >= 10

session = OpenAIResponsesCompactionSession(
    session_id="my-session",
    underlying_session=SQLiteSession("conversation.db"),
    model="gpt-4.1",
    should_trigger_compaction=my_compaction_hook,
)
```

**Important constraint:** `OpenAIResponsesCompactionSession` **cannot** wrap `OpenAIConversationsSession` because the Conversations API manages its own history:

```python
if isinstance(underlying_session, OpenAIConversationsSession):
    raise ValueError(
        "OpenAIResponsesCompactionSession cannot wrap OpenAIConversationsSession "
        "because it manages its own history on the server."
    )
```

---

## 5.9 🔥 Source Code Walkthrough: RunState — The Durable Pause/Resume Boundary

`RunState` (from `src/agents/run_state.py`) is the most complex state object in the SDK. It captures everything needed to resume an interrupted run.

### Schema Versioning

Before diving into fields, notice the schema policy at the top of the file:

```python
CURRENT_SCHEMA_VERSION = "1.9"

SCHEMA_VERSION_SUMMARIES: dict[str, str] = {
    "1.0": "Initial RunState snapshot format for HITL pause/resume flows.",
    "1.1": "Same payload as 1.0, but introduces explicit backward-read support policy.",
    "1.2": "Persists reasoning_item_id_policy for resumed and streamed follow-up turns.",
    "1.3": "Updates resumed trace semantics to reattach traces without duplicate starts.",
    "1.4": "Stores request_id alongside each serialized model response.",
    "1.5": "Renumbered unreleased baseline for tool-search snapshots and richer tool metadata.",
    "1.6": "Persists explicit approval rejection messages across resume flows.",
    "1.7": "Persists duplicate-name agent identities across agent-owned state and sandbox resume state.",
    "1.8": "Persists SDK-generated prompt cache keys across resume flows.",
    "1.9": "Persists pending custom tool calls and tool origin metadata across resume flows.",
}
SUPPORTED_SCHEMA_VERSIONS = frozenset(SCHEMA_VERSION_SUMMARIES)
```

**Schema policy rules:**
1. Keep versions shipped in releases readable
2. Unreleased versions may be renumbered or squashed
3. `to_json()` always emits `CURRENT_SCHEMA_VERSION`
4. Forward compatibility is intentionally **fail-fast** — older SDKs reject newer versions

### RunState fields (30+ fields, organized by category)

**Core state:**

| Field | Type | Purpose |
|---|---|---|
| `_current_turn` | `int` | Current turn number (0-based) |
| `_current_agent` | `TAgent | None` | The agent currently handling the conversation |
| `_starting_agent` | `TAgent | None` | The root agent (for stable identity resolution during resume) |
| `_original_input` | `str | list[Any]` | Original user input before any processing |
| `_max_turns` | `int` | Maximum allowed turns (default 10) |

**Conversation history:**

| Field | Type | Purpose |
|---|---|---|
| `_generated_items` | `list[RunItem]` | Items used to build model input when resuming; may be filtered by handoffs |
| `_session_items` | `list[RunItem]` | Full, unfiltered run items for session history |
| `_model_responses` | `list[ModelResponse]` | All model responses so far |
| `_current_turn_persisted_item_count` | `int` | How many items from this turn were already saved to session (prevents duplicates) |

**Server conversation:**

| Field | Type | Purpose |
|---|---|---|
| `_conversation_id` | `str | None` | For OpenAI server-managed conversation tracking |
| `_previous_response_id` | `str | None` | Response ID of the last server-managed response |
| `_auto_previous_response_id` | `bool` | Whether to automatically track previous_response_id |
| `_generated_prompt_cache_key` | `str | None` | SDK-generated prompt cache key (preserved across resume) |

**Guardrails:**

| Field | Type | Purpose |
|---|---|---|
| `_input_guardrail_results` | `list[InputGuardrailResult]` | Results from input guardrails |
| `_output_guardrail_results` | `list[OutputGuardrailResult]` | Results from output guardrails |
| `_tool_input_guardrail_results` | `list[ToolInputGuardrailResult]` | Results from tool input guardrails |
| `_tool_output_guardrail_results` | `list[ToolOutputGuardrailResult]` | Results from tool output guardrails |

**Interruption/resume:**

| Field | Type | Purpose |
|---|---|---|
| `_current_step` | `NextStepInterruption | None` | The interruption that paused the run |
| `_last_processed_response` | `ProcessedResponse | None` | Last processed model response (needed for resuming) |
| `_context` | `RunContextWrapper | None` | The run context (with approvals, usage) |

**Metadata:**

| Field | Type | Purpose |
|---|---|---|
| `_schema_version` | `str` | Schema version the snapshot was loaded from |
| `_tool_use_tracker_snapshot` | `dict[str, list[str]]` | Serialized agent→tools-used map |
| `_trace_state` | `TraceState | None` | Serialized trace metadata |
| `_reasoning_item_id_policy` | `"preserve" | "omit" | None` | How reasoning IDs appear in input |
| `_sandbox` | `dict | None` | Serialized sandbox resume payload |

### The constructor

```python
def __init__(
    self,
    context: RunContextWrapper[TContext],
    original_input: str | list[Any],
    starting_agent: TAgent,
    max_turns: int = 10,
    *,
    conversation_id: str | None = None,
    previous_response_id: str | None = None,
    auto_previous_response_id: bool = False,
):
    self._context = context
    self._original_input = _clone_original_input(original_input)
    self._starting_agent = starting_agent
    self._current_agent = starting_agent
    self._max_turns = max_turns
    self._conversation_id = conversation_id
    self._previous_response_id = previous_response_id
    self._auto_previous_response_id = auto_previous_response_id
    self._generated_prompt_cache_key = None
    self._reasoning_item_id_policy = None
    self._model_responses = []
    self._generated_items = []
    self._session_items = []
    self._input_guardrail_results = []
    self._output_guardrail_results = []
    self._tool_input_guardrail_results = []
    self._tool_output_guardrail_results = []
    self._current_step = None
    self._current_turn = 0
    self._last_processed_response = None
    self._generated_items_last_processed_marker = None
    self._current_turn_persisted_item_count = 0
    self._tool_use_tracker_snapshot = {}
    self._trace_state = None
    self._sandbox = None
    self._schema_version = CURRENT_SCHEMA_VERSION
    from .agent_tool_state import get_agent_tool_state_scope
    self._agent_tool_state_scope_id = get_agent_tool_state_scope(context)
```

### Public convenience methods

```python
state.get_interruptions()  # → list[ToolApprovalItem] from current_step
state.approve(approval_item, always_approve=False)  # delegates to context.approve_tool
state.reject(approval_item, always_reject=False, rejection_message=None)  # delegates to context.reject_tool
```

---

## 5.10 🔥 Source Code Walkthrough: RunState Serialization

The `to_json()` / `from_json()` methods are the heart of the pause/resume system. Let's walk through the key parts.

### `to_json()` — What gets serialized

```python
def to_json(
    self,
    *,
    context_serializer: ContextSerializer | None = None,
    strict_context: bool = False,
    include_tracing_api_key: bool = False,
) -> dict[str, Any]:
```

The output is a dictionary with these top-level keys:

```python
result = {
    "$schemaVersion": CURRENT_SCHEMA_VERSION,       # "1.9"
    "current_turn": self._current_turn,
    "current_agent": {"name": "BillingAgent", "identity": "..."},
    "original_input": [...],
    "model_responses": [...],
    "context": {
        "usage": {"input_tokens": 847, "output_tokens": 234, ...},
        "approvals": {"transfer_money": {"approved": True, "rejected": []}},
        "context": {"user_id": "u-123"},             # your custom context
        "context_meta": {"original_type": "dataclass", "serialized_via": "asdict", ...},
    },
    "tool_use_tracker": {"TriageAgent": ["lookup_account"]},
    "max_turns": 10,
    "no_active_agent_run": True,
    "guardrail_results": [...],
    "generated_items": [...],
    "session_items": [...],
    "current_step": {"type": "next_step_interruption", "data": {...}},
    "conversation_id": "conv_abc123",
    "previous_response_id": "resp_xyz789",
    "auto_previous_response_id": False,
    "generated_prompt_cache_key": None,
    "reasoning_item_id_policy": None,
    "current_turn_persisted_item_count": 3,
    "trace": None,
    "sandbox": None,
}
```

### Context serialization: the 5 strategies

The `_serialize_context_payload()` method tries 5 strategies in order:

| Priority | Strategy | When | `serialized_via` | `requires_deserializer` |
|---|---|---|---|---|
| 1 | None | `context` is None | `"none"` | No |
| 2 | Mapping passthrough | `context` is a `dict`/Mapping | `"mapping"` | No |
| 3 | `context_serializer` | You provided one | `"context_serializer"` | Yes |
| 4 | `model_dump()` | Context is a Pydantic model | `"model_dump"` | Yes |
| 5 | `dataclasses.asdict()` | Context is a dataclass | `"asdict"` | Yes |
| 6 | Omit (fallback) | None of the above | `"omitted"` | Yes |

**Key insight:** When `requires_deserializer` is True, the `context_meta` field captures the original type and class path so you can reconstruct it later. But the SDK **never auto-imports** the class — you must provide a `context_deserializer` or `context_override`.

**Error handling:** If `strict_context=True` and no serializer is provided for a non-mapping context, `to_json()` raises `UserError`. During `from_json()`, if the schema version is not in `SUPPORTED_SCHEMA_VERSIONS`, it raises `UserError` with a version mismatch message. For the full runner exception hierarchy (including `UserError`), see Chapter 4 §4.9.

### `from_json()` / `from_string()` — Deserialization

```python
@staticmethod
async def from_json(
    initial_agent: Agent[Any],
    state_json: dict[str, Any],
    *,
    context_override: ContextOverride | None = None,
    context_deserializer: ContextDeserializer | None = None,
    strict_context: bool = False,
) -> RunState[Any, Agent[Any]]:
```

**Parameters:**

| Parameter | Purpose | When to provide |
|---|---|---|
| `initial_agent` | The root agent for resolving agent references | Always |
| `state_json` | The serialized dict | Always |
| `context_override` | A `dict` or `RunContextWrapper` to use instead of the serialized context | When context was `omitted` or you want fresh state |
| `context_deserializer` | A function to rebuild your custom context type | When `requires_deserializer=True` |
| `strict_context` | If True, raise error for non-mapping contexts without serializer | Production safety |

### Complete round-trip example:

```python
from dataclasses import dataclass
from agents import Runner, RunState

@dataclass
class MyContext:
    user_id: str
    role: str

def serialize_ctx(ctx: MyContext) -> dict:
    return {"user_id": ctx.user_id, "role": ctx.role}

def deserialize_ctx(data: dict) -> MyContext:
    return MyContext(user_id=data["user_id"], role=data["role"])

# First run — pauses at an interruption
result1 = await Runner.run(agent, "Transfer $100", context=MyContext(user_id="u-1", role="admin"))
state = result1.to_state()

# Serialize with custom serializer
json_dict = state.to_json(context_serializer=serialize_ctx)

# ... save json_dict to database, user goes to lunch ...

# Deserialize with custom deserializer
restored_state = await RunState.from_json(
    initial_agent=agent,
    state_json=json_dict,
    context_deserializer=deserialize_ctx,
)

# Approve the pending tool call
for item in restored_state.get_interruptions():
    restored_state.approve(item)

# Resume
result2 = await Runner.run(agent, previous_run_state=restored_state)
```

---

## 5.11 🔥 Source Code Walkthrough: Session Persistence Internals

The `session_persistence.py` module (from `src/agents/run_internal/session_persistence.py`) is the bridge between the runner loop and the session backend. Let's walk through the three key functions.

### `prepare_input_with_session()` — Merging History with New Input

```
Runner.run(agent, "Hello", session=session)
       │
       ▼
prepare_input_with_session(input, session, callback, settings)
       │
       ├── session is None? → return (input, [])
       │
       ├── Resolve session_settings (explicit > session default)
       │
       ├── session.get_items(limit=resolved_limit) → history
       │
       ├── session_input_callback is None?
       │   ├── Yes → merged = history + new_items
       │   └── No  → merged = callback(history, new_items)
       │
       ├── Deduplicate (prefer latest version of each item)
       │
       └── Return (merged, session_items_snapshot)
            │
            ▼
       Merged input goes to model
       session_items_snapshot tracks what to persist
```

**Key insight:** The function returns TWO values: the prepared input (for the model) and the session items snapshot (for persistence). These can differ because the callback may reorder or filter history, but we must still persist the correct new items.

### `save_result_to_session()` — Saving After Each Turn

```python
async def save_result_to_session(
    session: Session | None,
    original_input: str | list[TResponseInputItem],
    new_items: list[RunItem],
    run_state: RunState | None = None,
    *,
    response_id: str | None = None,
    reasoning_item_id_policy: ReasoningItemIdPolicy | None = None,
    store: bool | None = None,
) -> int:
```

**The deduplication mechanism:**

```
Turn 1: new_items = [A, B, C]
    save_result_to_session() → saves A, B, C
    run_state._current_turn_persisted_item_count = 3

Turn 2 (streaming retry): new_items = [A, B, C, D, E]
    already_persisted = 3
    new_run_items = new_items[3:] = [D, E]
    saves only D, E
    run_state._current_turn_persisted_item_count = 5
```

This prevents duplicate items when the streaming pipeline retries or re-executes a turn.

### `rewind_session_items()` — Undoing After Failed Retries

When the model retry engine decides to retry (e.g., `ModelBehaviorError`), it needs to undo the session items that were already saved for the current turn. `rewind_session_items()` does this by calling `session.pop_item()` for each item that was added since the last successful turn.

```
Turn 2: model sends invalid response
    ├── save_result_to_session() already saved [A, B, C]
    │
    ├── get_response_with_retry() → ModelBehaviorError
    │
    ├── rewind_session_items() → pops C, B, A
    │
    └── Retry the turn with different input
```

---

## 5.12 RunItem: The Building Blocks of Conversation

Every step in a run produces a `RunItem`. The full hierarchy (from `src/agents/items.py`):

```
RunItemBase(Generic[T], abc.ABC)
│   ├── agent: Agent[Any]
│   ├── raw_item: T
│   ├── _agent_ref: weakref.ReferenceType  (for memory management)
│   ├── to_input_item() → TResponseInputItem
│   └── release_agent()  (drops strong ref, keeps weakref)
│
├── MessageOutputItem(ResponseOutputMessage)
│   └── type: "message_output_item"
│
├── ToolSearchCallItem(ToolSearchCallRawItem)
│   └── type: "tool_search_call_item"
│
├── ToolSearchOutputItem(ToolSearchOutputRawItem)
│   └── type: "tool_search_output_item"
│
├── HandoffCallItem(ResponseFunctionToolCall)
│   └── type: "handoff_call_item"
│
├── HandoffOutputItem(TResponseInputItem)
│   ├── source_agent: Agent[Any]
│   ├── target_agent: Agent[Any]
│   └── type: "handoff_output_item"
│
├── ToolCallItem(ToolCallItemTypes)
│   ├── tool_name: str | None
│   ├── tool_namespace: str | None
│   ├── tool_lookup_key: FunctionToolLookupKey | None
│   ├── tool_origin: ToolOrigin | None
│   └── type: "tool_call_item"
│
├── ToolCallOutputItem(TResponseInputItem)
│   ├── output: str | dict | ToolOutputText | ToolOutputImage | ToolOutputFileContent
│   ├── tool_name: str | None
│   ├── tool_namespace: str | None
│   └── type: "tool_call_output_item"
│
├── ToolApprovalItem(ToolApprovalItemTypes)
│   ├── tool_name: str | None
│   ├── tool_namespace: str | None
│   └── type: "tool_approval_item"
│
├── ReasoningItem(ResponseReasoningItem)
│   └── type: "reasoning_item"
│
├── CompactionItem(...)
│   └── type: "compaction_item"
│
├── MCPListToolsItem(McpListTools)
│   └── type: "mcp_list_tools_item"
│
├── MCPApprovalRequestItem(McpApprovalRequest)
│   └── type: "mcp_approval_request_item"
│
├── MCPApprovalResponseItem(McpApprovalResponse)
│   └── type: "mcp_approval_response_item"
│
└── ModelResponse(Response)
    └── (wraps the full API response)
```

### Type table — the 12 item types you'll encounter:

| Type string | Class | What it represents | Has `raw_item`? | Extra fields |
|---|---|---|---|---|
| `message_output_item` | `MessageOutputItem` | LLM text response | `ResponseOutputMessage` | — |
| `tool_call_item` | `ToolCallItem` | LLM decided to call a tool | `ResponseFunctionToolCall` etc. | `tool_name`, `tool_namespace`, `tool_origin` |
| `tool_call_output_item` | `ToolCallOutputItem` | Result from a tool call | `FunctionCallOutput` etc. | `output`, `tool_name` |
| `handoff_call_item` | `HandoffCallItem` | Agent is handing off | `ResponseFunctionToolCall` | — |
| `handoff_output_item` | `HandoffOutputItem` | Result of handoff | `TResponseInputItem` | `source_agent`, `target_agent` |
| `tool_approval_item` | `ToolApprovalItem` | Needs human approval | Various | `tool_name`, `tool_namespace` |
| `reasoning_item` | `ReasoningItem` | Model's thinking process | `ResponseReasoningItem` | — |
| `compaction_item` | `CompactionItem` | History was compacted | — | — |
| `mcp_list_tools_item` | `MCPListToolsItem` | MCP tool discovery | `McpListTools` | — |
| `mcp_approval_request_item` | `MCPApprovalRequestItem` | MCP tool needs approval | `McpApprovalRequest` | — |
| `mcp_approval_response_item` | `MCPApprovalResponseItem` | MCP approval response | `McpApprovalResponse` | — |
| `tool_search_call_item` | `ToolSearchCallItem` | Tool search request | `ResponseToolSearchCall` | — |

### `release_agent()` — Memory Management

Every `RunItemBase` holds a strong reference to the `Agent` that created it. For long conversations, this can keep large agent objects in memory. `release_agent()` drops the strong reference while keeping a weak reference:

```python
def release_agent(self) -> None:
    if "agent" not in self.__dict__:
        return
    agent = self.__dict__["agent"]
    if agent is None:
        return
    self._agent_ref = weakref.ref(agent) if agent is not None else None
    self.__dict__["agent"] = None  # Drop strong ref, keep weakref
```

After `release_agent()`, accessing `item.agent` still works as long as the agent is alive (resolved via weakref). If the agent was garbage-collected, it returns `None`.

`HandoffOutputItem` extends this pattern to `source_agent` and `target_agent` as well.

---

## 5.13 Putting It All Together: A Complete Human-in-the-Loop Flow

Let's build a complete HITL (human-in-the-loop) example that uses all three state layers: RunContextWrapper for permissions, Session for conversation history, and RunState for pause/resume.

```python
import asyncio
import json
from dataclasses import dataclass
from agents import Agent, Runner, RunContextWrapper, function_tool, RunConfig
from agents.memory import SQLiteSession
from agents.items import ToolApprovalItem

@dataclass
class UserContext:
    user_id: str
    role: str
    approval_limit: float

async def check_approval_needed(
    ctx: RunContextWrapper[UserContext],
    tool_params: dict[str, Any],
    call_id: str,
) -> bool:
    amount = float(tool_params.get("amount", 0))
    return ctx.context.role != "admin" and amount > ctx.context.approval_limit

@function_tool(needs_approval=check_approval_needed)
async def transfer_money(
    ctx: RunContextWrapper[UserContext],
    recipient: str,
    amount: float,
) -> str:
    return f"Transfer of ${amount} to {recipient} initiated."

agent = Agent[UserContext](
    name="BankAgent",
    instructions="Help with banking. For transfers over the user's approval limit, require human approval.",
    tools=[transfer_money],
)

session = SQLiteSession("banking_session.db")
ctx = UserContext(user_id="u-456", role="user", approval_limit=50.0)
```

### Round 1: Small transfer (auto-approved)

```python
result1 = await Runner.run(
    agent, "Transfer $30 to Alice",
    context=ctx,
    session=session,
)
print(result1.final_output)
# "Transfer of $30 to Alice initiated."
print(f"Turns: {len(result1.raw_responses)}")
# Turns: 1
```

### Round 2: Large transfer (requires approval → interruption)

```python
result2 = await Runner.run(
    agent, "Transfer $200 to Bob",
    context=ctx,
    session=session,
)
```

When the tool approval check returns True, the run produces `NextStepInterruption` and returns early:

```python
state = result2.to_state()
interruptions = state.get_interruptions()
print(f"Pending approvals: {len(interruptions)}")
# Pending approvals: 1

for item in interruptions:
    print(f"  Tool: {item.tool_name}, Call ID: {item.raw_item.call_id}")
```

### Save the RunState to JSON

```python
def serialize_ctx(ctx: UserContext) -> dict:
    return {"user_id": ctx.user_id, "role": ctx.role, "approval_limit": ctx.approval_limit}

state_json = state.to_json(context_serializer=serialize_ctx)
saved_json_str = json.dumps(state_json, indent=2)

# In production: save to database, Redis, etc.
print(f"State size: {len(saved_json_str)} bytes")
print(f"Schema version: {state_json['$schemaVersion']}")
# Schema version: 1.9
print(f"Current turn: {state_json['current_turn']}")
# Current turn: 1
```

### What the serialized RunState looks like (key fields):

```python
{
  "$schemaVersion": "1.9",
  "current_turn": 1,
  "current_agent": {"name": "BankAgent"},
  "original_input": "Transfer $200 to Bob",
  "model_responses": [
    {
      "usage": {"input_tokens": 412, "output_tokens": 67},
      "output": [{"type": "function_call", "name": "transfer_money", "call_id": "call_abc", ...}],
      "response_id": "resp_123",
      "request_id": "req_456"
    }
  ],
  "context": {
    "usage": {"input_tokens": 412, "output_tokens": 67, "total_tokens": 479},
    "approvals": {},
    "context": {"user_id": "u-456", "role": "user", "approval_limit": 50.0},
    "context_meta": {
      "original_type": "dataclass",
      "serialized_via": "context_serializer",
      "requires_deserializer": True,
      "class_path": "__main__:UserContext"
    }
  },
  "generated_items": [
    {"type": "tool_call_item", "raw_item": {"type": "function_call", "name": "transfer_money", ...}, "agent": {"name": "BankAgent"}}
  ],
  "session_items": [...],
  "current_step": {
    "type": "next_step_interruption",
    "data": {
      "interruptions": [
        {"type": "tool_approval_item", "tool_name": "transfer_money", "raw_item": {"type": "function_call", "call_id": "call_abc", ...}}
      ]
    }
  },
  "max_turns": 10,
  "current_turn_persisted_item_count": 1
}
```

### Round 3: Approve and resume

```python
def deserialize_ctx(data: dict) -> UserContext:
    return UserContext(user_id=data["user_id"], role=data["role"], approval_limit=data["approval_limit"])

restored = await RunState.from_json(
    initial_agent=agent,
    state_json=state_json,
    context_deserializer=deserialize_ctx,
)

for item in restored.get_interruptions():
    restored.approve(item, always_approve=False)
    print(f"Approved: {item.tool_name} (call_id={item.raw_item.call_id})")

result3 = await Runner.run(
    agent,
    previous_run_state=restored,
    session=session,
)
print(result3.final_output)
# "Transfer of $200 to Bob initiated."
print(f"Total turns across all runs: {len(result3.raw_responses)}")
```

### Post-run analysis: Session history

```python
items = await session.get_items()
print(f"Total session items: {len(items)}")
for item in items:
    role = item.get("role", item.get("type", "unknown"))
    content = str(item.get("content", item.get("name", "")))[:60]
    print(f"  [{role}] {content}")
# [user] Transfer $30 to Alice
# [function_call] transfer_money
# [function_call_output] Transfer of $30 to Alice initiated.
# [user] Transfer $200 to Bob
# [function_call] transfer_money
# [function_call_output] Transfer of $200 to Bob initiated.
```

The session now contains the complete conversation across all three rounds, including the tool calls and outputs. The RunState checkpoint was only needed for the pause/resume at the interruption point.

---

## 5.14 Key Takeaways

1. **Three state layers, three purposes** — RunContextWrapper (runtime), Session (persistence), RunState (pause/resume)
2. **RunContextWrapper is generic** — `Agent[MyContext]` gives your tools full type safety
3. **The approval system uses `bool | list[str]`** — `True` means "always", a list means "these specific call IDs"
4. **Forking shares state** — `_fork_with_tool_input()` creates a new wrapper but shares `context`, `usage`, and `_approvals`
5. **Session is a protocol** — implement 4 async methods (`get_items`, `add_items`, `pop_item`, `clear_session`) for any backend
6. **SessionInputCallback controls what the model sees** — without changing what's stored in the session
7. **OpenAIConversationsSession is lazy** — `session_id` is only available after the first API call
8. **Compaction wraps another session** — calls `responses.compact` when candidates exceed the threshold (default: 10)
9. **RunState has 30+ fields** — captures everything needed to resume an interrupted run
10. **Schema versioning is fail-fast** — older SDKs reject newer versions; every version has a summary
11. **Context serialization tries 5 strategies** — Mapping passthrough, serializer, model_dump, asdict, omit
12. **`release_agent()` uses weakrefs** — drops strong references to prevent memory leaks in long conversations
