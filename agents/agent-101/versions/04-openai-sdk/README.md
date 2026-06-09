# 04-openai-sdk

In step 03 we sent raw HTTP requests with Python `requests`. Now we do the **same thing using the OpenAI SDK** — a proper Python library.

## Why use an SDK?

In step 03, we manually built the HTTP request:

```python
requests.post(url, headers={...}, json={...})
response.json()["choices"][0]["message"]["content"]
```

This works, but it's verbose and error-prone. The OpenAI SDK wraps all of that into a clean Python API:

```python
client.chat.completions.create(model=..., messages=..., stop=...)
response.choices[0].message.content
```

Same result, less boilerplate, type hints, and better error messages.

## Wait — OpenAI SDK with other providers?

Yes! Many LLM providers are **compatible with the OpenAI API format**. That means you can use the OpenAI SDK by just pointing it to a different `base_url`:

```python
client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE   # points to your provider, not OpenAI
)
```

This is a common pattern — many LLM providers adopt the OpenAI API format so you can reuse the same SDK.

## The code

### Setup

```python
from openai import OpenAI

client = OpenAI(api_key=API_KEY, base_url=API_BASE)
```

One line to create the client. No manual headers, no URL construction.

### The call

```python
response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    stop=["<end_code>"]
)
```

Compare with step 03:

| Step 03 (raw requests) | Step 04 (OpenAI SDK) |
|------------------------|----------------------|
| Build URL manually | SDK handles it |
| Set headers manually | SDK handles it |
| `json=body` | Named parameters |
| Parse `response.json()` | Object attributes |

### The response

```python
response.choices[0].message.content
```

Instead of `response.json()["choices"][0]["message"]["content"]`, you get proper Python objects with attributes.

`response.model_dump_json(indent=2)` serializes the full response back to JSON for debugging — same structure we saw in step 03.

## What changed vs step 03?

Only **how** we make the request. Everything else is identical:

- Same system prompt
- Same user task
- Same messages format
- Same `stop` token
- Same response structure

The SDK is just a convenience layer over HTTP. Under the hood, it still sends the exact same POST request.

## How to run

```bash
uv run python agent.py
```

You'll see the full JSON response — same as step 03, but obtained with much cleaner code.

## Previous step

← [03-python-requests](../03-python-requests/README.md) - Send the request using raw HTTP

## Next step

→ [05-code-extraction](../05-code-extraction/README.md) - Extract Python code from the LLM response
