# Chapter 8: Patterns & Best Practices - Production-Grade Agent Design

## 8.1 Pattern 1: Agent Factories

Instead of creating agents inline, use factories:

```python
def create_agent_for_user(user_id: str, preferences: dict) -> Agent:
    """Create an agent tailored to a specific user."""
    return Agent(
        name=f"Assistant for {user_id}",
        instructions=build_user_instructions(preferences),
        tools=get_tools_for_user(user_id),
        model_settings=ModelSettings(
            temperature=preferences.get("creativity", 0.7)
        )
    )

# Usage
agent = create_agent_for_user("user-123", {"creativity": 0.9})
```

Benefits:
- Centralized configuration
- Easy to test
- Consistent agent creation

## 8.2 Pattern 2: Tool Registry

Don't scatter tool definitions! Use a registry:

```python
# tools/registry.py
from agents import FunctionTool
from dataclasses import dataclass
from typing import Dict

@dataclass
class ToolRegistry:
    _tools: Dict[str, FunctionTool] = field(default_factory=dict)
    
    def register(self, tool: FunctionTool):
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> FunctionTool:
        return self._tools[name]
    
    def get_all(self, *names: str) -> list[FunctionTool]:
        return [self._tools[name] for name in names]

# Create a global registry
registry = ToolRegistry()

# Decorator to auto-register
def registered_tool(func):
    tool = function_tool(func)
    registry.register(tool)
    return tool

# Usage
@registered_tool
async def get_weather(location: str) -> str:
    ...

# Then in your agent:
agent = Agent(
    name="Tool User",
    instructions="...",
    tools=registry.get_all("get_weather", "get_time")
)
```

## 8.3 Pattern 3: Context Builder Pattern

Build your context object with a builder:

```python
from dataclasses import dataclass

@dataclass
class AppContext:
    db: Any
    user_id: str
    logger: Any
    cache: Any

class ContextBuilder:
    def __init__(self):
        self._db = None
        self._user_id = None
        self._logger = None
        self._cache = None
    
    def with_db(self, db):
        self._db = db
        return self
    
    def with_user(self, user_id):
        self._user_id = user_id
        return self
    
    def with_logger(self, logger):
        self._logger = logger
        return self
    
    def with_cache(self, cache):
        self._cache = cache
        return self
    
    def build(self) -> AppContext:
        return AppContext(
            db=self._db,
            user_id=self._user_id,
            logger=self._logger,
            cache=self._cache
        )

# Usage
ctx = ContextBuilder()\
    .with_db(my_db)\
    .with_user("user-123")\
    .with_logger(my_logger)\
    .build()
```

## 8.4 Best Practice 1: Always Set Max Turns

Never run without a max_turns limit:

```python
from agents import Runner, RunConfig

result = await Runner.run(
    agent,
    input,
    run_config=RunConfig(
        max_turns=20  # Always set this!
    )
)
```

Why? Prevents infinite loops!

## 8.5 Best Practice 2: Use Tracing in Production

Always set up tracing:

```python
from agents import tracing
import os

# Set up tracing export
tracing.set_tracing_export_api_key(os.environ["OPENAI_API_KEY"])

# Or use OpenTelemetry for custom exporters
# (See SDK docs for details)
```

You'll thank yourself when debugging production issues!

## 8.6 Best Practice 3: Use Sessions for Multi-Turn Conversations

Don't build your own history management - use Sessions:

```python
from agents import SQLiteSession, Runner

# Create a session (persists to disk!)
session = SQLiteSession("my_conversation.db")

# First run
result = await Runner.run(
    agent,
    "Hello!",
    session=session
)

# Later, continue the conversation
result2 = await Runner.run(
    agent,
    "What did I just ask?",
    session=session  # Same session!
)
```

The SDK handles all the history for you!

## 8.7 Best Practice 4: Handle Tool Errors Gracefully

Don't let tool errors crash the whole run:

```python
from agents import function_tool

@function_tool(failure_error_function=lambda ctx, e: "Sorry, that tool failed")
async def flaky_api_call() -> str:
    # This might fail
    result = await call_external_api()
    return result
```

The LLM will see the error message and can recover!

## 8.8 Best Practice 5: Version Your Agents

When deploying, version your agent definitions:

```python
# agents/v1/customer_service.py
def create_customer_service_agent_v1() -> Agent:
    return Agent(
        name="Customer Service v1",
        instructions="..."  # Specific instructions
    )

# agents/v2/customer_service.py
def create_customer_service_agent_v2() -> Agent:
    return Agent(
        name="Customer Service v2",
        instructions="..."  # Improved!
    )
```

Canary rollout, A/B testing, easy rollbacks!

## 8.9 Best Practice 6: Write Unit Tests for Tools

Tools should be testable independently:

```python
# tests/test_tools.py
import pytest
from myapp.tools import get_weather

@pytest.mark.asyncio
async def test_get_weather():
    result = await get_weather("San Francisco")
    assert "weather" in result.lower()
    # Mock the API for true unit tests!
```

And write integration tests for full agent flows!

## 8.10 Pattern 4: Output Type for Structured Results

Always use structured output when possible:

```python
from dataclasses import dataclass
from agents import Agent

@dataclass
class CalendarEvent:
    title: str
    date: str
    time: str
    location: str

agent = Agent(
    name="Calendar Assistant",
    instructions="Create calendar events from user requests",
    output_type=CalendarEvent  # Structured!
)

# Result will be a CalendarEvent instance!
result = await Runner.run(agent, "Lunch tomorrow at noon at Joe's")
print(result.final_output.title)  # "Lunch"
print(result.final_output.date)   # "2025-04-28"
```

No more parsing strings! Type-safe outputs!

## 8.11 Pattern 5: Guardrail Chaining

Chain guardrails for complex validation:

```python
from agents import input_guardrail, InputGuardrailResult

@input_guardrail
async def check_length(input: str) -> InputGuardrailResult:
    if len(input) > 10000:
        return InputGuardrailResult(tripwire_triggered=True)
    return InputGuardrailResult(tripwire_triggered=False)

@input_guardrail
async def check_content(input: str) -> InputGuardrailResult:
    if "bad_word" in input:
        return InputGuardrailResult(tripwire_triggered=True)
    return InputGuardrailResult(tripwire_triggered=False)

# They run in parallel automatically!
agent = Agent(
    input_guardrails=[check_length, check_content]
)
```

## 8.12 Production Checklist

Before deploying to production:

- [ ] Set `max_turns`
- [ ] Set up tracing
- [ ] Use Sessions for multi-turn
- [ ] Add guardrails
- [ ] Add approval for sensitive tools
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Version your agents
- [ ] Set up logging
- [ ] Set up monitoring for token usage
- [ ] Error handling for tools
- [ ] Rate limiting

## 8.13 Key Takeaways

1. **Factories for consistency** - Centralize agent creation
2. **Registry for tools** - Keep tools organized
3. **Builder for context** - Make context construction clean
4. **Always max_turns** - Prevent infinite loops
5. **Trace everything** - Observability is crucial
6. **Use Sessions** - Don't reinvent history management
7. **Structured outputs** - Type safety > string parsing
8. **Test your tools** - Tools should be independently testable
9. **Version your agents** - Easy rollbacks and experimentation
10. **Production checklist** - Go through it before deploying

Congratulations! You made it through the cookbook. You now understand:
- How the SDK is architected
- Why it's designed that way
- How to use it effectively
- How to build production-grade agents
- And you even built your own mini SDK!

Go build something amazing! 🚀
