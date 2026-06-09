# 07a-prompt-structure

One change from 07: **require "Thought:" before code**.

## The problem with 07's prompt

07's prompt said:

> "Workflow: 1. Think: Briefly explain your approach 2. Code: Write Python code"

This is vague. The LLM might:
- Skip the thinking entirely and just dump code
- Mix reasoning and code together
- Output in an unpredictable format

## The fix: explicit structure

Now the prompt says:

> "In the 'Thought:' sequence, explain your reasoning and which tools you will use."
> "Always start with a 'Thought:' line before the code block, otherwise you will fail."

This forces the LLM to output something like:

```
Thought: I need to get the weather for Tokyo and calculate 25 * 30. I'll use get_weather and calculate tools.
```py
weather = get_weather("Tokyo")
result = calculate("25 * 30")
final_answer({"weather": weather, "calculation": result})
```<end_code>
```

## Why this matters

1. **Chain-of-thought**: The LLM reasons before acting. This improves accuracy — the LLM commits to a plan before writing code.
2. **Structured output**: We know the "Thought:" part is reasoning, and the ```py part is code. Easy to parse.
3. **Debuggability**: When the agent makes a mistake, we can see *why* — the Thought reveals its reasoning.

This is the first half of the **ReAct** pattern (Reason + Act). The "Thought:" is the Reason part.

## What changed vs 07?

| 07 | 07a |
|----|-----|
| "Briefly explain your approach" | "In the 'Thought:' sequence, explain your reasoning" |
| LLM might skip thinking | LLM must output "Thought:" before code |
| Unstructured output | Structured: Thought + Code |

Only the prompt changed. The code is identical.

## How to run

```bash
uv run versions/07a-prompt-structure/agent.py
```

Compare the LLM's output with 07 — you should see a clear "Thought:" line now.

## Previous step

← [07-tool-use](../07-tool-use/README.md) - LLM calls custom local functions

## Next step

→ [07b-prompt-example](../07b-prompt-example/README.md) - Add a concrete example to the prompt
