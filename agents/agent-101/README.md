# Agent 101 - Learn to Build AI Agents from Scratch

From the very bottom (HTTP requests) to a working ReAct agent, step by step.

---

## Learning Path

| Step | Name | What you learn |
|------|------|----------------|
| **01** | prompt-text | Write the system prompt and user task |
| **02** | message-format | Wrap text into the message structure |
| **03** | python-requests | Send HTTP request with Python |
| **04** | openai-sdk | Use the OpenAI SDK |
| **05** | code-extraction | Extract Python code from LLM response |
| **06** | code-execution | Execute the extracted code |
| **07** | tool-use | LLM calls custom local functions |
| **08** | react-loop | The full ReAct loop: Think → Act → Observe → Repeat |

---

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env, fill in your API key and model
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Start from step 01!

```bash
uv run python versions/01-prompt-text/agent.py
```

---

## Project Structure

```
agent-101/
├── versions/
│   ├── 01-prompt-text/
│   ├── 02-message-format/
│   ├── 03-python-requests/
│   ├── 04-openai-sdk/
│   ├── 05-code-extraction/
│   ├── 06-code-execution/
│   ├── 07-tool-use/
│   └── 08-react-loop/
├── .env.example
├── .gitignore
└── README.md
```

---

## Core Concept

An AI agent works like this:

```
Task -> Think -> Code -> Execute -> Observe -> ... -> Final Answer
```

This is the **ReAct framework** (Reasoning + Acting)!

---

## License

Apache 2.0
