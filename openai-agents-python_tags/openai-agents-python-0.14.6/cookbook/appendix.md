# Appendix: API Quick Reference

## Quick Index

- [Core Classes](#core-classes)
- [Decorators](#decorators)
- [Common Patterns](#common-patterns)
- [File Structure Map](#file-structure-map)

---

## Core Classes

### `Agent[TContext]

```python
from agents import Agent

agent = Agent(
    name="Agent Name",
    instructions="System prompt here",
    tools=[...],
    handoffs=[...],
    model="gpt-4",
    model_settings=ModelSettings(...),
    input_guardrails=[...],
    output_guardrails=[...],
    output_type=MyDataclass,
    hooks=MyHooks(),
    tool_use_behavior="run_llm_again",
    handoff_description="Description for when this is a handoff target"
)

new_agent = agent.clone(
    instructions="New instructions"
)
```

### `Runner`

```python
from agents import Runner, RunConfig

result = await Runner.run(
    agent,
    "User input here",
    context=my_context,
    run_config=RunConfig(
        max_turns=20,
        model_settings=ModelSettings(...)
    ),
    session=my_session,
    previous_run_state=previous_state
)

print(result.final_output)
```

### `RunResult`

```python
@dataclass
class RunResult:
    final_output: Any
    run_state: RunState
    usage: Usage
    # ... more
```

### `RunState`

```python
# Save
json_str = run_state.to_json(
    context_serializer=lambda ctx: {"key": "value"}
)

# Load
run_state = RunState.from_json(
    json_str,
    context_deserializer=lambda data: MyContext(**data)
)

# Access
for item in run_state.items:
    print(item)

# Approve
for approval in run_state.interruptions:
    run_state.approve(approval)
```

---

## Decorators

### `@function_tool`

```python
from agents import function_tool

@function_tool
async def my_tool(param: str) -> str:
    """Tool description here."""
    return "result"

# With options
@function_tool(
    name_override="custom_name",
    description_override="Custom description",
    timeout=30.0,
    needs_approval=True,
    strict_mode=True
)
async def my_tool(param: str) -> str:
    ...
```

### `@input_guardrail`, `@output_guardrail`

```python
from agents import input_guardrail, output_guardrail, InputGuardrailResult

@input_guardrail
async def check_input(input: str) -> InputGuardrailResult:
    return InputGuardrailResult(tripwire_triggered=False)
```

---

## Common Patterns

### Pattern: Agent as Tool

```python
from agents import Agent

specialized_agent = Agent(...)

main_agent = Agent(
    name="Main",
    tools=[
        specialized_agent.as_tool(
            tool_name="do_special",
            tool_description="Does special things"
        )
    ]
)
```

### Pattern: Session with SQLite

```python
from agents import SQLiteSession

session = SQLiteSession("conversations.db")

result = await Runner.run(agent, "Hello", session=session)
result2 = await Runner.run(agent, "What did I say?", session=session)
```

### Pattern: Structured Output

```python
from dataclasses import dataclass

@dataclass
class MyOutput:
    name: str
    value: int

agent = Agent(output_type=MyOutput)
```

---

## File Structure Map

```
src/agents/
├── __init__.py                 # Public API
├── agent.py                    # Agent dataclass
├── tool.py                     # Tool definitions
├── run.py                      # Runner
├── run_config.py               # RunConfig
├── run_state.py               # Serializable state
├── run_context.py             # Context wrapper
├── items.py                    # RunItem types
├── guardrail.py              # Guardrails
├── handoffs/
│   └── __init__.py
├── models/
│   ├── __init__.py
│   ├── interface.py         # Model interface
│   ├── openai_responses.py  # OpenAI Responses API
│   └── ...
├── realtime/
│   └── ...
├── memory/
│   ├── __init__.py
│   ├── session.py          # Session ABC
│   └── sqlite_session.py  # SQLite implementation
├── tracing/
│   └── ...
└── run_internal/           # ⚠️ INTERNAL ⚠️
    ├── run_loop.py        # Core loop
    ├── run_steps.py      # Next step types
    ├── turn_resolution.py # Process model output
    ├── turn_preparation.py # Prep for model
    ├── tool_execution.py # Run tools
    ├── approvals.py      # Approval logic
    ├── guardrails.py     # Run guardrails
    ├── error_handlers.py
    └── ...
```

**Note: `run_internal` is internal - don't import from it directly! Use the public API in `agents`!`

---

## Quick Cheat Sheet

| Task | Code |
|------|------|
| Create agent | `Agent(name="A", instructions="...")` |
| Run agent | `await Runner.run(agent, "Hi")` |
| Create tool | `@function_tool async def f(): ...` |
| Add guardrail | `@input_guardrail async def f(i): ...` |
| Use session | `SQLiteSession("file.db")` |
| Clone agent | `agent.clone(instructions="new")` |
| Pause/resume | Save `run_state.to_json()` |
