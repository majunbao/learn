import logging
import os
import re

from jinja2 import StrictUndefined, Template
from openai import OpenAI
from smolagents.local_python_executor import LocalPythonExecutor

from prompts import SYSTEM_PROMPT
from tools import FinalAnswerTool

BASE_BUILTIN_MODULES = [
    "collections",
    "datetime",
    "itertools",
    "math",
    "queue",
    "random",
    "re",
    "stat",
    "statistics",
    "time",
    "unicodedata",
]

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Agent:
    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        api_base: str | None = None,
        tools: list | None = None,
        authorized_imports: list[str] | None = None,
        max_steps: int = 10,
    ):
        self.model = model or os.environ.get("MODEL", "doubao-seed-2.0-pro")
        self.max_steps = max_steps

        self.tools = {tool.name: tool for tool in (tools or []) + [FinalAnswerTool()]}
        self.authorized_imports = authorized_imports or BASE_BUILTIN_MODULES

        self.python_executor = LocalPythonExecutor(
            additional_authorized_imports=self.authorized_imports,
        )
        self.python_executor.send_tools(self.tools)

        self.client = OpenAI(
            api_key=api_key or os.environ.get("ARK_API_KEY"),
            base_url=api_base or os.environ.get("ARK_API_BASE", "https://ark.cn-beijing.volces.com/api/coding/v3"),
        )

        self.system_prompt = self.initialize_system_prompt(SYSTEM_PROMPT)
        self.history = [{"role": "system", "content": self.system_prompt}]

    def _extract_python_code(self, text: str) -> str | None:
        pattern = r"```py([\s\S]*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def initialize_system_prompt(self, system_prompt_template: str) -> str:
        compiled_template = Template(system_prompt_template, undefined=StrictUndefined)
        variables = {
            "tools": self.tools,
            "authorized_imports": str(self.authorized_imports),
        }
        return compiled_template.render(**variables)

    def run(self, task: str) -> str:
        self.history.append({"role": "user", "content": f"Task: {task}"})
        
        print("\n" + "="*60)
        print(f"🎯 TASK: {task}")
        print("="*60 + "\n")
        
        # Print initial conversation history
        print("📋 CONVERSATION HISTORY:")
        print(f"Total messages: {len(self.history)}")
        for i, msg in enumerate(self.history):
            print(f"\n[{i}] {msg['role']}:")
            print(f"    {msg['content'][:200]}..." if len(msg['content']) > 200 else f"    {msg['content']}")
        print()

        for step in range(self.max_steps):
            print(f"\n{'='*60}")
            print(f"📍 STEP {step + 1}/{self.max_steps}")
            print(f"{'='*60}")
            
            is_final_answer, observation, output = self.step()
            
            print(f"\n📥 OBSERVATION:")
            print(f"{observation['content'][:500]}..." if len(observation['content']) > 500 else observation['content'])
            
            self.history.append(observation)
            
            # Print updated conversation history after each step
            print(f"\n📋 UPDATED HISTORY (after step {step + 1}):")
            print(f"Total messages: {len(self.history)}")
            for i, msg in enumerate(self.history[-2:]):  # Show last 2 messages
                print(f"\n[{len(self.history)-2+i}] {msg['role']}:")
                content_preview = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                print(f"    {content_preview}")
            
            if is_final_answer:
                print(f"\n{'='*60}")
                print(f"✅ FINAL ANSWER:")
                print(f"{'='*60}")
                return output
        
        print(f"\n{'='*60}")
        print(f"❌ FAILED: Maximum steps exceeded")
        print(f"{'='*60}")
        return "Could not solve task: Maximum number of steps exceeded."

    def step(self) -> tuple[bool, dict, str | None]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            stream=False,
            stop=["<end_code>"],
        )
        thought = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": thought})
        
        print(f"\n🤔 THOUGHT:")
        # Print thought without the code part
        code_start = thought.find("```")
        if code_start > 0:
            print(thought[:code_start].strip())
        else:
            print(thought.strip())
        
        code_action = self._extract_python_code(thought)
        
        print(f"\n💻 CODE ACTION:")
        print(code_action)

        result = self.python_executor(code_action=code_action)
        output = result.output
        execution_logs = result.logs
        is_final_answer = result.is_final_answer

        observation = {"role": "user", "content": "Observation:\n" + execution_logs}
        return is_final_answer, observation, output
