# Chapter 2: Agent Deep Dive - Why a dataclass, not a class?

## 2.1 The Big Question: Dataclass vs Regular Class

When you look at `src/agents/agent.py`, the first thing you notice is:

```python
@dataclass
class Agent(AgentBase, Generic[TContext]):
    """An agent is an AI model configured with instructions, tools, guardrails, handoffs and more."""
    
    instructions: str | Callable[...] | None = None
    model: str | Model | None = None
    model_settings: ModelSettings = field(default_factory=get_default_model_settings)
    tools: list[Tool] = field(default_factory=list)
    # ... and many more fields
```

**Why `@dataclass` instead of a regular class?** Let's explore the design decisions!

## 2.2 Dataclass Benefits: A Visual Comparison

Let's see what you get with dataclasses vs writing everything manually:

```
┌─────────────────────────────────────────────────────────────────┐
│                Regular Class Approach                          │
├─────────────────────────────────────────────────────────────────┤
│  class Agent:                                                   │
│      def __init__(                                              │
│          self,                                                 │
│          name: str,                                            │
│          instructions: str | None = None,                      │
│          model: str | None = None,                             │
│          tools: list[Tool] | None = None,                      │
│          # ... imagine 20+ parameters!                         │
│      ):                                                        │
│          self.name = name                                      │
│          self.instructions = instructions                      │
│          self.model = model                                    │
│          self.tools = tools or []                              │
│          # ... 20+ assignments!                                │
│                                                                 │
│      def __eq__(self, other):                                  │
│          # ... boilerplate                                     │
│                                                                 │
│      def __repr__(self):                                       │
│          # ... more boilerplate                                │
└─────────────────────────────────────────────────────────────────┘
         ↓ 20+ lines of boilerplate
┌─────────────────────────────────────────────────────────────────┐
│                  Dataclass Approach                             │
├─────────────────────────────────────────────────────────────────┤
│  @dataclass                                                     │
│  class Agent:                                                   │
│      name: str                                                 │
│      instructions: str | None = None                           │
│      model: str | Model | None = None                          │
│      tools: list[Tool] = field(default_factory=list)            │
│      # ... all fields!                                         │
└─────────────────────────────────────────────────────────────────┘
         ↑ Automatic __init__, __eq__, __repr__, __hash__!
```

## 2.3 The Agent Hierarchy

The `Agent` class inherits from `AgentBase`. Let's look at this hierarchy:

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentBase (dataclass)                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ name: str                                              │  │
│  │ handoff_description: str | None                        │  │
│  │ tools: list[Tool]                                      │  │
│  │ mcp_servers: list[MCPServer]                           │  │
│  │ mcp_config: MCPConfig                                  │  │
│  └───────────────────────────────────────────────────────┘  │
│              ↑ Shared with RealtimeAgent                     │
│                                                              │
┌─────────────────────────────────────────────────────────────┐
│                      Agent (dataclass)                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ instructions: str | Callable                           │  │
│  │ prompt: Prompt | DynamicPromptFunction                 │  │
│  │ handoffs: list[Agent | Handoff]                        │  │
│  │ model: str | Model                                     │  │
│  │ model_settings: ModelSettings                          │  │
│  │ input_guardrails: list[InputGuardrail]                 │  │
│  │ output_guardrails: list[OutputGuardrail]               │  │
│  │ output_type: type | AgentOutputSchemaBase              │  │
│  │ hooks: AgentHooks | None                               │  │
│  │ tool_use_behavior: ...                                 │  │
│  │ reset_tool_choice: bool                                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 2.4 Validation in `__post_init__`

Wait, dataclasses auto-generate `__init__`, but what about validation? The answer is `__post_init__`:

```python
def __post_init__(self):
    from typing import get_origin

    if not isinstance(self.name, str):
        raise TypeError(f"Agent name must be a string, got {type(self.name).__name__}")

    if self.handoff_description is not None and not isinstance(self.handoff_description, str):
        raise TypeError(
            f"Agent handoff_description must be a string or None, "
            f"got {type(self.handoff_description).__name__}"
        )

    # ... 20+ validation checks!
```

**Why validate here?**
- Early failure: catch mistakes before the agent runs
- Clear error messages
- Type safety beyond just type hints

## 2.5 Immutability vs Mutability

Let's visualize the data flow:

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Definition                         │
│  (Immutable Configuration)                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ name: "Assistant"                                      │  │
│  │ instructions: "Help users"                              │  │
│  │ tools: [get_weather]                                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│         This doesn't change during execution!                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Run State                                 │
│  (Mutable Execution Data)                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ current_turn: 3                                        │  │
│  │ conversation: [...]                                    │  │
│  │ tool_results: [...]                                    │  │
│  │ context: <your object>                                 │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│         This changes on every turn!                         │
└─────────────────────────────────────────────────────────────┘
```

**Key Insight:** The `Agent` itself is just configuration. The mutable state lives separately in `RunState`!

## 2.6 The Clone Method

Agents come with a `clone()` method. Let's see how it works:

```python
def clone(self, **kwargs: Any) -> Agent[TContext]:
    """Make a copy of the agent, with the given arguments changed."""
    return dataclasses.replace(self, **kwargs)
```

**Example usage:**

```python
base_agent = Agent(
    name="Assistant",
    instructions="You are helpful.",
    tools=[get_weather],
)

# Create a variation without changing the original
french_agent = base_agent.clone(
    name="Assistant Français",
    instructions="You are helpful and speak French.",
)

# Another variation
code_agent = base_agent.clone(
    name="Code Assistant",
    instructions="You write Python code.",
    tools=[get_weather, execute_code],
)
```

This pattern is powerful! You can create agent factories:

```
base_agent
    ├─→ clone() → french_agent
    ├─→ clone() → code_agent
    └─→ clone() → research_agent
```

## 2.7 The `as_tool()` Method

One of the most powerful features: convert any agent to a tool!

```python
def as_tool(
    self,
    tool_name: str | None,
    tool_description: str | None,
    # ... many options
) -> FunctionTool:
    """Transform this agent into a tool, callable by other agents."""
```

Let's visualize this:

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent A                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ name: "Planner"                                        │  │
│  │ tools: [AgentB.as_tool(), AgentC.as_tool()]           │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                  │
│         ┌────────────────┼────────────────┐                 │
│         ↓                ↓                ↓                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ Agent B  │    │ Agent C  │    │ Agent D  │             │
│  │ as tool  │    │ as tool  │    │ as tool  │             │
│  └──────────┘    └──────────┘    └──────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## 2.8 Generics: The `TContext` Type Parameter

Notice the `Generic[TContext]`? Let's understand what that does:

```python
@dataclass
class Agent(AgentBase, Generic[TContext]):
    # ...
```

**What is TContext?** It's the type of your custom context object!

```python
from dataclasses import dataclass

@dataclass
class MyContext:
    user_id: str
    preferences: dict[str, Any]
    db_connection: Any

# Agent knows about MyContext!
agent = Agent[MyContext](
    name="Assistant",
    instructions="Help the user.",
)
```

And in your tools:

```python
async def get_user_preferences(
    ctx: RunContextWrapper[MyContext],  # Type-safe!
) -> dict:
    # ctx.context has full type hints for MyContext
    return ctx.context.preferences
```

## 2.9 Field-by-Field Deep Dive

Let's look at the most important fields and what they do:

| Field | Type | Purpose |
|-------|------|---------|
| `name` | `str` | Agent's identity (for debugging, handoffs) |
| `instructions` | `str \| Callable` | System prompt (can be dynamic!) |
| `tools` | `list[Tool]` | What the agent can do |
| `handoffs` | `list[Agent \| Handoff]` | Who the agent can delegate to |
| `model` | `str \| Model` | Which LLM to use |
| `model_settings` | `ModelSettings` | Temperature, tokens, etc. |
| `input_guardrails` | `list[InputGuardrail]` | Validate input before processing |
| `output_guardrails` | `list[OutputGuardrail]` | Validate output before returning |
| `output_type` | `type \| None` | Structured output type |
| `hooks` | `AgentHooks \| None` | Lifecycle callbacks |

## 2.10 Why This Design Works

Let's summarize the wisdom behind this architecture:

### 1. Configuration vs State Separation
```
Agent = Immutable Configuration
RunState = Mutable Execution State
```

### 2. Composition over Inheritance
- Build complex agents by combining tools, handoffs, guardrails
- No deep inheritance hierarchies

### 3. Type Safety First
- Generics for context
- Type hints everywhere
- Runtime validation

### 4. Functional Patterns
- `clone()` for immutable updates
- Pure functions as tools
- No hidden state in Agent

## 2.11 Pop Quiz!

Before moving on, test your understanding:

**Q: Can an Agent change its own instructions mid-run?**
A: No! The Agent is immutable configuration. You'd need to create a new Agent with `clone()`.

**Q: Where does the conversation history live?**
A: In `RunState`, not in the Agent!

**Q: How do you create 10 similar agents with slight variations?**
A: Create a base agent, then call `clone()` 10 times with different parameters!

In the next chapter, we'll dive into the Tool system and understand how `FunctionTool` works internally!
