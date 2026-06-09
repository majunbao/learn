# 07-tool-use

In step 06 the LLM wrote Python code using only built-in libraries. But real agents need **tools** — custom functions that let the LLM interact with the outside world.

## The key idea: Tool Use

An agent without tools is just a calculator. Tools give the LLM abilities it doesn't have:

| Without tools | With tools |
|---------------|------------|
| Can only compute with Python builtins | Can call external APIs |
| Can't access real-time data | Can get weather, time, search results |
| Can't interact with systems | Can read files, send messages, etc. |

In this step, we define custom functions and **inject** them into the executor. The LLM can then call these functions in its code.

## The tools

We define three custom functions:

```python
def get_weather(city):
    return f"Weather in {city}: Sunny, 25°C"

def calculate(expression):
    return str(eval(expression))

def get_current_time():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

These are simple mock implementations. In a real agent:
- `get_weather` would call a weather API
- `calculate` would use a safe math parser
- `get_current_time` would return the actual time

The point is: **the LLM doesn't know how these functions work internally**. It just knows what they do (from the prompt) and calls them.

## The code

### Inject tools into executor

```python
executor = LocalPythonExecutor(additional_authorized_imports=[])
executor.send_tools({
    "final_answer": final_answer,
    "get_weather": get_weather,
    "calculate": calculate,
    "get_current_time": get_current_time,
})
```

Compare with step 06:

| Step 06 | Step 07 |
|---------|---------|
| `send_tools({"final_answer": final_answer})` | `send_tools({"final_answer": ..., "get_weather": ..., ...})` |
| LLM can only call `final_answer()` | LLM can call 4 functions |

### Tell the LLM about the tools

```python
system_prompt = """You are an assistant that solves problems using Python code.

You have access to the following tools:
- get_weather(city: str) -> str: Get the current weather for a city
- calculate(expression: str) -> str: Evaluate a math expression
- get_current_time() -> str: Get the current date and time
- final_answer(answer) -> any: Return the final answer when done
...
"""
```

The LLM needs to know:
1. **What tools exist** — function names
2. **What they do** — descriptions
3. **How to call them** — parameter types and names

### The LLM calls the tools

When the task is `"What's the weather in Beijing? Also calculate 15 * 23"`, the LLM writes:

```python
weather = get_weather("Beijing")
calc_result = calculate("15 * 23")
print(f"Weather: {weather}")
print(f"Calculation: {calc_result}")
final_answer({"weather": weather, "calculation": calc_result})
```

The LLM decides **which tools to call** and **what arguments to pass**. We just provide the tools.

## What changed vs step 06?

| Step 06 | Step 07 |
|---------|---------|
| Only `final_answer` injected | Multiple custom functions injected |
| LLM uses only Python builtins | LLM calls custom tools |
| Prompt: no tool descriptions | Prompt: lists available tools |
| Can't access external data | Can get weather, time, etc. |

The execution flow is the same. The difference is **what functions are available**.

## Why this matters

This is the foundation of all agent frameworks:
- **LangChain**: Tools = chains, retrievers, etc.
- **OpenAI Function Calling**: Tools = function definitions
- **AutoGPT**: Tools = commands (search, browse, write file, etc.)

Tools turn a chatbot into an agent. The more tools you give it, the more it can do.

## How to run

```bash
uv run python agent.py
```

You'll see:
1. The LLM's response (with code that calls `get_weather`, `calculate`, etc.)
2. The extracted code
3. The execution result (logs + output)

## Previous step

← [06-code-execution](../06-code-execution/README.md) - Execute the extracted code

## Next step

→ [07a-prompt-structure](../07a-prompt-structure/README.md) - Force "Thought:" before code