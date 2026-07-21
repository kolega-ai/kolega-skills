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

Create 2–3 independent candidate implementations, each in **an isolated workspace**.

**Branch naming convention:** All candidate branches follow the pattern:
`feature/<name>-attempt<A>-candidate<M>`
where `<A>` is the attempt number (starting at 1, incremented on each full retry) and
`<M>` is the candidate index (1..N). This prevents collisions when retrying after failed
attempts.

### Preflight — verify clean working tree

Before creating any workspaces or branches, check for uncommitted changes:
```bash
if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: Working tree is dirty. Commit or stash changes first."
    exit 1
fi
```
If the tree is dirty, stop and ask the user to commit or stash. Do not proceed with
uncommitted changes — they would carry onto candidate workspaces and could be lost.

Identify the starting branch and its HEAD commit:
```bash
ORIGINAL_BRANCH=$(git branch --show-current)
BASE_COMMIT=$(git rev-parse HEAD)
```

### With Gigacode (preferred)

When `run_workflow` is available, dispatch parallel coder sub-agents via
`agent(agent_type="coder")` in a workflow pipeline. **Each agent MUST work in an isolated
directory** — coder agents share one working tree, so parallel implementations of the same
feature will overwrite each other. Never run competing implementations concurrently in the
same working directory.

For each candidate M (1, 2, 3), create an isolated Git worktree from the base commit:
```bash
git worktree add ../feature-<name>-attempt<A>-candidate-M "$BASE_COMMIT"
```
Each agent works inside its own `../feature-<name>-attempt<A>-candidate-M` directory.

If the project is not a Git repository, copy the entire working directory instead:
```bash
cp -r . ../candidate-M
```

Give each coder agent:
- The same CONTRACT.md.
- A unique candidate identifier (candidate-1, candidate-2, candidate-3).
- Its isolated workspace path.
- Instructions to implement the full feature in a single self-contained pass.

After all agents complete, produce a diff from each workspace (against the base commit).
The diffs are the candidate implementations. The workspaces themselves are read-only
after generation — do not merge from them directly.

### Without Gigacode

Generate candidates sequentially using branches on the main working tree.

For each candidate M (1, 2, 3):
1. Create a dedicated branch from the base commit:
   `git checkout -b feature/<name>-attempt<A>-candidate-<M> "$BASE_COMMIT"`
2. Implement the full feature on that branch.
3. Commit the implementation.
4. Switch back to the original branch:
   `git checkout "$ORIGINAL_BRANCH"`

**Safety rules:**
- Never use `git reset --hard` on ORIGINAL_BRANCH.
- Never use wildcard `git branch -D`. Delete only by exact branch name.
- Never use `rsync --delete` or any whole-project destructive operation.

## Phase 2 — VERIFY

Grade each candidate against the CONTRACT.md independently.

Dispatch investigation sub-agents (one per candidate) with:
- The candidate's diff or branch name.
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
2. **Preserve all branches and worktrees.** Do not delete anything until verification
   passes.
3. Check out the winning candidate's workspace (its worktree or branch) and **run the
   full test suite first**, before merging or deleting anything.
4. **On test success:**
   a. Switch back to the original branch:
      `git checkout "$ORIGINAL_BRANCH"`
   b. Merge the winner into the original branch:
      `git merge feature/<name>-attempt<A>-candidate-<W>`
   c. Delete the losing candidate branches by exact name (one at a time):
      `git branch -D feature/<name>-attempt<A>-candidate-<X>`
   d. Delete the winning branch:
      `git branch -D feature/<name>-attempt<A>-candidate-<W>`
   e. Remove losing candidate worktrees (one at a time, exact path):
      `git worktree remove ../feature-<name>-attempt<A>-candidate-<X>`
   f. Remove the winning worktree:
      `git worktree remove ../feature-<name>-attempt<A>-candidate-<W>`
5. **On test failure:**
   - The winner failed. Do NOT delete any branches or worktrees — losing candidates may
     still be viable fallbacks.
   - Try the next-highest-ranked candidate: return to step 3 with candidate-W+1.
   - If no remaining candidate passes, proceed to step 6 (retry).
6. Maximum 3 generation attempts. If all candidates fail verification:
   a. Analyze what was common across failures.
   b. Update CONTRACT.md with refined criteria.
   c. **Clean up every failed attempt branch by exact name** before retrying:
      `git branch -D feature/<name>-attempt<A>-candidate-1`
      (repeat for candidate-2, candidate-3)
   d. **Clean up every failed attempt worktree by exact path:**
      `git worktree remove ../feature-<name>-attempt<A>-candidate-1`
      (repeat for candidate-2, candidate-3)
   e. Increment attempt counter (A = A + 1).
   f. Return to Phase 1 with the updated contract and new attempt number.
7. On the third failure, report findings and ask the user for direction.

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
