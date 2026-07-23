# Evidence and reporting

Use this reference to keep deep research rigorous without turning every report into
an institutional audit. The evidence rules are fixed; the report's structure and
voice are reader-dependent.

## Briefing and source planning

Topic-specific intake questions should change what is researched, not serve as
procedural form-filling. Before assigning source classes to lanes, use the answers
from intake to narrow scope and select evidence:

- **Scope answer** sets the timeframe, jurisdiction, geography, or comparison set
  for every lane, eliminating irrelevant source classes before acquisition begins.
- **Interpretive-lens question** (historical/cultural) targets primary texts,
  scholarly commentary, and reception records rather than news sources.
- **Options/constraints question** (product/market) determines whether technical
  documentation, independent benchmarks, or regulatory filings belong in scope.
- **Jurisdiction/decision question** (disputed/high-stakes) specifies which legal,
  clinical, or policy evidence applies and at what threshold.
- **Communities/period question** (experiential/community) identifies the platforms,
  forums, or archival sources appropriate for lived-experience evidence.
- **Audience and use answer** calibrates evidence depth: a practitioner audience
  may need primary or technical sources where a general audience benefits from
  authoritative synthesis.

Treat intake as a research-design step. If the topic-specific answers do not change
any lane boundary, source class, or evidence standard, the questions were not
specific enough.

## 1. Build claims from evidence

Separate four layers:

1. **Source** — who published the material, when, and under what incentives.
2. **Evidence** — the specific passage, datum, observation, or record.
3. **Claim** — the proposition that the evidence supports.
4. **Inference** — the analyst's interpretation that joins multiple claims.

Record evidence atomically. One evidence record should support one proposition and
name the source URL that can be cited. Do not use an entire document as if every
claim in it had been verified.

For each candidate claim, record:

- stable lane-local claim and evidence IDs;
- claim text;
- evidence IDs;
- importance: `background`, `supporting`, or `conclusion-driving`;
- whether the claim is disputed, surprising, or high-stakes; and
- a short qualification when support is partial.

The reader-facing report must never expose internal IDs.

## 2. Judge source fitness

Use the strongest available source for the claim:

1. primary record, official data, standard, or original research;
2. high-quality scholarly synthesis or authoritative technical documentation;
3. reputable specialist reporting or analysis;
4. contemporaneous reporting, trade material, or institutional commentary;
5. community or anecdotal material for experience and discovery, not universal
   factual claims.

Source class is not a universal ranking. A community post can be the primary source
for what a participant said; it is not primary evidence for broad prevalence.

Assess:

- directness: does the source actually support the proposition?
- authority: does the author or institution have relevant competence?
- independence: are apparently separate sources copying one origin?
- date fitness: is the evidence current enough for the claim?
- scope fitness: does the sample, jurisdiction, population, or period match?
- incentives and missing context;
- access stability and whether the citation is reader-verifiable.

Use discovery pages to locate authoritative evidence. Do not cite a search snippet
when the underlying source is available.

## 3. Acquire proportionally

### Lane ceilings

| Tier | Materially different searches | Fetches |
| --- | ---: | ---: |
| Focused | 4 | 6 |
| Standard | 6 | 8 |
| Extended | 8 | 12 |

Ceilings are upper bounds, not quotas. Stop when:

- every conclusion-driving claim in the lane has adequate direct support;
- another source would merely repeat established background;
- remaining uncertainty is unlikely to change the answer; or
- the writing/audit reserve would be threatened.

No source-count minimum applies. Prefer two independent strong sources for a
disputed conclusion-driving claim when they are realistically available; do not
manufacture independence by citing syndicated copies.

### Failed-acquisition ledger

Keep a compact shared ledger:

```text
canonical URL | failure class | attempts | alternate tried | claim affected
```

Canonicalize away fragments and tracking/query variants for retry decisions.

Terminal failures require zero same-source retries:

- 403/404 or other access denial;
- login, paywall, or robots restriction;
- certificate or protocol failure;
- unsupported or oversized content;
- scanned/no-text content;
- a source that requires prohibited or unavailable tooling.

If the source could change a conclusion, try at most one obvious lawful accessible
equivalent: an author manuscript, official mirror, archived official copy, or another
source reporting the same primary evidence. If that attempt fails, record the gap.

A transient timeout may be retried once. A second timeout is terminal.

Do not:

- repeat an identical query;
- vary only protocol, fragment, query string, mirror endpoint, or download parameter
  to create the appearance of a new attempt;
- let a verifier revisit a URL or access strategy already marked terminal;
- download and shell-convert a document merely because ordinary fetching failed; or
- treat OCR output as strong evidence without checking the relevant passage.

Focused and Standard runs never initiate OCR by default. Extended/high-stakes or
explicitly exhaustive work may use one Browser **or** local conversion/OCR
escalation—not both—only for an irreplaceable source that could change the answer.
Bound the target and question before the attempt. Stop after failure and disclose
the gap.

## 4. Verify selectively

Verification is for:

- conclusion-driving claims;
- disputed or surprising claims;
- claims whose scope, date, or causal language may exceed the evidence;
- conflicts between credible sources; and
- pivotal translations or interpretations.

Background claims with direct authoritative support do not need a wholesale second
research pass.

A verifier receives:

- the lane's compact scout record;
- the global failed-acquisition ledger;
- the claims selected for verification; and
- a small verification acquisition ceiling.

It returns a delta only:

- verdict per claim: `supported`, `qualified`, `unsupported`, or `disputed`;
- approved existing evidence IDs;
- concise qualifications;
- rejected evidence IDs and reason;
- genuinely new sources/evidence; and
- new failed acquisitions or gaps.

It must not echo the scout record or broadly re-fetch every source. Independence
means finding separate support for a material proposition, not mechanically
repeating the same acquisition work.

## 5. Handle disagreement honestly

When credible sources disagree:

1. identify the exact proposition in dispute;
2. compare definitions, dates, jurisdiction, samples, and incentives;
3. distinguish factual conflict from interpretive difference;
4. prefer the source closest to the underlying event or data when appropriate;
5. state what is established, what is probable, and what remains open.

Do not collapse a live disagreement into false certainty. Do not give fringe claims
equal weight merely because they exist.

Calibrate language:

- **Strong:** demonstrates, establishes, directly records.
- **Moderate:** supports, indicates, is consistent with.
- **Tentative:** suggests, may reflect, is plausibly explained by.
- **Unresolved:** evidence is insufficient or credible sources disagree.

## 6. Use compact handoffs

Research cost grows when every stage reproduces full source cards. Pass only what
the next stage needs.

### Scout record

- lane ID and a short synthesis;
- compact source cards: local ID, title, URL, publisher, date, type;
- atomic evidence: local ID, claim, source ID, short quote/paraphrase;
- candidate claims with importance and dispute flags;
- failed acquisitions; and
- unresolved gaps.

### Verification delta

- claim verdicts and approved evidence IDs;
- qualifications and rejections;
- only new sources/evidence;
- new failures and remaining gaps; and
- a short verifier synthesis.

### Coverage input

- one short supported synthesis per lane;
- conclusion-driving claim index;
- source-class coverage;
- unresolved gaps and failed-source effects; and
- the inferred target length and report profile needed to decide drafting shape.

Do not pass complete fetched text, search transcripts, duplicated source cards, or
full evidence ledgers into coverage and audit prompts.

### Drafting-shape decision

The skill decides the drafting shape; do not ask the user to choose an
implementation detail.

Use one drafting agent by default. Use bounded section drafting when:

- the inferred target is roughly 5,000 words or more; or
- coverage analysis identifies at least two genuinely independent sections with
  distinct claim sets whose parallel drafting improves clarity or context fit.

Do not use section fan-out merely because research had multiple lanes. Lanes are
evidence boundaries; report sections are reader-facing argument boundaries.

When section drafting is warranted:

1. coverage returns a short outline, purpose, and supported claim IDs per section;
2. draft the bounded sections in parallel using only their assigned claims;
3. run one synthesis pass to remove repetition, reconcile transitions, normalize
   voice, and preserve the opening thesis and conclusion; and
4. build the bibliography from the synthesized body, not from section-reported
   source lists.

## 7. Reader-fit report contract

### Core invariants

Every report must:

- answer the research question early;
- cite material factual claims with descriptive Markdown links;
- distinguish sourced fact from synthesis or inference;
- preserve material disagreement and uncertainty;
- conclude only as strongly as the evidence allows; and
- contain exactly one `## Sources` section with deduplicated sources actually cited
  in the body.

Keep uncertainty next to the affected claim. Consolidate secondary caveats instead
of repeating "the accessible evidence is limited" in every section. Do not expose
research lanes, worker names, evidence IDs, audit verdicts, or retry history unless
the user explicitly asks for methods.

The user's requested format wins. Otherwise choose the closest profile below.

### Historical, cultural, and humanities

- Open with a clear thesis in natural prose.
- Use a narrative, chronological, or thematic arc suited to the material.
- Write a specific, engaging title and concrete period-appropriate headings.
- Integrate interpretive disputes where they arise.
- Use a brief, naturally titled note on gaps only if it changes how the history
  should be read.
- Do not default to headings named `Executive answer`, `Methods`, or `Limitations`.

For a history of Saturnian magic, for example, prefer headings tied to periods,
texts, and transformations over corporate or methodological labels. Evocative does
not mean sensational: preserve ambiguity between documentary fact, later tradition,
and modern reconstruction.

### Product, market, and policy decision

- Lead with the answer or decision frame.
- Compare options on criteria that matter to the stated audience.
- Explain trade-offs, recommendation, risks, and what would change the choice.
- Use an executive summary when the decision-maker benefits from one.

### Scientific, technical, and high-stakes

- State scope and definitions precisely.
- Explain method, evidence quality, and uncertainty where they affect
  interpretation.
- Distinguish association, mechanism, and causation.
- Give limitations their own section when needed for safe use of the findings.

### Community, trend, and experiential

- Organize around observed patterns and participant voices.
- Identify the sampled community and missing groups.
- Treat anecdotes as experience evidence, not prevalence estimates.
- State representativeness limits once clearly rather than as a disclaimer in every
  paragraph.

### Voice

Match the user's register and the subject's texture. Prefer concrete nouns and
active sentences. Avoid generic institutional phrases, audit-shaped headings, and
inflated abstractions when plain language is more accurate.

Do not:

- imitate a living author;
- manufacture scenes, quotations, or emotional certainty;
- sensationalize cultural or religious material;
- trade factual precision for color; or
- force all discovered sources into the prose.

## 8. Cite economically and immediately

Use descriptive Markdown links near the supported claim:

```markdown
The [official release notes](https://example.com/release) date the change to May.
```

Avoid:

- bare URLs in body prose;
- one citation at the end of a paragraph containing several unrelated claims;
- bibliography entries never cited in the body;
- multiple citations that all derive from one origin; and
- citation density that obscures the argument when one stronger source suffices.

The deterministic bibliography builder should extract URLs from the final body,
resolve them against the canonical registry, and create `## Sources`. Writer-reported
source lists are advisory only.

## 9. Audit proportionally

One combined evidence/editorial audit is enough for Focused and ordinary Standard
reports. It checks:

- whether material claims are supported by cited registry sources;
- whether claim strength matches the evidence;
- whether disagreement and scope limits are represented fairly;
- whether the answer addresses the settled brief; and
- whether structure, headings, and voice fit the report profile.

Use two independent audits for Extended or high-stakes work: one evidence-focused
and one reader/editorial-focused. Revise only when an audit identifies a material
issue.

An independent closure review is justified only when high-stakes revision leaves an
unresolved critical or major evidence issue. Deterministic checks—not agents—own:

- unknown citation URLs;
- duplicate citation URLs or headings;
- missing cited sources;
- uncited bibliography entries;
- empty sections;
- malformed Markdown output; and
- missing/empty output files.

If evidence cannot support a material claim, remove or narrow the claim and name
the gap. More process is not a substitute for better evidence.
