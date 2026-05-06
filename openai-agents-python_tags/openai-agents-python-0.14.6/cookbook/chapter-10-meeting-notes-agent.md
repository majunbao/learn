# Chapter 10: Meeting Notes Agent — Internal Enterprise Tool

This chapter builds a **meeting notes agent** — an internal enterprise tool that processes meeting transcripts, extracts action items, and routes tasks. It extends the patterns from Chapter 9 with **role-based access control**, **multi-turn refinement**, **human-in-the-loop review**, and **structured output extraction**.

We continue using **Doubao (doubao-seed-2.0-pro)** via Volcengine Ark API.

## How to Read This Chapter

**Pass 1 — Build the core (~30 min):** Read 10.1 → 10.2 → 10.3. Set up the project, create the transcript agent, and extract action items.

**Pass 2 — Add enterprise features (~45 min):** Read 10.4 → 10.5 → 10.6 → 10.7. Add role-based access, multi-turn refinement, output guardrails, and human review.

**Pass 3 — Integration (~20 min):** Read 10.8 → 10.9 → 10.10. System integration, walkthroughs, and key takeaways.

> **Prerequisites:** Chapter 9 (Smart Customer Service) covers Doubao setup, tools, context, sessions, guardrails, and error handling. This chapter adds new patterns on top of those foundations.

---

## 10.1 Project Setup

### 10.1.1 Create the Project

```bash
uv init meeting-agent
cd meeting-agent
uv add openai-agents python-dotenv
```

### 10.1.2 Reuse Doubao Config

Copy `config.py` from Chapter 9 (or create a shared package). The setup is identical:

```python
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import set_default_openai_client, set_default_openai_api, set_tracing_disabled

load_dotenv()

ARK_API_KEY = os.getenv("ARK_API_KEY")
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3"
MODEL_NAME = "doubao-seed-2.0-pro"


def setup_doubao():
    client = AsyncOpenAI(
        api_key=ARK_API_KEY,
        base_url=ARK_BASE_URL,
    )
    set_default_openai_client(client, use_for_tracing=False)
    set_default_openai_api("chat_completions")
    set_tracing_disabled(True)
```

### 10.1.3 Project Structure

```
meeting-agent/
├── pyproject.toml
├── uv.lock
├── .env
├── config.py            # Doubao configuration (same as Ch9)
├── context.py           # MeetingContext with role-based fields
├── tools.py             # @function_tool definitions
├── guardrails.py        # Output guardrails for confidentiality
├── main.py              # Entry point with HITL review flow
└── sample_transcript.txt # Sample meeting transcript for testing
```

### 10.1.4 Sample Transcript

Create `sample_transcript.txt` for testing:

```
Product Planning Meeting - 2025-01-15
Attendees: Alice (PM), Bob (Engineering), Carol (Design), Dave (QA)

Alice: Let's finalize the Q2 roadmap. The top priority is the mobile app redesign.
Bob: We need 3 sprints for the redesign. I'll draft the technical spec by Jan 20.
Carol: I'll have the design mockups ready by Jan 18. Need Bob's API spec first.
Dave: QA needs 1 sprint for regression testing. I'll create the test plan by Jan 25.
Alice: Good. Bob, also please schedule the architecture review with the platform team.
Bob: Will do. Let me check their calendar — target Jan 22.
Alice: One more thing — the client demo is Feb 1. Carol, can you prepare a demo flow?
Carol: Yes, I'll have it by Jan 28.
Alice: Great. Summary: redesign is top priority, specs due Jan 20, mockups Jan 18, test plan Jan 25, demo Feb 1.

Action Items:
- Bob: Draft technical spec by Jan 20
- Carol: Design mockups by Jan 18
- Dave: Test plan by Jan 25
- Bob: Schedule architecture review by Jan 22
- Carol: Prepare demo flow by Jan 28
```

---

## 10.2 Transcript Input Agent

### 10.2.1 Define the Context

Create `context.py`:

```python
from dataclasses import dataclass, field
from enum import Enum


class UserRole(str, Enum):
    PARTICIPANT = "participant"
    MANAGER = "manager"
    EXECUTIVE = "executive"


@dataclass
class MeetingContext:
    user_id: str
    user_name: str
    role: UserRole = UserRole.PARTICIPANT
    department: str = "engineering"
    can_see_confidential: bool = False
    attended_meetings: list[str] = field(default_factory=list)
```

The `role` field drives **role-based access control** (§10.4) — different roles see different detail levels.

### 10.2.2 Basic Transcript Agent

```python
import asyncio
from agents import Agent, Runner
from config import setup_doubao
from context import MeetingContext

setup_doubao()

agent = Agent[MeetingContext](
    name="Meeting Notes Agent",
    instructions="""You are a meeting notes assistant. When given a meeting transcript:
1. Generate a concise summary (3-5 bullet points)
2. List key decisions made
3. List action items with owners and deadlines

Be factual — only include information explicitly stated in the transcript.""",
)

async def main():
    with open("sample_transcript.txt") as f:
        transcript = f.read()

    ctx = MeetingContext(
        user_id="U-001",
        user_name="Alice",
        role="participant",
    )

    result = await Runner.run(agent, transcript, context=ctx)
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

Run:

```bash
uv run main.py
```

---

## 10.3 Action Item Extraction

Free-form text output isn't enough for downstream systems. We need **structured action items** that can be tracked, assigned, and updated.

### 10.3.1 Define Structured Output Types

Add to `context.py`:

```python
from dataclasses import dataclass, field
from enum import Enum


class UserRole(str, Enum):
    PARTICIPANT = "participant"
    MANAGER = "manager"
    EXECUTIVE = "executive"


@dataclass
class ActionItem:
    description: str
    owner: str
    deadline: str
    priority: str = "medium"
    status: str = "pending"


@dataclass
class MeetingSummary:
    meeting_title: str
    date: str
    attendees: list[str]
    summary: list[str]
    decisions: list[str]
    action_items: list[ActionItem]
    confidential_notes: list[str] = field(default_factory=list)
```

### 10.3.2 Agent with output_type

```python
from context import MeetingContext, MeetingSummary

agent = Agent[MeetingContext](
    name="Meeting Notes Agent",
    instructions="""You are a meeting notes assistant. When given a meeting transcript:
1. Extract the meeting title and date
2. List all attendees
3. Generate a concise summary (3-5 bullet points)
4. List key decisions made
5. Extract ALL action items with owner, deadline, and priority (high/medium/low)
6. If there are any confidential discussions (personnel, budget, legal), list them separately

You MUST respond in the MeetingSummary format with valid JSON.""",
    output_type=MeetingSummary,
)
```

### 10.3.3 Process the Result

```python
async def main():
    with open("sample_transcript.txt") as f:
        transcript = f.read()

    ctx = MeetingContext(
        user_id="U-001",
        user_name="Alice",
        role="participant",
    )

    result = await Runner.run(agent, transcript, context=ctx)
    summary: MeetingSummary = result.final_output

    print(f"Meeting: {summary.meeting_title} ({summary.date})")
    print(f"Attendees: {', '.join(summary.attendees)}")
    print("\nSummary:")
    for point in summary.summary:
        print(f"  • {point}")
    print("\nAction Items:")
    for item in summary.action_items:
        print(f"  [{item.priority.upper()}] {item.description} — {item.owner} (by {item.deadline})")

if __name__ == "__main__":
    asyncio.run(main())
```

Expected output:

```
Meeting: Product Planning Meeting (2025-01-15)
Attendees: Alice, Bob, Carol, Dave

Summary:
  • Q2 roadmap finalized with mobile app redesign as top priority
  • Redesign requires 3 sprints from engineering
  • Client demo scheduled for Feb 1
  ...

Action Items:
  [HIGH] Draft technical spec — Bob (by Jan 20)
  [HIGH] Design mockups — Carol (by Jan 18)
  [MEDIUM] Test plan — Dave (by Jan 25)
  [MEDIUM] Schedule architecture review — Bob (by Jan 22)
  [MEDIUM] Prepare demo flow — Carol (by Jan 28)
```

---

## 10.4 Role-Based Access

Different roles should see different levels of detail:

```
┌────────────────────────────────────────────────────────────────┐
│              Role-Based Output Levels                          │
├────────────┬──────────────────────────────────────────────────-┤
│  Role      │  What they see                                   │
├────────────┼──────────────────────────────────────────────────-┤
│  Executive │  Summary only, high-priority action items         │
│  Manager   │  Summary + all action items + decisions           │
│  Participant│ Full detail: summary, decisions, their own        │
│            │  action items, confidential if attended           │
└────────────┴──────────────────────────────────────────────────-┘
```

### 10.4.1 Role-Based Tool: Filter Output

Create `tools.py`:

```python
from agents import function_tool, RunContextWrapper
from context import MeetingContext, MeetingSummary, ActionItem


@function_tool
async def filter_for_role(
    ctx: RunContextWrapper[MeetingContext],
    summary_json: str,
) -> str:
    """Filter a meeting summary based on the user's role. Returns a tailored version."""
    import json

    context = ctx.context
    data = json.loads(summary_json)

    if context.role.value == "executive":
        filtered = {
            "meeting_title": data.get("meeting_title", ""),
            "date": data.get("date", ""),
            "summary": data.get("summary", []),
            "action_items": [
                item for item in data.get("action_items", [])
                if item.get("priority") == "high"
            ],
        }
        return json.dumps(filtered, ensure_ascii=False)

    if context.role.value == "manager":
        filtered = {
            "meeting_title": data.get("meeting_title", ""),
            "date": data.get("date", ""),
            "summary": data.get("summary", []),
            "decisions": data.get("decisions", []),
            "action_items": data.get("action_items", []),
        }
        return json.dumps(filtered, ensure_ascii=False)

    user_items = [
        item for item in data.get("action_items", [])
        if item.get("owner", "").lower() == context.user_name.lower()
    ]
    filtered = {
        "meeting_title": data.get("meeting_title", ""),
        "date": data.get("date", ""),
        "summary": data.get("summary", []),
        "action_items": user_items,
    }
    if context.can_see_confidential:
        filtered["confidential_notes"] = data.get("confidential_notes", [])
    return json.dumps(filtered, ensure_ascii=False)
```

### 10.4.2 Agent with Role-Based Instructions

```python
agent = Agent[MeetingContext](
    name="Meeting Notes Agent",
    instructions="""You are a meeting notes assistant.

Step 1: Analyze the transcript and extract a full MeetingSummary.
Step 2: Use filter_for_role to tailor the output for the current user's role.
Step 3: Present the filtered result to the user.

Important role rules:
- Executives only see high-level summary and high-priority items
- Managers see all action items and decisions
- Participants see only their own action items
- Confidential notes are only shown if the user has permission

Always use the filter_for_role tool before presenting results.""",
    tools=[filter_for_role],
    output_type=MeetingSummary,
)
```

---

## 10.5 Multi-Turn Refinement

After the initial extraction, users want to refine: "Expand item 3", "Change the owner of item 5 to Carol", "Add a missing action item".

### 10.5.1 Session-Based Refinement

```python
from agents import SQLiteSession

session = SQLiteSession("meeting-abc-123", db_path="meeting_sessions.db")

result1 = await Runner.run(agent, transcript, context=ctx, session=session)
print(result1.final_output)

result2 = await Runner.run(
    agent,
    "Change the owner of 'Schedule architecture review' to Carol",
    context=ctx,
    session=session,
)
print(result2.final_output)

result3 = await Runner.run(
    agent,
    "Add a new action item: Alice to send meeting recap by Jan 16, priority high",
    context=ctx,
    session=session,
)
print(result3.final_output)
```

### 10.5.2 🔥 Refinement Flow

```
  Turn 1: [Full transcript]
         │
         ▼
  ┌─ Agent ──────────────────────────────────────────┐
  │  1. Parse transcript → MeetingSummary             │
  │  2. filter_for_role → tailored output             │
  │  3. Return structured result                      │
  └───────────────────────────────────────────────────┘
         │
         ▼
  Session stores: [user_input, tool_calls, agent_response]

  Turn 2: "Change owner of item 5 to Carol"
         │
         ▼
  ┌─ Agent ──────────────────────────────────────────┐
  │  1. Session provides previous context             │
  │  2. Agent understands "item 5" = architecture     │
  │     review from Turn 1                            │
  │  3. Updates the action item                       │
  │  4. filter_for_role → updated output              │
  └───────────────────────────────────────────────────┘
```

The key insight: the session carries the full conversation history, so the LLM naturally resolves references like "item 5" or "that deadline".

---

## 10.6 Output Guardrail — Prevent Information Leakage

When a **non-attendee** asks about a meeting, we must prevent leaking confidential information.

### 10.6.1 Define the Guardrail

Create `guardrails.py`:

```python
from agents import GuardrailFunctionOutput, output_guardrail, RunContextWrapper, Agent
from context import MeetingContext


CONFIDENTIAL_KEYWORDS = [
    "salary", "compensation", "layoff", "firing", "budget cut",
    "acquisition", "merger", "revenue", "profit margin",
    "personnel issue", "performance review",
]


@output_guardrail
async def prevent_confidential_leak(
    ctx: RunContextWrapper[MeetingContext],
    agent: Agent,
    agent_output: str,
) -> GuardrailFunctionOutput:
    context = ctx.context
    output_lower = str(agent_output).lower()

    if not context.can_see_confidential:
        found = [kw for kw in CONFIDENTIAL_KEYWORDS if kw in output_lower]
        if found:
            return GuardrailFunctionOutput(
                tripwire_triggered=True,
                output_info={
                    "reason": f"Confidential information detected: {found}",
                    "user_role": context.role.value,
                },
            )

    return GuardrailFunctionOutput(
        tripwire_triggered=False,
        output_info={"checked": True},
    )
```

### 10.6.2 Attach to Agent

```python
from guardrails import prevent_confidential_leak

agent = Agent[MeetingContext](
    name="Meeting Notes Agent",
    instructions="...",
    tools=[filter_for_role],
    output_guardrails=[prevent_confidential_leak],
)
```

### 10.6.3 Guardrail vs Role-Based Filtering — What's the Difference?

```
┌─────────────────────────────────────────────────────────────────┐
│  Two-Layer Protection                                           │
├──────────────────────┬──────────────────────────────────────────┤
│  Layer 1: Tool       │  filter_for_role (§10.4)                 │
│  (cooperative)       │  Tailors output to role BEFORE the LLM   │
│                      │  presents it. LLM cooperates by using    │
│                      │  the tool.                                │
│                      │  ⚠️ LLM might skip the tool              │
├──────────────────────┼──────────────────────────────────────────┤
│  Layer 2: Guardrail  │  prevent_confidential_leak (§10.6)      │
│  (enforced)          │  Checks ALL output AFTER the LLM         │
│                      │  generates it. Cannot be bypassed.       │
│                      │  ✅ Hard guarantee                       │
└──────────────────────┴──────────────────────────────────────────┘
```

**Why both?** The tool-based filter is the primary mechanism — it produces clean, role-appropriate output. The guardrail is the safety net — if the LLM forgets to use the tool or hallucinates confidential info, the guardrail catches it.

---

## 10.7 Human Review — HITL Approval

Before distributing meeting notes, a **manager must review and approve** the extracted action items. This is the human-in-the-loop (HITL) pattern.

### 10.7.1 Mark Tools for Approval

Add a `distribute_notes` tool that requires approval:

```python
@function_tool(needs_approval=True)
async def distribute_notes(
    ctx: RunContextWrapper[MeetingContext],
    meeting_title: str,
    recipient_roles: str,
) -> str:
    """Distribute meeting notes to specified roles. Requires manager approval."""
    return f"Meeting notes for '{meeting_title}' distributed to {recipient_roles}."
```

### 10.7.2 🔥 The HITL Flow

```
  User: "Distribute these notes to all participants"
         │
         ▼
  ┌─ Agent Runs ────────────────────────────────────┐
  │  LLM decides to call distribute_notes(...)       │
  │  → needs_approval=True → PAUSE ⏸️               │
  └──────────────────────────────────────────────────┘
         │
         ▼
  result.interruptions = [ToolApprovalItem(
    tool_name="distribute_notes",
    arguments='{"meeting_title":"Product Planning",...}'
  )]
         │
         ▼
  ┌─ Human Review ──────────────────────────────────┐
  │  Manager sees: "Approve distribute_notes with    │
  │  {...}? [y/N]"                                   │
  │  → approve or reject                              │
  └──────────────────────────────────────────────────┘
         │
         ▼
  state = result.to_state()
  state.approve(interruption)  → resume
  ── OR ──
  state.reject(interruption)   → tool rejected, LLM adapts
         │
         ▼
  result = await Runner.run(agent, state)
```

### 10.7.3 Conditional Approval — Only for Sensitive Meetings

For routine meetings, auto-approve. For sensitive ones (e.g., budget discussions), require human review:

```python
async def needs_manager_approval(ctx: RunContextWrapper[MeetingContext], params: dict, _call_id: str) -> bool:
    sensitive_keywords = {"budget", "layoff", "acquisition", "salary", "restructuring"}
    recipient_roles = params.get("recipient_roles", "").lower()
    if "executive" in recipient_roles:
        return True
    meeting_title = params.get("meeting_title", "").lower()
    return any(kw in meeting_title for kw in sensitive_keywords)


@function_tool(needs_approval=needs_manager_approval)
async def distribute_notes(
    ctx: RunContextWrapper[MeetingContext],
    meeting_title: str,
    recipient_roles: str,
) -> str:
    """Distribute meeting notes to specified roles. Requires approval for sensitive meetings or executive recipients."""
    return f"Meeting notes for '{meeting_title}' distributed to {recipient_roles}."
```

### 10.7.4 The Approval Loop in Code

```python
from agents import Agent, Runner, RunState, OutputGuardrailTripwireTriggered
from context import MeetingContext

async def run_with_approval(agent, user_input, ctx, session):
    result = await Runner.run(agent, user_input, context=ctx, session=session)

    while result.interruptions:
        for interruption in result.interruptions:
            tool_name = interruption.name or "unknown"
            arguments = interruption.arguments
            print(f"\n⚠️  Approval Required: {tool_name}")
            print(f"   Arguments: {arguments}")

            answer = input("   Approve? [y/N]: ").strip().lower()
            state = result.to_state()

            if answer in {"y", "yes"}:
                state.approve(interruption)
                print("   ✅ Approved")
            else:
                state.reject(
                    interruption,
                    rejection_message="Distribution rejected by manager. Please inform the user.",
                )
                print("   ❌ Rejected")

        result = await Runner.run(agent, state)

    return result
```

### 10.7.5 Sticky Decisions

If a manager approves `distribute_notes` once, they might want to auto-approve all future distributions in the same meeting:

```python
state.approve(interruption, always_approve=True)
```

This records a permanent approval for `distribute_notes` within the current run — subsequent calls won't pause for review.

---

## 10.8 Integration: Write to Project Tracker

Extracted action items should flow into your project management system.

### 10.8.1 Project Tracker Tool

```python
import json
from agents import function_tool, RunContextWrapper
from context import MeetingContext


_PROJECT_TRACKER: dict[str, list[dict]] = {}


@function_tool
async def create_tasks(
    ctx: RunContextWrapper[MeetingContext],
    tasks_json: str,
) -> str:
    """Create tasks in the project tracker from a JSON array of action items.
    Each task should have: description, owner, deadline, priority."""
    tasks = json.loads(tasks_json)
    meeting_id = f"meeting-{ctx.context.user_id}-{len(_PROJECT_TRACKER)}"
    created = []

    for task in tasks:
        task_record = {
            "id": f"TASK-{len(created) + 1:03d}",
            "description": task.get("description", ""),
            "owner": task.get("owner", ""),
            "deadline": task.get("deadline", ""),
            "priority": task.get("priority", "medium"),
            "status": "pending",
            "meeting_id": meeting_id,
            "created_by": ctx.context.user_name,
        }
        created.append(task_record)

    _PROJECT_TRACKER[meeting_id] = created
    return f"Created {len(created)} tasks in project tracker: {[t['id'] for t in created]}"
```

### 10.8.2 Error Handling for Tool Failures

The project tracker API might fail. Add `failure_error_function` so the agent can adapt:

```python
@function_tool(
    failure_error_function=lambda ctx, error: (
        f"Failed to create tasks in project tracker: {error}. "
        "Please present the action items to the user so they can be added manually."
    )
)
async def create_tasks(
    ctx: RunContextWrapper[MeetingContext],
    tasks_json: str,
) -> str:
    ...
```

---

## 10.9 Complete System

### 10.9.1 Full main.py

```python
import asyncio
from agents import (
    Agent, Runner, SQLiteSession, RunState,
    OutputGuardrailTripwireTriggered,
    ModelSettings, ModelRetrySettings, retry_policies,
)
from config import setup_doubao
from context import MeetingContext, MeetingSummary
from tools import filter_for_role, distribute_notes, create_tasks
from guardrails import prevent_confidential_leak


def create_agent() -> Agent[MeetingContext]:
    return Agent[MeetingContext](
        name="Meeting Notes Agent",
        instructions="""You are a meeting notes assistant for internal enterprise use.

When given a meeting transcript:
1. Extract a full MeetingSummary with all details
2. Use filter_for_role to tailor output for the current user's role
3. Present the filtered result

After the user reviews the notes:
- If they ask to distribute, use distribute_notes (requires approval)
- If they ask to create tasks, use create_tasks with the action items

Rules:
- Never reveal confidential information to users without permission
- Always use filter_for_role before presenting results
- If distribution is rejected, inform the user and suggest alternatives
- Respond in MeetingSummary format for structured queries""",
        tools=[filter_for_role, distribute_notes, create_tasks],
        output_type=MeetingSummary,
        output_guardrails=[prevent_confidential_leak],
        model_settings=ModelSettings(
            temperature=0.1,
            retry=ModelRetrySettings(
                max_retries=3,
                backoff={
                    "initial_delay": 1.0,
                    "max_delay": 10.0,
                    "multiplier": 2.0,
                    "jitter": True,
                },
                policy=retry_policies.any(
                    retry_policies.provider_suggested(),
                    retry_policies.retry_after(),
                    retry_policies.network_error(),
                    retry_policies.http_status([429, 500, 502, 503]),
                ),
            ),
        ),
    )


async def run_with_approval(agent, user_input, ctx, session):
    result = await Runner.run(agent, user_input, context=ctx, session=session)

    while result.interruptions:
        for interruption in result.interruptions:
            tool_name = interruption.name or "unknown"
            arguments = interruption.arguments
            print(f"\n⚠️  Approval Required: {tool_name}")
            print(f"   Arguments: {arguments}")

            answer = input("   Approve? [y/N/a(always)]: ").strip().lower()
            state = result.to_state()

            if answer in {"y", "yes"}:
                state.approve(interruption)
                print("   ✅ Approved")
            elif answer in {"a", "always"}:
                state.approve(interruption, always_approve=True)
                print("   ✅ Approved (always for this run)")
            else:
                state.reject(
                    interruption,
                    rejection_message="Distribution rejected by reviewer.",
                )
                print("   ❌ Rejected")

        result = await Runner.run(agent, state)

    return result


async def main():
    setup_doubao()

    agent = create_agent()

    ctx = MeetingContext(
        user_id="U-001",
        user_name="Alice",
        role="manager",
        department="product",
        can_see_confidential=True,
    )

    session = SQLiteSession("meeting-review-session", db_path="meeting_sessions.db")

    print("=" * 50)
    print("  Meeting Notes Agent (Doubao-powered)")
    print("  Commands: 'file:<path>' to load transcript")
    print("            'quit' to exit")
    print("=" * 50)

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            break

        if user_input.startswith("file:"):
            path = user_input[5:].strip()
            try:
                with open(path) as f:
                    user_input = f.read()
            except FileNotFoundError:
                print(f"File not found: {path}")
                continue

        try:
            result = await run_with_approval(agent, user_input, ctx, session)
            output = result.final_output
            if isinstance(output, MeetingSummary):
                print(f"\n📝 Meeting: {output.meeting_title} ({output.date})")
                print(f"   Attendees: {', '.join(output.attendees)}")
                print("\n   Summary:")
                for point in output.summary:
                    print(f"   • {point}")
                if output.decisions:
                    print("\n   Decisions:")
                    for d in output.decisions:
                        print(f"   ✓ {d}")
                if output.action_items:
                    print("\n   Action Items:")
                    for item in output.action_items:
                        print(f"   [{item.priority.upper()}] {item.description} — {item.owner} (by {item.deadline})")
            else:
                print(f"\nAgent: {output}")

        except OutputGuardrailTripwireTriggered:
            print("\n⚠️  I cannot display that information due to confidentiality restrictions.")
        except Exception as e:
            print(f"\n[Error] {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 10.9.2 Three Scenario Walkthroughs

**Scenario 1: Manager Reviews Meeting**

```
You: file:sample_transcript.txt

📝 Meeting: Product Planning Meeting (2025-01-15)
   Attendees: Alice, Bob, Carol, Dave

   Summary:
   • Q2 roadmap finalized with mobile app redesign as top priority
   • Redesign requires 3 engineering sprints
   • Client demo scheduled for Feb 1

   Decisions:
   ✓ Mobile app redesign is Q2 top priority
   ✓ Demo date set for Feb 1

   Action Items:
   [HIGH] Draft technical spec — Bob (by Jan 20)
   [HIGH] Design mockups — Carol (by Jan 18)
   [MEDIUM] Test plan — Dave (by Jan 25)
   [MEDIUM] Schedule architecture review — Bob (by Jan 22)
   [MEDIUM] Prepare demo flow — Carol (by Jan 28)
```

**Scenario 2: Distribute with Approval**

```
You: Distribute these notes to all participants

⚠️  Approval Required: distribute_notes
   Arguments: {"meeting_title":"Product Planning Meeting","recipient_roles":"participants"}
   Approve? [y/N/a(always)]: y
   ✅ Approved

Agent: Meeting notes for 'Product Planning Meeting' have been distributed to all participants.
```

**Scenario 3: Create Tasks in Tracker**

```
You: Create tasks from the action items in the project tracker

Agent: Created 5 tasks in project tracker: ['TASK-001', 'TASK-002', 'TASK-003', 'TASK-004', 'TASK-005']
```

---

## 10.10 Key Takeaways

1. **Structured output for downstream systems** — `output_type=MeetingSummary` turns free-form LLM output into typed data that tools, APIs, and databases can consume. With Doubao, use lower `temperature` and explicit prompt instructions to improve JSON consistency.

2. **Role-based access as a tool** — `filter_for_role` is the cooperative layer that tailors output. The LLM calls it voluntarily. This is flexible but not guaranteed.

3. **Guardrails as the safety net** — `@output_guardrail` is the enforced layer that catches what tools miss. Use both: tools for the happy path, guardrails for the safety net.

4. **Multi-turn refinement via sessions** — `SQLiteSession` carries conversation history, so the LLM naturally resolves references like "item 3" or "that deadline". No special code needed.

5. **HITL approval flow** — `needs_approval=True` pauses execution. `result.interruptions` shows pending approvals. `state.approve()` or `state.reject()` resumes. This is the production pattern for any action with real-world side effects.

6. **Conditional approval with callables** — `needs_approval=callable` lets you decide per-call whether to require approval. Use it for tiered sensitivity: auto-approve routine actions, require review for sensitive ones.

7. **Sticky decisions reduce friction** — `always_approve=True` records a permanent decision for the rest of the run. Use it when a manager trusts a tool for all subsequent calls.

8. **Tool error handling for integration** — `failure_error_function` turns tool exceptions into helpful messages the LLM can adapt to. When your project tracker API is down, the agent can present items manually instead of crashing.

> **Next:** Chapter 11 combines everything into a multi-agent office assistant — a Triage Agent routing to IT, HR, Finance, and Knowledge Base specialists, with permission isolation, multi-level approval chains, and cross-agent cost monitoring.
