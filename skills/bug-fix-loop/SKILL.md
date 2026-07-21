---
name: bug-fix-loop
description: Structured bug-fixing with mandatory investigation. Reproduce → Investigate (2-pass, non-negotiable) → Act → Check → Adapt → Report. Use for bugs, crashes, errors, broken behavior, regressions. Do not use for feature requests, code review, or prose changes.
license: Apache-2.0
compatibility: Requires Git. Gigacode (run_workflow) recommended for parallel investigation sub-agents. Works without it via sequential investigation.
metadata:
  author: Jost Faganel
  version: "1.0"
---

# Bug Fix Loop

Structure a bug fix through five disciplined phases, with mandatory investigation before any
code change. The methodology prevents target fixation — the #1 failure mode of AI coding
agents — by requiring a complete two-pass system investigation before writing fix code.

## ⚠️ Investigation Is MANDATORY

You MUST complete the full two-pass investigation (Phase 1) BEFORE writing any fix code.

Target fixation is the most common cause of failed bug fixes. If you find yourself wanting to
"just try this quick fix" — STOP. You are target-fixating. Complete the investigation first.

The investigation phase is not "nice to have" or "if time permits." It is the CORE of this
methodology and cannot be skipped, shortened, or bypassed.

## Activation

Activated by the user via `/bug-fix-loop <bug description>` or the agent offers it when a
bug is described. If no description is provided, ask:

> What bug should I fix? Describe the symptom, expected behavior, and any error messages or
> stack traces.

Do not activate for feature requests, code review, small edits, or prose changes.

## Phase 0 — REPRODUCE

1. Write or locate a minimal reproduction test that demonstrates the bug.
2. Run it to confirm it fails. Record the exact reproduction command.
3. If reproduction fails (the test passes unexpectedly), report this and stop. The bug may
   be environment-specific, intermittent, or already fixed.
4. Record: reproduction command, expected output, actual output, any relevant error
   messages or stack traces.

## Phase 1 — INVESTIGATE (MANDATORY)

Complete two investigation passes before any fix. Dispatch investigation sub-agents for
each pass. When `run_workflow` is available, use a gigacode workflow with `agent_type="investigation"`. Otherwise, dispatch investigation agents sequentially or do the work
yourself.

### Pass 1 — Broad System Understanding

Dispatch two parallel investigation sub-agents. Each explores from a different angle:

- **Architecture and contracts:** Module boundaries, data flow, public APIs, interfaces.
- **Intended behavior:** Relevant documentation, specifications, existing tests.
- **Recent changes:** `git log` on affected files, related commits, PRs, or issues.
- **Analogous code:** Similar patterns in the codebase that work correctly.

Give each sub-agent:
- The bug description and symptoms.
- The affected file paths or module names.
- The reproduction details from Phase 0.
- Instructions to explore the four areas above and produce a structured diagnostic report.

Merge the reports into a single diagnostic brief. The brief must include: relevant
architecture, expected vs observed behavior at key boundaries, recent changes to affected
areas, and analogous working patterns.

### Pass 2 — Error Path Trace + Hypotheses

Dispatch fresh investigation sub-agents with the merged Pass 1 diagnostic brief plus:

- The exact error message and stack trace.
- The reproduction steps from Phase 0.
- The affected code paths identified in Pass 1.

Each sub-agent must:

1. Trace the execution path from entry point to failure location.
2. Check for unexpected causes: configuration, environment variables, data state,
   concurrency, resource exhaustion, dependency version mismatches.
3. Generate and rank 2–3 distinct fix hypotheses with confidence levels and reasoning.

Merge the hypotheses. Present ALL hypotheses to the user before proceeding to Phase 2.

### Scope

- **First attempt:** NEIGHBORHOOD scope — affected file plus direct dependencies (callees,
  callers, imports within the same module).
- **On retry (Phase 4):** escalate to SYSTEM scope — the full codebase.

## Phase 2 — ACT

Only after Phase 1 is complete and all hypotheses have been presented to the user.

1. Select the highest-confidence hypothesis.
2. Implement the fix using normal coding tools. Do not use `git reset --hard`, wildcard
   `git branch -D`, whole-project `rsync --delete`, or any destructive operation.
3. Apply the Rule of Least Leverage: prefer the smallest change that addresses the root
   cause. A one-line fix is better than a ten-line refactor.
4. Document what was changed, which files, and why this approach was chosen.

## Phase 3 — CHECK

1. Run the reproduction test from Phase 0. It must pass.
2. Run the full test suite for the affected module and its direct dependents.
3. Verify no regressions in related functionality.
4. If any check fails, go to Phase 4.

## Phase 4 — ADAPT

If the fix fails any Phase 3 check:
1. Analyze the failure. What did the check reveal that was missed?
2. Escalate the investigation scope from NEIGHBORHOOD to SYSTEM.
3. **Rerun the investigation at system scope.** Dispatch fresh investigation sub-agents
   with the escalated scope (full codebase). Discard neighborhood-level hypotheses — the
   system perspective often reveals different root causes. Each sub-agent must examine
   cross-module interactions, service boundaries, external APIs, data flow, and side
   effects that were invisible at neighborhood scope.
4. **Update and rerank hypotheses** based on the system-scope investigation. Generate new
   hypotheses if the expanded context reveals previously undetectable causes. Present the
   updated ranked list to the user before proceeding.
5. Return to Phase 2 (ACT) with the reranked system-scope hypotheses.
6. Track attempts in conversation context. Maximum two fix attempts.
7. On the second failure, produce a detailed report of what was tried, what was learned,
   and ask the user for direction. Do not loop indefinitely.

## Phase 5 — REPORT

Output a structured report:

```
## Bug Fix Report
- **Bug:** [original description]
- **Root cause:** [what was wrong and why]
- **Fix:** [what was changed, files and line ranges]
- **Verification:** [reproduction test passed, suite results]
- **Attempts:** [N of maximum 2]
```

## Near-Miss Requests

Do NOT activate this skill for:
- "Review this PR" → use the `review` skill instead
- "Build a new calculator module" → This skill is exclusively for bug fixing. Do not use it for new feature implementation.
- "Add a docstring to utils.py" → handle as a normal coding task
- "What does this error mean?" → handle as a normal investigation
- "Refactor the auth module" → handle as a normal coding task
- Prose changes, documentation-only updates, or formatting fixes
