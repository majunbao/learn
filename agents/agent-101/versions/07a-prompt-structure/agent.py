"""
07a-prompt-structure: Force LLM to output Thought + Code structure.

One change from 07: the prompt now requires the LLM to write a "Thought:" line
before each code block, making its reasoning explicit.
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

# ── The ONE change: require "Thought:" before code ──
# In 07, the prompt said "Briefly explain your approach" — vague, easy to skip.
# Now we explicitly require a "Thought:" line, which:
# 1. Forces the LLM to reason before coding (chain-of-thought)
# 2. Makes the output structured and predictable
# 3. Gives us a clear separation between reasoning and action
system_prompt = """You are an assistant that solves tasks using Python code.

To solve a task, you proceed in a cycle of Thought and Code steps:
- In the 'Thought:' sequence, explain your reasoning and which tools you will use.
- In the Code sequence, write Python code. The block MUST open with ```py and close with ```<end_code>.

You have access to the following tools (already available, DO NOT import them):
- get_weather(city: str) -> str: Get weather for a city
- calculate(expression: str) -> str: Evaluate a math expression
- get_current_time() -> str: Get current date and time
- final_answer(answer) -> any: Return the final answer when done

IMPORTANT: Always start with a 'Thought:' line before the code block, otherwise you will fail.
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
