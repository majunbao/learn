"""
Plain prompt text - no structure yet.
"""

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

print("System Prompt:")
print(system_prompt)
print()
print("User Task:")
print(user_task)
