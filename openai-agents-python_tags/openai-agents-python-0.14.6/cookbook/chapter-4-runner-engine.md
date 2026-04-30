# Chapter 4: Runner Engine - The core loop in run_internal.py

## 4.1 The Big Picture: What Does the Runner Do?

Let's start with the highest-level view of the engine:

```
Runner.run(agent, "Hello!")
        ↓
    Initialize:
        • Create RunContext
        • Create RunState
        • Load Session (if any)
        • Set up tracing
        ↓
    The Loop:
        while not done:
            • Run Input Guardrails
            • Call LLM (run_single_turn)
            • Process Response
            • Execute Tools
            • Check for Handoffs
            • Check for Final Output
            • Check Turn Limit
        ↓
    Cleanup:
        • Run Output Guardrails
        • Save to Session
        • Finalize tracing
        ↓
    Return:
        • RunResult (or RunResultStreaming)
```

That's the basic flow! Now let's dive deeper.

## 4.2 The Module Architecture in `run_internal`

Look at all those files! The SDK is beautifully modularized:

```
run_internal/
├── run_loop.py              ← Main orchestration
├── run_steps.py            ← Next step decisions
├── turn_resolution.py      ← Process model output
├── turn_preparation.py     ← Prepare for model call
├── tool_execution.py       ← Actually call tools
├── tool_planning.py        ← MCP stuff
├── tool_actions.py         ← Shell/Computer actions
├── tool_use_tracker.py     ← Track tool usage
├── guardrails.py           ← Input/Output guardrails
├── error_handlers.py       ← Error handling
├── approvals.py            ← Tool approval logic
├── session_persistence.py  ← Save/load history
├── streaming.py            ← Streaming utilities
├── items.py                ← Item normalization
├── model_retry.py          ← Retry failed model calls
├── oai_conversation.py     ← Server-managed conversation
├── agent_bindings.py       ← Agent → internal format
└── agent_runner_helpers.py ← Utilities
```

Single Responsibility Principle in action! Each file does one thing well.

## 4.3 The Heart: `run_single_turn`

Let's zoom into the core function - `run_single_turn` in `run_loop.py`. This is where one full turn happens!

```
┌─────────────────────────────────────────────────────────────────┐
│  1. TURN PREPARATION                                            │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ • Get agent's tools (get_all_tools)                  │  │
│     │ • Get agent's handoffs (get_handoffs)                 │  │
│     │ • Get output schema (get_output_schema)               │  │
│     │ • Build model settings                                │  │
│     └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. CALL THE MODEL                                              │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ get_new_response(...) → talks to LLM!                │  │
│     │ • Handles retries (model_retry.py)                   │  │
│     │ • Handles streaming (if enabled)                     │  │
│     └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. PROCESS RESPONSE                                            │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ get_single_step_result_from_response(...)            │  │
│     │ • Parse model output                                 │  │
│     │ • Find tool calls                                    │  │
│     │ • Find handoff calls                                 │  │
│     │ • Find final output                                  │  │
│     └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. "What's Next?" Decision (NextStep!)                        │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ Can be:                                               │  │
│     │ • NextStepFinalOutput → we're done!                  │  │
│     │ • NextStepHandoff → switch agents!                   │  │
│     │ • NextStepRunAgain → tools were called, go again!    │  │
│     │ • NextStepInterruption → need approval first!        │  │
│     └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. EXECUTE! (If needed)                                        │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ execute_tools_and_side_effects(...)                   │  │
│     │ • Runs function tools in parallel!                   │  │
│     │ • Runs computer tools                                │  │
│     │ • Runs shell tools                                   │  │
│     │ • Runs handoffs (but that's a whole new agent!)       │  │
│     └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  6. UPDATE STATE                                                │
│     ┌───────────────────────────────────────────────────────┐  │
│     │ • Add items to RunState                               │  │
│     │ • Save to Session (if configured)                    │  │
│     │ • Update tracing spans                               │  │
│     └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

This is one turn! And we loop this until we get `NextStepFinalOutput` or hit `MaxTurnsExceeded`.

## 4.4 The NextStep Types: A State Machine

Let's look at these elegant dataclasses in `run_steps.py`:

```python
@dataclass
class NextStepFinalOutput:
    output: Any  # We're done! Return this.

@dataclass
class NextStepHandoff:
    new_agent: Agent[Any]  # Switch agents!

@dataclass
class NextStepRunAgain:
    pass  # Tools were called, go again!

@dataclass
class NextStepInterruption:
    interruptions: list[ToolApprovalItem]  # Pause for approval!
```

This is a classic State Pattern! Instead of a bunch of `if/else`, we have clear state types.

And here's how we decide which one to return (from `turn_resolution.py`):

```
Model Response → ProcessedResponse
                  ↓
              Look at items:
                  ├── Has final output? → NextStepFinalOutput
                  ├── Has handoff? → NextStepHandoff
                  ├── Has tool calls? → NextStepRunAgain
                  └── Needs approval? → NextStepInterruption
```

## 4.5 The ProcessedResponse: What the Model Actually Said

This is the key intermediate structure! Look at `ProcessedResponse`:

```python
@dataclass
class ProcessedResponse:
    new_items: list[RunItem]  # All items from this turn
    
    # Things to execute locally:
    handoffs: list[ToolRunHandoff]
    functions: list[ToolRunFunction]
    computer_actions: list[ToolRunComputerAction]
    local_shell_calls: list[ToolRunLocalShellCall]
    shell_calls: list[ToolRunShellCall]
    apply_patch_calls: list[ToolRunApplyPatchCall]
    
    # Other things:
    tools_used: list[str]
    mcp_approval_requests: list[ToolRunMCPApprovalRequest]
    interruptions: list[ToolApprovalItem]  # Things needing approval!
```

And there's a handy method:

```python
def has_tools_or_approvals_to_run(self) -> bool:
    # Do we have work to do?
    return any([
        self.handoffs,
        self.functions,
        self.computer_actions,
        # ... etc
    ])
```

Beautiful!

## 4.6 Tool Execution: Parallel is Faster!

When we have multiple tool calls, the SDK doesn't wait for one to finish before starting the next! Look at `execute_function_tool_calls`:

```
ToolCall[0]  ToolCall[1]  ToolCall[2]
    │            │            │
    ├────────────┼────────────┤
    │            │            │
  Start       Start        Start
    │            │            │
    └────────────┴────────────┘
           ↓ (asyncio.gather!)
    ┌───────────────────────┐
    │ Wait for ALL to finish │
    └───────────────────────┘
           ↓
    Collect all results!
```

This is smart! Tools are often I/O bound (API calls, databases, etc.), so parallelizing them makes things faster.

## 4.7 The Full Loop: From `run.py`

Let's look at the very high-level flow from the public `Runner.run` down:

```
Public API: Runner.run(agent, input, run_config)
        ↓
    Creates:
        • RunContextWrapper
        • RunState
        • Trace (tracing!)
        ↓
    The Loop (in pseudo-code):
        turn_count = 0
        current_agent = agent
        while True:
            turn_count += 1
            if turn_count > max_turns:
                raise MaxTurnsExceeded()
            
            # Do one turn!
            step_result = run_single_turn(
                current_agent,
                run_state,
                # ...
            )
            
            # Decide what to do next
            if isinstance(step_result.next_step, NextStepFinalOutput):
                return build_final_result(...)
            elif isinstance(step_result.next_step, NextStepHandoff):
                current_agent = step_result.next_step.new_agent
            elif isinstance(step_result.next_step, NextStepRunAgain):
                continue  # Just go again!
            elif isinstance(step_result.next_step, NextStepInterruption):
                return build_interruption_result(...)
```

Simple, elegant, and easy to follow!

## 4.8 Streaming Mode: It's Just an Async Queue!

When you use streaming, there's `start_streaming` and `run_single_turn_streamed`. The difference is:

```
Normal Mode:
    Call LLM → Wait for full response → Process

Streaming Mode:
    Call LLM → Stream chunks to queue → Process as they come
                  ↓
            Asyncio.Queue!
                  ↓
            User can iterate as things happen!
```

And look at this sentinel value:

```python
class QueueCompleteSentinel:
    """Sentinel used to signal completion when streaming run loop results."""

QUEUE_COMPLETE_SENTINEL = QueueCompleteSentinel()
```

Classic pattern for "we're done" in queues!

## 4.9 Model Retries: Robustness Built In

What if the LLM call fails? No problem! Look at `model_retry.py`:

```
First attempt:
    Call LLM
        ↓
    Success? → Return response
        ↓
    Failed?
        ↓
    Is it retryable? (Rate limit, network error, etc.)
        ↓
    Yes → Wait (exponential backoff) → Try again!
        ↓
    No → Raise exception
```

This makes your agents much more robust to transient failures!

## 4.10 Guardrails: Safety Before and After

Let's visualize when guardrails run:

```
BEFORE the model call (Input Guardrails):
    User Input → [Input Guardrail 1] → [Input Guardrail 2] → ... → Model
                    ↓ (if any fail)
              Tripwire triggered → Interrupt!

AFTER the model produces final output (Output Guardrails):
    Model Output → [Output Guardrail 1] → [Output Guardrail 2] → ... → User
                    ↓ (if any fail)
              Tripwire triggered → Don't return output!
```

And tool guardrails run right before/after each tool call!

## 4.11 Let's Build a Mini Runner!

Let's distill the core ideas into 100 lines of code! This will help you understand the essence:

```python
from dataclasses import dataclass
from typing import Any, Literal

# Our simple state machine
@dataclass
class NextStepFinal:
    output: Any

@dataclass
class NextStepAgain:
    pass

# A simple agent
@dataclass
class MiniAgent:
    name: str
    instructions: str

# A simple tool
@dataclass
class MiniTool:
    name: str
    func: Any

# The runner!
class MiniRunner:
    @staticmethod
    async def run(agent: MiniAgent, user_input: str, max_turns: int = 10):
        turn = 0
        conversation = [{"role": "user", "content": user_input}]
        
        while turn < max_turns:
            turn += 1
            print(f"Turn {turn}...")
            
            # Step 1: "Call LLM" (we'll mock this)
            llm_response = await MiniRunner._mock_llm_call(agent, conversation)
            conversation.append({"role": "assistant", "content": llm_response})
            
            # Step 2: Decide next step
            if "[FINAL]" in llm_response:
                output = llm_response.replace("[FINAL]", "").strip()
                return NextStepFinal(output=output)
            elif "[TOOL]" in llm_response:
                # Mock tool execution
                tool_result = "Tool called successfully!"
                conversation.append({"role": "tool", "content": tool_result})
                print(f"Executed tool: {tool_result}")
                continue  # NextStepAgain
            else:
                return NextStepFinal(output=llm_response)
        
        raise Exception("Max turns exceeded!")
    
    @staticmethod
    async def _mock_llm_call(agent, conversation):
        # Super simple mock - just echo with some logic
        last_msg = conversation[-1]["content"]
        if "weather" in last_msg.lower():
            return "[TOOL] get_weather(lat=37, lon=-122)"
        else:
            return f"[FINAL] {agent.name} says: I understand '{last_msg}'"

# Let's try it!
async def main():
    agent = MiniAgent(name="Assistant", instructions="Help users")
    result = await MiniRunner.run(agent, "What's the weather?")
    print(f"Final output: {result.output}")

# Run it!
import asyncio
asyncio.run(main())
```

This captures the essence:
- Loop with turn limit
- Call model
- Decide next step
- Execute tools if needed
- Return when done

## 4.12 Key Takeaways

1. **The Runner is a state machine** - NextStep types make decisions clear
2. **One turn = model call + tool execution** - Loop until final output
3. **Tools run in parallel** - asyncio.gather for speed
4. **Guardrails run at key points** - before model, after model, around tools
5. **Streaming uses async queues** - for real-time feedback
6. **Retries make it robust** - handle transient LLM failures
7. **Modules are cleanly separated** - each file has one job

In the next chapter, we'll look at State Management with `RunContext` and `RunState`!
