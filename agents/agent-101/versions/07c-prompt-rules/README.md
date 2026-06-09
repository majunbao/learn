# 07c-prompt-rules

One change from 07b: **add explicit rules** to prevent common LLM mistakes.

## The problem with 07b's prompt

07b has a good example, but the LLM still makes predictable mistakes:

| Mistake | Example | Why it fails |
|---------|---------|-------------|
| Dict arguments | `get_weather({"city": "Paris"})` | Function expects positional arg |
| Variable name collision | `final_answer = "result"` | Overwrites the tool function |
| Importing tools | `import get_weather` | Tools are pre-injected |
| Chaining unpredictable calls | `result = tool_a(tool_b(x))` | tool_b's format is unknown |

These aren't random — they're patterns that LLMs fall into. The prompt needs to explicitly forbid them.

## The fix: numbered rules

Now the prompt includes:

```
Rules you must always follow:
1. Always provide a 'Thought:' sequence, and a '```py' sequence ending with '```<end_code>', else you will fail.
2. Use only variables that you have defined!
3. Always use the right arguments for the tools. DO NOT pass the arguments as a dict as in 'get_weather({"city": "Paris"})', but use the arguments directly as in 'get_weather("Paris")'.
4. For tools with unpredictable output: do not chain too many sequential tool calls in the same code block. Rather output results with print() to use them in the next block.
5. Never name a variable the same as a tool (e.g. don't reuse `final_answer`).
6. Do not import the pre-loaded tools — just call them directly.
```

These rules come from smolagents' [code_agent.yaml](https://github.com/huggingface/smolagents/blob/main/src/smolagents/prompts/code_agent.yaml) — they encode real-world failure patterns observed in production.

## Why each rule matters

| Rule | Prevents | Origin |
|------|----------|--------|
| 1. Thought + code block format | LLM outputs raw code without structure | smolagents rule #1 |
| 2. Use only defined variables | NameError from hallucinated variables | smolagents rule #2 |
| 3. Direct args, not dict | `TypeError: unexpected keyword argument` | smolagents rule #3 |
| 4. Don't chain unpredictable calls | Output format mismatch between tools | smolagents rule #4 |
| 5. No variable-tool name collision | `final_answer = x` breaks `final_answer()` | smolagents `fix_final_answer_code()` |
| 6. Don't import tools | `ImportError` for pre-injected functions | Common beginner mistake |

## What changed vs 07b?

| 07b | 07c |
|-----|-----|
| Example only (no rules) | Example + explicit rules |
| LLM might use dict args | Rule 3 forbids it |
| LLM might shadow tool names | Rule 5 forbids it |
| LLM might chain unpredictable calls | Rule 4 advises against it |

Only the prompt changed. The code is identical.

## How to run

```bash
uv run versions/07c-prompt-rules/agent.py
```

## Previous step

← [07b-prompt-example](../07b-prompt-example/README.md) - Add a concrete example to the prompt

## Next step

→ [08-react-loop](../08-react-loop/README.md) - The full ReAct loop: Think → Act → Observe → Repeat
