# 08-react-loop

In step 07 the LLM called custom tools and executed code — but only **once**. If the code didn't call `final_answer()`, or if you wanted the LLM to see the execution output and keep working, you were stuck.

Now we add the **loop**: the agent keeps thinking and acting until it produces a final answer (or hits a limit).

## Why a loop?

Step 07's task was simple: *"Get weather for Tokyo and calculate 25 * 30"*. The LLM can do it in one shot. But what about a task like:

> *"Compare the weather in Tokyo and Beijing, and calculate the temperature difference."*

This might play out in multiple steps:

```
Step 1: LLM writes code to get Tokyo's weather
        → Output: "Sunny, 22°C"
        → No final_answer() yet, so the loop continues

Step 2: LLM sees Tokyo's weather, now gets Beijing's weather and calculates the difference
        → Output: "Cloudy, 18°C, difference = 4°C"
        → Calls final_answer() → Done!
```

The LLM doesn't always get it right in one step. It might:
- Use `print()` instead of `final_answer()` on the first try
- Need to see intermediate results before deciding the next step
- Make a mistake and need to self-correct

The loop lets it **keep going** naturally.

## The key idea: ReAct Loop

ReAct = **Reason + Act + Observe + Repeat**

Step 07 showed one cycle:
```
Think → Act → Observe → Stop
```

Step 08 adds the loop:
```
Think → Act → Observe
        ↓
        Got final_answer?
        ├── Yes → Done!
        └── No  → Feed observation back → Repeat
```

## The flow

```python
for step in range(1, max_steps + 1):
    # Think: LLM generates code
    response = client.chat.completions.create(...)
    messages.append({"role": "assistant", "content": response_text})

    # Act: Extract and execute code
    result = executor(code_action=extracted_code)

    # Observe: Is the task done?
    if result.is_final_answer:
        break  # Done!

    # Not done: Feed execution output back to LLM
    observation = f"Observation:\n{result.logs}"
    messages.append({"role": "user", "content": observation})
```

Compare with step 07:

| Step 07 | Step 08 |
|---------|---------|
| Single attempt | Loop with `max_steps` limit |
| No retry if LLM forgets `final_answer()` | Automatic retry with observation feedback |
| Simple task (one-shot) | Multi-step task (needs iteration) |
| No safety limit | `max_steps = 5` prevents infinite loops |

The key difference is the `for` loop. Everything inside is the same Think → Act → Observe cycle from step 07, but now it repeats automatically.

## What changed vs step 07?

1. **The task** — something that genuinely benefits from multiple steps
2. **The loop** — `for step in range(1, max_steps + 1)` instead of running once
3. **Observation feedback** — when `final_answer()` isn't called, execution output is fed back as a user message so the LLM can continue
4. **Safety limit** — `max_steps` prevents infinite loops

## Why this matters

This is what makes it a **real agent**:

- **Self-correcting**: If code fails or doesn't call `final_answer()`, it sees the output and tries again
- **Iterative problem solving**: Complex tasks need multiple steps
- **Learning from observation**: Each attempt informs the next

Without the loop, the agent is just a fancy calculator. With the loop, it becomes a problem solver.

## How to run

```bash
uv run versions/08-react-loop/agent.py
```

You'll see:
- `=== Step 1 ===`, `=== Step 2 ===`, ... — each iteration
- `✓ Final answer: <result>` — when the agent succeeds
- Or stops after 5 steps if it never succeeds

## Previous step

← [07c-prompt-rules](../07c-prompt-rules/README.md) - Add explicit rules to prevent common mistakes

## Next step

This is the final step. You now have a complete minimal agent that can:
- Understand tasks
- Write Python code
- Call custom tools
- Execute code safely
- Observe results
- Iterate until success

From here, you can extend it with:
- More tools (web search, file operations, etc.)
- Better prompts
- Error handling
- Memory/state management
