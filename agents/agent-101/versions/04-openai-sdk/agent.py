"""
04-openai-sdk: Send request using OpenAI SDK.
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.environ["ARK_API_KEY"]
API_BASE = os.environ["ARK_API_BASE"]
MODEL = os.environ["MODEL"]

client = OpenAI(api_key=API_KEY, base_url=API_BASE)

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

response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    stop=["<end_code>"]
)

print(response.model_dump_json(indent=2))
