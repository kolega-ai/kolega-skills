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

Create 2–3 independent candidate implementations, each in **isolated workspaces**.

**Branch naming convention:** All candidate branches follow the pattern:
`feature/<name>-attempt<A>-candidate<M>` where `<A>` is the attempt number (starting at 1,
incremented on each full retry) and `<M>` is the candidate index (1..N). This prevents
collisions when retrying after failed attempts.

### With Gigacode (preferred)

When `run_workflow` is available, dispatch parallel coder sub-agents via
`agent(agent_type="coder")` in a workflow pipeline. **Each agent MUST work in an isolated
directory** — coder agents share one working tree, so parallel implementations of the same
feature will overwrite each other.

**If the project is a Git repository:**
Create a separate worktree per candidate from the current HEAD:
```bash
git worktree add ../feature-<name>-attempt<A>-candidate-M feature/<name>-base
```
Each agent works inside its own worktree directory.

**If the project is not a Git repository:**
Copy the entire working directory into a dedicated folder per candidate:
```bash
cp -r . ../candidate-M
```
Each agent operates in its corresponding copy.

Give each coder agent:
- The same CONTRACT.md.
- A unique candidate identifier (candidate-1, candidate-2, candidate-3).
- Its isolated workspace path.
- Instructions to implement the full feature in a single self-contained pass.

### Without Gigacode

Generate candidates sequentially using safe branch isolation.

**Preflight — verify clean working tree:**
Before creating any branches, check for uncommitted changes:
```bash
if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: Working tree is dirty. Commit or stash changes first."
    exit 1
fi
```
If the tree is dirty, stop and ask the user to commit or stash. Do not proceed with
uncommitted changes — they would carry onto candidate branches and could be lost.

1. Record the starting branch: `git branch --show-current` and save it as ORIGINAL_BRANCH.
2. For each candidate M (1, 2, 3):
   a. Create a dedicated branch: `git checkout -b feature/<name>-attempt<A>-candidate-<M>`
   b. Implement the full feature on that branch.
   c. Commit the implementation.
   d. Switch back to ORIGINAL_BRANCH before creating the next branch:
      `git checkout <ORIGINAL_BRANCH>`

**Safety rules:**
- Never use `git reset --hard` on ORIGINAL_BRANCH.
- Never use wildcard `git branch -D`. Delete only by exact branch name.
- Never use `rsync --delete` or any whole-project destructive operation.

## Phase 2 — VERIFY

Grade each candidate against the CONTRACT.md independently.

Dispatch investigation sub-agents (one per candidate) with:
- The candidate's branch name or diff.
- The full CONTRACT.md.
- Instructions to check: correctness, completeness, performance, style consistency, test
  coverage, edge case handling, and integration compliance.

Each grader produces a structured verdict:
```
Candidate: <M>
Score: <1–10>
Pass: <yes/no>
Strengths: [list]
Weaknesses: [list]
Notes: [any observations]
```

Merge the grades into a comparison matrix. Present it to the user.

## Phase 3 — SELECT

1. Identify the best candidate (highest verified score among those that pass).
2. **Preserve all branches.** Do not delete anything until verification passes.
3. If using branch isolation:
   a. Switch to the winning branch: `git checkout feature/<name>-attempt<A>-candidate-<W>`
   b. **Run the full test suite first**, before merging or deleting anything.
   c. **On test success:**
      - Switch to ORIGINAL_BRANCH: `git checkout <ORIGINAL_BRANCH>`
      - Merge the winner: `git merge feature/<name>-attempt<A>-candidate-<W>`
      - Delete losing branches by exact name:
        `git branch -D feature/<name>-attempt<A>-candidate-<X>`
      - Delete the winning branch: `git branch -D feature/<name>-attempt<A>-candidate-<W>`
      - Clean up worktrees: `git worktree remove ../feature-<name>-attempt<A>-candidate-*`
   d. **On test failure:**
      - The winner failed. Do NOT delete any branches — losing candidates may still be
        viable fallbacks.
      - Try the next-highest-ranked candidate: return to step 3b with candidate-W+1.
      - If no remaining candidate passes, proceed to step 5 (retry).
4. Maximum 3 generation attempts. If all candidates fail verification:
   a. Analyze what was common across failures.
   b. Update CONTRACT.md with refined criteria.
   c. **Clean up failed attempt branches** by exact name before retrying:
      `git branch -D feature/<name>-attempt<A>-candidate-1` (repeat for each).
   d. Increment attempt counter (A = A + 1).
   e. Return to Phase 1 with the updated contract and new attempt number.
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
- "Fix the login 500 error" → This skill is only for new feature development. Must not be used for bug fixing.
- "Review PR #42" → use the `review` skill instead
- "Rename this variable" → handle as a normal coding task
- "Refactor the auth module" → handle as a normal coding task
- Small single-file edits, documentation updates, or configuration changes
