---
name: deep-research
description: >
  Conduct rigorous multi-source investigation and create citation-backed Markdown
  reports with reader-appropriate structure and voice. Use for explicit deep-research
  requests, historical or cultural reports, decision comparisons, disputed claims,
  literature landscapes, and questions requiring source discovery, selective
  verification, synthesis, and uncertainty analysis. Do not use for a single-fact
  lookup, a one-URL summary, routine coding research, or a simple search-result list.
license: Apache-2.0
compatibility: >
  Requires web search and page-reading tools for live research. Best with Kolega
  Code Gigacode workflows and runtime model discovery; prompts to enable Gigacode
  before offering a bounded sequential fallback when orchestration is unavailable.
metadata:
  owner: Kolega
  version: "2.0"
---

# Deep Research

Produce a useful report, not a transcript of research operations. Research only as
widely as the question, stakes, and remaining uncertainty require. Preserve source
quality and uncertainty while adapting the report's shape and voice to its readers.

## Activation examples

Use this skill for requests such as:

- "Run deep research and create a report on Saturnian magic throughout history."
- "Compare these three observability platforms and recommend one for a small
  regulated team."
- "Investigate the disputed claim that this policy reduced housing costs, and show
  what the best evidence supports."

Do not activate it for near misses such as:

- "What year did the policy take effect?" — answer the fact directly.
- "Summarize this one article." — read and summarize that source without a research
  workflow.

## Check Gigacode before research

For every substantive deep-research request, check whether `run_workflow` is
available before acquiring sources. If it is unavailable and the user has not
already requested sequential execution or told you to continue without Gigacode,
pause and offer this choice:

> Gigacode is off. Parallel research is faster and keeps the bounded research lanes
> isolated. Run `/gigacode on` and then resend this research request, or tell me to
> continue without Gigacode.

Do not claim that the skill can execute a TUI slash command itself. Do not start the
sequential fallback until the user chooses it. If the user continues without
Gigacode, do not ask again during that research request. If `run_workflow` is
available, proceed without this prompt; absence of `list_subagent_models` alone does
not mean Gigacode is off.

After this preflight, read
[Evidence and reporting](references/evidence-and-reporting.md) before research.
When Gigacode is available, also read the concise
[Gigacode workflow guide](references/gigacode-workflow.md) and invoke the bundled
[`scripts/deep-research.workflow`](scripts/deep-research.workflow) instead of
generating a new orchestration script.

## 1. Settle the brief and delivery before research

Infer low-risk details; ask only questions whose answers materially change the work.
Record:

- the exact question and decision or reader need;
- audience, timeframe, geography, comparison set, and exclusions;
- requested length and due date, if any;
- report profile and voice;
- whether the question is current, historical, disputed, or high-stakes;
- explicit user formatting requirements; and
- output mode and path.

### Artifact-first delivery

In an edit-enabled session, an explicit report request produces a Markdown file by
default:

1. Honor a user-supplied path.
2. Otherwise derive a short topic slug and announce
   `reports/<topic-slug>.md` before research starts.
3. Never silently overwrite. If the path exists and overwrite was not requested,
   choose `<topic-slug>-2.md`, then `-3`, and so on.
4. Treat conversation-only delivery as an explicit format choice.
5. In read-only mode, return the report in conversation and say that no file could be
   written.

After a workflow run, immediately use
[`scripts/materialize_report.py`](scripts/materialize_report.py) with its
`resultPath`. Verify a nonempty title, body, and exactly one `## Sources` section.
Finish with the report path and a short status; do not paste the full report again.

## 2. Choose proportional effort

Choose by uncertainty and consequence, not by topic breadth alone.

| Tier | Use when | Base lanes | Per-lane acquisition ceiling |
| --- | --- | ---: | --- |
| Focused | Narrow, low-stakes synthesis with modest uncertainty | 2 | 4 searches, 6 fetches |
| Standard | Default multi-source report or comparison | 3–4 | 6 searches, 8 fetches |
| Extended | Explicitly exhaustive, high-stakes, or unusually disputed | 5–6 | 8 searches, 12 fetches |

These are ceilings, never quotas. Stop a lane as soon as its material claims have
adequate support. Lane ownership must be disjoint; do not add a cross-cutting lane
that re-fetches every period or option.

Focused runs skip follow-up research by default. Standard runs may add at most one
follow-up, and only when the gap could change the thesis or recommendation. Extended
runs may use one acquisition escalation under the rules below, not an open-ended
retry chain.

## 3. Plan source classes, not source counts

Before searching, identify the source classes the question needs: primary records,
official data, peer-reviewed analysis, technical documentation, contemporary
reporting, or lived-experience sources. Assign each class to one lane.

Use discovery sources to find authoritative evidence, then cite the authoritative
evidence. Prefer a smaller set of strong, representative citations over collecting
sources to meet a quota.

## 4. Route stages at runtime

When Gigacode and model discovery are available:

1. Call `list_subagent_models` once.
2. Use the user's requested model family when specified; otherwise anchor routing
   to the effective Investigation default's provider and model family.
3. Keep stage roles in that family. Prefer the same exact model with lower effort
   for bounded discovery, extraction, coverage classification, and
   mechanical/editorial checks; next prefer a clearly related faster sibling from
   the same provider and family.
4. Use higher effort or the stronger sibling in that same family for difficult
   conclusion-driving verification, conflict resolution, and synthesis.
5. If family membership is unclear, stay on the same exact model or omit the
   override. Do not assemble a sampler of unrelated providers or model families
   merely to specialize each stage.
6. Cross the family boundary only when the user directs it or the chosen family
   lacks a required capability, such as vision for the one permitted Browser
   escalation. Limit the exception to the affected role and disclose it.
7. Pass only exact configured routes in workflow `args.routes`. If no safe
   same-family alternate is clear, omit that role's override and inherit the
   configured agent-type default.

Never guess a route. Do not copy a provider, model ID, or effort value into this
skill or its resources. Routes are complete runtime values returned by the current
session's discovery tool. A shared provider name alone does not establish a shared
model family; use only an obvious lineage shown by runtime model names, and treat
ambiguous cases as unrelated.

Use read-only Investigation workers for ordinary research. A Browser worker is an
exception for one approved acquisition escalation and requires a runtime-discovered
vision-capable route when an override is used.

## 5. Use the bounded workflow

With Gigacode:

1. Read [`scripts/deep-research.workflow`](scripts/deep-research.workflow) verbatim.
2. Pass it to `run_workflow` with the settled brief, disjoint lanes, tier, ceilings,
   report profile, writing reserve, and optional runtime routes.
3. Use a tier-appropriate budget. Do not increase an exhausted budget by a large
   multiplier without changing scope or workflow shape.
4. On interruption, inspect `resultPath` and `transcriptPath`. Resume only to reuse
   valid persisted calls while narrowing optional work; do not rerun merely to
   recover omitted inline output.
5. Materialize the final or explicitly supported partial report from `resultPath`.

The workflow researches lanes in bounded batches, verifies only important or
disputed claims, constructs its registry and bibliography deterministically, and
uses one ordinary drafting agent. The skill—not the user—decides whether section
fan-out is warranted after coverage analysis. It uses sections for an explicitly
long report, usually around 5,000 words or more, or when the verified evidence
separates into genuinely independent sections that benefit from bounded parallel
drafting. A synthesis pass then unifies argument, transitions, voice, and citations.

### Sequential fallback

If Gigacode is unavailable and the user chooses to continue without it:

1. Research the same 2–6 disjoint lanes sequentially with the same ceilings.
2. Keep one compact source/evidence registry and failed-acquisition ledger.
3. Verify only conclusion-driving or disputed claims with genuinely independent
   support.
4. Run one combined evidence/editorial audit for Focused or Standard work.
5. Revise only if the audit finds a material problem.
6. Construct `## Sources` from URLs actually cited in the final body.
7. Write the report directly using the artifact-first path rules.

Orchestration improves speed and cost control; its absence must not weaken the
evidence standard or prevent delivery.

## 6. Stop failed acquisition quickly

Every worker prompt must carry these rules:

- Never repeat an identical query.
- Never retry a terminally failed URL by changing only protocol, anchor, query
  string, or endpoint shape.
- Treat 403/404, login/paywall, robots denial, certificate failure, unsupported
  type, oversized document, and scanned/no-text results as terminal for that source.
- For a conclusion-driving source, try at most one obvious accessible equivalent.
- Retry a transient timeout once, then move on.
- Pass failures to verification; verifiers must not retry known failures or broadly
  re-fetch every scout source.
- Prefer a substitute source or narrower claim over downloading, conversion,
  browser automation, or OCR.
- Focused and Standard runs do not initiate OCR.
- Extended/high-stakes or explicitly exhaustive work may use at most one Browser
  **or** local conversion/OCR escalation—not both—for an irreplaceable source that
  could change the answer. If it fails, disclose the gap and continue.

## 7. Draft for the reader

All reports must answer the question early, cite material factual claims, separate
evidence from inference, preserve important disagreement, and include exactly one
deduplicated Sources section containing only cited sources.

Presentation is adaptive:

- **Historical/cultural/humanities:** use a narrative or chronological arc, a
  specific title, concrete period-appropriate headings, and an opening thesis. Do
  not default to `Executive answer`, `Methods`, or `Limitations`.
- **Product/market/policy:** lead with the answer, comparisons, trade-offs,
  recommendation, and risks. An executive summary may fit.
- **Scientific/technical/high-stakes:** foreground method, evidence quality,
  uncertainty, and limitations when they aid interpretation.
- **Community/trend/experiential:** organize around patterns and voices while making
  representativeness limits clear without repetitive disclaimers.

Match the user's register and the subject's texture without sensationalizing,
imitating an author, or sacrificing precision. Keep material uncertainty near the
affected claim, but do not expose worker mechanics, evidence IDs, audit language, or
repeated boilerplate caveats in the report.

Infer a numeric target length from the request for orchestration purposes. Do not
ask the user to choose single-agent versus section-based drafting.

## 8. Audit only what needs judgment

- Focused and ordinary Standard: one combined evidence/editorial audit.
- Extended or high-stakes: two independent audits are allowed.
- Revise only for material issues.
- Use an independent closure review only for unresolved critical or major evidence
  issues in high-stakes work.
- Never dispatch an agent for deterministic citation, bibliography, duplicate
  heading, empty-section, or output-file checks.

If a critical claim remains unsupported, remove or narrow it. A disclosed gap is
better than another expensive loop that is unlikely to change the answer.
