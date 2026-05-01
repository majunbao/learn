---
name: "cookbook-chapter-improver"
description: "Improves OpenAI Agents SDK cookbook chapters: adds source code walkthroughs, flow diagrams, progressive learning structure, and learner-perspective review. Invoke when user wants to rewrite or improve a cookbook chapter."
---

# Cookbook Chapter Improver

This skill transforms superficial cookbook chapters into deep, source-code-driven learning materials for the OpenAI Agents SDK project at `/Users/mayun/Documents/learn/openai-agents-python_tags/openai-agents-python-0.14.6/`.

## When to Invoke

- User wants to rewrite or improve a cookbook chapter
- User says a chapter is "too simple" or "lacks depth"
- User wants to add source code analysis to a chapter
- User wants a learner-perspective review of a chapter

## Workflow

Follow these phases **in order**. Do NOT skip phases.

### Phase 1: Research — Read Everything First

Before writing a single line, you MUST read all of the following:

1. **The target chapter** — read the full current content
2. **Source code files** — use `SearchCodebase` and `Glob` to dynamically discover and read ALL relevant `.py` files under `src/agents/`. Do NOT rely on a fixed list — the SDK evolves and each chapter needs a different set of source files. Start from the chapter's topic keywords and trace imports/call chains to find everything that's relevant. When in doubt, read more rather than less.
3. **Other cookbook chapters** — read all existing chapters to avoid content overlap (check `cookbook/chapter-*.md`)
4. **Official docs** — read corresponding docs under `docs/` for reference

**How to discover relevant source code:**

1. Start from the chapter's main topic (e.g., "Agent" → `agent.py`, "Tools" → `tool.py`)
2. Trace the import chain — when a file imports from another, read that file too
3. Trace the call chain — when a function calls another, read the callee
4. Search for related types — if the chapter mentions `RunResult`, search for all files that reference `RunResult`
5. Check `src/agents/run_internal/` for engine code that powers the public API

**Commonly needed source files** (as a starting point, NOT an exhaustive list):

| Area | Key Files |
|---|---|
| Core | `agent.py`, `run.py`, `result.py`, `run_context.py`, `items.py` |
| Tools | `tool.py`, `function_schema.py`, `tool_context.py`, `tool_guardrails.py` |
| Config | `run_config.py`, `model_settings.py`, `lifecycle.py` |
| Safety | `guardrail.py`, `tool_guardrails.py`, `exceptions.py`, `run_error_handlers.py` |
| Engine | `run_internal/` (run_loop.py, tool_execution.py, turn_resolution.py, guardrails.py, etc.) |
| Output | `agent_output.py`, `usage.py` |
| Memory | `memory/` (SQLiteSession, InMemorySession, etc.) |
| Streaming | `stream_events.py` |
| Handoffs | `handoffs/` |
| Sandbox | `sandbox/` |
| Misc | `retry.py`, `tracing/` |

### Phase 2: First Rewrite — Add Depth

Rewrite the chapter with these principles:

1. **Source Code Walkthroughs** — Add at least 2-3 per chapter. Each walkthrough must:
   - Show **simplified real source code** (not pseudocode, not just type signatures)
   - Add **inline annotations** explaining what each section does
   - End with **numbered key insights** (3-6 per walkthrough)
   - Mark with 🔥 in the heading

2. **Flow Diagrams Before Code** — Before any source code walkthrough, provide a simple ASCII flow diagram to build intuition first. The learner should see the big picture before reading implementation details.

3. **Progressive Disclosure** — Don't dump all information at once. Organize fields/concepts into tiers:
   - "Day one" — what you need immediately
   - "As it grows" — intermediate features
   - "Production hardening" — advanced/production features

4. **Practical Examples** — Every concept should have a runnable code example. Examples should build on each other. Additional rules:
   - **Multi-turn examples must show 3+ rounds.** Two-round examples don't illustrate the pattern well enough. The reader needs to see the repetition to internalize the mechanism. For `to_input_list()`, show at least 4 rounds; for Session and `previous_response_id`, show at least 3 rounds.
   - **"Show, don't tell" for output structures.** When you say "the list grows to include tool calls and tool outputs" or "the output contains X, Y, Z", you MUST show the actual output with a concrete example. Describing what something contains without showing it is the #1 cause of shallow sections. Example: instead of just saying "`to_input_list()` returns a list with tool calls", show the actual list with `function_call` and `function_call_output` entries.

5. **Correct API Usage** — Verify all code against actual source. Common bugs to avoid:
   - `FunctionTool(fn)` constructor → use `@function_tool` decorator instead
   - `RunConfig(model_settings={"temperature": 0.7})` → must be `ModelSettings(temperature=0.7)`
   - `type(item)` vs `type(event.item)` in streaming — check variable names carefully

6. **Merge Thin Sections** — If a section has fewer than 10 lines of substantive content, merge it with a related section.

7. **"How to Read This Chapter"** — Add at the top after the intro paragraph. Three-pass structure with specific navigation:
   - Pass 1: Build intuition — list the exact section sequence. For sections with deep subsections (e.g., RunResult with Guardrail/ContextWrapper subsections), explicitly note which subsections to skip on first pass to avoid information overload
   - Pass 2: Dive into source code — list all 🔥 walkthroughs by section number. Adjust time estimate based on content depth
   - Pass 3: Fill gaps — provide an **itemized list** with one bullet per topic area, each pointing to the specific section(s) and subsections. Do NOT use vague one-liners like "Need context? → 1.8". Instead, be specific: "Context system & dynamic instructions? → 1.8 + 1.9" or "RunResult details (guardrails, context wrapper, methods)? → 1.5 (Guardrail Results, Context Wrapper, Key Methods subsections)"

### Phase 3: Learner-Perspective Review

After the first rewrite, role-play as a **first-time learner** reading the chapter from line 1 to the end. Evaluate:

1. **Learning flow** — Is information introduced in the right order? Are prerequisites met before a concept is used?
2. **Source code clarity** — Are the walkthroughs understandable? Are there unexplained types/functions?
3. **Boundary clarity** — When code calls another function, is it clear who calls whom and why?
4. **Thin sections** — Are any sections still too shallow? Do they need real scenarios or examples?
5. **Bugs** — Any incorrect API usage, wrong variable names, or misleading code?

Write a structured review with:
- Section-by-section notes (✅ good, ⚠️ needs improvement, 🔥 highlight)
- A numbered list of specific improvements
- Any bugs found

### Phase 4: Apply Improvements

Fix every issue found in Phase 3. Common improvements include:

- Adding explanations for unexplained types/functions (e.g., `NextStep*` dataclasses, `run_single_turn` role)
- Replacing `...` in type signatures with actual type names + inline comments
- Adding flow diagrams where code is dumped without prior context
- Expanding thin sections with real-world scenarios
- Fixing variable name bugs in code examples
- Adding boundary explanations (who calls whom)

### Phase 5: Depth Audit — The Systematic Check

After Phase 4, perform a **systematic depth audit** on every section of the chapter. This is the critical step that catches superficial content. For each section, ask:

**"Is this section just a list/table/code snippet, or does it have real source code analysis and practical examples?"**

Specifically check each section for:

1. **Field-by-field deep dives** — When presenting a class (e.g., `RunResultBase`, `Usage`, `ModelSettings`), do NOT just list the fields with one-line comments. Each field should get its own explanation with:
   - What it stores and why it exists
   - Practical example of accessing/using it
   - Non-obvious behavior (e.g., `input` may be mutated by handoff filters)

2. **Method deep dives** — When presenting methods (e.g., `final_output_as()`, `release_agents()`, `to_state()`), do NOT just list them in a code block. Each method should get:
   - Source code walkthrough (simplified from real source)
   - Behavior table for parameters (e.g., `raise_if_incorrect_type` True vs False)
   - When to use guidance
   - Example code

3. **Parameter deep dives** — When presenting a function signature (e.g., `Runner.run()`), do NOT just show the code with inline comments. Explain each parameter with:
   - Type and acceptable values
   - Purpose and default behavior
   - Edge cases (e.g., `input` can be string, list, or RunState)
   - Cross-reference to the section that covers it in detail

4. **Source code for "obvious" things** — Even seemingly simple functions benefit from source code walkthroughs because they reveal non-obvious behavior:
   - `get_system_prompt()` → callable instructions are called **every turn**, not once
   - `ModelSettings.resolve()` → only non-None values from override are applied
   - `last_response_id` → returns None if no raw_responses exist
   - `RunItemBase.release_agent()` → uses weakref pattern for memory management

5. **Comparison tables** — When there are two or more similar/related concepts, always provide a comparison table:
   - `RunResult` vs `RunResultStreaming`
   - `RunContextWrapper` vs `AgentHookContext`
   - Static vs Dynamic vs None instructions
   - `cancel("immediate")` vs `cancel("after_turn")`
   - Session backends (SQLite vs InMemory vs Redis vs SQLAlchemy vs Encrypted)

6. **Cross-reference deduplication** — When a concept is explained in detail in one section, do NOT repeat the full explanation in another section. Instead:
   - Briefly mention the concept with a reference ("as we saw in section X")
   - Add only the NEW perspective or use case
   - Example: `RunContextWrapper` is fully explained in 1.5 (RunResult section). In 1.8 (Context System), reference that explanation and focus on `AgentHookContext` difference and `inspect.signature()` tool injection.

7. **Practical patterns** — For features like streaming, don't stop at event type tables. Provide:
   - Real-time text display example (the most common use case)
   - Cancel mechanism with mode comparison table
   - Silent failure detection (e.g., `run_loop_exception`)

8. **Complete exception hierarchies** — When showing exception trees, include ALL subclasses from the source code (e.g., `ToolInputGuardrailTripwireTriggered`, `ToolOutputGuardrailTripwireTriggered`, `MCPToolCancellationError`), not just the most common ones. For important exceptions:
   - Show the source code with fields
   - Provide a usage example (e.g., accessing `exception.run_data`)

9. **Section depth balance** — After deepening individual sections, check that ALL sections have comparable depth. Count lines per section and look for outliers. If one section is 267 lines with 5 sub-headings while another is 49 lines with none, the thin section needs expansion. Target: every substantive section (except intro/summary) should have 100+ lines and at least 1 sub-heading.

10. **Hidden internal mechanisms** — Some SDK behaviors are controlled by internal mechanisms that aren't obvious from the public API. These MUST be explained because they affect runtime behavior:
    - `_is_wrapped` in `AgentOutputSchema` — some types get wrapped in `{"response": ...}`
    - `strict_json_schema` — controls whether Structured Outputs mode is enabled
    - `_fork_with_tool_input()` / `_fork_without_tool_input()` — how context is shared across tool calls
    - `_approvals` dict — how tool approval state persists across the run
    - `ensure_strict_json_schema()` — how schemas are made strict-compatible
    For each internal mechanism, show the source code and explain the user-visible impact.

11. **Feature lifecycles** — When presenting a feature (e.g., Session, streaming, handoffs), don't just show usage code. Show the **internal lifecycle** with an ASCII flow diagram:
    - Session: `get_items() → prepend to input → run agent → add_items() → return result`
    - Streaming: `run_streamed() → background task → event queue → stream_events() → complete`
    - Tool execution: `guardrails → hooks.on_tool_start → invoke function → guardrails → hooks.on_tool_end → return result`

12. **"Putting it together" sections need post-run analysis** — Complete example sections should NOT end with just the code. Add a "What Happens When You Run This" subsection that walks through how to inspect the `RunResult`:
    - How to access structured output
    - How many turns were taken
    - What items were generated (with expected types)
    - Token usage breakdown
    - Which agent handled the request (relevant for handoffs)
    - Guardrail check results
    This teaches the reader the debugging pattern: `RunResult` is your complete audit trail.

Write a structured audit report in TWO parts. **Do NOT skip Part 2.**

**Part 1 — Section-by-section verdicts:**
- List each section with line count and verdict: ✅ deep enough, ⚠️ needs depth, ❌ superficial
- For each ⚠️/❌ section, specify exactly what's missing (field deep dive, method walkthrough, comparison table, lifecycle diagram, post-run analysis, etc.)

**Part 2 — Checklist-by-checklist pass (MANDATORY, do NOT skip):**
Go through ALL 17 checklist items one by one. For each item, write:
- ✅ if the chapter fully satisfies the check, with a one-line evidence (e.g., "✅ Class fields: ToolOutputText/ToolOutputImage/ToolOutputFileContent each have field-level explanation in §3.6")
- ❌ if the chapter fails the check, with a specific fix (e.g., "❌ Exception hierarchy: ToolInputGuardrailTripwireTriggered and ToolTimeoutError are mentioned but never shown with source code or fields → add exception tree + catch example to §3.7")
- ⚠️ if partially satisfied (explain what's missing)

This format prevents superficial audits where you just stamp ✅ on every section without actually checking the 17 criteria. If you find yourself writing ✅ for more than 3 checklist items in a row without evidence, you are probably not checking carefully enough.

### Phase 6: Overlap Check

Verify the chapter does NOT overlap with other cookbook chapters:
- Read all other chapter files
- If overlap exists, either: trim the overlap from this chapter (if it belongs elsewhere), or add a cross-reference note like "Chapter X covers Y in depth"

## Depth Audit Checklist

Use this checklist during Phase 5. For each section, verify:

| Check | What to Verify |
|---|---|
| Class fields | Each field has individual explanation + practical example, not just a one-line comment |
| Methods | Each method has source code walkthrough + behavior table + when-to-use + example |
| Function parameters | Each parameter has type, purpose, default, edge cases explained |
| "Obvious" code | Even simple functions have source walkthroughs revealing non-obvious behavior |
| Similar concepts | Comparison table provided when 2+ concepts are related |
| Cross-references | No repeated explanations; reference prior detailed sections |
| Practical patterns | Common use cases (e.g., real-time streaming display) have complete examples |
| Exception hierarchy | Complete tree from source, with source code + examples for important types |
| Session/backend choices | Comparison table with import, storage, and use case |
| Advanced features | Hidden/gem features (e.g., `call_model_input_filter`, `tool_error_formatter`) are documented |
| Section depth balance | Every substantive section has 100+ lines and ≥1 sub-heading; no section is disproportionately thin |
| Internal mechanisms | Hidden mechanisms (`_is_wrapped`, `_fork`, `_approvals`, `strict_json_schema`) are explained with source code |
| Feature lifecycles | Features like Session/Streaming/Handoffs have ASCII lifecycle flow diagrams |
| Post-run analysis | "Putting it together" examples include RunResult inspection walkthrough |
| Multi-turn examples | Multi-turn patterns show 3+ rounds, not just 2 |
| Show-don't-tell | When describing output/data structures, always show a concrete example instead of just listing what's in it |
| "How to Read" sync | After all content changes, verify that Pass 1 skips the right deep subsections, Pass 2 lists all 🔥 walkthroughs, and Pass 3 lists every substantive subsection with a parenthetical detail hint. If you added new sections, exception hierarchies, comparison tables, or multi-turn examples, these MUST appear in the appropriate pass. |

## Important Rules

- **Only modify files within the `cookbook/` directory** unless the user explicitly says otherwise
- **Never delete source code walkthroughs** — they are the core value. Make them stronger, don't remove them
- **Write chapter content in English** — the chapter is a technical document
- **No comments in code** unless explicitly asked (but inline annotations in source code walkthroughs are fine — those are explanatory, not code comments)
- **Code examples must be runnable** — verify imports, variable names, and API usage against actual source
- **Architecture diagrams belong at the END** of a chapter, not the beginning — the learner needs context first
- **Every table needs at least 3 columns** — a 2-column "name/description" table is usually too thin. Add "typical use", "when to choose", "trade-off", or similar context columns
- **Source file references must be accurate** — always verify the file path and line numbers against the actual codebase before citing them
