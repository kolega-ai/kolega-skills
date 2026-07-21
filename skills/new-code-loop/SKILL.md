---
name: new-code-loop
description: Structured feature-building with parallel generation and independent verification. Goal → Generate (parallel candidates) → Verify → Select → Report. Use for new features, modules, components, or significant additions. Do not use for bug fixes, small edits, refactors, or code review.
license: Apache-2.0
compatibility: Requires Git. Gigacode (run_workflow) strongly recommended for parallel candidate generation. Works without it via sequential generation on isolated branches.
metadata:
  author: Jost Faganel
  version: "1.0"
---

# New Code Loop

Build a new feature through five phases with parallel candidate generation and independent
verification. The methodology produces multiple competing implementations and keeps only the
best one, verified against explicit acceptance criteria.

## Activation

Activated by the user via `/new-code-loop <feature description>`. If no description is
provided, ask:

> What feature should I build? Describe the goal, constraints, and acceptance criteria.

Do not activate for bug fixes, small edits, refactors, code review, or prose changes.

## Phase 0 — GOAL

Define specific, verifiable success criteria before any code is written.

1. Create a CONTRACT.md file in the project root (or use conversation context for
   lightweight features) with:
   - **What must work:** Inputs, outputs, and expected behavior.
   - **Constraints:** Performance bounds, memory limits, API compatibility.
   - **Integration points:** Required imports, public signatures, configuration.
   - **Test requirements:** What tests must pass (or be written).
2. Present the CONTRACT.md to the user for confirmation before proceeding.

## Phase 1 — GENERATE

Create 2–3 independent candidate implementations, each in isolation.

### With Gigacode (preferred)

When `run_workflow` is available, dispatch parallel coder sub-agents via
`agent(agent_type="coder")` in a workflow pipeline. Give each coder agent:
- The same CONTRACT.md.
- A unique candidate identifier (candidate-1, candidate-2, candidate-3).
- Instructions to implement the full feature in a single self-contained pass.

Each candidate is produced as a complete diff or branch without interfering with the others.

### Without Gigacode

Generate candidates sequentially using safe branch isolation:

1. Record the starting branch: `git branch --show-current` and save it as ORIGINAL_BRANCH.
2. For each candidate N (1, 2, 3):
   a. Create a dedicated branch: `git checkout -b feature/<name>-candidate-<N>`
   b. Implement the full feature on that branch.
   c. Commit the implementation.
   d. Switch back to ORIGINAL_BRANCH before creating the next branch: `git checkout <ORIGINAL_BRANCH>`
3. All candidates remain on their branches. Never merge until Phase 3.

**Safety rules:**
- Never use `git reset --hard` on ORIGINAL_BRANCH.
- Never use wildcard `git branch -D`. Delete only by exact branch name.
- Never use `rsync --delete` or any whole-project destructive operation.
- Candidate branches are named `feature/<name>-candidate-N` with an exact, predictable
  pattern.

## Phase 2 — VERIFY

Grade each candidate against the CONTRACT.md independently.

Dispatch investigation sub-agents (one per candidate) with:
- The candidate's branch name or diff.
- The full CONTRACT.md.
- Instructions to check: correctness, completeness, performance, style consistency, test
  coverage, edge case handling, and integration compliance.

Each grader produces a structured verdict:
```
Candidate: <N>
Score: <1–10>
Pass: <yes/no>
Strengths: [list]
Weaknesses: [list]
Notes: [any observations]
```

Merge the grades into a comparison matrix. Present it to the user.

## Phase 3 — SELECT

1. Identify the best candidate (highest verified score among those that pass).
2. If using branch isolation:
   a. Switch to ORIGINAL_BRANCH: `git checkout <ORIGINAL_BRANCH>`
   b. Merge the winning branch: `git merge feature/<name>-candidate-<N>`
   c. Delete the losing branches by exact name: `git branch -D feature/<name>-candidate-<X>`
   d. Delete the winning branch after merge: `git branch -D feature/<name>-candidate-<N>`
3. Run the full test suite on the merged result.
4. Maximum 3 generation attempts. If all candidates fail verification:
   a. Analyze what was common across failures.
   b. Update CONTRACT.md with refined criteria.
   c. Return to Phase 1 with the updated contract.
5. On the third failure, report findings and ask the user for direction.

## Phase 4 — REPORT

Output a structured report:

```
## Feature Build Report
- **Feature:** [description]
- **Candidates generated:** [N]
- **Winner:** [candidate identifier]
- **Score:** [verification score]
- **Key strengths:** [list]
- **Verification:** [suite results, any notes]
- **Merged into:** [branch name]
- **Attempts:** [N of maximum 3]
```

## Near-Miss Requests

Do NOT activate this skill for:
- "Fix the login 500 error" → use the `bug-fix-loop` skill instead
- "Review PR #42" → use the `review` skill instead
- "Rename this variable" → handle as a normal coding task
- "Refactor the auth module" → handle as a normal coding task
- Small single-file edits, documentation updates, or configuration changes
