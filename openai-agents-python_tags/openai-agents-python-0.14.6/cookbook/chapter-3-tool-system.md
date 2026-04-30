# Chapter 3: Tool System - FunctionTool internals & calling flow

## 3.1 The Tool Family Tree

First, let's visualize all the tool types available:

```
Tool (Union Type)
├── FunctionTool
│   ├── Custom Python function
│   └── Agent.as_tool()
├── FileSearchTool
├── WebSearchTool
├── ComputerTool
├── HostedMCPTool
├── CustomTool
├── ShellTool
├── ApplyPatchTool
├── LocalShellTool
├── ImageGenerationTool
├── CodeInterpreterTool
└── ToolSearchTool
```

But the heart and soul is `FunctionTool` - that's what you'll use 90% of the time!

## 3.2 From Python Function to Tool: The Journey

Let's start with a simple function and trace what happens:

```python
@function_tool
async def get_weather(latitude: float, longitude: float) -> str:
    """Get the current weather for a location.
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    return f"Weather at {latitude}, {longitude}: 72°F, sunny"
```

Let's visualize the transformation pipeline:

```
Your Python Function
        ↓
    Inspect signature
        ↓
    Parse docstring
        ↓
    Generate JSON Schema
        ↓
    Wrap in invoker
        ↓
    Add error handling
        ↓
    Add guardrails
        ↓
    Add approval
        ↓
    Add timeout
        ↓
   FunctionTool! 🎉
```

## 3.3 The `@function_tool` Decorator Deep Dive

Let's look at what this decorator actually does! First, notice the overloads:

```python
@overload
def function_tool(func: ToolFunction[...]) -> FunctionTool:
    """Overload for usage as @function_tool (no parentheses)."""

@overload
def function_tool(*, name_override: str | None = None, ...) -> Callable[...]:
    """Overload for usage as @function_tool(...)."""
```

This is a classic decorator pattern - works both with and without parentheses!

### Step 1: Function Schema Generation

The magic happens in `function_schema()` from `.function_schema`. Let's see what it extracts:

```
Your Function
├── Name: "get_weather"
├── Docstring: "Get the current weather..."
├── Parameters:
│   ├── latitude: float
│   │   └── Description: "Latitude of the location"
│   └── longitude: float
│       └── Description: "Longitude of the location"
└── Return Type: str
```

All this becomes a JSON Schema!

### Step 2: The Invoker Wrapper

Here's the key insight: your function isn't called directly. It's wrapped!

```
LLM sends JSON
    ↓
Parse JSON to Python args
    ↓
Validate with Pydantic
    ↓
Call your function
    ↓
Capture result
    ↓
Convert to output format
    ↓
Return to LLM
```

And look at this clever class in the source:

```python
class _FailureHandlingFunctionToolInvoker:
    """Internal callable that rebinds wrapper error handling for copied FunctionTools."""
    
    async def __call__(self, ctx: ToolContext[Any], input: str) -> Any:
        try:
            return await self._invoke_tool_impl(ctx, input)
        except Exception as e:
            # Error handling magic here!
            result = await maybe_invoke_function_tool_failure_error_function(...)
            if result is None:
                raise
            return result
```

This is the Decorator pattern at work!

## 3.4 FunctionTool Dataclass Fields

Let's look at what's inside a `FunctionTool`:

```python
@dataclass(eq=False)
class FunctionTool:
    name: str
    description: str
    params_json_schema: dict[str, Any]
    
    # The actual executor!
    on_invoke_tool: Callable[[ToolContext[Any], str], Awaitable[Any]]
    
    # Safety & control
    strict_json_schema: bool = True
    is_enabled: bool | Callable[...] = True
    needs_approval: bool | Callable[...] = False
    
    # Guardrails
    tool_input_guardrails: list[ToolInputGuardrail] = field(default_factory=list)
    tool_output_guardrails: list[ToolOutputGuardrail] = field(default_factory=list)
    
    # Timeout
    timeout_seconds: float | None = None
    timeout_behavior: ToolTimeoutBehavior = "error_as_result"
    timeout_error_function: ToolErrorFunction | None = None
    
    # ... and more!
```

## 3.5 Tool Calling Flow: The Complete Picture

Now let's visualize the full execution pipeline when the LLM calls a tool:

```
┌─────────────────────────────────────────────────────────────────┐
│  1. LLM Decision                                                 │
│     "I should call get_weather(37.7749, -122.4194)"             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. Parse & Validate                                             │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ JSON Input:                                           │  │
│     │ {                                                     │  │
│     │   "latitude": 37.7749,                                │  │
│     │   "longitude": -122.4194                              │  │
│     │ }                                                     │  │
│     └───────────────────────────────────────────────────────┘  │
│                              ↓                                  │
│     Pydantic validation against params_json_schema              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. Input Guardrails                                            │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ Run all tool_input_guardrails                        │  │
│     │ If any fail, return error to LLM                     │  │
│     └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. Approval Check                                              │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ needs_approval?                                       │  │
│     │ Yes → Interrupt run, wait for approve()              │  │
│     │ No → Continue                                         │  │
│     └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. Timeout Wrapper                                             │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ asyncio.wait_for(..., timeout=timeout_seconds)       │  │
│     └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  6. Call YOUR Function!                                         │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ await get_weather(37.7749, -122.4194)                │  │
│     └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  7. Output Guardrails                                           │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ Run all tool_output_guardrails                       │  │
│     └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  8. Format Result                                               │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ str → ToolOutputText                                  │  │
│     │ Image → ToolOutputImage                               │  │
│     │ File → ToolOutputFileContent                          │  │
│     └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  9. Return to LLM!                                              │
│     "Weather at 37.7749, -122.4194: 72°F, sunny"              │
└─────────────────────────────────────────────────────────────────┘
```

That's a lot of steps, but they all happen automatically!

## 3.6 Tool Context: What's That First Parameter?

Notice that functions can have three different signatures:

```python
# Form 1: No context
async def get_weather(latitude: float, longitude: float) -> str: ...

# Form 2: With RunContextWrapper
async def get_weather(
    ctx: RunContextWrapper[MyContext],
    latitude: float,
    longitude: float,
) -> str: ...

# Form 3: With ToolContext
async def get_weather(
    ctx: ToolContext[MyContext],
    latitude: float,
    longitude: float,
) -> str: ...
```

Let's visualize what's in each:

```
RunContextWrapper
├── context: MyContext (your custom data)
├── run_config: RunConfig
└── current_agent: Agent

ToolContext (extends RunContextWrapper)
├── Everything from RunContextWrapper
├── tool_call_id: str
├── raw_arguments: str
└── parent_trace_id: str | None
```

The SDK automatically detects which signature you used and injects the right context!

## 3.7 Error Handling: The Safety Net

What if your function raises an exception? Let's see the flow:

```
Your function raises ValueError("Invalid coordinates")
        ↓
    Captured by _FailureHandlingFunctionToolInvoker
        ↓
    Call failure_error_function(ctx, error)
        ↓
    If returns string: send to LLM as tool result
        ↓
    If returns None: re-raise the exception
```

By default, it uses `default_tool_error_function`, which returns something like:
```
"Error: Invalid coordinates"
```

And the LLM sees that as the tool output, so it can recover!

## 3.8 Timeouts: Prevent Hanging Forever

Tools can have timeouts. Here's how:

```python
@function_tool(timeout=5.0)
async def slow_api_call(query: str) -> str:
    # This will timeout after 5 seconds
    await asyncio.sleep(10)
    return "Done"
```

And you can customize the timeout behavior:

```python
@function_tool(
    timeout=5.0,
    timeout_behavior="error_as_result",  # Or "raise_exception"
    timeout_error_function=lambda ctx, e: f"Slow API timed out: {e}"
)
```

## 3.9 Approval: Human-in-the-Loop

Sometimes you want humans to approve tool calls. Here's how:

```python
@function_tool(needs_approval=True)
async def transfer_money(amount: float, to: str) -> str:
    # This will pause and wait for .approve()
    return f"Transferred ${amount} to {to}"
```

Or with a dynamic check:

```python
async def should_approve(
    ctx: RunContextWrapper[MyContext],
    args: dict[str, Any],
    tool_name: str,
) -> bool:
    # Approve small transfers automatically
    return args["amount"] < 100

@function_tool(needs_approval=should_approve)
async def transfer_money(amount: float, to: str) -> str: ...
```

## 3.10 Tool Output Types: More Than Just Strings

Your tool can return different types of outputs:

```python
# Plain text (most common)
return "The weather is sunny"

# Or explicit ToolOutputText
return ToolOutputText(text="The weather is sunny")

# Image
return ToolOutputImage(image_url="https://example.com/weather.png")

# File
return ToolOutputFileContent(
    file_data="base64_encoded_data",
    filename="weather.csv"
)

# Or a list!
return [
    ToolOutputText(text="Here's the weather report"),
    ToolOutputImage(image_url="https://example.com/chart.png")
]
```

## 3.11 The Copy Mechanism: Why `__copy__`?

Look at this method in the source:

```python
def __copy__(self) -> FunctionTool:
    copied_tool = dataclasses.replace(self)
    # ... complex copying logic for non-dataclass fields
    for attr_name, attr_value in self.__dict__.items():
        if attr_name not in dataclass_field_names:
            setattr(copied_tool, attr_name, attr_value)
    return copied_tool
```

Why? Because `FunctionTool` has:
- Dataclass fields (serializable)
- Non-dataclass fields (like the invoker function)

When you copy, you need both!

## 3.12 Tool Origins: Where Did This Tool Come From?

Look at `ToolOrigin`:

```python
@dataclass(frozen=True)
class ToolOrigin:
    type: ToolOriginType  # FUNCTION, MCP, or AGENT_AS_TOOL
    mcp_server_name: str | None = None
    agent_name: str | None = None
    agent_tool_name: str | None = None
```

This helps with debugging and tracing!

## 3.13 Let's Build It: A Mini FunctionTool

Now that we understand, let's build a simplified version from scratch!

```python
from dataclasses import dataclass
import inspect
import json
from typing import Any, Callable

@dataclass
class MiniFunctionTool:
    name: str
    description: str
    params_json_schema: dict[str, Any]
    func: Callable
    
    async def invoke(self, args_json: str) -> str:
        # Step 1: Parse JSON
        args = json.loads(args_json)
        
        # Step 2: Call function
        result = await self.func(**args)
        
        # Step 3: Return string
        return str(result)

def mini_function_tool(func):
    # Extract name
    name = func.__name__
    
    # Extract docstring
    description = func.__doc__ or ""
    
    # Extract signature (simplified - real one uses type hints!)
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    
    # Build simple schema (real one is much more complex!)
    schema = {
        "type": "object",
        "properties": {p: {"type": "string"} for p in params},
        "required": params
    }
    
    return MiniFunctionTool(
        name=name,
        description=description,
        params_json_schema=schema,
        func=func
    )

# Use it!
@mini_function_tool
async def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"
```

The real SDK does all this plus validation, guardrails, error handling, timeouts, approval, etc!

## 3.14 Key Takeaways

1. **Tools are just wrapped functions** - with lots of safety layers
2. **JSON Schema is auto-generated** from type hints and docstrings
3. **Multiple function signatures supported** - context or no context
4. **Error handling is configurable** - let LLM recover or raise exceptions
5. **Human approval built-in** - pause execution when needed
6. **Timeouts prevent hangs** - 5 seconds, 30 seconds, whatever you need
7. **Multiple output types** - text, images, files, lists

In the next chapter, we'll dive into the Runner engine and see how all these pieces fit together in the main loop!
