# Chapter 7: Advanced Features - Handoffs, Guardrails, Tracing

## 7.1 Handoffs: Agent-to-Agent Delegation

Handoffs let one agent delegate to another. Think:

```
User asks a math question
    ↓
General Agent → "This is math, let me call the Math Agent!"
    ↓
Math Agent solves the problem
    ↓
Result goes back to user
```

### How Handoffs Work in Code

```python
from agents import Agent, Runner, handoff

# Create specialized agents
math_agent = Agent(
    name="Math Agent",
    instructions="You solve math problems",
    handoff_description="Use this for math questions"
)

weather_agent = Agent(
    name="Weather Agent",
    instructions="You answer weather questions",
    handoff_description="Use this for weather questions"
)

# Create a router agent
router_agent = Agent(
    name="Router",
    instructions="You route questions to the right agent",
    handoffs=[math_agent, weather_agent]
)

# Run it!
result = await Runner.run(router_agent, "What's 2 + 2?")
# The router will hand off to Math Agent!
```

### Handoff Flow Visualized

```
┌─────────────────────────────────────────────────────┐
│  1. Start with Agent A                              │
│     User input                                      │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  2. LLM decides: "Should I hand off to Agent B?"    │
│     Yes!                                            │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  3. Create HandoffCallItem                         │
│     • Pass conversation history? (configurable!)   │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  4. Start running Agent B                          │
│     • Gets the handoff input                       │
│     • Does its work                                │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  5. Agent B finishes                                │
│     • Return final output                          │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  6. Back to Agent A OR return to user              │
│     (depends on config!)                           │
└─────────────────────────────────────────────────────┘
```

Handoffs are incredibly powerful for multi-agent systems!

## 7.2 Guardrails: Safety First

Guardrails are checks that run at key points:

```
Input Guardrails → BEFORE the model sees the input
    ↓
Model runs
    ↓
Tool Input Guardrails → BEFORE a tool executes
    ↓
Tool executes
    ↓
Tool Output Guardrails → AFTER a tool executes
    ↓
Output Guardrails → BEFORE the user sees the output
```

### How to Write Guardrails

```python
from agents import input_guardrail, output_guardrail, InputGuardrailResult

@input_guardrail
async def no_secrets(input: str) -> InputGuardrailResult:
    """Don't let secret information through."""
    if "password" in input.lower() or "secret" in input.lower():
        return InputGuardrailResult(tripwire_triggered=True)
    return InputGuardrailResult(tripwire_triggered=False)

@output_guardrail
async def no_pii(output: str) -> InputGuardrailResult:
    """Don't output personally identifiable information."""
    import re
    if re.search(r"\d{3}-\d{2}-\d{4}", output):  # SSN-like
        return InputGuardrailResult(tripwire_triggered=True)
    return InputGuardrailResult(tripwire_triggered=False)

# Use them!
safe_agent = Agent(
    name="Safe Agent",
    instructions="Be helpful",
    input_guardrails=[no_secrets],
    output_guardrails=[no_pii]
)
```

### Tool Guardrails Too!

```python
from agents import tool_input_guardrail, tool_output_guardrail, ToolInputGuardrailResult

@tool_input_guardrail
async def check_transfer_amount(tool_name: str, args: dict) -> ToolInputGuardrailResult:
    """Check large transfers."""
    if tool_name == "transfer_money":
        amount = args.get("amount", 0)
        if amount > 10000:
            return ToolInputGuardrailResult(tripwire_triggered=True)
    return ToolInputGuardrailResult(tripwire_triggered=False)
```

## 7.3 Tracing: See What Happened

Tracing lets you visualize exactly what your agent did:

```
Trace
└── Span 1: Agent Start
    ├── Span 2: Input Guardrails
    ├── Span 3: Model Call
    │   └── Generation: Tokens used
    ├── Span 4: Tool Call (get_weather)
    │   └── Function Span: get_weather executed
    └── Span 5: Output Guardrails
```

### How to Use Tracing

```python
from agents import tracing

# Add a trace processor
def my_processor(trace: tracing.Trace) -> None:
    print(f"Trace finished: {trace.id}")
    for span in trace.spans:
        print(f"  • {span.name} ({span.duration_ms}ms)")

tracing.add_trace_processor(my_processor)

# Or use OpenTelemetry!
# (The SDK supports exporting traces anywhere)
```

### What Gets Traced

- Agent start/end
- Tool calls
- LLM generations
- Guardrails
- Handoffs
- Errors

Everything you need to debug and optimize!

## 7.4 Advanced: Agent Hooks

Hooks let you run code at lifecycle events:

```python
from agents import Agent, AgentHooks

class MyHooks(AgentHooks):
    async def on_start(self, ctx):
        print(f"Agent starting! Turn: {ctx.turn_count}")
    
    async def on_end(self, ctx, output):
        print(f"Agent done! Output: {output}")
    
    async def on_tool_start(self, ctx, tool_name):
        print(f"Calling tool: {tool_name}")
    
    async def on_tool_end(self, ctx, tool_name, result):
        print(f"Tool {tool_name} returned: {result}")

# Use them!
agent = Agent(
    name="Hooked Agent",
    instructions="Be helpful",
    hooks=MyHooks()
)
```

## 7.5 Advanced: Custom Model Providers

Don't want to use OpenAI? No problem!

```python
from agents import Model, ModelProvider

class MyCustomModel(Model):
    async def generate(self, ...):
        # Call your own model here!
        return "My custom response"

# Use it!
agent = Agent(
    name="Custom Agent",
    instructions="Be helpful",
    model=MyCustomModel()
)
```

Or use built-in providers like LiteLLM or AnyLLM for 100+ models!

## 7.6 Mini Example: Multi-Agent with Handoffs

Let's build a simple multi-agent system with our mini SDK pattern:

```python
# In your mini_agents.py (from Chapter 6)

@dataclass
class Handoff:
    target_agent: "Agent"
    description: str

@dataclass
class Agent(Generic[TContext]):
    # ... existing fields ...
    handoffs: list[Handoff] = field(default_factory=list)

# Update Runner to handle handoffs
class Runner:
    @staticmethod
    async def run(agent, user_input, ...):
        # ... existing loop ...
        
        # In _parse_llm_response():
        if "[HANDOFF]" in llm_response:
            agent_name = llm_response.split()[1]
            # Find the handoff
            for handoff in agent.handoffs:
                if handoff.target_agent.name == agent_name:
                    # Recursively run the target agent!
                    print(f"HANDING OFF TO {agent_name}!")
                    handoff_result = await Runner.run(
                        handoff.target_agent,
                        user_input,  # Or filtered history
                        context
                    )
                    return handoff_result
```

This is the essence of how real handoffs work!

## 7.7 Key Takeaways

1. **Handoffs = Multi-agent** - Delegate to specialized agents
2. **Guardrails = Safety** - Check input, output, and tool calls
3. **Tracing = Observability** - See exactly what happened
4. **Hooks = Lifecycle** - Run code at key events
5. **Custom Models = Flexibility** - Use any model you want
6. **All Composable** - Use these features together!

In the next chapter, we'll look at production patterns and best practices!
