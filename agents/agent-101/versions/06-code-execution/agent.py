"""
06-code-execution: Execute the extracted code.
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

executor = LocalPythonExecutor(additional_authorized_imports=[])
executor.send_tools({"final_answer": final_answer})

system_prompt = """You are an assistant that solves problems using Python code.

CRITICAL OUTPUT FORMAT:
You MUST wrap your code in ```py blocks and end with <end_code>.

Example:
```py
import math
result = math.sqrt(2024)
print(f"Result: {result}")
final_answer(result)
```<end_code>

Your response MUST follow this EXACT format. Do NOT output code without the ```py wrapper.

Workflow:
1. Think: Briefly explain your approach
2. Code: Write Python code in the format above
3. The code MUST call final_answer() to return the result
"""

user_task = "Task: Find the maximum value in the list [3, 1, 4, 1, 5, 9] and return the result."

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

print("Response text:")
print(repr(response_text))
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
