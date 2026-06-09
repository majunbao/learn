# 07b-prompt-example

One change from 07a: **add a concrete worked example** to the prompt.

## The problem with 07a's prompt

07a told the LLM the *rules* — "use Thought: then ```py" — but didn't *show* it. This is like telling someone how to ride a bike without ever demonstrating it.

LLMs are few-shot learners. They follow examples much better than abstract instructions.

## The fix: a worked example

Now the prompt includes:

```
Here is an example using notional tools:
---
Task: "What is the temperature in Paris plus 10?"

Thought: I will get Paris weather, print it so I can see the structure, then compute the answer.
```py
weather = get_weather("Paris")
print(weather)
```<end_code>
Observation: sunny, 20°C

Thought: Paris is 20°C. I add 10 and return the final answer.
```py
final_answer(calculate("20 + 10"))
```<end_code>
---
```

This example teaches three things at once:
1. **The format**: Thought → ```py → code → ```<end_code>
2. **The print pattern**: Use `print()` for intermediate results, not `final_answer()`
3. **The multi-step pattern**: Step 1 explores, Step 2 concludes

## Why this matters

Without an example, the LLM might:
- Forget the `<end_code>` tag
- Call `final_answer()` too early
- Not use `print()` for intermediate results (making the loop useless later)
- Mix Thought and Code together

With an example, the LLM *mimics* the format. This is the single most effective prompt engineering technique for structured output.

## What changed vs 07a?

| 07a | 07b |
|-----|-----|
| Rules only ("use Thought: then ```py") | Rules + concrete example |
| LLM might guess the format wrong | LLM copies the example format |
| No demonstration of print() pattern | Example shows print() → Observation flow |

Only the prompt changed. The code is identical.

## How to run

```bash
uv run versions/07b-prompt-example/agent.py
```

Compare the LLM's output with 07a — the format should be more consistent and closer to the example.

## Previous step

← [07a-prompt-structure](../07a-prompt-structure/README.md) - Force "Thought:" before code

## Next step

→ [07c-prompt-rules](../07c-prompt-rules/README.md) - Add specific rules and constraints
