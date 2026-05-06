# Chapter 3: System Prompt — How the Agent Knows What to Do

The system prompt is the most important piece of the agent. It tells the LLM what it is, how to behave, what tools it has, and what rules to follow. This chapter dissects the Jinja2 template in [prompts.py](../src/minimal_agent/prompts.py) and shows how it's rendered at initialization time.

**What you'll learn:** The six-part structure of the system prompt, how tools are dynamically injected, what the 10 rules enforce, and how the few-shot examples teach the LLM the ReAct pattern.

**Prerequisites:** Chapter 2 (you understand how the Agent class uses the prompt).

## How to Read This Chapter

**Pass 1 — Build intuition:**
3.1 → 3.2 → 3.3 (skip 🔥 Source Walkthrough) → 3.4 → 3.5

**Pass 2 — Dive into source code:**
- §3.3 🔥 Dynamic tool injection — how the Jinja2 loop renders tools

**Pass 3 — Fill gaps:**
- Prompt structure overview? → §3.1
- Few-shot examples and what they teach? → §3.2
- The 10 rules and why each matters? → §3.4
- How `initialize_system_prompt` works? → §3.5

---

## 3.1 Prompt Structure Overview

The system prompt lives in [prompts.py](../src/minimal_agent/prompts.py) as a single `SYSTEM_PROMPT` string containing Jinja2 template syntax. It has six distinct sections:

```
┌────────────────────────────────────────────────────┐
│  SYSTEM PROMPT (Jinja2 Template)                   │
│                                                    │
│  1. Role definition                                │
│     "You are an expert assistant..."               │
│                                                    │
│  2. ReAct instruction                              │
│     "plan forward in a cycle of                    │
│      Thought → Code → Observation"                 │
│                                                    │
│  3. Few-shot examples (6 examples!)                │
│     Each shows: Task → Thought → Code → Obs        │
│     Demonstrates: web search, computation,         │
│     multi-step reasoning, error recovery           │
│                                                    │
│  4. Tool descriptions {% for tool in tools %}      │
│     Dynamically injected from self.tools           │
│     Format: name, description, inputs, output_type │
│                                                    │
│  5. 10 Rules                                       │
│     Mandatory thought+code format, variable        │
│     naming, import restrictions, persistence, etc. │
│                                                    │
│  6. Motivation                                     │
│     "$1,000,000 reward" (common LLM trick)         │
│                                                    │
└────────────────────────────────────────────────────┘
```

The prompt is rendered once in `Agent.__init__` using the `initialize_system_prompt()` method (covered in §3.5). After rendering, the template variables are replaced with actual tool descriptions and import lists.

---

## 3.2 The Few-Shot Examples

The prompt includes 6 carefully chosen examples that teach the LLM the ReAct pattern by demonstration. Each example shows a complete Thought → Code → Observation (and sometimes multi-step) cycle.

### Example 1: Simple Tool Chain

```
Task: "Generate an image of the oldest person in this document."

Thought: I will proceed step by step and use the following tools:
         `document_qa` to find the oldest person, then `image_generator`.
Code:
```py
answer = document_qa(document=document, question="Who is the oldest person mentioned?")
print(answer)
```<end_code>
Observation: "The oldest person in the document is John Doe..."

Thought: I will now generate an image showcasing the oldest person.
Code:
```py
image = image_generator("A portrait of John Doe...")
final_answer(image)
```<end_code>
```

**What it teaches:** The LLM can chain tool calls across multiple steps. The first step uses one tool, inspects the result via `print()`, and the second step uses a different tool based on what it learned.

### Example 2: Pure Computation

```
Task: "What is the result of the following operation: 5 + 3 + 1294.678?"

Thought: I will use python code to compute the result.
Code:
```py
result = 5 + 3 + 1294.678
final_answer(result)
```<end_code>
```

**What it teaches:** Not every task needs a tool call. Simple math can be done directly in Python. Also, `final_answer()` accepts any type — here it receives a float.

### Example 3: Multi-Step Research with Error Recovery

```
Task: "In a 1979 interview, Stanislaus Ulam discusses... What does he say..."

Thought: I need to find and read the 1979 interview.
Code:
```py
pages = search(query="1979 interview Stanislaus Ulam Martin Sherwin physicists Einstein")
print(pages)
```<end_code>
Observation: No result found for query...

Thought: The query was maybe too restrictive. Let's try again with a broader query.
Code:
```py
pages = search(query="1979 interview Stanislaus Ulam")
print(pages)
```<end_code>
Observation: Found 6 pages: [Stanislaus Ulam 1979 interview](https://...)...

Thought: I will read the first 2 pages to know more.
Code:
```py
for url in ["https://...", "https://..."]:
    whole_page = visit_webpage(url)
    print(whole_page)
    print("\n" + "="*80 + "\n")
```<end_code>
Observation: Stanislaus Ulam was a Polish-American mathematician...

Thought: I now have the final answer.
Code:
```py
final_answer("diminished")
```<end_code>
```

**What it teaches:** This is the most important example. It demonstrates:
1. **Error recovery** — when the first search fails, the LLM broadens the query
2. **Multi-step research** — search → visit webpage → extract answer
3. **`print()` for inspection** — always print intermediate results before using them
4. **Loops in code** — the LLM can write `for` loops to visit multiple pages

### Progressive Learning Through Examples

| Example | Steps | Key Skill Taught |
|---------|-------|-----------------|
| 1 (Image generation) | 2 | Tool chaining across steps |
| 2 (Math) | 1 | Direct computation, `final_answer()` with non-string types |
| 3 (Ulam interview) | 4 | Error recovery, query refinement, multi-step research |
| 4 (City population) | 2 | Using search results directly, comparison |
| 5 (Pope age) | 2 | Cross-referencing sources, computation on found data |
| 6 (Translator + image QA) | 2 | Tool composition, additional arguments |

The examples are ordered from simple to complex, building up the LLM's understanding of the ReAct pattern progressively.

---

## 3.3 Dynamic Tool Injection

### 🔥 Source Walkthrough: The Jinja2 Template Loop

The most interesting part of the prompt is how tools are dynamically listed. The Jinja2 template contains this block:

```jinja2
On top of performing computations in the Python code snippets that you create,
you only have access to these tools:
{%- for tool in tools.values() %}
- {{ tool.name }}: {{ tool.description }}
    Takes inputs: {{tool.inputs}}
    Returns an output of type: {{tool.output_type}}
{%- endfor %}
```

When rendered with the default tools from `run_agent.py`, this produces:

```
On top of performing computations in the Python code snippets that you create,
you only have access to these tools:
- web_search: Performs a duckduckgo web search based on your query...
    Takes inputs: {'query': {'type': 'string', 'description': 'The search query to perform.'}}
    Returns an output of type: string
- visit_webpage: Visits a webpage at the given url and reads its content...
    Takes inputs: {'url': {'type': 'string', 'description': 'The url of the webpage to visit.'}}
    Returns an output of type: string
- final_answer: Provides a final answer to the given problem.
    Takes inputs: {'answer': {'type': 'any', 'description': 'The final answer to the problem'}}
    Returns an output of type: any
```

**Key Insights:**

1. **`tools.values()`** — The template iterates over the dict values, which are the Tool objects. The order matches the insertion order (Python 3.7+ guarantees dict ordering).

2. **Tool metadata comes from class attributes** — Each tool class defines `name`, `description`, `inputs`, and `output_type` as class-level attributes. These are read directly by the template — no serialization or schema generation step.

3. **`final_answer` is always listed last** — Since it's appended after the user-provided tools, it appears at the bottom of the tool list. This is intentional: the LLM should try other tools first and only call `final_answer` when truly done.

4. **Authorized imports also rendered** — Later in the template: `you can use imports in your code, but only from the following list of modules: {{authorized_imports}}`. This tells the LLM what imports are allowed. The actual enforcement happens in the executor (see Chapter 5).

5. **No type safety in template rendering** — The `inputs` dict is rendered using Python's `str()` representation. This means the LLM sees `{'query': {'type': 'string', 'description': '...'}}` as a literal string, which it then learns to parse. There's no JSON schema validation.

---

## 3.4 The 10 Rules

The system prompt includes 10 rules that constrain the LLM's behavior. Here they are with annotations explaining why each exists:

| # | Rule | Why It Matters | What Happens If Violated |
|---|------|---------------|--------------------------|
| 1 | Always provide Thought + Code sequences ending with `<end_code>` | Without this, the regex extractor fails and the agent can't execute anything | Agent receives `None` as `code_action`, executor returns empty logs |
| 2 | Use only variables you have defined | Prevents hallucinated variable references | `NameError` in execution |
| 3 | Use right argument syntax, not dict-style | `tool(query="x")` not `tool({"query": "x"})` | `TypeError` in execution |
| 4 | Don't chain too many tool calls in one block | Unpredictable output formats can derail subsequent calls | Tool B receives garbled input from Tool A |
| 5 | Call tools only when needed, don't re-do same call | Saves tokens and avoids redundant API calls | Wasted steps, possible rate limiting |
| 6 | Don't name variables the same as tools | `final_answer = ...` would shadow the `final_answer` tool function | Can't call `final_answer()` anymore |
| 7 | Never create notional variables | Only use variables that exist in the execution context | `NameError` |
| 8 | Only import from authorized list | Security — prevents `os.system("rm -rf /")` etc. | Executor blocks the import (hard constraint) |
| 9 | State persists between executions | Variables defined in step N are available in step N+1 | Enables incremental progress across steps |
| 10 | Don't give up | Motivational nudge to keep trying different approaches | Agent gives up prematurely |

### Rule 9 in Depth: State Persistence

Rule 9 is particularly interesting — it means the LLM can build up state incrementally across steps. A search result from step 2 is still available in step 5. This is a consequence of using `LocalPythonExecutor` which maintains a persistent namespace.

For example, the LLM might write:

```
# Step 1:
search_result = web_search(query="hottest day 2024")
print(search_result)

# Step 2 (search_result is still accessible!):
visit_result = visit_webpage(url="https://...")
print(visit_result)

# Step 3 (both variables still accessible):
combined = search_result + visit_result
final_answer(combined)
```

This persistence is a feature, but it also means the namespace can get cluttered over many steps. The LLM might accidentally reference a variable from a much earlier step that it has forgotten about.

### Rule 4 in Depth: Why Not Chain Tool Calls

Rule 4 warns against chaining tool calls in the same code block. Consider this anti-pattern:

```python
# BAD: Chaining unpredictable outputs
result = web_search(query="hottest day")
answer = visit_webpage(url=result)  # result is not a URL!
```

The output of `web_search` is a formatted string with titles and URLs — not a single URL. By using `print()` first, the LLM can inspect the output and extract the URL in the next step:

```python
# GOOD: Print first, use in next step
result = web_search(query="hottest day")
print(result)
# Next step: use the URL from the printed output
page = visit_webpage(url="https://actual-url-from-results.com")
```

---

## 3.5 The `initialize_system_prompt` Method

The `Agent.__init__` calls `initialize_system_prompt()` to render the Jinja2 template:

```python
def initialize_system_prompt(self, system_prompt_template: str) -> str:
    compiled_template = Template(system_prompt_template, undefined=StrictUndefined)
    variables = {
        "tools": self.tools,
        "authorized_imports": str(self.authorized_imports),
    }
    return compiled_template.render(**variables)
```

| Aspect | Detail |
|--------|--------|
| `StrictUndefined` | If the template references a variable not in `variables`, Jinja2 raises an `UndefinedError` instead of silently rendering empty string — catches typos early |
| `str(self.authorized_imports)` | The list is converted to its Python string representation (e.g., `"['math', 'datetime']"`) — rendered literally into the prompt |
| Called once at init | The system prompt is rendered once and stored. If you add tools after init, the prompt won't update — you'd need to call `initialize_system_prompt()` again manually |
| `system_prompt_template` parameter | Takes the raw template string, not a file path. The template is defined in `prompts.py` and imported as `SYSTEM_PROMPT` |

### Template Variables

| Variable | Source | Format in Prompt |
|----------|--------|-----------------|
| `tools` | `self.tools` (dict of Tool objects) | Loop renders each tool's name, description, inputs, output_type |
| `authorized_imports` | `self.authorized_imports` (list of strings) | `str()` renders as `"['collections', 'datetime', ...]"` |

There are only two template variables. The prompt is intentionally simple — no model-specific configuration, no task-specific parameters, no dynamic examples. Everything is static except the tool list and import list.

---

## 3.6 Prompt Engineering Insights

The system prompt is a masterclass in minimal but effective prompt engineering for code agents:

### The `stop="<end_code>"` Trick

As covered in Chapter 2, the `stop` parameter in the LLM API call tells the model to stop generating at the `<end_code>` token. The system prompt instructs the LLM to end each code block with this token. Without it, the LLM would continue generating and might hallucinate:

```
# What the LLM might generate without stop="<end_code>":
Thought: I'll search for that.
Code:
```py
result = web_search(query="...")
print(result)
```<end_code>
Observation: [Hallucinated observation that the LLM makes up!]
Thought: [Continues based on the hallucinated observation...]
```

The `stop` parameter prevents this by cutting off generation at `<end_code>`, so the agent system provides the *real* observation.

### The `$1,000,000 Reward

The prompt ends with: *"Now Begin! If you solve the task correctly, you will receive a reward of $1,000,000."*

This is a well-known prompt engineering trick. LLMs tend to perform better when there's a stated incentive. It's not that the LLM "wants" money — it's that the reward framing shifts the model's output distribution toward more thorough, careful responses. Studies have shown this works even with obviously fictional rewards.

### What's Missing

The prompt does **not** include:

| Missing Feature | Why It Matters | How Production Frameworks Handle It |
|-----------------|---------------|-------------------------------------|
| Token budget awareness | LLM doesn't know how many tokens it can use | Some agents include `"you have X tokens remaining"` |
| Task decomposition planning | LLM jumps straight into code | Smolagents has an optional `planning_step` |
| Reflection / self-critique | LLM doesn't check its own work | Some agents add a "Review your answer" step |
| Error recovery instructions | LLM only learns this from Example 3 | Production agents add explicit retry rules |

These are tradeoffs of the minimal approach. Adding them would make the prompt more robust but also longer and harder to understand.
