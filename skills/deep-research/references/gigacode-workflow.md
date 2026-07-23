# Bounded Gigacode workflow

Use the bundled [`scripts/deep-research.workflow`](scripts/deep-research.workflow)
verbatim. Do not ask a coordinator agent to generate another workflow.

This guide defines the runtime arguments, routing procedure, budget behavior, and
recovery path. Kolega Code's injected Gigacode authoring guide remains authoritative
for primitive signatures.

## Before invocation

1. Settle the brief, report profile, tier, output path, and disjoint lanes.
2. If `list_subagent_models` is available, call it exactly once.
3. Select complete exact route objects only from that response. Omit a route when no
   safe alternate is clear.
4. Read `scripts/deep-research.workflow` and pass its content unchanged to
   `run_workflow`.
5. Announce the output path before starting.

No provider, model ID, or fixed effort selection belongs in this skill. Route
objects exist only in the current invocation's arguments.

## Arguments

Pass an object with this shape:

```json
{
  "brief": {
    "question": "The settled research question",
    "audience": "Who will read and use the report",
    "scope": "Timeframe, geography, comparison set, and exclusions",
    "current_as_of": "Optional user-supplied date",
    "high_stakes": false
  },
  "tier": "standard",
  "lanes": [
    {
      "id": "lane-1",
      "title": "A disjoint source/subject boundary",
      "question": "What this lane alone must establish",
      "source_classes": ["primary records", "scholarly synthesis"]
    }
  ],
  "acquisition": {
    "searches_per_lane": 6,
    "fetches_per_lane": 8,
    "verification_searches": 2,
    "verification_fetches": 4
  },
  "report_profile": {
    "kind": "historical-cultural",
    "voice": "Engaging, precise, and accessible",
    "target_words": 3000,
    "required_structure": [],
    "avoid_structure": ["Executive answer", "Methods", "Limitations"]
  },
  "writing_reserve_tokens": 18000,
  "research_batch_size": 2,
  "allow_acquisition_escalation": false,
  "escalation": null,
  "routes": {
    "discovery": "<optional complete runtime route object>",
    "verification": "<optional complete runtime route object>",
    "synthesis": "<optional complete runtime route object>",
    "audit": "<optional complete runtime route object>",
    "acquisition": "<optional complete runtime route object>"
  }
}
```

The example values describe a Standard run; adjust ceilings to the tier table in
`SKILL.md`. Do not pass string placeholders as routes in a real invocation. Include
a route key only when its value is a complete object returned for the current
session.

Infer `target_words` conservatively from the user's request and tier. The user does
not select a drafting mode. After verification, coverage analysis decides whether
the report needs bounded section drafting. A target of roughly 5,000 words or more
qualifies; a shorter report qualifies only when it has at least two genuinely
independent reader-facing sections with distinct verified claim sets.

Lane-count validation:

- Focused: exactly 2;
- Standard: 3 or 4;
- Extended: 5 or 6.

Lanes must not overlap. A historical run might divide by periods; a product run
might divide by options or evidence domains. Cross-lane comparison happens after
verification, not in another broad research lane.

## Stage routing

Map work to runtime routes by capability:

- `discovery`: bounded search, source metadata, direct extraction;
- `verification`: disputed, ambiguous, or conclusion-driving claims;
- `synthesis`: coverage judgment, final argument, and material revision;
- `audit`: bounded evidence/editorial checks;
- `acquisition`: the one permitted Browser or local escalation.

The workflow omits `model_override` when a key is absent. It never invents a partial
override or falls back from an invalid one.

## Budget and concurrency

Set a tier-appropriate workflow budget and reserve enough completed-output capacity
for coverage, drafting, audit, and possible material revision. The workflow:

- researches lanes in small parallel batches;
- checks the writing reserve before each new batch;
- filters failed workers at every barrier;
- skips optional follow-up when it would threaten the reserve; and
- returns a supported partial status when some lanes fail but the remaining evidence
  can answer the question honestly.

Budget admission cannot stop workers already in flight. Keep
`research_batch_size` at 2 for Focused/Standard and no higher than 3 for Extended.
Do not launch every lane at once and rely on the global ceiling.

Do not respond to exhaustion with a blanket budget multiplier. Inspect persisted
artifacts, remove low-value optional work, and resume from the run ID so unchanged
successful calls are reused.

## Optional acquisition escalation

Default `allow_acquisition_escalation` to `false`.

Set it to `true` only for Extended/high-stakes or explicitly exhaustive work and
provide one bounded `escalation` object:

```json
{
  "kind": "browser",
  "target": "Exact source URL",
  "question": "The one conclusion-changing fact to recover"
}
```

`kind` is `browser` or `local`. The workflow performs one attempt total. Browser
requires an available Browser worker and, when overridden, a runtime-discovered
vision-capable route. Local means one bounded read-only conversion/OCR investigation.
Do not combine kinds or retry a failed escalation.

## Results and materialization

The workflow returns a compact object:

```json
{
  "status": "complete | partial | failed",
  "report_markdown": "Present for complete or supported partial results",
  "cited_sources": [{"id": "S001", "title": "...", "url": "..."}],
  "gaps": ["Concise unresolved gap"],
  "run_summary": {
    "tier": "standard",
    "base_lanes_requested": 4,
    "base_lanes_completed": 4,
    "followups_run": 0,
    "escalations_run": 0,
    "draft_mode": "single | sections"
  }
}
```

Raw scout, verifier, coverage, and audit outputs remain visible in normal workflow
artifacts and are not copied into the final result.

Run the materializer with the manifest's `resultPath`:

```bash
python skills/deep-research/scripts/materialize_report.py \
  /path/to/workflow/result.md \
  reports/topic.md \
  --collision-safe
```

Use the available Python 3.11+ interpreter; do not assume the executable is literally
`python`. Use `--overwrite` only when the user explicitly approved replacing the
target.

## Resume and failure handling

- Read `resultPath` first when inline workflow output is omitted.
- Read `transcriptPath` only to diagnose stage failure or budget use.
- Resume to reuse an unchanged successful prefix while narrowing later work.
- If some lanes failed, proceed only when verified surviving evidence supports an
  honest answer. Mark the result `partial` and name the consequential gaps.
- If no supported report exists, return `failed`; the materializer must not create an
  empty file.
- Never rerun a completed workflow solely to recover a long result from chat output.
