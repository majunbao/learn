# Chapter 1: Quick Start - Zero To Agent With Full Source Code Understanding

## 1.1 The Simplest Agent

Let's start with the classic "Hello World" of agents. This is the simplest example you'll find in `examples/basic/hello_world.py`:

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
    # Function calls itself,
    # Looping in smaller pieces,
    # Endless by design.

if __name__ == "__main__":
    asyncio.run(main())
```

That's it! Just two core classes: `Agent` and `Runner`. Let's understand what happens under the hood.

## 1.2 Architecture Overview

Here's a high-level view of how the SDK is structured:

```
┌─────────────────────────────────────────────────────────────┐
│                     User Application                         │
│  ┌──────────┐          ┌──────────┐                        │
│  │  Agent   │─────────▶│  Runner  │                        │
│  └──────────┘          └─────┬────┘                        │
└──────────────────────────────┼─────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   SDK Core Layer                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              run_internal/ (The Engine)                 │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │ │
│  │  │  run_loop.py │  │tool_execution│  │turn_resolution│ │ │
│  │  └──────────────┘  └──────────────┘  └───────────────┘ │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │  Tool    │  │Handoffs  │  │Guardrails│  │  Memory   │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Model Layer                              │
│  ┌──────────────────┐  ┌───────────────────────────┐       │
│  │OpenAI Responses  │  │OpenAI Chat Completions    │       │
│  └──────────────────┘  └───────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## 1.3 The Agent Dataclass

Looking at `src/agents/agent.py`, you'll see `Agent` is defined as a `@dataclass`, not a regular class. Let's see why:

```python
@dataclass
class Agent(AgentBase[TContext], Generic[TContext]):
    """An agent that can be run by the SDK."""

    instructions: str
    """The instructions for the agent. This is the system prompt for the LLM."""

    model: str | Model | None = None
    """The model to use. If not provided, we'll use the default model."""

    model_settings: ModelSettings | None = None
    """Settings for the model, like temperature, max tokens, etc."""
    
    # ... and more fields
```

**Why a dataclass?**

1. **Immutability by default** - Once created, the agent definition doesn't change
2. **Automatic serialization** - Easy to save/load agent definitions
3. **Clear field definitions** - Self-documenting configuration
4. **Simple construction** - No `__init__` boilerplate needed

## 1.4 What Happens When You Call Runner.run()

Let's trace the execution flow. Here's the call stack:

```
Runner.run(agent, input)
    ↓
runner._run()
    ↓
run_internal.run_loop.run_single_turn()
    ↓
model.generate()
    ↓
LLM API Call
```

Let's visualize the full flow with a sequence diagram:

```
User Application        Runner         Run Loop         Model           LLM API
     │                     │               │             │                 │
     ├─ Runner.run() ─────>│               │             │                 │
     │                     ├─ init() ─────>│             │                 │
     │                     │               ├─ get tools─>│                 │
     │                     │               │             ├─ call API ─────>│
     │                     │               │             │<── response ────┤
     │                     │               │<─ process──>│                 │
     │                     │               │  response   │                 │
     │                     │<── result ────│             │                 │
     │<── result ──────────│               │             │                 │
```

## 1.5 Let's Add a Tool

Now let's make it more interesting with a tool. First, look at `examples/basic/tools.py`:

```python
import asyncio
from agents import Agent, FunctionTool, Runner


async def get_weather(latitude: float, longitude: float) -> str:
    """Get the current weather for a location."""
    # In real life, call a weather API
    return f"Weather at {latitude}, {longitude}: 72°F, sunny"


async def main():
    agent = Agent(
        name="Weather Assistant",
        instructions="You help users get weather information.",
        tools=[FunctionTool(get_weather)],
    )

    result = await Runner.run(
        agent,
        "What's the weather in San Francisco (37.7749, -122.4194)?",
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
```

## 1.6 The Tool Calling Flow

When the agent uses a tool, here's what happens internally:

```
┌───────────────────────────────────────────────────────────────────┐
│                        Turn 1                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 1. LLM decides to call get_weather(37.7749, -122.4194)      │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────┐
│                        Tool Execution                              │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 2. SDK extracts tool name + parameters                       │  │
│  │ 3. SDK validates parameters (using type hints!)              │  │
│  │ 4. SDK calls your function                                   │  │
│  │ 5. SDK captures the result                                   │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────┐
│                        Turn 2                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 6. LLM receives tool result: "72°F, sunny"                   │  │
│  │ 7. LLM generates final answer                                │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

This multi-turn pattern is the heart of agent systems!

## 1.7 Key Takeaways from Chapter 1

1. **`Agent` = configuration** - It's a dataclass that defines what the agent is
2. **`Runner` = execution** - It's the engine that runs the agent
3. **Multi-turn by design** - Tools create natural conversation turns
4. **Type hints matter** - The SDK uses Python's type system heavily

In the next chapter, we'll dive deep into the `Agent` dataclass and understand why it's designed the way it is!
