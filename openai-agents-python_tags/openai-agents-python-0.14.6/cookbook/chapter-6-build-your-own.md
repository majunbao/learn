# Chapter 6: Build Your Own - 100-line Mini SDK from Scratch

## 6.1 Let's Build It!

We're going to create a tiny but fully-functional SDK that captures the essence:

- Agent as a dataclass
- Function tools
- A runner with a loop
- Turn-based execution

Let's do this in one file!

## 6.2 The Complete Mini SDK (200 lines!)

Create `mini_agents.py`:

```python
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar
import inspect
import json

TContext = TypeVar("TContext")

# ============================================
# TOOL SYSTEM
# ============================================

@dataclass
class FunctionTool:
    name: str
    description: str
    params_json_schema: dict[str, Any]
    func: Callable

def function_tool(func: Callable) -> FunctionTool:
    """Decorator to create a FunctionTool from a Python function."""
    name = func.__name__
    description = func.__doc__ or "No description"
    
    # Extract parameters (simple version)
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    
    # Skip first param if it's a context-like thing
    if params and params[0].name in ("ctx", "context", "self"):
        params = params[1:]
    
    # Build simple JSON schema
    properties = {}
    required = []
    for param in params:
        param_name = param.name
        properties[param_name] = {"type": "string"}
        if param.default is inspect.Parameter.empty:
            required.append(param_name)
    
    params_json_schema = {
        "type": "object",
        "properties": properties,
        "required": required
    }
    
    return FunctionTool(
        name=name,
        description=description,
        params_json_schema=params_json_schema,
        func=func
    )

# ============================================
# AGENT
# ============================================

@dataclass
class Agent(Generic[TContext]):
    name: str
    instructions: str
    tools: list[FunctionTool] = field(default_factory=list)
    model: str = "gpt-4"

# ============================================
# CONTEXT WRAPPER
# ============================================

@dataclass
class RunContextWrapper(Generic[TContext]):
    context: TContext
    turn_count: int = 0

# ============================================
# RUNNER ENGINE
# ============================================

@dataclass
class RunResult:
    final_output: str
    turn_count: int
    conversation: list[dict]

class Runner:
    @staticmethod
    async def run(
        agent: Agent[TContext],
        user_input: str,
        context: TContext | None = None,
        max_turns: int = 10
    ) -> RunResult:
        # Initialize
        ctx = RunContextWrapper(context=context or {})
        conversation = [{"role": "user", "content": user_input}]
        
        # Build tool map for quick lookup
        tool_map = {tool.name: tool for tool in agent.tools}
        
        # The Loop!
        while ctx.turn_count < max_turns:
            ctx.turn_count += 1
            print(f"\n--- Turn {ctx.turn_count} ---")
            
            # Step 1: "Call LLM" (we'll mock this)
            llm_response = await Runner._mock_llm_call(agent, conversation, tool_map)
            print(f"LLM says: {llm_response}")
            
            # Step 2: Parse the response
            parsed = Runner._parse_llm_response(llm_response)
            
            # Step 3: Decide what to do
            if parsed["type"] == "final_output":
                # We're done!
                conversation.append({"role": "assistant", "content": parsed["content"]})
                return RunResult(
                    final_output=parsed["content"],
                    turn_count=ctx.turn_count,
                    conversation=conversation
                )
            elif parsed["type"] == "tool_call":
                # Need to call a tool!
                tool_name = parsed["tool_name"]
                tool_args = parsed["args"]
                
                if tool_name not in tool_map:
                    conversation.append({
                        "role": "tool",
                        "content": f"Error: Tool {tool_name} not found"
                    })
                    continue
                
                # Execute the tool
                tool = tool_map[tool_name]
                print(f"Calling tool: {tool_name} with args: {tool_args}")
                
                try:
                    # Check if tool expects a context
                    sig = inspect.signature(tool.func)
                    params = list(sig.parameters.values())
                    
                    if params and params[0].name in ("ctx", "context", "self"):
                        # Call with context
                        tool_result = await tool.func(ctx, **tool_args)
                    else:
                        # Call without
                        tool_result = await tool.func(**tool_args)
                    
                    print(f"Tool result: {tool_result}")
                    conversation.append({
                        "role": "tool",
                        "content": str(tool_result)
                    })
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    print(error_msg)
                    conversation.append({"role": "tool", "content": error_msg})
        
        # Max turns hit
        raise Exception(f"Max turns exceeded ({max_turns})")
    
    @staticmethod
    async def _mock_llm_call(agent, conversation, tool_map):
        """Mock LLM - simulates what a real LLM would do."""
        last_msg = conversation[-1]["content"]
        
        # Simple heuristics
        if conversation[-1]["role"] == "tool":
            # We just got a tool result, respond naturally
            return f"[FINAL] The tool returned: {last_msg}. Is there anything else I can help with?"
        
        if "weather" in last_msg.lower():
            # Call weather tool
            return "[TOOL] get_weather(location='San Francisco')"
        
        if "time" in last_msg.lower():
            # Call time tool
            return "[TOOL] get_time()"
        
        if "joke" in last_msg.lower():
            # Call joke tool
            return "[TOOL] get_joke()"
        
        # Just respond
        return f"[FINAL] I'm {agent.name}! You said: {last_msg}"
    
    @staticmethod
    def _parse_llm_response(response: str) -> dict:
        """Parse our mock LLM format."""
        if response.startswith("[FINAL]"):
            return {
                "type": "final_output",
                "content": response[len("[FINAL]"):].strip()
            }
        elif response.startswith("[TOOL]"):
            tool_part = response[len("[TOOL]"):].strip()
            # Parse "tool_name(arg1=val1, arg2=val2)"
            if "(" in tool_part:
                tool_name = tool_part[:tool_part.index("(")]
                args_part = tool_part[tool_part.index("(")+1:tool_part.rindex(")")]
                # Simple arg parsing
                args = {}
                if args_part.strip():
                    for arg in args_part.split(","):
                        key, val = arg.split("=")
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        args[key] = val
                return {
                    "type": "tool_call",
                    "tool_name": tool_name,
                    "args": args
                }
            else:
                return {
                    "type": "tool_call",
                    "tool_name": tool_part,
                    "args": {}
                }
        else:
            return {
                "type": "final_output",
                "content": response
            }

# ============================================
# LET'S TEST IT!
# ============================================

@function_tool
async def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    return f"Sunny, 72°F in {location}"

@function_tool
async def get_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

@function_tool
async def get_joke() -> str:
    """Tell a programming joke."""
    return "Why do programmers prefer dark mode? Because light attracts bugs!"

@function_tool
async def get_user(ctx: RunContextWrapper[dict]) -> str:
    """Get the current user from context."""
    return f"Current user: {ctx.context.get('user_id', 'anonymous')}"

async def main():
    print("="*50)
    print("Mini Agents SDK - Demo")
    print("="*50)
    
    # Create an agent
    agent = Agent(
        name="Helper",
        instructions="You are a helpful assistant",
        tools=[get_weather, get_time, get_joke, get_user]
    )
    
    # Test 1: Basic chat
    print("\n\n--- Test 1: Basic chat ---")
    result = await Runner.run(agent, "Hello!")
    print(f"Final output: {result.final_output}")
    
    # Test 2: Weather tool
    print("\n\n--- Test 2: Weather ---")
    result = await Runner.run(agent, "What's the weather?")
    print(f"Final output: {result.final_output}")
    
    # Test 3: With custom context
    print("\n\n--- Test 3: Context ---")
    result = await Runner.run(
        agent,
        "Who am I?",
        context={"user_id": "john_doe_123"}
    )
    print(f"Final output: {result.final_output}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## 6.3 Let's Run It!

Save and run! You should see:

```
==================================================
Mini Agents SDK - Demo
==================================================

--- Test 1: Basic chat ---

--- Turn 1 ---
LLM says: [FINAL] I'm Helper! You said: Hello!
Final output: I'm Helper! You said: Hello!

--- Test 2: Weather ---

--- Turn 1 ---
LLM says: [TOOL] get_weather(location='San Francisco')
Calling tool: get_weather with args: {'location': 'San Francisco'}
Tool result: Sunny, 72°F in San Francisco

--- Turn 2 ---
LLM says: [FINAL] The tool returned: Sunny, 72°F in San Francisco. Is there anything else I can help with?
Final output: The tool returned: Sunny, 72°F in San Francisco. Is there anything else I can help with?

--- Test 3: Context ---

--- Turn 1 ---
LLM says: [FINAL] I'm Helper! You said: Who am I?
Final output: I'm Helper! You said: Who am I?
```

(The last one didn't trigger our tool - exercise for you to improve the mock LLM!)

## 6.4 What We Built

Let's list what's in our mini SDK:

✅ **Agent dataclass** - Configuration, not state  
✅ **Tool system with decorator** - `@function_tool`  
✅ **RunContextWrapper** - Your custom data + turn count  
✅ **Runner with loop** - Turn-based execution  
✅ **Mock LLM** - So we can test without API calls  
✅ **Tool execution** - Calls your functions  
✅ **Conversation history** - List of messages  

Not bad for 200 lines!

## 6.5 Let's Extend It: Add Guardrails

Let's add one more feature to see how extensible this pattern is:

```python
# Add this to mini_agents.py

from typing import Awaitable

GuardrailFunction = Callable[[str], Awaitable[bool]]

@dataclass
class Agent(Generic[TContext]):
    name: str
    instructions: str
    tools: list[FunctionTool] = field(default_factory=list)
    model: str = "gpt-4"
    input_guardrails: list[GuardrailFunction] = field(default_factory=list)
    output_guardrails: list[GuardrailFunction] = field(default_factory=list)

# Update Runner.run() to add:
class Runner:
    @staticmethod
    async def run(...):
        # ... existing code ...
        
        # Before anything: run input guardrails
        for guardrail in agent.input_guardrails:
            allowed = await guardrail(user_input)
            if not allowed:
                return RunResult(
                    final_output="Input rejected by guardrail",
                    turn_count=0,
                    conversation=conversation
                )
        
        # ... rest of the loop ...
        
        # After final output: run output guardrails
        if parsed["type"] == "final_output":
            for guardrail in agent.output_guardrails:
                allowed = await guardrail(parsed["content"])
                if not allowed:
                    return RunResult(
                        final_output="Output rejected by guardrail",
                        turn_count=ctx.turn_count,
                        conversation=conversation
                    )
            # ... rest ...

# Usage:
async def no_secret_info(input: str) -> bool:
    if "secret" in input.lower():
        return False
    return True

agent = Agent(
    name="SafeAgent",
    instructions="Be helpful",
    input_guardrails=[no_secret_info]
)
```

This shows how easy it is to add features with this architecture!

## 6.6 Compare with the Real SDK

Let's map our mini SDK to the real one:

| Mini SDK | Real SDK |
|----------|----------|
| `Agent` | `Agent` (dataclass too!) |
| `@function_tool` | `@function_tool` (way more features) |
| `RunContextWrapper` | `RunContextWrapper` (exact same pattern!) |
| `Runner.run()` | `Runner.run()` (same flow!) |
| `_mock_llm_call()` | Models in `src/agents/models/` |
| `_parse_llm_response()` | `turn_resolution.py` |
| (Conversation as list) | `RunState` with `_items` |

The real SDK is just a more sophisticated, production-grade version of what we just built!

## 6.7 Key Takeaways

1. **Start small** - You can build the core in 200 lines
2. **Dataclasses are perfect** - For configuration (Agent, FunctionTool)
3. **Loops + state machines** - The runner is just a loop deciding next steps
4. **Generics give type safety** - `Agent[YourContext]` works great
5. **Decorators make nice APIs** - `@function_tool` is clean
6. **Composition over inheritance** - Build complex agents from tools, guardrails, etc.

In the next chapter, we'll look at the advanced features: Handoffs, Guardrails, and Tracing!
