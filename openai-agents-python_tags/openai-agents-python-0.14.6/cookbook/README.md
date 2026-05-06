# OpenAI Agents SDK - Source Code Analysis & Cookbook

## 📖 Table of Contents

### Part I: Source Code Deep Dive (Ch1-8)

| Chapter | Title | Topic | Status |
|---------|-------|-------|--------|
| 1 | Quick Start | Zero To Agent With Full Source Code Understanding | ✅ Complete |
| 2 | Agent Deep Dive | Why a dataclass, not a class? | ✅ Complete |
| 3 | Tool System | FunctionTool internals & calling flow | ✅ Complete |
| 4 | Runner Engine | The core loop in run_internal.py | ✅ Complete |
| 5 | State Management | RunContext & RunState | ✅ Complete |
| 6 | Build Your Own | 100-line mini SDK from scratch | ✅ Complete |
| 7 | Advanced Features | Handoffs, Guardrails, Tracing | ✅ Complete |
| 8 | Patterns & Best Practices | Production grade agent design | ✅ Complete |

### Part II: Project Practice (Ch9-11)

These three chapters use **Doubao (doubao-seed-2.0-pro)** via Volcengine Ark API as the LLM backend, walking you through building real projects from zero to production.

| Chapter | Title | Topic | Status |
|---------|-------|-------|--------|
| 9 | Smart Customer Service | Your first real project: environment setup → single Agent → tools → session → guardrails → full system | 📝 Planned |
| 10 | Meeting Notes Agent | Internal enterprise tool: multi-turn summarization → action extraction → role-based access → HITL review → structured output | 📝 Planned |
| 11 | Multi-Agent Office Assistant | Unified enterprise entry point: Triage → IT/HR/Finance/Knowledge Base agents, permission isolation, approval chains, cost monitoring | 📝 Planned |

| Appendix | Title | Topic | Status |
|----------|-------|-------|--------|
| A | API Quick Reference | Agent, Runner, Tool, Guardrail, Hook cheat sheets | ✅ Complete |

### Chapter 9 Outline: Smart Customer Service

A progressive tutorial from `uv init` to a complete customer service system, using Doubao via OpenAI-compatible Chat Completions API.

| Section | Title | What You Build | Key APIs |
|---------|-------|----------------|----------|
| 9.1 | Environment Setup | uv project, Doubao config, 3 integration methods | `uv add`, `set_default_openai_client`, `OpenAIChatCompletionsModel` |
| 9.2 | First Agent | Minimal runnable agent, verify Doubao connectivity | `Agent`, `Runner.run()` |
| 9.3 | Adding Tools | `lookup_order`, `check_refund` | `@function_tool` |
| 9.4 | Context & Identity | User info injection, tool reads context | `TContext`, `RunContextWrapper` |
| 9.5 | Structured Output | Order receipt as dataclass (JSON Mode workaround for Doubao) | `output_type`, `response_format` |
| 9.6 | Multi-Turn Session | Conversation persistence across calls | `SQLiteSession` |
| 9.7 | Safety Guardrails | Block profanity, prevent refund abuse | `@input_guardrail`, `@output_guardrail` |
| 9.8 | Error Handling | Tool failure recovery, MaxTurns handler, retry for rate limits | `failure_error_function`, `RunErrorHandlers`, `RetryPolicy` |
| 9.9 | Observability | Usage logging, token/cost monitoring | `RunHooks`, `Usage` |
| 9.10 | Complete System | All features combined, 4 scenario walkthroughs | Full integration |
| 9.11 | Key Takeaways | 8 production lessons | — |

### Chapter 10 Outline: Meeting Notes Agent

An internal enterprise tool that processes meeting transcripts, extracts action items, and routes tasks — demonstrating multi-turn flows, permission control, and human review.

| Section | Title | What You Build | Key APIs |
|---------|-------|----------------|----------|
| 10.1 | Project Setup | New uv project, reuse Doubao config from Ch9 | `uv init` |
| 10.2 | Transcript Input Agent | Accept meeting text, generate summary | `Agent`, structured prompt |
| 10.3 | Action Item Extraction | Extract decisions, action items, deadlines, owners | `@function_tool`, `output_type` |
| 10.4 | Role-Based Access | Different output detail levels for boss vs. participant | `TContext`, `RunContextWrapper` |
| 10.5 | Multi-Turn Refinement | "Expand item 3", "Change owner of item 5" | `SQLiteSession`, follow-up turns |
| 10.6 | Output Guardrail | Prevent leaking confidential items to wrong roles | `@output_guardrail` |
| 10.7 | Human Review | Manager reviews extracted items before distribution | `needs_approval`, `RunState` |
| 10.8 | Integration: Write to System | Send items to project tracker (simulated API) | `@function_tool`, `failure_error_function` |
| 10.9 | Complete System | Full pipeline with 3 scenario walkthroughs | Full integration |
| 10.10 | Key Takeaways | 8 internal-tool lessons | — |

### Chapter 11 Outline: Multi-Agent Office Assistant

The enterprise unified entry point — a Triage Agent routes to IT, HR, Finance, and Knowledge Base specialists, with permission isolation, multi-level approval chains, and cost monitoring.

| Section | Title | What You Build | Key APIs |
|---------|-------|----------------|----------|
| 11.1 | Project Setup | New uv project, shared config module | `uv init` |
| 11.2 | Triage Agent | Single agent that classifies and routes | `Agent` with `handoffs` |
| 11.3 | IT Support Agent | Password reset, permission request, ticket creation | `@function_tool`, `handoff_prompt` |
| 11.4 | HR Agent | Onboarding guide, policy lookup, leave balance | `@function_tool`, context-based filtering |
| 11.5 | Finance Agent | Expense check, refund status, budget query | `@function_tool`, structured output |
| 11.6 | Knowledge Base Agent | Internal docs search, process lookup | `@function_tool`, `remove_all_tools` filter |
| 11.7 | Permission Isolation | Same agent, different data visibility by role | `TContext`, `@input_guardrail` |
| 11.8 | Multi-Level Approval | Auto-approve <5k, manager 5k-50k, VP >50k | `needs_approval` callable, `RunState` |
| 11.9 | Cross-Agent Memory | Session persists across handoffs | `SQLiteSession` with handoff filter |
| 11.10 | Cost Monitoring | Per-agent token tracking, budget alerts | `RunHooks`, `Usage`, `call_model_input_filter` |
| 11.11 | Error & Retry | Rate limit handling (Doubao 429), partial failure recovery | `RetryPolicy`, `RunErrorHandlers` |
| 11.12 | Complete System | Full multi-agent system with 4 scenario walkthroughs | Full integration |
| 11.13 | Key Takeaways | 8 multi-agent lessons | — |

## 📁 Files

- [README.md](README.md) - This file
- [chapter-1-quick-start.md](chapter-1-quick-start.md) - Quick start with source code
- [chapter-2-agent-deep-dive.md](chapter-2-agent-deep-dive.md) - Agent internals
- [chapter-3-tool-system.md](chapter-3-tool-system.md) - Tool system deep dive
- [chapter-4-runner-engine.md](chapter-4-runner-engine.md) - Runner core loop
- [chapter-5-state-management.md](chapter-5-state-management.md) - State management
- [chapter-6-build-your-own.md](chapter-6-build-your-own.md) - Mini SDK from scratch
- [chapter-7-advanced-features.md](chapter-7-advanced-features.md) - Advanced features
- [chapter-8-patterns-practices.md](chapter-8-patterns-practices.md) - Patterns & best practices
- [chapter-9-smart-customer-service.md](chapter-9-smart-customer-service.md) - Smart customer service project
- [chapter-10-meeting-notes-agent.md](chapter-10-meeting-notes-agent.md) - Meeting notes agent project
- [chapter-11-multi-agent-office.md](chapter-11-multi-agent-office.md) - Multi-agent office assistant
- [appendix.md](appendix.md) - API quick reference

## About This Book

This cookbook takes you deep into the source code of the OpenAI Agents SDK. You'll not only learn how to use the SDK but also understand *why* it's designed the way it is and *how* it works under the hood.

**Part I (Ch1-8)** reads the SDK's own Python source code line by line. **Part II (Ch9-11)** builds real projects from scratch using Doubao (doubao-seed-2.0-pro) as the LLM backend, progressing from a simple customer service bot to a full multi-agent enterprise system.

## Philosophy

- **Readable Code First** - Every explanation ties directly to the actual source
- **Practical Examples** - Learn by building, not just reading
- **From Simple to Complex** - Start with 100 lines, then understand the full SDK
- **Visual Learning** - Diagrams and flowcharts explain complex systems
- **Real LLM Backend** - Part II uses Doubao (Volcengine Ark API) to demonstrate OpenAI-compatible provider integration

## Who Should Read This?

- Developers who want to deeply understand agent systems
- Engineers building production-grade agent applications
- Anyone curious about how modern LLM frameworks work internally
- Teams adopting the Agents SDK with non-OpenAI LLM providers (especially Chinese LLMs like Doubao)
