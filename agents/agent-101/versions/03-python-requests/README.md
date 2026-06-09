# 03-python-requests

In step 02 we built the message JSON. Now we **actually send it** to the LLM over HTTP.

## What's happening?

Calling an LLM is just an HTTP request. Nothing magical:

```
┌─────────────┐    HTTP POST    ┌──────────────┐
│   Your PC   │ ──────────────> │   LLM API    │
│             │                  │   server     │
│             │ <────────────── │              │
└─────────────┘    JSON reply    └──────────────┘
```

That's it. The LLM lives behind an HTTP endpoint.

## The HTTP request

To call the API, we need 4 things:

### 1. URL
```
POST {API_BASE}/chat/completions
```
The endpoint that accepts chat messages. The actual URL comes from your `.env` config.

### 2. Headers
```
Authorization: Bearer <YOUR_API_KEY>
Content-Type: application/json
```
- `Authorization` - Proves who you are (your API key)
- `Content-Type` - Tells the server the body is JSON

### 3. Body (JSON)
```json
{
  "model": "your-model-name",
  "messages": [...],
  "stop": ["<end_code>"]
}
```
- `model` - Which model to use
- `messages` - The conversation (built in step 02)
- `stop` - Tokens that tell the model to stop generating

### 4. Why `stop: ["<end_code>"]`?

Remember the prompt format from step 01:
```
```py
# Your Python code here
final_answer(your_answer)
```<end_code>
```

We told the LLM to put `<end_code>` after the code block. By passing it as a `stop` token, the API stops generation right when it sees `<end_code>`. This keeps responses clean and avoids extra text.

## The response

The API returns JSON with a structure like:

```json
{
  "id": "...",
  "model": "your-model-name",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "I will calculate the square root...\n```py\nimport math\n...\n```"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 123,
    "completion_tokens": 45
  }
}
```

The LLM's actual reply is in `choices[0].message.content`.

## Configuration via .env

We use environment variables so secrets stay out of code:

```bash
ARK_API_KEY=your-api-key-here
ARK_API_BASE=https://your-api-base-url/v1
MODEL=your-model-name
```

`load_dotenv()` loads these from `.env` into `os.environ`.

## How to run

```bash
uv run python agent.py
```

You'll see:
1. The full request body that gets sent
2. The full raw response from the API

## Previous step

← [02-message-format](../02-message-format/README.md) - Build the message JSON

## Next step

→ [04-openai-sdk](../04-openai-sdk/README.md) - Use the OpenAI SDK instead of raw HTTP
