# 06-code-execution

In step 05 we extracted Python code from the LLM response. Now we **execute it** — this is where the agent actually "does" something.

## The key idea

An agent isn't just a chatbot that talks. It **takes action**. In our case, the action is running Python code that the LLM writes.

The flow is now:

```
User task → LLM generates code → Extract code → Execute code → Get result
```

Steps 01-05 covered the first three arrows. This step adds the last two.

## Why not just `exec()`?

You *could* do this:

```python
exec(extracted_code)  # ⚠️ Dangerous!
```

But `exec()` has problems:
- **No sandbox** — the code can do anything (delete files, make network requests, etc.)
- **No output capture** — `print()` goes to stdout, you can't easily get the result
- **No `final_answer()`** — we need a way for the code to return a structured result

Instead, we use `LocalPythonExecutor` from `smolagents` — a sandboxed Python executor that:
- Runs code in a controlled environment
- Captures `print()` output as logs
- Lets us inject custom functions like `final_answer()`

## The code

### Same as step 05

```python
client = OpenAI(api_key=API_KEY, base_url=API_BASE)

response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    stop=["<end_code>"]
)

response_text = response.choices[0].message.content
code_match = re.search(r"```py([\s\S]*?)```", response_text)
```

Nothing new — same SDK call, same regex extraction.

### New: set up the executor

```python
from smolagents import LocalPythonExecutor

def final_answer(answer):
    return answer

executor = LocalPythonExecutor(additional_authorized_imports=[])
executor.send_tools({"final_answer": final_answer})
```

- `LocalPythonExecutor(additional_authorized_imports=[])` — creates a sandboxed Python runtime (empty list means no extra imports allowed beyond defaults)
- `send_tools({"final_answer": final_answer})` — injects `final_answer()` into the executor's namespace so the LLM's code can call it

### New: execute the code

```python
if code_match:
    extracted_code = code_match.group(1).strip()
    result = executor(code_action=extracted_code)
    print(f"logs: {repr(result.logs)}")
    print(f"output: {repr(result.output)}")
    print(f"is_final_answer: {result.is_final_answer}")
```

The result object has:

| Field | Meaning |
|-------|---------|
| `logs` | Anything `print()` outputs |
| `output` | The value passed to `final_answer()` |
| `is_final_answer` | Whether `final_answer()` was called |

## What changed vs step 05?

| Step 05 | Step 06 |
|---------|---------|
| Extract code | Extract code |
| Print extracted code | Execute extracted code |
| — | Print execution result (logs + output) |

The LLM call and extraction are identical. We just added execution.

## Why this matters

This is the moment the system becomes an **agent** — it doesn't just generate text, it **acts** on it. The LLM decides what code to write, and we run it.

But there's a limitation: it only runs **one** step. If the code fails or the result is wrong, there's no retry. The next steps will add that.

## How to run

```bash
uv run python agent.py
```

You'll see:
1. The execution logs (from `print()`)
2. The final answer (from `final_answer()`)
3. Whether `final_answer()` was called

## Previous step

← [05-code-extraction](../05-code-extraction/README.md) - Extract Python code from the LLM response

## Next step

→ [07-tool-use](../07-tool-use/README.md) - LLM calls custom local functions (tools)
