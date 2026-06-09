# 02-message-format

In step 01 we wrote plain text. Now we need to wrap it into the **message structure** that the LLM API requires.

## What is a message?

The LLM API doesn't accept raw text. It accepts a **list of messages**, where each message has:

- `role` - Who is speaking
- `content` - What they say

## The three roles

| Role | Who | Purpose |
|------|-----|---------|
| `system` | You (the developer) | Define how the LLM should behave |
| `user` | The end user | Ask questions, give tasks |
| `assistant` | The LLM | Respond to the user |

## How it works

```
┌─────────────────────────────────────────────┐
│  Message List (conversation history)        │
├─────────────────────────────────────────────┤
│  {"role": "system",  "content": "..."}      │  ← Always first
│  {"role": "user",    "content": "..."}      │  ← The task
│  {"role": "assistant", "content": "..."}    │  ← LLM response (added later)
│  {"role": "user",    "content": "..."}      │  ← Observation (added later)
│  ...                                        │
└─────────────────────────────────────────────┘
```

The message list **grows over time** as the conversation continues. In later steps, we'll add assistant responses and user observations to this list.

## Our messages

From step 01, we had two pieces of text. Now we wrap them:

```python
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_task}
]
```

That's it. The API will receive this JSON array.

## The raw JSON output

When you run `agent.py`, you'll see the exact JSON that gets sent to the API:

```json
[
  {
    "role": "system",
    "content": "You are an assistant that can solve problems using Python code.\n\nWorkflow:\n1. Think: ...\n2. Code: ...\n3. Call final_answer(): ...\n\n..."
  },
  {
    "role": "user",
    "content": "Task: What is the square root of 2024?"
  }
]
```

This is the raw data. No magic, just JSON.

## How to run

```bash
uv run python agent.py
```

## Previous step

← [01-prompt-text](../01-prompt-text/README.md) - The plain text prompts

## Next step

→ [03-python-requests](../03-python-requests/README.md) - Send this JSON to the API using Python requests
