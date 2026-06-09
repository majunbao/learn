"""
Send request using Python requests.
"""

import os
import json
from dotenv import load_dotenv
import requests

load_dotenv()

API_KEY = os.environ.get("ARK_API_KEY")
API_BASE = os.environ["ARK_API_BASE"]
MODEL = os.environ["MODEL"]

system_prompt = """You are an assistant that can solve problems using Python code.

Workflow:
1. Think: Explain your approach in natural language
2. Code: Write Python code to implement your approach
3. Call final_answer(): Use this function to return your answer when done

Code format:
```py
# Your Python code here
final_answer(your_answer)
```<end_code>

Important:
- Use print() for intermediate output
- Always end with final_answer() to return the final result

Let's begin!"""

user_task = "Task: What is the square root of 2024?"

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_task}
]

request_data = {
    "model": MODEL,
    "messages": messages,
    "stop": ["<end_code>"]
}

print("Request data:")
print(json.dumps(request_data, indent=2, ensure_ascii=False))
print()

response = requests.post(
    f"{API_BASE}/chat/completions",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json=request_data
)

print("Response:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
