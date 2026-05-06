# Chapter 11: Multi-Agent Office Assistant — Enterprise Unified Entry Point

This chapter builds the most complex system in the book: a **multi-agent office assistant** where a single Triage Agent routes requests to IT, HR, Finance, and Knowledge Base specialists. It brings together every pattern from Chapters 9-10 and adds **cross-agent handoffs**, **permission isolation**, **multi-level approval chains**, **cross-agent session memory**, and **per-agent cost monitoring**.

We continue using **Doubao (doubao-seed-2.0-pro)** via Volcengine Ark API.

## How to Read This Chapter

**Pass 1 — Understand the architecture (~20 min):** Read 11.1 → 11.2. Set up the project, understand the Triage Agent pattern, and see how handoffs work.

**Pass 2 — Build the specialist agents (~40 min):** Read 11.3 → 11.4 → 11.5 → 11.6. Build IT, HR, Finance, and Knowledge Base agents with their tools and context filters.

**Pass 3 — Add enterprise hardening (~40 min):** Read 11.7 → 11.8 → 11.9 → 11.10 → 11.11. Add permission isolation, multi-level approval, cross-agent memory, cost monitoring, and error handling.

**Pass 4 — Complete system (~20 min):** Read 11.12 → 11.13. See the full integrated system and key takeaways.

> **Prerequisites:** Chapters 9 and 10 cover Doubao setup, tools, context, sessions, guardrails, HITL, and error handling. This chapter adds multi-agent orchestration on top of those foundations.

---

## 11.1 Project Setup

### 11.1.1 Create the Project

```bash
uv init office-assistant
cd office-assistant
uv add openai-agents python-dotenv
```

### 11.1.2 Reuse Doubao Config

Copy `config.py` from Chapter 9 or 10. Same setup:

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

### 11.1.3 Project Structure

```
office-assistant/
├── pyproject.toml
├── uv.lock
├── .env
├── config.py                # Doubao configuration
├── context.py               # OfficeContext with role/department
├── my_agents/
│   ├── __init__.py          # create_all_agents()
│   ├── triage.py            # Triage Agent (router)
│   ├── it_support.py        # IT Support Agent
│   ├── hr.py                # HR Agent
│   ├── finance.py           # Finance Agent
│   └── knowledge.py         # Knowledge Base Agent
├── my_tools/
│   ├── __init__.py
│   ├── it_tools.py          # reset_password, request_permission, create_ticket
│   ├── hr_tools.py          # lookup_policy, check_leave, onboard_employee
│   ├── finance_tools.py     # check_budget, query_expense, submit_refund
│   └── kb_tools.py          # search_docs, lookup_process
├── guardrails.py            # Permission isolation guardrails
├── hooks.py                 # Per-agent cost tracking
└── main.py                  # Entry point
```

---

## 11.2 Triage Agent

The Triage Agent is the **single entry point** — it classifies user requests and hands off to the right specialist.

### 11.2.1 Shared Context

Create `context.py`:

```python
from dataclasses import dataclass, field
from enum import Enum


class UserRole(str, Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"


class Department(str, Enum):
    ENGINEERING = "engineering"
    HR = "hr"
    FINANCE = "finance"
    MARKETING = "marketing"
    EXECUTIVE = "executive"


@dataclass
class OfficeContext:
    user_id: str
    user_name: str
    role: UserRole = UserRole.EMPLOYEE
    department: Department = Department.ENGINEERING
    employee_id: str = ""
    cost_center: str = ""
```

### 11.2.2 Define Specialist Agents (Stubs)

First, let's create minimal agent stubs. We'll fill in their tools in later sections.

Create `my_agents/it_support.py`:

```python
from agents import Agent
from context import OfficeContext

it_agent = Agent[OfficeContext](
    name="IT Support",
    instructions="You are an IT support agent. Help with password resets, permission requests, and ticket creation.",
    tools=[],
)
```

Create `my_agents/hr.py`:

```python
from agents import Agent
from context import OfficeContext

hr_agent = Agent[OfficeContext](
    name="HR Assistant",
    instructions="You are an HR assistant. Help with policy lookup, leave balance, and onboarding.",
    tools=[],
)
```

Create `my_agents/finance.py`:

```python
from agents import Agent
from context import OfficeContext

finance_agent = Agent[OfficeContext](
    name="Finance Assistant",
    instructions="You are a finance assistant. Help with budget checks, expense queries, and refund submissions.",
    tools=[],
)
```

Create `my_agents/knowledge.py`:

```python
from agents import Agent
from context import OfficeContext

kb_agent = Agent[OfficeContext](
    name="Knowledge Base",
    instructions="You are a knowledge base assistant. Help with internal docs, process lookup, and company policies.",
    tools=[],
)
```

### 11.2.3 🔥 Triage Agent with Handoffs

Create `my_agents/triage.py`:

```python
from agents import Agent, handoff
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from context import OfficeContext
from my_agents.it_support import it_agent
from my_agents.hr import hr_agent
from my_agents.finance import finance_agent
from my_agents.knowledge import kb_agent


triage_agent = Agent[OfficeContext](
    name="Triage Agent",
    instructions=prompt_with_handoff_instructions(
        """You are the unified entry point for all internal company requests.

Analyze the user's request and hand off to the appropriate specialist:

- IT Support: password resets, permission requests, software issues, hardware problems, VPN/access issues
- HR Assistant: leave/benefits questions, policy lookup, onboarding, employee relations
- Finance Assistant: budget queries, expense reports, refunds, purchase orders
- Knowledge Base: company docs, process guides, org charts, general questions

If the request is ambiguous, ask a brief clarifying question before handing off.
If the request spans multiple areas, handle the primary concern and suggest the user ask about the secondary concern next.

IMPORTANT: When you hand off, do NOT mention the handoff mechanism to the user. Just help them naturally."""
    ),
    handoffs=[
        handoff(it_agent, tool_description_override="Transfer to IT Support for technical issues, access, and software problems"),
        handoff(hr_agent, tool_description_override="Transfer to HR for leave, benefits, policies, and employee questions"),
        handoff(finance_agent, tool_description_override="Transfer to Finance for budget, expenses, refunds, and purchase orders"),
        handoff(kb_agent, tool_description_override="Transfer to Knowledge Base for documentation, processes, and general info"),
    ],
)
```

### 11.2.4 The Handoff Flow

```
  User: "I forgot my password and need to check my leave balance"
         │
         ▼
  ┌─ Triage Agent ───────────────────────────────────────────┐
  │  Analyzes: "forgot password" → IT                        │
  │            "leave balance" → HR                           │
  │  Primary concern: password → handoff to IT Support       │
  └───────────────────────────────────────────────────────────┘
         │
         ▼ (handoff: Triage → IT)
  ┌─ IT Support Agent ───────────────────────────────────────┐
  │  Uses reset_password tool                                │
  │  "Your password has been reset. Check your email."       │
  │  → Final output                                         │
  └───────────────────────────────────────────────────────────┘
         │
         ▼
  Result: "Your password has been reset. Check your email.
           For your leave balance, you can ask me again and
           I'll connect you to HR."
```

Key points:
- `prompt_with_handoff_instructions()` adds SDK-recommended context about the multi-agent system.
- `tool_description_override` customizes the handoff tool description so the LLM routes more accurately.
- The Triage Agent itself has **no tools** — it only classifies and routes.

### 11.2.5 Run the Triage Agent

```python
import asyncio
from agents import Runner
from config import setup_doubao
from context import OfficeContext
from my_agents.triage import triage_agent

setup_doubao()

ctx = OfficeContext(
    user_id="U-001",
    user_name="Alice",
    role="employee",
    department="engineering",
)

async def main():
    result = await Runner.run(triage_agent, "I forgot my laptop password", context=ctx)
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 11.3 IT Support Agent

### 11.3.1 IT Tools

Create `my_tools/it_tools.py`:

```python
from agents import function_tool, RunContextWrapper
from context import OfficeContext


_PASSWORD_RESET_LOG: set[str] = set()


@function_tool
async def reset_password(ctx: RunContextWrapper[OfficeContext], username: str) -> str:
    """Reset a user's password. A reset link will be sent to their email."""
    context = ctx.context
    if username.lower() != context.user_name.lower() and context.role.value != "admin":
        return f"Permission denied: you can only reset your own password. Your username is {context.user_name}."
    _PASSWORD_RESET_LOG.add(username.lower())
    return f"Password reset link sent to {username}'s email. The link expires in 15 minutes."


@function_tool
async def request_permission(
    ctx: RunContextWrapper[OfficeContext],
    resource: str,
    reason: str,
) -> str:
    """Request access to a resource (e.g., VPN, production database, admin panel)."""
    context = ctx.context
    return (
        f"Access request submitted: {resource}\n"
        f"Requester: {context.user_name} ({context.department.value})\n"
        f"Reason: {reason}\n"
        f"Status: Pending manager approval"
    )


@function_tool
async def create_ticket(
    ctx: RunContextWrapper[OfficeContext],
    title: str,
    description: str,
    priority: str = "medium",
) -> str:
    """Create an IT support ticket."""
    context = ctx.context
    ticket_id = f"IT-{hash(title) % 10000:04d}"
    return (
        f"Ticket created: {ticket_id}\n"
        f"Title: {title}\n"
        f"Priority: {priority}\n"
        f"Submitted by: {context.user_name}\n"
        f"Status: Open"
    )
```

### 11.3.2 Update IT Agent

```python
from agents import Agent
from context import OfficeContext
from my_tools.it_tools import reset_password, request_permission, create_ticket

it_agent = Agent[OfficeContext](
    name="IT Support",
    instructions="""You are an IT support agent for internal employees.

Available actions:
- reset_password: Reset a user's password (users can only reset their own)
- request_permission: Request access to resources (requires manager approval)
- create_ticket: Create a support ticket for issues

Rules:
- Users can only reset their own password unless they are an admin
- For access requests, always ask for the reason
- Create a ticket for issues that can't be resolved immediately
- Be concise and action-oriented""",
    tools=[reset_password, request_permission, create_ticket],
)
```

---

## 11.4 HR Agent

### 11.4.1 HR Tools

Create `my_tools/hr_tools.py`:

```python
from agents import function_tool, RunContextWrapper
from context import OfficeContext


_POLICIES = {
    "remote work": "Remote work is allowed up to 3 days/week with manager approval. Full-remote requires VP approval.",
    "leave policy": "Annual leave: 15 days (standard), 20 days (5+ years), 25 days (10+ years). Sick leave: 10 days/year.",
    "dress code": "Business casual Monday-Thursday, casual Friday. Client-facing days: business formal.",
    "expense policy": "Expenses <¥500: auto-approved. ¥500-5000: manager approval. >¥5000: VP approval.",
}


_LEAVE_BALANCE = {
    "Alice": {"annual": 12, "sick": 8},
    "Bob": {"annual": 18, "sick": 10},
}


@function_tool
async def lookup_policy(ctx: RunContextWrapper[OfficeContext], topic: str) -> str:
    """Look up a company policy by topic (e.g., 'remote work', 'leave policy')."""
    topic_lower = topic.lower()
    for key, value in _POLICIES.items():
        if topic_lower in key or key in topic_lower:
            return f"Policy: {key}\n{value}"
    return f"No policy found for '{topic}'. Available topics: {', '.join(_POLICIES.keys())}"


@function_tool
async def check_leave(ctx: RunContextWrapper[OfficeContext], employee_name: str) -> str:
    """Check an employee's leave balance."""
    context = ctx.context
    if employee_name.lower() != context.user_name.lower() and context.role.value not in ("manager", "admin"):
        return "Permission denied: you can only check your own leave balance."
    balance = _LEAVE_BALANCE.get(employee_name, {"annual": 15, "sick": 10})
    return f"Leave balance for {employee_name}: Annual={balance['annual']} days, Sick={balance['sick']} days"


@function_tool
async def onboard_employee(
    ctx: RunContextWrapper[OfficeContext],
    new_employee_name: str,
    department: str,
    start_date: str,
) -> str:
    """Start the onboarding process for a new employee. Requires HR admin approval."""
    context = ctx.context
    if context.role.value not in ("manager", "admin"):
        return "Permission denied: only managers and admins can initiate onboarding."
    return (
        f"Onboarding initiated for {new_employee_name}\n"
        f"Department: {department}\n"
        f"Start date: {start_date}\n"
        f"Checklist: email setup, equipment request, access provisioning, orientation scheduling"
    )
```

### 11.4.2 Update HR Agent

```python
from agents import Agent
from context import OfficeContext
from my_tools.hr_tools import lookup_policy, check_leave, onboard_employee

hr_agent = Agent[OfficeContext](
    name="HR Assistant",
    instructions="""You are an HR assistant for internal employees.

Available actions:
- lookup_policy: Look up company policies by topic
- check_leave: Check leave balance (employees can only see their own)
- onboard_employee: Start onboarding (managers/admins only)

Rules:
- Employees can only check their own leave balance
- Only managers and admins can initiate onboarding
- Be helpful but enforce access controls
- Reference specific policies when answering questions""",
    tools=[lookup_policy, check_leave, onboard_employee],
)
```

---

## 11.5 Finance Agent

### 11.5.1 Finance Tools

Create `my_tools/finance_tools.py`:

```python
from agents import function_tool, RunContextWrapper
from context import OfficeContext


_BUDGETS = {
    "engineering": {"total": 500000, "spent": 320000},
    "marketing": {"total": 300000, "spent": 180000},
    "hr": {"total": 200000, "spent": 95000},
}


@function_tool
async def check_budget(ctx: RunContextWrapper[OfficeContext], department: str) -> str:
    """Check a department's budget allocation and remaining funds."""
    context = ctx.context
    dept_lower = department.lower()
    if dept_lower != context.department.value and context.role.value not in ("manager", "admin"):
        return f"Permission denied: you can only view your own department's budget."
    budget = _BUDGETS.get(dept_lower)
    if not budget:
        return f"No budget data found for department '{department}'."
    remaining = budget["total"] - budget["spent"]
    return (
        f"Budget for {dept_lower}:\n"
        f"  Total: ¥{budget['total']:,.0f}\n"
        f"  Spent: ¥{budget['spent']:,.0f}\n"
        f"  Remaining: ¥{remaining:,.0f} ({remaining/budget['total']*100:.0f}%)"
    )


@function_tool
async def query_expense(ctx: RunContextWrapper[OfficeContext], expense_id: str) -> str:
    """Query the status of an expense report."""
    return f"Expense {expense_id}: Status=Approved, Amount=¥1,200, Category=Travel, Submitted=2025-01-10"


@function_tool
async def submit_refund(
    ctx: RunContextWrapper[OfficeContext],
    amount: str,
    reason: str,
    order_id: str = "",
) -> str:
    """Submit a refund request. Requires approval based on amount."""
    context = ctx.context
    try:
        amount_val = float(amount.replace("¥", "").replace(",", ""))
    except ValueError:
        return f"Invalid amount: {amount}. Please provide a numeric value."

    if amount_val < 5000:
        approval = "auto-approved"
    elif amount_val < 50000:
        approval = "pending manager approval"
    else:
        approval = "pending VP approval"

    refund_id = f"REF-{hash(reason) % 10000:04d}"
    return (
        f"Refund submitted: {refund_id}\n"
        f"Amount: ¥{amount_val:,.0f}\n"
        f"Reason: {reason}\n"
        f"Requester: {context.user_name} ({context.department.value})\n"
        f"Status: {approval}"
    )
```

### 11.5.2 Update Finance Agent

```python
from agents import Agent
from context import OfficeContext
from my_tools.finance_tools import check_budget, query_expense, submit_refund

finance_agent = Agent[OfficeContext](
    name="Finance Assistant",
    instructions="""You are a finance assistant for internal employees.

Available actions:
- check_budget: View department budget (employees: own dept only; managers/admins: any dept)
- query_expense: Check expense report status
- submit_refund: Submit a refund request (approval level based on amount)

Approval tiers:
- <¥5,000: auto-approved
- ¥5,000-50,000: manager approval
- >¥50,000: VP approval

Rules:
- Employees can only view their own department's budget
- Always confirm amounts before submitting refunds
- Be precise with numbers""",
    tools=[check_budget, query_expense, submit_refund],
)
```

---

## 11.6 Knowledge Base Agent

### 11.6.1 KB Tools

Create `my_tools/kb_tools.py`:

```python
from agents import function_tool, RunContextWrapper
from context import OfficeContext


_DOCS = {
    "onboarding guide": "New employee onboarding: 1) Complete HR paperwork 2) IT setup (email, VPN, equipment) 3) Manager intro 4) 30-day check-in",
    "vpn setup": "VPN Setup: 1) Download client from IT portal 2) Use your AD credentials 3) Select 'Corporate-Internal' profile 4) Contact IT if MFA fails",
    "expense process": "Expense Process: 1) Submit via ExpensePortal 2) Attach receipts 3) Manager approves 4) Finance processes within 5 business days",
    "org chart": "CEO → VP Engineering / VP Product / VP Sales / CFO / CHRO. Engineering: 3 teams (Platform, Mobile, Infra). Product: 2 teams (Consumer, Enterprise).",
    "holiday calendar": "2025 Company Holidays: Jan 1 (New Year), Jan 28-31 (Spring Festival), Apr 4 (Qingming), May 1-3 (Labor Day), Jun 2 (Dragon Boat), Oct 1-7 (National Day)",
}


@function_tool
async def search_docs(ctx: RunContextWrapper[OfficeContext], query: str) -> str:
    """Search internal documentation by keyword or topic."""
    query_lower = query.lower()
    results = []
    for title, content in _DOCS.items():
        if query_lower in title or any(word in content.lower() for word in query_lower.split()):
            results.append(f"📄 {title}:\n   {content}")
    if results:
        return "\n\n".join(results)
    return f"No documents found for '{query}'. Try: {', '.join(_DOCS.keys())}"


@function_tool
async def lookup_process(ctx: RunContextWrapper[OfficeContext], process_name: str) -> str:
    """Look up a company process or workflow by name."""
    return await search_docs(ctx, process_name)
```

### 11.6.2 Update KB Agent

```python
from agents import Agent
from context import OfficeContext
from my_tools.kb_tools import search_docs, lookup_process

kb_agent = Agent[OfficeContext](
    name="Knowledge Base",
    instructions="""You are a knowledge base assistant for internal company information.

Available actions:
- search_docs: Search internal documentation by keyword
- lookup_process: Look up a specific process or workflow

Rules:
- Always search the docs before answering from memory
- If no docs match, suggest what topics are available
- Provide direct, actionable answers
- Reference the document name when quoting content""",
    tools=[search_docs, lookup_process],
)
```

---

## 11.7 Permission Isolation

Different users should see different data even when talking to the **same agent**. We implement this at two levels:

```
┌────────────────────────────────────────────────────────────────────┐
│              Permission Isolation: Two Layers                       │
├──────────────────────┬─────────────────────────────────────────────┤
│  Layer 1: Tool-level │  Each tool checks ctx.context.role and      │
│  (fine-grained)      │  ctx.context.department before returning    │
│                      │  data. E.g., check_budget only shows your   │
│                      │  own department unless you're a manager.    │
├──────────────────────┼─────────────────────────────────────────────┤
│  Layer 2: Guardrail  │  @input_guardrail blocks requests from      │
│  (coarse-grained)    │  unauthorized roles entirely. E.g., only    │
│                      │  admins can access finance agent for        │
│                      │  cross-department queries.                  │
└──────────────────────┴─────────────────────────────────────────────┘
```

### 11.7.1 Input Guardrail — Restrict Agent Access

Create `guardrails.py`:

```python
from agents import GuardrailFunctionOutput, input_guardrail, RunContextWrapper, Agent
from context import OfficeContext


@input_guardrail(name="finance_access_check")
async def finance_access_guardrail(
    ctx: RunContextWrapper[OfficeContext],
    agent: Agent,
    input: str | list,
) -> GuardrailFunctionOutput:
    context = ctx.context
    if agent.name == "Finance Assistant" and context.role.value == "employee":
        text = input if isinstance(input, str) else str(input)
        restricted = ["other department", "all departments", "company budget", "total budget"]
        text_lower = text.lower()
        if any(kw in text_lower for kw in restricted):
            return GuardrailFunctionOutput(
                tripwire_triggered=True,
                output_info={"reason": f"Employee role cannot access cross-department financial data"},
            )
    return GuardrailFunctionOutput(tripwire_triggered=False, output_info={"checked": True})


@input_guardrail(name="hr_admin_check")
async def hr_admin_guardrail(
    ctx: RunContextWrapper[OfficeContext],
    agent: Agent,
    input: str | list,
) -> GuardrailFunctionOutput:
    context = ctx.context
    if agent.name == "HR Assistant":
        text = input if isinstance(input, str) else str(input)
        admin_actions = ["onboard", "terminate", "salary", "compensation"]
        text_lower = text.lower()
        if any(kw in text_lower for kw in admin_actions):
            if context.role.value not in ("manager", "admin"):
                return GuardrailFunctionOutput(
                    tripwire_triggered=True,
                    output_info={"reason": f"{context.role.value} role cannot perform admin HR actions"},
                )
    return GuardrailFunctionOutput(tripwire_triggered=False, output_info={"checked": True})
```

### 11.7.2 Attach Guardrails to Specialist Agents

```python
from guardrails import finance_access_guardrail, hr_admin_guardrail

it_agent = Agent[OfficeContext](
    name="IT Support",
    instructions="...",
    tools=[reset_password, request_permission, create_ticket],
    input_guardrails=[],
)

hr_agent = Agent[OfficeContext](
    name="HR Assistant",
    instructions="...",
    tools=[lookup_policy, check_leave, onboard_employee],
    input_guardrails=[hr_admin_guardrail],
)

finance_agent = Agent[OfficeContext](
    name="Finance Assistant",
    instructions="...",
    tools=[check_budget, query_expense, submit_refund],
    input_guardrails=[finance_access_guardrail],
)
```

---

## 11.8 Multi-Level Approval

The Finance Agent's `submit_refund` tool already has tiered approval logic in its instructions. But for **actual enforcement**, we use `needs_approval` with a callable that checks the amount:

### 11.8.1 Conditional Approval for Refunds

```python
from agents import function_tool, RunContextWrapper
from context import OfficeContext


async def refund_needs_approval(ctx: RunContextWrapper[OfficeContext], params: dict, _call_id: str) -> bool:
    amount_str = params.get("amount", "0")
    try:
        amount_val = float(str(amount_str).replace("¥", "").replace(",", ""))
    except ValueError:
        return False
    return amount_val >= 5000


@function_tool(needs_approval=refund_needs_approval)
async def submit_refund(
    ctx: RunContextWrapper[OfficeContext],
    amount: str,
    reason: str,
    order_id: str = "",
) -> str:
    """Submit a refund request. Refunds >=¥5,000 require manager approval."""
    context = ctx.context
    try:
        amount_val = float(amount.replace("¥", "").replace(",", ""))
    except ValueError:
        return f"Invalid amount: {amount}. Please provide a numeric value."

    refund_id = f"REF-{hash(reason) % 10000:04d}"
    return (
        f"Refund approved: {refund_id}\n"
        f"Amount: ¥{amount_val:,.0f}\n"
        f"Reason: {reason}\n"
        f"Requester: {context.user_name} ({context.department.value})"
    )
```

### 11.8.2 🔥 Three-Tier Approval Flow

```
  User: "Submit a refund for ¥8,000 for conference travel"
         │
         ▼
  ┌─ Finance Agent ──────────────────────────────────────────┐
  │  LLM calls submit_refund(amount="8000", reason="conf..") │
  │  → refund_needs_approval(params) → True (¥8000 ≥ ¥5000) │
  │  → PAUSE ⏸️                                              │
  └───────────────────────────────────────────────────────────┘
         │
         ▼
  result.interruptions = [ToolApprovalItem(
    tool_name="submit_refund",
    arguments='{"amount":"8000","reason":"conference travel"}'
  )]
         │
         ▼
  ┌─ Approval Decision ──────────────────────────────────────┐
  │  ¥5,000-50,000 → Manager approval                        │
  │  >¥50,000 → VP approval                                  │
  │                                                           │
  │  Manager approves: state.approve(interruption)            │
  │  → Runner.run(agent, state) → tool executes               │
  └───────────────────────────────────────────────────────────┘
```

---

## 11.9 Cross-Agent Memory

When the Triage Agent hands off to a specialist, the conversation continues in the same session. The specialist sees the full history.

### 11.9.1 Session with Handoffs

```python
from agents import SQLiteSession

session = SQLiteSession("user-alice-session", db_path="office_sessions.db")

result = await Runner.run(triage_agent, "I forgot my password", context=ctx, session=session)
# → Triage hands off to IT → IT resets password

result = await Runner.run(triage_agent, "Also check my leave balance", context=ctx, session=session)
# → Triage hands off to HR → HR sees "Alice" from context, checks leave
```

### 11.9.2 Handoff Input Filter

By default, the specialist agent sees the **entire conversation history** including the Triage Agent's messages. For a cleaner experience, use `remove_all_tools` to strip tool call details:

```python
from agents import handoff
from agents.extensions.handoff_filters import remove_all_tools

handoff(it_agent, input_filter=remove_all_tools)
```

This removes tool call items from the history, so the specialist only sees the human-readable conversation.

### 11.9.3 🔥 Cross-Agent Memory Flow

```
  Turn 1: "I forgot my password"
         │
         ▼
  ┌─ Triage ──handoff──▶ IT Support ────────────────────────┐
  │  IT: reset_password("Alice") → "Reset link sent"        │
  │  Session stores: [user_msg, handoff, IT_tool, IT_reply]  │
  └──────────────────────────────────────────────────────────-┘
         │
         ▼
  Turn 2: "Also check my leave balance"
         │
         ▼
  ┌─ Triage ──handoff──▶ HR Assistant ──────────────────────┐
  │  HR sees session history: knows user is Alice,           │
  │  just had a password reset                               │
  │  HR: check_leave("Alice") → "Annual=12, Sick=8"         │
  └──────────────────────────────────────────────────────────-┘
```

---

## 11.10 Cost Monitoring

With multiple agents in a single run, you need **per-agent token tracking** to understand which specialist is most expensive.

### 11.10.1 Per-Agent Cost Hooks

Create `hooks.py`:

```python
import time
from agents import RunHooksBase, RunContextWrapper, AgentHookContext, Agent, Tool
from context import OfficeContext


DOUBAO_PRICE_PER_MILLION_INPUT = 4.0
DOUBAO_PRICE_PER_MILLION_OUTPUT = 16.0


class OfficeHooks(RunHooksBase[OfficeContext, Agent]):
    def __init__(self):
        self._agent_start_times: dict[str, float] = {}
        self._agent_costs: dict[str, dict] = {}

    def _ensure_agent_entry(self, agent_name: str):
        if agent_name not in self._agent_costs:
            self._agent_costs[agent_name] = {
                "calls": 0,
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0,
                "time": 0.0,
            }

    async def on_agent_start(
        self, ctx: AgentHookContext[OfficeContext], agent: Agent[OfficeContext]
    ) -> None:
        self._agent_start_times[agent.name] = time.time()
        self._ensure_agent_entry(agent.name)
        self._agent_costs[agent.name]["calls"] += 1

    async def on_handoff(
        self,
        ctx: RunContextWrapper[OfficeContext],
        from_agent: Agent[OfficeContext],
        to_agent: Agent[OfficeContext],
    ) -> None:
        print(f"[Handoff] {from_agent.name} → {to_agent.name}")

    async def on_agent_end(
        self,
        ctx: AgentHookContext[OfficeContext],
        agent: Agent[OfficeContext],
        output,
    ) -> None:
        elapsed = time.time() - self._agent_start_times.get(agent.name, time.time())
        usage = ctx.usage
        cost = (usage.input_tokens / 1e6) * DOUBAO_PRICE_PER_MILLION_INPUT + \
               (usage.output_tokens / 1e6) * DOUBAO_PRICE_PER_MILLION_OUTPUT

        entry = self._agent_costs[agent.name]
        entry["total_tokens"] += usage.total_tokens
        entry["input_tokens"] += usage.input_tokens
        entry["output_tokens"] += usage.output_tokens
        entry["cost"] += cost
        entry["time"] += elapsed

    def print_summary(self):
        print("\n" + "=" * 60)
        print("  Per-Agent Cost Summary")
        print("=" * 60)
        total_cost = 0.0
        for name, data in sorted(self._agent_costs.items()):
            total_cost += data["cost"]
            print(
                f"  {name:20s} | Calls: {data['calls']:2d} | "
                f"Tokens: {data['total_tokens']:6d} | "
                f"Cost: ¥{data['cost']:.4f} | "
                f"Time: {data['time']:.2f}s"
            )
        print(f"  {'TOTAL':20s} | {'':7s} | {'':14s} | Cost: ¥{total_cost:.4f}")
        print("=" * 60)
```

### 11.10.2 Usage

```python
hooks = OfficeHooks()

result = await Runner.run(
    triage_agent,
    "I need to reset my password",
    context=ctx,
    hooks=hooks,
)

hooks.print_summary()
```

Example output:

```
============================================================
  Per-Agent Cost Summary
============================================================
  Triage Agent         | Calls:  1 | Tokens:    89 | Cost: ¥0.0007 | Time: 0.45s
  IT Support           | Calls:  1 | Tokens:   245 | Cost: ¥0.0019 | Time: 1.84s
  TOTAL                |          |               | Cost: ¥0.0026
============================================================
```

---

## 11.11 Error & Retry

### 11.11.1 Rate Limit Handling (Doubao 429)

With multiple agents making concurrent LLM calls, rate limits are more likely. Use `ModelRetrySettings` on the `RunConfig` so it applies to all agents:

```python
from agents import RunConfig, ModelSettings, ModelRetrySettings, retry_policies

run_config = RunConfig(
    model_settings=ModelSettings(
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
        )
    )
)

result = await Runner.run(
    triage_agent,
    user_input,
    context=ctx,
    session=session,
    hooks=hooks,
    run_config=run_config,
)
```

### 11.11.2 Tool Failure Recovery

Add `failure_error_function` to critical tools:

```python
@function_tool(
    failure_error_function=lambda ctx, error: (
        f"IT system temporarily unavailable: {error}. "
        "A ticket has been auto-created. IT will follow up within 1 hour."
    )
)
async def reset_password(ctx: RunContextWrapper[OfficeContext], username: str) -> str:
    ...
```

### 11.11.3 MaxTurns Handler

In a multi-agent flow, the Triage → Specialist → back-to-Triage loop can exceed max turns. Add a `RunErrorHandlers`:

```python
from agents import RunErrorHandlers, RunErrorHandlerInput, RunErrorHandlerResult

async def handle_max_turns(
    input: RunErrorHandlerInput,
) -> RunErrorHandlerResult:
    return RunErrorHandlerResult(
        final_output="I'm sorry, I wasn't able to fully resolve your request. Your ticket has been escalated to a human agent.",
    )

error_handlers = RunErrorHandlers(max_turns=handle_max_turns)
```

---

## 11.12 Complete System

### 11.12.1 my_agents/__init__.py — Wire Everything Together

```python
from agents import handoff
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from agents.extensions.handoff_filters import remove_all_tools
from context import OfficeContext
from my_tools.it_tools import reset_password, request_permission, create_ticket
from my_tools.hr_tools import lookup_policy, check_leave, onboard_employee
from my_tools.finance_tools import check_budget, query_expense, submit_refund
from my_tools.kb_tools import search_docs, lookup_process
from guardrails import finance_access_guardrail, hr_admin_guardrail


def create_all_agents():
    it_agent = Agent[OfficeContext](
        name="IT Support",
        instructions="""You are an IT support agent. Help with password resets, access requests, and support tickets.
Rules: Users can only reset their own password. Always ask for a reason on access requests. Create tickets for unresolved issues.""",
        tools=[reset_password, request_permission, create_ticket],
    )

    hr_agent = Agent[OfficeContext](
        name="HR Assistant",
        instructions="""You are an HR assistant. Help with policies, leave balance, and onboarding.
Rules: Employees can only check their own leave. Only managers/admins can onboard. Reference specific policies.""",
        tools=[lookup_policy, check_leave, onboard_employee],
        input_guardrails=[hr_admin_guardrail],
    )

    finance_agent = Agent[OfficeContext](
        name="Finance Assistant",
        instructions="""You are a finance assistant. Help with budgets, expenses, and refunds.
Approval tiers: <¥5K auto, ¥5K-50K manager, >¥50K VP. Employees see only their own department budget. Confirm amounts before submitting.""",
        tools=[check_budget, query_expense, submit_refund],
        input_guardrails=[finance_access_guardrail],
    )

    kb_agent = Agent[OfficeContext](
        name="Knowledge Base",
        instructions="""You are a knowledge base assistant. Search docs and look up processes.
Always search before answering. Reference document names. Suggest available topics if nothing matches.""",
        tools=[search_docs, lookup_process],
    )

    triage_agent = Agent[OfficeContext](
        name="Triage Agent",
        instructions=prompt_with_handoff_instructions(
            """You are the unified entry point for all internal company requests.

Route to the right specialist:
- IT Support: password, access, software/hardware issues
- HR Assistant: leave, benefits, policies, onboarding
- Finance Assistant: budget, expenses, refunds
- Knowledge Base: docs, processes, org charts, general info

If ambiguous, ask a brief clarifying question. Handle the primary concern first.
Do NOT mention the handoff mechanism to the user."""
        ),
        handoffs=[
            handoff(it_agent, tool_description_override="Transfer to IT Support for technical issues"),
            handoff(hr_agent, tool_description_override="Transfer to HR for leave, benefits, policies"),
            handoff(finance_agent, tool_description_override="Transfer to Finance for budget, expenses, refunds"),
            handoff(kb_agent, tool_description_override="Transfer to Knowledge Base for docs and processes"),
        ],
    )

    return triage_agent, it_agent, hr_agent, finance_agent, kb_agent
```

### 11.12.2 main.py — Full Interactive System

```python
import asyncio
from agents import (
    Runner, SQLiteSession, RunConfig, RunState,
    RunErrorHandlers, RunErrorHandlerInput, RunErrorHandlerResult,
    ModelSettings, ModelRetrySettings, retry_policies,
    InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered,
)
from config import setup_doubao
from context import OfficeContext
from my_agents import create_all_agents
from hooks import OfficeHooks


async def handle_max_turns(input: RunErrorHandlerInput) -> RunErrorHandlerResult:
    return RunErrorHandlerResult(
        final_output="I wasn't able to fully resolve your request. A human agent will follow up.",
    )


async def run_with_approval(agent, user_input, ctx, session, hooks, run_config, error_handlers):
    result = await Runner.run(
        agent, user_input,
        context=ctx, session=session, hooks=hooks,
        run_config=run_config, error_handlers=error_handlers,
    )

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
                state.reject(interruption, rejection_message="Action rejected by reviewer.")
                print("   ❌ Rejected")

        result = await Runner.run(
            agent, state,
            hooks=hooks, run_config=run_config, error_handlers=error_handlers,
        )

    return result


async def main():
    setup_doubao()

    triage_agent, *_ = create_all_agents()
    hooks = OfficeHooks()

    run_config = RunConfig(
        model_settings=ModelSettings(
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
            )
        )
    )

    error_handlers = RunErrorHandlers(max_turns=handle_max_turns)

    ctx = OfficeContext(
        user_id="U-001",
        user_name="Alice",
        role="employee",
        department="engineering",
    )

    session = SQLiteSession("user-alice-office", db_path="office_sessions.db")

    print("=" * 60)
    print("  Office Assistant (Doubao-powered Multi-Agent)")
    print("  Type 'quit' to exit, 'cost' for usage, 'role:<role>' to switch")
    print("=" * 60)

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            hooks.print_summary()
            break
        if user_input.lower() == "cost":
            hooks.print_summary()
            continue
        if user_input.lower().startswith("role:"):
            new_role = user_input[5:].strip()
            try:
                ctx.role = OfficeContext.__dataclass_fields__["role"].type(new_role)
                print(f"Role switched to: {ctx.role.value}")
            except ValueError:
                print(f"Unknown role. Available: employee, manager, admin")
            continue

        try:
            result = await run_with_approval(
                triage_agent, user_input, ctx, session,
                hooks, run_config, error_handlers,
            )
            print(f"\n🤖 {result.final_output}")
        except InputGuardrailTripwireTriggered:
            print("\n⚠️  You don't have permission for that action. Contact your manager or IT admin.")
        except OutputGuardrailTripwireTriggered:
            print("\n⚠️  I can't display that information due to access restrictions.")
        except Exception as e:
            print(f"\n[Error] {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 11.12.3 Four Scenario Walkthroughs

**Scenario 1: IT Password Reset**

```
You: I forgot my laptop password
[Handoff] Triage Agent → IT Support

🤖 I'll reset your password right away. A reset link has been sent to Alice's email.
    The link expires in 15 minutes. Please check your inbox and spam folder.
```

**Scenario 2: HR Leave Check**

```
You: How many vacation days do I have left?
[Handoff] Triage Agent → HR Assistant

🤖 Your leave balance: Annual=12 days, Sick=8 days. You have plenty of annual leave remaining!
```

**Scenario 3: Finance Refund with Approval**

```
You: Submit a refund for ¥8,000 for conference travel
[Handoff] Triage Agent → Finance Assistant

⚠️  Approval Required: submit_refund
   Arguments: {"amount":"8000","reason":"conference travel"}
   Approve? [y/N/a(always)]: y
   ✅ Approved

🤖 Refund approved: REF-2847
   Amount: ¥8,000
   Reason: conference travel
   Requester: Alice (engineering)
```

**Scenario 4: Permission Denied**

```
You: I want to onboard a new team member
[Handoff] Triage Agent → HR Assistant

⚠️  You don't have permission for that action. Contact your manager or IT admin.

You: role:manager
Role switched to: manager

You: I want to onboard a new team member named Dave in engineering starting Feb 1
[Handoff] Triage Agent → HR Assistant

🤖 Onboarding initiated for Dave
   Department: engineering
   Start date: Feb 1
   Checklist: email setup, equipment request, access provisioning, orientation scheduling
```

---

## 11.13 Key Takeaways

1. **Triage Agent is the single entry point** — It classifies and routes. Give it `prompt_with_handoff_instructions()` and `handoff()` for each specialist. The Triage Agent should have **no tools** of its own.

2. **Handoff descriptions matter** — `tool_description_override` on `handoff()` tells the Triage Agent exactly when to route. Be specific: "Transfer to IT for password, VPN, and software issues" is better than "Transfer to IT".

3. **Permission isolation at two levels** — Tool-level checks (fine-grained, per-action) + guardrail checks (coarse-grained, per-role). Tools handle the happy path; guardrails catch what tools miss.

4. **Conditional approval with callables** — `needs_approval=callable` enables tiered sensitivity: auto-approve small amounts, require human review for large ones. The callable receives `(RunContextWrapper, params_dict, call_id)`.

5. **Cross-agent session memory** — Pass the same `SQLiteSession` to every `Runner.run()`. The specialist sees the full conversation history, so it naturally understands context like "my" and "also".

6. **`remove_all_tools` filter for clean handoffs** — `handoff(agent, input_filter=remove_all_tools)` strips tool calls from history so the specialist only sees human-readable conversation, saving tokens and reducing confusion.

7. **Per-agent cost tracking** — `RunHooksBase` receives `on_handoff` callbacks, so you can track which agents are called most and how much each costs. Essential for production budgeting.

8. **RunConfig applies to all agents** — `ModelRetrySettings` and `call_model_input_filter` on `RunConfig` apply across all agents in the run. This is the right place for rate-limit retry and token budget management.

> **Congratulations!** You've now built three progressively complex systems: a single-agent customer service bot (Ch9), a meeting notes agent with HITL (Ch10), and a full multi-agent office assistant (Ch11). Together with the source code deep dives in Chapters 1-8, you have both the "how it works" and "how to build it" knowledge to ship production-grade agent systems.
