# 01-prompt-text

Everything starts with text. Before we send anything to an LLM, we need to write the prompts.

## What is a prompt?

A prompt is just text that you send to an LLM. There are two types:

### System Prompt

The **system prompt** tells the LLM **how to behave**. It defines:
- Who the assistant is (role)
- What it can do (capabilities)
- How it should respond (format / rules)

Think of it as job instructions you give to a new employee.

### User Task

The **user task** is the actual question or problem you want the LLM to solve.

## Our System Prompt Breakdown

```
You are an assistant that can solve problems using Python code.
```
**Role definition** - Tell the LLM who it is.

```
Workflow:
1. Think: Explain your approach in natural language
2. Code: Write Python code to implement your approach
3. Call final_answer(): Use this function to return your answer when done
```
**Workflow** - Tell the LLM how to work step by step.

```
Code format:
```py
# Your Python code here
final_answer(your_answer)
```<end_code>
```
**Output format** - Tell the LLM exactly how to format its code output. This is critical because we need to parse it later with regex.

```
Important:
- Use print() for intermediate output
- Always end with final_answer() to return the final result
```
**Rules** - Additional constraints.

## Why does the format matter?

The LLM's output is just text. If we want to extract and execute code from it, we need the LLM to write code in a predictable format. That's why we specify:
- Code must be inside ````py ... ``` `` blocks
- Code must end with `final_answer()`
- We use `<end_code>` as a stop token (will explain in later steps)

## How to run

```bash
uv run python agent.py
```

## Next step

→ [02-message-format](../02-message-format) - Wrap these texts into the message structure that the API requires.
