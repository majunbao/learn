# 05-code-extraction

In step 04 we got the LLM's response as text. But the response contains **both natural language and code** — we need to extract just the code part.

## The problem

The LLM responds with something like:

```
I will calculate the square root of 2024.

```py
import math
result = math.sqrt(2024)
print(result)
final_answer(result)
```
```

We can't run this directly — we need to pull out just the `import math...final_answer(result)` part.

## The solution: regex extraction

The LLM follows our prompt format and wraps code in ` ```py ... ``` ` blocks. We can extract it with a simple regex:

```python
code_match = re.search(r"```py([\s\S]*?)```", response_text)
if code_match:
    extracted_code = code_match.group(1).strip()
```

How it works:

| Part | Meaning |
|------|---------|
| `` ```py `` | Matches the opening code fence |
| `([\s\S]*?)` | Captures everything inside (non-greedy) |
| `` ``` `` | Matches the closing code fence |
| `.strip()` | Removes leading/trailing whitespace |

The `?` makes it **non-greedy** — it stops at the first closing ` ``` `, not the last one.

## The code

### Same as step 04

```python
client = OpenAI(api_key=API_KEY, base_url=API_BASE)

response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    stop=["<end_code>"]
)

response_text = response.choices[0].message.content
```

Nothing new here — same SDK call, same `stop` token.

### New: extract the code

```python
import re

code_match = re.search(r"```py([\s\S]*?)```", response_text)
if code_match:
    extracted_code = code_match.group(1).strip()
    print(extracted_code)
```

That's it. Two lines to go from raw text to runnable code.

## What changed vs step 04?

Only **what we do after getting the response**:

| Step 04 | Step 05 |
|---------|---------|
| Print full JSON response | Print response text |
| — | Extract code with regex |
| — | Print extracted code |

The LLM call is identical. We just added post-processing.

## Why this matters

This is the first step toward **making the LLM's output actionable**. Right now we just print the code. In the next step, we'll actually **run** it.

## How to run

```bash
uv run python agent.py
```

You'll see:
1. The full response text (with thinking + code)
2. The extracted code (just the Python part)

## Previous step

← [04-openai-sdk](../04-openai-sdk/README.md) - Use the OpenAI SDK instead of raw HTTP

## Next step

→ [06-code-execution](../06-code-execution/README.md) - Execute the extracted code
