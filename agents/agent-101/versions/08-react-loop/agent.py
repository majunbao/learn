"""
08-react-loop: The full ReAct loop: Think → Act → Observe → Repeat.
"""

import json
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
    """Return the final answer to the user."""
    return answer


def search_flights(destination):
    """Search flights to a destination. Returns a list of flight IDs."""
    flights_db = {
        "tokyo": ["FL101", "FL202", "FL303", "FL404"],
        "paris": ["FL501", "FL602"],
        "london": ["FL701", "FL802", "FL903"],
    }
    return flights_db.get(destination.lower(), [])


def get_flight_price(flight_id):
    """Get the price (USD) of a specific flight."""
    prices = {
        "FL101": 580, "FL202": 320, "FL303": 750, "FL404": 410,
        "FL501": 290, "FL602": 360,
        "FL701": 450, "FL802": 380, "FL903": 520,
    }
    return prices.get(flight_id, -1)


executor = LocalPythonExecutor(additional_authorized_imports=[])
executor.send_tools({
    "final_answer": final_answer,
    "search_flights": search_flights,
    "get_flight_price": get_flight_price,
})

system_prompt = """You are an expert assistant who solves tasks using Python code.

To solve a task, you proceed in a cycle of **Thought → Code → Observation** steps:
- In the 'Thought:' sequence, explain your reasoning and which tools you will use.
- In the 'Code:' sequence, write simple Python code. The block MUST start with ```py and end with ```<end_code>.
- Use `print()` to expose intermediate results — they will appear in the next step's 'Observation:'.
- When you have the answer, call `final_answer(answer)` to return it.

You have access to the following tools (already available, DO NOT import them):
- search_flights(destination: str) -> list[str]: Search flights to a destination. Returns a list of flight IDs (you don't know them in advance).
- get_flight_price(flight_id: str) -> int: Get the price (USD) of a specific flight by ID.
- final_answer(answer) -> any: Return the final answer when done

Here is an example of the expected format:

Task: "Find the cheapest flight to Berlin."

Thought: I don't know which flights exist. First I'll search and print the list.
```py
flights = search_flights("Berlin")
print(flights)
```<end_code>
Observation: ['FL001', 'FL002']

Thought: Now I have the flight IDs. I'll look up each price and pick the cheapest.
```py
prices = {f: get_flight_price(f) for f in ['FL001', 'FL002']}
print(prices)
cheapest = min(prices, key=prices.get)
final_answer({"flight": cheapest, "price": prices[cheapest]})
```<end_code>

Rules you must always follow:
1. ALWAYS start with a 'Thought:' line before the code block, otherwise you will fail.
2. State persists between steps: variables and imports from previous steps remain available.
3. Use `print()` to surface intermediate values you need in the next step.
4. Only call `final_answer()` when you actually have the final result.
5. Use exact tool argument names, e.g. `search_flights("Berlin")`, not `search_flights({"destination": "Berlin"})`.
6. Never name a variable the same as a tool (e.g. don't reuse `final_answer`).
7. Do not import the pre-loaded tools — just call them directly.

Now Begin!
"""

# A task that genuinely needs multiple steps:
# Step 1: search_flights() to discover which flight IDs exist (LLM can't guess them)
# Step 2: After observing the list, call get_flight_price() for each, pick cheapest
user_task = "Find the cheapest flight to Tokyo and tell me its ID and price."

max_steps = 5

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_task}
]

MESSAGES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "messages.txt")

for step in range(1, max_steps + 1):
    print(f"=== Step {step} ===")

    # Think: LLM generates code
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        stop=["<end_code>"]
    )

    response_text = response.choices[0].message.content
    print(f"LLM response:\n{response_text}\n")
    messages.append({"role": "assistant", "content": response_text})

    # Act: Extract and execute code
    code_match = re.search(r"```py([\s\S]*?)```", response_text)
    if code_match:
        extracted_code = code_match.group(1).strip()
        print(f"Extracted code:\n{extracted_code}\n")
        print("Executing code...")
        try:
            result = executor(code_action=extracted_code)
        except Exception as e:
            error_msg = str(e)
            print(f"  Error: {error_msg}\n")
            # Execution failed — feed error back so LLM can self-correct
            observation = f"Observation:\nCode execution failed with error:\n{error_msg}\n\nPlease fix the error and try again."
            messages.append({"role": "user", "content": observation})
            # Dump messages
            with open(MESSAGES_FILE, "w") as f:
                f.write(json.dumps(messages, indent=2, ensure_ascii=False))
            continue

        print(f"Execution result:")
        print(f"  logs: '{result.logs}'")
        print(f"  output: '{result.output}'")
        print(f"  is_final_answer: {result.is_final_answer}")
        print()

        # Observe: Is the task done?
        if result.is_final_answer:
            print(f"✓ Final answer: {result.output}")
            # Dump messages
            with open(MESSAGES_FILE, "w") as f:
                f.write(json.dumps(messages, indent=2, ensure_ascii=False))
            break

        # Not done yet — feed execution output back so LLM can continue
        observation = f"Observation:\n{result.logs}\n\nThe code ran but final_answer() was not called. Continue working and call final_answer() when done."
        messages.append({"role": "user", "content": observation})
    else:
        print("No code found in response")
        messages.append({"role": "user", "content": "Please provide code in ```py blocks."})

    # Dump messages after each step
    with open(MESSAGES_FILE, "w") as f:
        f.write(json.dumps(messages, indent=2, ensure_ascii=False))

else:
    print(f"Reached max_steps ({max_steps}) without final answer")
