# doubao-minimal-agent

A minimalistic implementation of an LLM code agent powered by [Doubao Seed](https://www.volcengine.com/activity/codingplan) (ByteDance's Volcengine Ark platform). Based on [minimal-agent](https://github.com/Antropath/minimal-agent), adapted for the Doubao API.

The core `agent.py` module is ~100 lines long. It uses the OpenAI-compatible API provided by Volcengine Ark, following the [ReAct framework](https://arxiv.org/abs/2210.03629).

## Differences from minimal-agent

| Aspect | minimal-agent | doubao-minimal-agent |
|--------|--------------|----------------------|
| LLM SDK | LiteLLM | OpenAI SDK (direct) |
| Default model | Varies (LiteLLM routing) | `doubao-seed-2.0-pro` |
| API endpoint | LiteLLM auto-routing | `https://ark.cn-beijing.volces.com/api/coding/v3` |
| Auth | Per-provider env vars | `ARK_API_KEY` |
| `tools=None` bug | Crashes | Fixed: defaults to `[]` |
| `while` loop bug | `or` condition (dead variable) | Fixed: `for` loop with `range` |
| `authorized_imports` disconnect | Not propagated to executor | Propagated to `additional_authorized_imports` |
| `DuckDuckGoSearchTool` no results | Raises exception | Returns error string |
| `super().__init__()` calls | Present (no base class) | Removed |

## Usage

### 1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and clone

```bash
git clone <this-repo-url>
cd doubao-minimal-agent
```

### 2. Configure Volcengine Ark

Create a `.env` file:

```bash
ARK_API_KEY=<YOUR-ARK-API-KEY>
ARK_API_BASE=https://ark.cn-beijing.volces.com/api/coding/v3
MODEL=doubao-seed-2.0-pro
```

To get started:
1. Register at [Volcengine Ark](https://console.volcengine.com/ark) and complete identity verification
2. Subscribe to a [Coding Plan](https://www.volcengine.com/activity/codingplan) (Lite: ¥9.9/month for first purchase)
3. Create an API Key in Ark console → API Key Management
4. Enable the `doubao-seed-2.0-pro` model in Model Management

> **Note:** The `/api/coding/v3` endpoint is for Coding Plan subscribers. The standard endpoint is `/api/v3`.

### 3. Run

```bash
uv run run_agent.py
```

### Customizing the Task

Edit `run_agent.py`:

```python
res = agent.run("<Your task here in natural language>")
```

## Agent Architecture

The architecture follows the [ReAct framework](https://arxiv.org/abs/2210.03629). In each step the agent "Reasons" and "Acts":

1. LLM generates Thought + Code
2. System extracts code block via regex
3. Python executor runs the code in a sandbox
4. Observation (output) is fed back
5. Loop repeats until `final_answer()` is called or `max_steps` is reached

## License

Apache 2.0
