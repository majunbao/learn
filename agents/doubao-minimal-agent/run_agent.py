import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from agent import Agent
from tools import WebSearchTool, VisitWebpageTool

if __name__ == "__main__":
    agent = Agent(
        tools=[
            WebSearchTool(max_results=5),
            VisitWebpageTool(max_output_length=1000),
        ],
    )

    # res = agent.run("安徽童仁智能科技有限公司的简介")
    res = agent.run("你觉的现在做什么事情赚钱容易")

    print(20 * "-")
    print(f"The final answer is:\n\n{res}")
