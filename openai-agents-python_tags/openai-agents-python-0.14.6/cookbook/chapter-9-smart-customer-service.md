# Chapter 9: Smart Customer Service — From Zero to Production

This chapter builds a complete customer service agent from scratch using **Doubao (doubao-seed-2.0-pro)** via Volcengine Ark API as the LLM backend. Every section adds a new feature — each one is runnable on its own. By the end, you'll have a production-ready system with tools, context, sessions, guardrails, error handling, and observability.

## How to Read This Chapter

**Pass 1 — Get it running (~30 min):** Read 9.1 → 9.2 → 9.3. Set up the environment, run the first agent, add tools. Copy-paste the code and verify it works end-to-end.

**Pass 2 — Add enterprise features (~45 min):** Read 9.4 → 9.5 → 9.6 → 9.7. Add context, structured output, sessions, and guardrails. These are the features that separate a demo from a real product.

**Pass 3 — Production hardening (~30 min):** Read 9.8 → 9.9 → 9.10. Error handling, observability, and the complete integrated system.

**Key marker:** Sections marked with 🔥 are the highlights — prioritize them.

> **Prerequisites:** This chapter assumes you've read at least Chapter 1 (Quick Start) for the conceptual overview. Source code internals from Chapters 2-8 are cross-referenced but not required.

---

## 9.1 Environment Setup

### 9.1.1 Install uv

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:

```bash
uv --version
```

### 9.1.2 Create the Project

```bash
uv init smart-support
cd smart-support
uv add openai-agents python-dotenv
```

This creates:

```
smart-support/
├── .python-version
├── pyproject.toml
├── uv.lock
└── hello.py
```

### 9.1.3 Configure API Key

Create `.env` in the project root:

```bash
ARK_API_KEY=your-volcengine-ark-api-key
```

### 9.1.4 Project Structure (Final)

```
smart-support/
├── pyproject.toml
├── uv.lock
├── .env
├── .python-version
├── main.py              # Entry point
├── config.py            # Doubao model configuration
├── context.py           # SupportContext definition
├── tools.py             # @function_tool definitions
├── guardrails.py        # Input/output guardrails
└── hooks.py             # Usage logging & cost monitoring
```

### 9.1.5 Three Ways to Connect Doubao

The Agents SDK supports three integration patterns for OpenAI-compatible providers like Doubao:

```
┌────────────────────────────────────────────────────────────────────┐
│              Three Ways to Connect Doubao                          │
├────────────────┬─────────────────┬────────────────────────────────-┤
│  Method 1      │  Method 2       │  Method 3                      │
│  Global Default│  Per-Agent Model│  Per-Run Provider               │
│                │                 │                                 │
│  set_default_  │  OpenAIChat-    │  OpenAIProvider +               │
│  openai_client │  Completions-   │  RunConfig(                    │
│                │  Model          │    model_provider=provider)     │
├────────────────┼─────────────────┼────────────────────────────────-┤
│  4 lines       │  6 lines        │  8 lines                       │
│  Global scope  │  Per-Agent      │  Per-Run                       │
│  Simplest      │  Most flexible  │  Good for env switching        │
├────────────────┼─────────────────┼────────────────────────────────-┤
│  Only Doubao   │  Mix Doubao +   │  Same agent, different         │
│  for all agents│  other models   │  envs (dev/prod)               │
└────────────────┴─────────────────┴────────────────────────────────┘
```

**Method 1: Global Default** (we'll use this throughout the chapter)

```python
from openai import AsyncOpenAI
from agents import set_default_openai_client, set_default_openai_api, set_tracing_disabled

client = AsyncOpenAI(
    api_key="your-ark-api-key",
    base_url="https://ark.cn-beijing.volces.com/api/coding/v3",
)
set_default_openai_client(client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(True)
```

Key points:
- `use_for_tracing=False` — because the Ark API key is not for OpenAI tracing.
- `set_default_openai_api("chat_completions")` — Doubao uses Chat Completions, not Responses API.
- `set_tracing_disabled(True)` — tracing uploads to OpenAI by default; disable it since we're not using OpenAI endpoints.

**Method 2: Per-Agent Model**

```python
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, set_tracing_disabled

set_tracing_disabled(True)

client = AsyncOpenAI(
    api_key="your-ark-api-key",
    base_url="https://ark.cn-beijing.volces.com/api/coding/v3",
)

doubao_model = OpenAIChatCompletionsModel(
    model="doubao-seed-2.0-pro",
    openai_client=client,
)

agent = Agent(name="Support", model=doubao_model)
```

Use this when different agents need different models (e.g., a cheap model for triage, a powerful one for complex tasks).

**Method 3: Per-Run Provider**

```python
from agents import Agent, OpenAIProvider, RunConfig, Runner, set_tracing_disabled

set_tracing_disabled(True)

provider = OpenAIProvider(
    api_key="your-ark-api-key",
    base_url="https://ark.cn-beijing.volces.com/api/coding/v3",
    use_responses=False,
)

result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(model_provider=provider),
)
```

Use this when you want the same agent code to work with different backends in different environments.

### 9.1.6 config.py — Our Shared Configuration

We'll put the Doubao setup in `config.py` so every example can import it:

```python
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import set_default_openai_client, set_default_openai_api, set_tracing_disabled

load_dotenv()

ARK_API_KEY = os.getenv("ARK_API_KEY")
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3"
MODEL_NAME = "doubao-seed-2.0-pro"


def setup_doubao():
    client = AsyncOpenAI(
        api_key=ARK_API_KEY,
        base_url=ARK_BASE_URL,
    )
    set_default_openai_client(client, use_for_tracing=False)
    set_default_openai_api("chat_completions")
    set_tracing_disabled(True)
```

> **Why `use_for_tracing=False`?** The SDK's default tracer uploads spans to OpenAI's backend using the same API key. Since our key is for Volcengine Ark, tracing would fail. Setting `use_for_tracing=False` tells the SDK not to use this key for tracing. Combined with `set_tracing_disabled(True)`, all tracing is safely disabled.

---

## 9.2 First Agent

Let's verify the Doubao connection works with the smallest possible agent.

### 9.2.1 Minimal Agent

```python
import asyncio
from agents import Agent, Runner
from config import setup_doubao

setup_doubao()

agent = Agent(
    name="Support Agent",
    instructions="You are a helpful customer support agent. Respond concisely.",
)

async def main():
    result = await Runner.run(agent, "Hello, I need help with my order.")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
uv run main.py
```

If you see a response from Doubao, congratulations — the connection works! If not, check:
1. `.env` has the correct `ARK_API_KEY`
2. The API key has access to `doubao-seed-2.0-pro`
3. Network can reach `ark.cn-beijing.volces.com`

### 9.2.2 What Happens Behind the Scenes

```
  Runner.run(agent, "Hello, I need help...")
         │
         ▼
  ┌─ Setup ──────────────────────────────────────────┐
  │  1. Resolve model name → OpenAIChatCompletions-  │
  │     Model (because set_default_openai_api)        │
  │  2. Use our AsyncOpenAI client (base_url=Ark)     │
  │  3. Tracing disabled → NoOpTrace                  │
  └───────────────────────────────────────────────────┘
         │
         ▼
  ┌─ The Loop ────────────────────────────────────────┐
  │  1. Send chat.completions.create(                 │
  │       model="doubao-seed-2.0-pro",                │
  │       messages=[...],                             │
  │     ) to Ark API                                  │
  │  2. Get response → final output (no tools yet)    │
  └───────────────────────────────────────────────────┘
         │
         ▼
  Return RunResult(final_output="...")
```

Because our agent has no tools and no `output_type`, the LLM returns a text response immediately — no looping.

> **Doubao vs OpenAI:** At this level, the experience is identical. The SDK's `OpenAIChatCompletionsModel` translates its internal representation into a standard Chat Completions request, which the Ark API accepts because it's OpenAI-compatible.

---

## 9.3 Adding Tools

A support agent without tools is just a chatbot. Let's give it the ability to look up orders and check refund eligibility.

### 9.3.1 Define Tools

Create `tools.py`:

```python
from agents import function_tool, RunContextWrapper


@function_tool
async def lookup_order(ctx: RunContextWrapper, order_id: str) -> str:
    """Look up an order by its ID. Returns order status and details."""
    orders = {
        "ORD-001": {"status": "shipped", "items": ["Widget A", "Widget B"], "total": 59.99},
        "ORD-002": {"status": "processing", "items": ["Gadget C"], "total": 29.99},
        "ORD-003": {"status": "delivered", "items": ["Widget A"], "total": 19.99},
    }
    order = orders.get(order_id)
    if order:
        return f"Order {order_id}: status={order['status']}, items={order['items']}, total=${order['total']}"
    return f"Order {order_id} not found."


@function_tool
async def check_refund(ctx: RunContextWrapper, order_id: str) -> str:
    """Check if an order is eligible for a refund."""
    refund_eligible = {"ORD-001", "ORD-003"}
    if order_id in refund_eligible:
        return f"Order {order_id} is eligible for a refund. Please confirm to proceed."
    return f"Order {order_id} is not eligible for a refund (still processing)."
```

Key points:
- `ctx: RunContextWrapper` is optional — include it only if you need context access (we'll use it in §9.4).
- The docstring becomes the tool description sent to the LLM.
- Return a `str` — the SDK sends this string back to the LLM as the tool result.

### 9.3.2 Attach Tools to Agent

```python
import asyncio
from agents import Agent, Runner
from config import setup_doubao
from tools import lookup_order, check_refund

setup_doubao()

agent = Agent(
    name="Support Agent",
    instructions="You are a helpful customer support agent. Use tools to look up orders and check refund eligibility. Be concise.",
    tools=[lookup_order, check_refund],
)

async def main():
    result = await Runner.run(agent, "What's the status of order ORD-001?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### 9.3.3 The Tool Call Flow

```
  User: "What's the status of order ORD-001?"
         │
         ▼
  ┌─ Turn 1 ───────────────────────────────────────┐
  │  LLM decides to call lookup_order(order_id=    │
  │  "ORD-001")                                     │
  └──────┬──────────────────────────────────────────┘
         │
         ▼
  ┌─ Tool Execution ────────────────────────────────┐
  │  SDK runs lookup_order("ORD-001")               │
  │  → "Order ORD-001: status=shipped, items=..."   │
  └──────┬──────────────────────────────────────────┘
         │
         ▼
  ┌─ Turn 2 ───────────────────────────────────────┐
  │  LLM receives tool result, generates:           │
  │  "Your order ORD-001 has been shipped..."       │
  │  → final output ✅                              │
  └─────────────────────────────────────────────────┘
```

> **Doubao compatibility:** Tool calling via Chat Completions format is fully supported. The SDK converts `FunctionTool` definitions to OpenAI's `tools` parameter format, which the Ark API accepts.

---

## 9.4 Context & Identity

Hardcoded order data isn't realistic. In production, tools need to know **who** is asking — a customer service agent should see the user's identity, preferences, and recent orders.

### 9.4.1 Define a Context Class

Create `context.py`:

```python
from dataclasses import dataclass, field


@dataclass
class SupportContext:
    user_id: str
    user_name: str
    membership_tier: str = "basic"
    recent_orders: list[str] = field(default_factory=list)
```

### 9.4.2 Use Context in Tools

Update `tools.py`:

```python
from agents import function_tool, RunContextWrapper
from context import SupportContext


@function_tool
async def lookup_order(ctx: RunContextWrapper[SupportContext], order_id: str) -> str:
    """Look up an order by its ID. Returns order status and details."""
    context = ctx.context

    if order_id not in context.recent_orders:
        return f"Order {order_id} not associated with user {context.user_name}. Please verify the order ID."

    orders = {
        "ORD-001": {"status": "shipped", "items": ["Widget A", "Widget B"], "total": 59.99},
        "ORD-002": {"status": "processing", "items": ["Gadget C"], "total": 29.99},
        "ORD-003": {"status": "delivered", "items": ["Widget A"], "total": 19.99},
    }
    order = orders.get(order_id)
    if order:
        return f"Order {order_id}: status={order['status']}, items={order['items']}, total=${order['total']}"
    return f"Order {order_id} not found."


@function_tool
async def check_refund(ctx: RunContextWrapper[SupportContext], order_id: str) -> str:
    """Check if an order is eligible for a refund."""
    context = ctx.context

    if order_id not in context.recent_orders:
        return f"Order {order_id} not associated with user {context.user_name}."

    refund_eligible = {"ORD-001", "ORD-003"}
    if order_id in refund_eligible:
        tier_msg = f" ({context.membership_tier} member: priority processing)" if context.membership_tier == "premium" else ""
        return f"Order {order_id} is eligible for a refund{tier_msg}. Please confirm to proceed."
    return f"Order {order_id} is not eligible for a refund (still processing)."
```

### 9.4.3 Pass Context to Runner

```python
import asyncio
from agents import Agent, Runner
from config import setup_doubao
from context import SupportContext
from tools import lookup_order, check_refund

setup_doubao()

agent = Agent[SupportContext](
    name="Support Agent",
    instructions="You are a helpful customer support agent. Use tools to look up orders and check refund eligibility. Be concise.",
    tools=[lookup_order, check_refund],
)

ctx = SupportContext(
    user_id="U-12345",
    user_name="Alice",
    membership_tier="premium",
    recent_orders=["ORD-001", "ORD-003"],
)

async def main():
    result = await Runner.run(agent, "Can I get a refund for ORD-001?", context=ctx)
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

Key points:
- `Agent[SupportContext]` — the generic parameter tells the type checker what context type to expect.
- `context=ctx` on `Runner.run` — the SDK wraps it in a `RunContextWrapper` and passes it to every tool.
- Inside tools, `ctx.context` gives you the raw `SupportContext` with user identity.

> **How it works internally:** The SDK creates a `RunContextWrapper(context=ctx)` and passes it to every tool function, guardrail, and hook. The context is never sent to the LLM — it stays on your machine. See Ch5 §5.3 for the full source code walkthrough.

---

## 9.5 Structured Output

Sometimes you want the agent's response in a structured format, not free-form text. For example, a refund result should have clear fields: `order_id`, `refund_amount`, `status`.

### 9.5.1 🔥 The Doubao Constraint

OpenAI's Responses API supports **Structured Outputs** — the LLM is guaranteed to return valid JSON matching your schema. However, Doubao's Chat Completions endpoint does **not** support the `response_format={"type": "json_schema", ...}` strict mode.

Our workaround:

```
┌────────────────────────────────────────────────────────────┐
│  OpenAI Responses API          │  Doubao Chat Completions  │
│  ✅ strict json_schema         │  ❌ not supported          │
│  ✅ guaranteed valid JSON      │  ⚠️ best-effort JSON      │
│                                │                            │
│  → output_type=MyDataclass    │  → output_type still works │
│    just works                  │    but may need retries    │
│                                │    if LLM returns invalid  │
│                                │    JSON                    │
└────────────────────────────────────────────────────────────┘
```

The good news: the SDK's `output_type` parameter works with Chat Completions models too. It sends `response_format={"type": "json_object"}` and parses the response. If the LLM returns invalid JSON, the SDK retries automatically.

### 9.5.2 Define Output Type

```python
from dataclasses import dataclass


@dataclass
class RefundResult:
    order_id: str
    refund_amount: float
    status: str
    message: str
```

### 9.5.3 Use output_type

```python
import asyncio
from agents import Agent, Runner, ModelSettings
from config import setup_doubao
from context import SupportContext
from tools import lookup_order, check_refund

setup_doubao()

agent = Agent[SupportContext](
    name="Refund Agent",
    instructions="""You are a refund processing agent. When a user requests a refund:
1. Use check_refund to verify eligibility
2. If eligible, respond with a structured RefundResult
Always respond in the RefundResult format.""",
    tools=[lookup_order, check_refund],
    output_type=RefundResult,
    model_settings=ModelSettings(temperature=0.1),
)

ctx = SupportContext(
    user_id="U-12345",
    user_name="Alice",
    membership_tier="premium",
    recent_orders=["ORD-001", "ORD-003"],
)

async def main():
    result = await Runner.run(agent, "I want a refund for ORD-001", context=ctx)
    refund: RefundResult = result.final_output
    print(f"Order: {refund.order_id}")
    print(f"Amount: ${refund.refund_amount}")
    print(f"Status: {refund.status}")
    print(f"Message: {refund.message}")

if __name__ == "__main__":
    asyncio.run(main())
```

> **Tip for Doubao:** Lower `temperature` (0.1-0.3) helps the LLM produce more consistent JSON. If you still get parsing errors, add a retry instruction to the system prompt: "You MUST respond with valid JSON matching the schema."

---

## 9.6 Multi-Turn Session

A real support conversation isn't one-shot — customers ask follow-up questions. `SQLiteSession` persists conversation history across turns.

### 9.6.1 Session Basics

```python
from agents import SQLiteSession

session = SQLiteSession("user-alice-123")

result1 = await Runner.run(agent, "What's the status of ORD-001?", context=ctx, session=session)
print(result1.final_output)

result2 = await Runner.run(agent, "Can I refund that one?", context=ctx, session=session)
print(result2.final_output)
```

The second call ("Can I refund that one?") works because the session remembers that "that one" refers to ORD-001 from the previous turn.

### 9.6.2 🔥 How SQLiteSession Works

```
  Turn 1: "What's the status of ORD-001?"
         │
         ▼
  ┌─ Runner.run ────────────────────────────────────┐
  │  1. session.get_items() → [] (first turn)       │
  │  2. Send input + LLM response to LLM            │
  │  3. session.store_items([...]) → save to SQLite  │
  └──────────────────────────────────────────────────┘
         │
         ▼
  Turn 2: "Can I refund that one?"
         │
         ▼
  ┌─ Runner.run ────────────────────────────────────┐
  │  1. session.get_items() → [Turn 1 history]      │
  │  2. Append new input to history                  │
  │  3. LLM sees full conversation → understands     │
  │     "that one" = ORD-001                         │
  │  4. session.store_items([...]) → update SQLite   │
  └──────────────────────────────────────────────────┘
```

### 9.6.3 Persistent vs In-Memory

```python
# In-memory (lost when process exits)
session = SQLiteSession("user-123")

# Persistent (survives restarts)
session = SQLiteSession("user-123", db_path="support_sessions.db")
```

### 9.6.4 Interactive Chat Loop

```python
import asyncio
from agents import Agent, Runner, SQLiteSession
from config import setup_doubao
from context import SupportContext
from tools import lookup_order, check_refund

setup_doubao()

agent = Agent[SupportContext](
    name="Support Agent",
    instructions="You are a helpful customer support agent. Use tools to look up orders and check refund eligibility. Be concise and friendly.",
    tools=[lookup_order, check_refund],
)

ctx = SupportContext(
    user_id="U-12345",
    user_name="Alice",
    membership_tier="premium",
    recent_orders=["ORD-001", "ORD-003"],
)

session = SQLiteSession("user-alice-123", db_path="support_sessions.db")

async def main():
    print("Customer Support Agent (type 'quit' to exit)")
    print("-" * 40)
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "quit":
            break
        result = await Runner.run(agent, user_input, context=ctx, session=session)
        print(f"Agent: {result.final_output}\n")

if __name__ == "__main__":
    asyncio.run(main())
```

Run with `uv run main.py` and have a multi-turn conversation:

```
You: What's the status of ORD-001?
Agent: Your order ORD-001 has been shipped. It contains Widget A and Widget B, totaling $59.99.

You: Can I get a refund for it?
Agent: Order ORD-001 is eligible for a refund (premium member: priority processing)...

You: What about ORD-002?
Agent: Order ORD-002 is still processing, so it's not eligible for a refund yet.

You: quit
```

---

## 9.7 Safety Guardrails

Guardrails protect your system from abuse. Two common needs for customer service:

1. **Input guardrail:** Block profanity and malicious prompts
2. **Output guardrail:** Prevent the agent from revealing internal system information

### 9.7.1 Input Guardrail — Block Profanity

Create `guardrails.py`:

```python
from agents import GuardrailFunctionOutput, input_guardrail, output_guardrail, RunContextWrapper, Agent


PROFANITY_WORDS = {"badword1", "badword2", "badword3"}


@input_guardrail
async def block_profanity(
    ctx: RunContextWrapper,
    agent: Agent,
    input: str | list,
) -> GuardrailFunctionOutput:
    if isinstance(input, str):
        text = input.lower()
    else:
        text = " ".join(
            item.get("content", "") for item in input
            if isinstance(item, dict) and item.get("role") == "user"
        ).lower()

    found = [w for w in PROFANITY_WORDS if w in text]
    if found:
        return GuardrailFunctionOutput(
            tripwire_triggered=True,
            output_info={"reason": f"Profanity detected: {found}"},
        )
    return GuardrailFunctionOutput(
        tripwire_triggered=False,
        output_info={"checked": True},
    )
```

### 9.7.2 Output Guardrail — Prevent Information Leakage

```python
INTERNAL_KEYWORDS = ["database", "sql", "internal_api", "server_error", "stack_trace", "admin"]


@output_guardrail
async def prevent_info_leak(
    ctx: RunContextWrapper,
    agent: Agent,
    agent_output: str,
) -> GuardrailFunctionOutput:
    output_lower = str(agent_output).lower()
    found = [kw for kw in INTERNAL_KEYWORDS if kw in output_lower]
    if found:
        return GuardrailFunctionOutput(
            tripwire_triggered=True,
            output_info={"reason": f"Internal information leaked: {found}"},
        )
    return GuardrailFunctionOutput(
        tripwire_triggered=False,
        output_info={"checked": True},
    )
```

### 9.7.3 Attach Guardrails to Agent

```python
from guardrails import block_profanity, prevent_info_leak

agent = Agent[SupportContext](
    name="Support Agent",
    instructions="You are a helpful customer support agent...",
    tools=[lookup_order, check_refund],
    input_guardrails=[block_profanity],
    output_guardrails=[prevent_info_leak],
)
```

### 9.7.4 Guardrail Execution Flow

```
  Runner.run(agent, user_input)
         │
         ▼
  ┌─ Input Guardrails ──────────────────────────────┐
  │  block_profanity(input)                          │
  │  ├─ Clean? → Continue                           │
  │  └─ Profanity? → tripwire_triggered=True        │
  │     → Raise InputGuardrailTripwireTriggered      │
  │     → Agent never runs                           │
  └──────────────────────────────────────────────────┘
         │ (clean input)
         ▼
  ┌─ Agent Runs (LLM + Tools) ──────────────────────┐
  │  ... normal processing ...                       │
  └──────────────────────────────────────────────────┘
         │
         ▼
  ┌─ Output Guardrails ─────────────────────────────┐
  │  prevent_info_leak(output)                       │
  │  ├─ Safe? → Return result to user               │
  │  └─ Leaked? → tripwire_triggered=True           │
  │     → Raise OutputGuardrailTripwireTriggered     │
  └──────────────────────────────────────────────────┘
```

> **Handling guardrail exceptions:** When a guardrail triggers, it raises an exception. You should catch it in your main loop:

```python
from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered

try:
    result = await Runner.run(agent, user_input, context=ctx, session=session)
    print(f"Agent: {result.final_output}")
except InputGuardrailTripwireTriggered as e:
    print("Agent: I'm sorry, I can't process that request. Please rephrase.")
except OutputGuardrailTripwireTriggered as e:
    print("Agent: I apologize, I can't provide that information. Let me connect you with a human agent.")
```

---

## 9.8 Error Handling

Production systems must handle failures gracefully. Three common failure modes:

```
┌──────────────────────────────────────────────────────────┐
│              Error Handling: Three Layers                 │
├──────────────────┬───────────────────────────────────────┤
│  Layer 1         │  Tool-level error                     │
│                  │  Tool throws → failure_error_function │
│                  │  → Error msg sent back to LLM         │
│                  │  → LLM retries or apologizes          │
├──────────────────┼───────────────────────────────────────┤
│  Layer 2         │  Run-level error                      │
│                  │  MaxTurnsExceeded → RunErrorHandlers  │
│                  │  → Custom recovery logic              │
├──────────────────┼───────────────────────────────────────┤
│  Layer 3         │  Model-level retry                    │
│                  │  API rate limit (429) → RetryPolicy   │
│                  │  → Auto-retry with backoff            │
└──────────────────┴───────────────────────────────────────┘
```

### 9.8.1 Tool Error Handling — failure_error_function

When a tool throws an exception, the default behavior sends a generic error message to the LLM so it can retry. You can customize this:

```python
from agents import function_tool, RunContextWrapper


@function_tool(
    failure_error_function=lambda ctx, error: f"Order lookup temporarily unavailable. Error: {error}. Please try again or ask the user for their order ID."
)
async def lookup_order(ctx: RunContextWrapper, order_id: str) -> str:
    """Look up an order by its ID."""
    if not order_id.startswith("ORD-"):
        raise ValueError(f"Invalid order ID format: {order_id}. Expected format: ORD-XXX")
    orders = {
        "ORD-001": {"status": "shipped", "items": ["Widget A"], "total": 59.99},
    }
    order = orders.get(order_id)
    if order:
        return f"Order {order_id}: status={order['status']}, total=${order['total']}"
    raise ValueError(f"Order {order_id} not found in system")
```

Now if `lookup_order` raises, the LLM receives a helpful error message instead of crashing the run.

### 9.8.2 Run-Level Error Handling — RunErrorHandlers

`MaxTurnsExceeded` happens when the agent loops too many times without producing a final output. By default, it raises an exception. `RunErrorHandlers` lets you recover gracefully:

```python
from agents import RunErrorHandlers, RunErrorHandlerInput, RunErrorHandlerResult, RunConfig

async def handle_max_turns(
    input: RunErrorHandlerInput,
) -> RunErrorHandlerResult:
    return RunErrorHandlerResult(
        final_output="I'm sorry, I wasn't able to resolve your request. A human agent will follow up shortly.",
    )

error_handlers = RunErrorHandlers(max_turns=handle_max_turns)

result = await Runner.run(
    agent,
    user_input,
    context=ctx,
    session=session,
    error_handlers=error_handlers,
)
```

### 9.8.3 Model-Level Retry — RetryPolicy for Doubao Rate Limits

When Doubao returns HTTP 429 (rate limit), we want automatic retry with backoff:

```python
from agents import Agent, ModelSettings, ModelRetrySettings, RunConfig, retry_policies

agent = Agent[SupportContext](
    name="Support Agent",
    instructions="...",
    tools=[lookup_order, check_refund],
    model_settings=ModelSettings(
        retry=ModelRetrySettings(
            max_retries=3,
            backoff={
                "initial_delay": 1.0,
                "max_delay": 10.0,
                "multiplier": 2.0,
                "jitter": True,
            },
            policy=retry_policies.any(
                retry_policies.provider_suggested(),
                retry_policies.retry_after(),
                retry_policies.network_error(),
                retry_policies.http_status([429, 500, 502, 503]),
            ),
        )
    ),
)
```

The retry flow:

```
  LLM Request → 429 Too Many Requests
         │
         ▼
  ┌─ RetryPolicy ───────────────────────────────────┐
  │  provider_suggested() → checks response body     │
  │  retry_after() → checks Retry-After header       │
  │  http_status([429, ...]) → matches status code   │
  │  any(...) → any sub-policy says retry            │
  └──────────────────────────────────────────────────┘
         │
         ▼
  Backoff: 1s → 2s → 4s (with jitter)
         │
         ▼
  Retry request → 200 OK → continue
```

> **Why `retry_policies.any()`?** It composes multiple policies — if ANY of them says "retry", we retry. This handles the case where Doubao returns 429 with a `Retry-After` header (caught by `retry_after()`) or without one (caught by `http_status([429])`). See Ch8 §8.6 for the full RetryPolicy source code walkthrough.

---

## 9.9 Observability

You need to know how much your agent costs and whether it's performing well. The SDK's `RunHooksBase` gives you event-level callbacks for every LLM call, tool execution, and agent lifecycle event.

### 9.9.1 Usage Logging Hook

Create `hooks.py`:

```python
import time
from agents import RunHooksBase, RunContextWrapper, AgentHookContext, Agent, Tool
from context import SupportContext


class SupportHooks(RunHooksBase[SupportContext, Agent]):
    def __init__(self):
        self._turn_start: float = 0

    async def on_agent_start(
        self, ctx: AgentHookContext[SupportContext], agent: Agent[SupportContext]
    ) -> None:
        self._turn_start = time.time()
        print(f"[Hook] Agent '{agent.name}' started for user '{ctx.context.user_name}'")

    async def on_tool_start(
        self, ctx: RunContextWrapper[SupportContext], agent: Agent[SupportContext], tool: Tool
    ) -> None:
        print(f"[Hook] Calling tool '{tool.name}' for user '{ctx.context.user_name}'")

    async def on_tool_end(
        self, ctx: RunContextWrapper[SupportContext], agent: Agent[SupportContext], tool: Tool, result: str
    ) -> None:
        print(f"[Hook] Tool '{tool.name}' returned: {result[:80]}...")

    async def on_agent_end(
        self, ctx: AgentHookContext[SupportContext], agent: Agent[SupportContext], output
    ) -> None:
        elapsed = time.time() - self._turn_start
        usage = ctx.usage
        print(f"[Hook] Agent finished in {elapsed:.2f}s | "
              f"Tokens: {usage.input_tokens}in/{usage.output_tokens}out | "
              f"Total: {usage.total_tokens}")
```

### 9.9.2 Cost Estimation for Doubao

Doubao pricing (approximate, check Volcengine for current rates):

```python
DOUBAO_PRICE_PER_MILLION_INPUT = 4.0    # ¥/M tokens
DOUBAO_PRICE_PER_MILLION_OUTPUT = 16.0  # ¥/M tokens


def estimate_cost(usage) -> float:
    input_cost = (usage.input_tokens / 1_000_000) * DOUBAO_PRICE_PER_MILLION_INPUT
    output_cost = (usage.output_tokens / 1_000_000) * DOUBAO_PRICE_PER_MILLION_OUTPUT
    return input_cost + output_cost
```

### 9.9.3 Attach Hooks to Runner

```python
from hooks import SupportHooks

hooks = SupportHooks()

result = await Runner.run(
    agent,
    user_input,
    context=ctx,
    session=session,
    hooks=hooks,
)
```

Example output:

```
[Hook] Agent 'Support Agent' started for user 'Alice'
[Hook] Calling tool 'lookup_order' for user 'Alice'
[Hook] Tool 'lookup_order' returned: Order ORD-001: status=shipped, items=['Widget A', 'Widget B'], total=$59...
[Hook] Agent finished in 1.84s | Tokens: 156in/89out | Total: 245
```

---

## 9.10 Complete System

Let's integrate everything into a complete, runnable customer service system.

### 9.10.1 Full main.py

```python
import asyncio
from agents import (
    Agent, Runner, SQLiteSession, RunConfig,
    RunErrorHandlers, RunErrorHandlerInput, RunErrorHandlerResult,
    InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered,
    ModelSettings, ModelRetrySettings, retry_policies,
)
from config import setup_doubao
from context import SupportContext
from tools import lookup_order, check_refund
from guardrails import block_profanity, prevent_info_leak
from hooks import SupportHooks, estimate_cost


async def handle_max_turns(
    input: RunErrorHandlerInput,
) -> RunErrorHandlerResult:
    return RunErrorHandlerResult(
        final_output="I'm sorry, I wasn't able to resolve your request. A human agent will follow up shortly.",
    )


def create_agent() -> Agent[SupportContext]:
    return Agent[SupportContext](
        name="Support Agent",
        instructions="""You are a helpful customer support agent for our online store.

Rules:
- Always verify the order belongs to the user before providing details
- Use lookup_order to check order status
- Use check_refund to check refund eligibility
- Be concise but friendly
- If you're unsure, suggest connecting with a human agent""",
        tools=[lookup_order, check_refund],
        input_guardrails=[block_profanity],
        output_guardrails=[prevent_info_leak],
        model_settings=ModelSettings(
            temperature=0.2,
            retry=ModelRetrySettings(
                max_retries=3,
                backoff={
                    "initial_delay": 1.0,
                    "max_delay": 10.0,
                    "multiplier": 2.0,
                    "jitter": True,
                },
                policy=retry_policies.any(
                    retry_policies.provider_suggested(),
                    retry_policies.retry_after(),
                    retry_policies.network_error(),
                    retry_policies.http_status([429, 500, 502, 503]),
                ),
            ),
        ),
    )


async def main():
    setup_doubao()

    agent = create_agent()
    hooks = SupportHooks()
    error_handlers = RunErrorHandlers(max_turns=handle_max_turns)

    ctx = SupportContext(
        user_id="U-12345",
        user_name="Alice",
        membership_tier="premium",
        recent_orders=["ORD-001", "ORD-003"],
    )

    session = SQLiteSession("user-alice-123", db_path="support_sessions.db")

    print("=" * 50)
    print("  Smart Customer Support (Doubao-powered)")
    print("  Type 'quit' to exit, 'cost' for usage stats")
    print("=" * 50)

    total_cost = 0.0

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            print(f"\nTotal session cost: ¥{total_cost:.4f}")
            break
        if user_input.lower() == "cost":
            print(f"Current session cost: ¥{total_cost:.4f}")
            continue

        try:
            result = await Runner.run(
                agent,
                user_input,
                context=ctx,
                session=session,
                hooks=hooks,
                error_handlers=error_handlers,
            )
            cost = estimate_cost(result.usage)
            total_cost += cost
            print(f"\nAgent: {result.final_output}")
            print(f"(¥{cost:.4f} | {result.usage.total_tokens} tokens)")
        except InputGuardrailTripwireTriggered:
            print("\nAgent: I'm sorry, I can't process that request. Please rephrase politely.")
        except OutputGuardrailTripwireTriggered:
            print("\nAgent: I apologize for the confusion. Let me connect you with a human agent.")
        except Exception as e:
            print(f"\n[Error] {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 9.10.2 Four Scenario Walkthroughs

**Scenario 1: Order Inquiry**

```
You: What's the status of ORD-001?
[Hook] Agent 'Support Agent' started for user 'Alice'
[Hook] Calling tool 'lookup_order' for user 'Alice'
[Hook] Tool 'lookup_order' returned: Order ORD-001: status=shipped...
[Hook] Agent finished in 1.84s | Tokens: 156in/89out | Total: 245

Agent: Your order ORD-001 has been shipped! It contains Widget A and Widget B, totaling $59.99.
(¥0.0019 | 245 tokens)
```

**Scenario 2: Refund Request**

```
You: I want a refund for ORD-001
[Hook] Agent 'Support Agent' started for user 'Alice'
[Hook] Calling tool 'check_refund' for user 'Alice'
[Hook] Tool 'check_refund' returned: Order ORD-001 is eligible for a refund (premium member...

Agent: Great news! Order ORD-001 is eligible for a refund. As a premium member, you'll receive priority processing.
(¥0.0016 | 198 tokens)
```

**Scenario 3: Guardrail Triggered**

```
You: <profanity>
Agent: I'm sorry, I can't process that request. Please rephrase politely.
```

**Scenario 4: Unauthorized Order Access**

```
You: What's the status of ORD-999?
[Hook] Agent 'Support Agent' started for user 'Alice'
[Hook] Calling tool 'lookup_order' for user 'Alice'
[Hook] Tool 'lookup_order' returned: Order ORD-999 not associated with user Alice...

Agent: I couldn't find order ORD-999 associated with your account. Please double-check the order ID.
(¥0.0014 | 178 tokens)
```

---

## 9.11 Key Takeaways

1. **Three integration patterns** — `set_default_openai_client` (global), `OpenAIChatCompletionsModel` (per-agent), `OpenAIProvider` (per-run). Start with Method 1, move to Method 2 when you need mixed models.

2. **Always set `set_default_openai_api("chat_completions")`** when using Doubao — it tells the SDK to use Chat Completions format instead of the Responses API.

3. **Always disable tracing** with `set_tracing_disabled(True)` for non-OpenAI providers — the default tracer uploads to OpenAI's backend.

4. **Context is your security boundary** — use `SupportContext` to carry user identity, and check it in tools to enforce data access rules. Never trust the LLM input alone.

5. **Structured output with Doubao** — `output_type` works but isn't guaranteed like OpenAI's strict mode. Lower `temperature` and explicit prompt instructions help.

6. **SQLiteSession for multi-turn** — just pass `session=session` to `Runner.run`. The SDK handles history management. Use `db_path` for persistence across restarts.

7. **Guardrails catch what prompts can't** — use `@input_guardrail` for input validation and `@output_guardrail` for output safety. Catch their exceptions in your main loop.

8. **Three error layers** — `failure_error_function` (tool-level), `RunErrorHandlers` (run-level), `RetryPolicy` (model-level). Each handles a different failure mode.

> **Next:** Chapter 10 builds on these foundations with a meeting notes agent — adding role-based access control, multi-turn refinement, human-in-the-loop review, and structured output extraction.
