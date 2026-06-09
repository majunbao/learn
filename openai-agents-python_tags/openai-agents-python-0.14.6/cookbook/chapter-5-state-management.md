# Chapter 5: State Management - RunContext & RunState

## 5.1 The Two Types of State

First, let's make this clear:

```
┌─────────────────────────────────────────────────────────────┐
│  RunContextWrapper                                           │
│  • Your custom data (context!)                              │
│  • Usage tracking (tokens)                                  │
│  • Approval state (per-tool, per-call)                      │
│  • Turn input                                               │
│                                                             │
│  → Lives ONLY during one run!                               │
│  → NOT serialized! (usually)                                │
└─────────────────────────────────────────────────────────────┘
                      ↓ (separate!)
┌─────────────────────────────────────────────────────────────┐
│  RunState                                                   │
│  • Conversation items (RunItem list)                       │
│  • Turn count                                               │
│  • Model responses                                          │
│  • Pending interruptions (approvals needed)                 │
│  • Schema version (for serialization!)                     │
│                                                             │
│  → Can be serialized to JSON!                               │
│  → Can be resumed later!                                    │
└─────────────────────────────────────────────────────────────┘
```

One is for the current run, one is for durable pause/resume!

## 5.2 RunContextWrapper: Your Data + SDK Data

Look at this simple but powerful dataclass:

```python
@dataclass(eq=False)
class RunContextWrapper(Generic[TContext]):
    context: TContext  # YOUR DATA HERE!
    
    usage: Usage  # Token counts, etc.
    
    turn_input: list[TResponseInputItem]
    
    _approvals: dict[str, _ApprovalRecord]  # Internal state!
    
    tool_input: Any | None = None
```

The magic is `Generic[TContext]`! This means:

1. You define your own context type
2. The SDK passes it around with type safety
3. Your tools get it with full type hints!

### Example: Your Custom Context

```python
from dataclasses import dataclass

@dataclass
class MyAppContext:
    db_connection: Any
    user_id: str
    preferences: dict[str, Any]
    logger: Any

# Then use it:
agent = Agent[MyAppContext](...)

# In a tool:
@function_tool
async def get_user_prefs(ctx: RunContextWrapper[MyAppContext]) -> dict:
    # ctx.context has full type hints!
    return ctx.context.preferences
```

Beautiful! Type-safe custom state!

## 5.3 The Approval System in RunContext

Look at `_ApprovalRecord` - it's clever!

```python
@dataclass(eq=False)
class _ApprovalRecord:
    approved: bool | list[str]  # True = always, list = specific call IDs
    rejected: bool | list[str]
    rejection_messages: dict[str, str]  # Per-call messages
    sticky_rejection_message: str | None  # Always use this message
```

And the public methods:

```python
ctx.approve_tool(approval_item, always_approve=False)
ctx.reject_tool(approval_item, always_reject=False, rejection_message="Nope!")
status = ctx.is_tool_approved(tool_name, call_id)
```

This means:
- Approve just this one tool call
- Approve ALL future calls to this tool
- Same for rejection
- With optional custom messages!

## 5.4 RunState: Serialization with Schema Versioning

Now THIS is impressive! Look at the top of `run_state.py`:

```python
CURRENT_SCHEMA_VERSION = "1.9"

SCHEMA_VERSION_SUMMARIES: dict[str, str] = {
    "1.0": "Initial RunState snapshot format for HITL pause/resume flows.",
    "1.1": "Same payload as 1.0, but introduces explicit backward-read support policy.",
    "1.2": "Persists reasoning_item_id_policy...",
    # ... and so on, every version has a summary!
}
```

And the policy comment:

```
# RunState schema policy.
# 1. Keep schema versions shipped in releases readable.
# 2. Unreleased schema versions may be renumbered or squashed...
# 3. to_json() always emits CURRENT_SCHEMA_VERSION.
# 4. Forward compatibility is intentionally fail-fast...
```

This is how you do durable serialization properly!

### What's In RunState?

Let's look at the dataclass (simplified):

```python
@dataclass
class RunState(Generic[TContext, TAgent]):
    # Basic state
    _current_turn: int = 0
    _items: list[RunItem] = field(default_factory=list)
    
    # Agent info (for resuming)
    _agent_name: str | None = None
    _agent_instructions: str | ... | None = None
    
    # Model stuff
    _last_model_response: ModelResponse | None = None
    _request_ids: list[str] = field(default_factory=list)
    
    # Pause/resume
    _interruptions: list[ToolApprovalItem] = field(default_factory=list)
    _processed_response: Any | None = None  # For resuming
    
    # Schema versioning
    _schema_version: str = field(default_factory=lambda: CURRENT_SCHEMA_VERSION)
    _schema_version_summaries: dict[str, str] = field(default_factory=dict)
    
    # Context (custom!)
    _context: Any | None = None
    _context_serialized: dict[str, Any] | None = None
    
    # Usage
    _usage: Usage | None = None
    
    # And more...
```

Everything you need to resume exactly where you left off!

## 5.5 Serializing RunState: to_json() and from_json()

The key methods:

```python
# Save it:
json_str = run_state.to_json()

# Load it back:
run_state = RunState.from_json(json_str)
```

But wait - what about YOUR custom context? Because Python functions can't be serialized to JSON!

That's why there are these parameters:

```python
RunState.to_json(
    context_serializer=lambda ctx: {"user_id": ctx.user_id, ...}
)

RunState.from_json(
    json_str,
    context_deserializer=lambda data: MyContext(user_id=data["user_id"], ...)
)
```

Perfect! You control how your context is serialized!

## 5.6 The Resumption Flow: Pause → Later → Resume

Let's visualize how pause/resume works:

```
[FIRST RUN]
    Runner.run(agent, input)
        ↓
    ... runs ...
        ↓
    Needs approval! (NextStepInterruption)
        ↓
    Return RunResult with RunState
        ↓
    You: save run_state.to_json() to database
        ↓
    [TIME PASSES - user goes to lunch!]
        ↓
[SECOND RUN - LATER]
    You: load run_state from database
        ↓
    You: get approval_item from run_state.interruptions
        ↓
    You: approval_item.approve() (or reject())
        ↓
    Runner.run(agent, previous_run_state=run_state)
        ↓
    RESUMES EXACTLY WHERE IT LEFT OFF!
        ↓
    Finishes the agent run!
```

This is how you build real-world human-in-the-loop systems!

## 5.7 RunItem: The Building Blocks of Conversation

All conversation history is a list of `RunItem`. Let's look at the hierarchy:

```
RunItem (base)
├── MessageOutputItem
│   └── Text from the agent
├── ToolCallItem
│   └── Agent decided to call a tool
├── ToolCallOutputItem
│   └── Result from a tool call
├── HandoffCallItem
│   └── Agent is handing off
├── HandoffOutputItem
│   └── Result of handoff
├── ToolApprovalItem
│   └── Needs human approval
├── ReasoningItem
│   └── Model's thinking process
├── CompactionItem
│   └── History was compacted
└── ... more types!
```

Every step is a well-typed item!

## 5.8 Mini State System: Let's Build It!

Let's distill these ideas into a simple version:

```python
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

TContext = TypeVar("TContext")

# First, context wrapper
@dataclass
class MiniContextWrapper(Generic[TContext]):
    context: TContext
    turn_count: int = 0
    approved_calls: set[str] = field(default_factory=set)
    
    def approve_call(self, call_id: str):
        self.approved_calls.add(call_id)
    
    def is_approved(self, call_id: str) -> bool:
        return call_id in self.approved_calls

# Now, serializable state
@dataclass
class MiniState(Generic[TContext]):
    schema_version: str = "1.0"
    turn_count: int = 0
    conversation: list[dict] = field(default_factory=list)
    pending_approval: dict | None = None
    context_snapshot: dict | None = None
    
    def to_json(self, context_serializer=None) -> str:
        import json
        data = {
            "schema_version": self.schema_version,
            "turn_count": self.turn_count,
            "conversation": self.conversation,
            "pending_approval": self.pending_approval,
        }
        if context_serializer and self.context_snapshot:
            data["context"] = context_serializer(self.context_snapshot)
        return json.dumps(data, indent=2)
    
    @staticmethod
    def from_json(json_str: str, context_deserializer=None) -> "MiniState":
        import json
        data = json.loads(json_str)
        
        # Check schema version (simple version)
        if data["schema_version"] != "1.0":
            raise Exception(f"Unsupported schema: {data['schema_version']}")
        
        state = MiniState(
            schema_version=data["schema_version"],
            turn_count=data["turn_count"],
            conversation=data["conversation"],
            pending_approval=data.get("pending_approval"),
        )
        
        if context_deserializer and "context" in data:
            state.context_snapshot = context_deserializer(data["context"])
        
        return state

# Let's use it!
@dataclass
class MyContext:
    user_id: str

# Create state
state = MiniState(
    turn_count=2,
    conversation=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ],
    pending_approval={"call_id": "123", "tool": "transfer_money"},
    context_snapshot=MyContext(user_id="user-123")
)

# Serialize!
json_str = state.to_json(
    context_serializer=lambda ctx: {"user_id": ctx.user_id}
)
print("Serialized:")
print(json_str[:200] + "...")

# Deserialize!
loaded = MiniState.from_json(
    json_str,
    context_deserializer=lambda data: MyContext(user_id=data["user_id"])
)
print(f"\nLoaded, turn count: {loaded.turn_count}")
print(f"Loaded, user_id: {loaded.context_snapshot.user_id}")
```

This captures the core ideas:
- Generic context
- Schema versioning
- Custom serialization hooks
- Conversation history

## 5.9 Key Takeaways

1. **Two state types** - RunContext (per-run) and RunState (durable)
2. **Schema versioning is critical** - always track changes with summaries
3. **Custom serialization hooks** - you control how your context is saved/loaded
4. **Approval state is rich** - per-call, always-approve, with messages
5. **Full conversation history** - every step is a typed RunItem
6. **Pause/resume is built-in** - save state, come back later, continue!
7. **Type safety with generics** - RunContextWrapper[YourType]

In the next chapter, we'll build a full mini SDK from scratch that ties everything together!
