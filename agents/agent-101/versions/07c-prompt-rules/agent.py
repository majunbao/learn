"""
07c-prompt-rules: Add explicit rules to prevent common LLM mistakes.

One change from 07b: the prompt now includes a numbered list of rules
that prevent the most frequent errors (wrong argument format, variable
name collisions, etc.).
"""

import os
import re
from dotenv import load_dotenv
from openai import OpenAI
from smolagents import LocalPythonExecutor

load_dotenv()

API_KEY = os.environ["ARK_API_KEY"]
API_BASE = os.environ["ARK_API_BASE"]
MODEL = os.environ["MODEL"]

client = OpenAI(api_key=API_KEY, base_url=API_BASE)


def final_answer(answer):
    return answer


def get_weather(city):
    """Get weather for a city."""
    return "sunny, 25°C"


def calculate(expression):
    """Evaluate a math expression."""
    result = eval(expression)
    return result


def get_current_time():
    """Get current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


executor = LocalPythonExecutor(additional_authorized_imports=[])
executor.send_tools({
    "final_answer": final_answer,
    "get_weather": get_weather,
    "calculate": calculate,
    "get_current_time": get_current_time,
})

# ── The ONE change: add explicit rules ──
# In 07b, the LLM knows the format from the example, but still makes mistakes:
# - Passes tool arguments as a dict: search_flights({"destination": "Berlin"})
# - Names a variable the same as a tool: final_answer = "result"
# - Tries to import tools: import get_weather
# - Chains too many tool calls in one block (output unpredictable)
#
# These rules are learned from smolagents' code_agent.yaml — they encode
# real-world failure patterns observed in production.
system_prompt = """You are an assistant that solves tasks using Python code.

To solve a task, you proceed in a cycle of Thought and Code steps:
- In the 'Thought:' sequence, explain your reasoning and which tools you will use.
- In the Code sequence, write Python code. The block MUST open with ```py and close with ```<end_code>.
- Use `print()` to expose intermediate results — they will appear in the next step's 'Observation:'.
- When you have the answer, call `final_answer(answer)` to return it.

You have access to the following tools (already available, DO NOT import them):
- get_weather(city: str) -> str: Get weather for a city
- calculate(expression: str) -> str: Evaluate a math expression
- get_current_time() -> str: Get current date and time
- final_answer(answer) -> any: Return the final answer when done

Here is an example using notional tools:
---
Task: "What is the temperature in Paris plus 10?"

Thought: I will get Paris weather, print it so I can see the structure, then compute the answer.
```py
weather = get_weather("Paris")
print(weather)
```<end_code>
Observation: sunny, 20°C

Thought: Paris is 20°C. I add 10 and return the final answer.
```py
final_answer(calculate("20 + 10"))
```<end_code>
---

Rules you must always follow:
1. Always provide a 'Thought:' sequence, and a '```py' sequence ending with '```<end_code>', else you will fail.
2. Use only variables that you have defined!
3. Always use the right arguments for the tools. DO NOT pass the arguments as a dict as in 'get_weather({"city": "Paris"})', but use the arguments directly as in 'get_weather("Paris")'.
4. For tools with unpredictable output: do not chain too many sequential tool calls in the same code block. Rather output results with print() to use them in the next block.
5. Never name a variable the same as a tool (e.g. don't reuse `final_answer`).
6. Do not import the pre-loaded tools — just call them directly.
"""

user_task = "What's the weather in Tokyo and calculate 25 * 30?"

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_task}
]

response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    stop=["<end_code>"]
)

response_text = response.choices[0].message.content

print("LLM response:")
print(response_text)
print()

code_match = re.search(r"```py([\s\S]*?)```", response_text)

if code_match:
    extracted_code = code_match.group(1).strip()
    print("Extracted code:")
    print(extracted_code)
    print()

    result = executor(code_action=extracted_code)
    print("Execution result:")
    print(f"  logs: {repr(result.logs)}")
    print(f"  output: {repr(result.output)}")
    print(f"  is_final_answer: {result.is_final_answer}")
else:
    print("No code block found in response.")
