"""
07-tool-use: LLM calls custom local functions (tools).
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

system_prompt = """You are an assistant that solves problems using Python code.

You have access to the following tools (already available, DO NOT import them):
- get_weather(city: str) -> str: Get weather for a city
- calculate(expression: str) -> str: Evaluate a math expression
- get_current_time() -> str: Get current date and time
- final_answer(answer) -> any: Return the final answer when done

IMPORTANT: These functions are pre-loaded. Just call them directly. DO NOT write "import get_weather" or any import statement for these tools.

CRITICAL OUTPUT FORMAT:
You MUST wrap your code in ```py blocks and end with <end_code>.

Example:
```py
weather = get_weather("Paris")
final_answer(weather)
```<end_code>

IMPORTANT: Call final_answer() with the result directly. Do NOT wrap it in extra text.
- Good: final_answer(weather)
- Bad: final_answer(f"Weather in Beijing: {weather}")

Workflow:
1. Think: Briefly explain your approach
2. Code: Write Python code that calls the tools directly (no import needed)
3. Call final_answer() with the result directly
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
