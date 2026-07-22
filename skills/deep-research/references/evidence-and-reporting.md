# Evidence and reporting contract

Use this reference to design the research brief, evidence lanes, structured worker
outputs, citations, audits, and long-report sections.

## Contents

- [Research brief](#research-brief)
- [Conceptual lanes](#conceptual-lanes)
- [Choose sources for the claim](#choose-sources-for-the-claim)
- [Structured records](#structured-records)
- [Evidence interpretation](#evidence-interpretation)
- [Citation checks](#citation-checks)
- [Section-based reporting](#section-based-reporting)
- [Default report contract](#default-report-contract)
- [Failure and degradation](#failure-and-degradation)

## Research brief

Keep the brief compact enough to include in every research worker prompt.

```text
ResearchBrief
- question
- intended_use
- audience
- as_of_date
- timeframe
- geography_or_context
- scope:
    include[]
    exclude[]
- definitions[]
- source_policy:
    required[]
    preferred[]
    prohibited[]
    access_constraints[]
- output:
    format
    target_length
    target_words
    required_sections[]
    citation_style
    requested_path
- assumptions[]
- effort_tier: focused | standard | extended
- drafting_mode: single | sectioned
- lanes[]
```

Separate hard constraints from preferences. "Use only these archives" is a constraint;
"prefer interviews" is a preference. Preserve the user's wording when a subtle distinction
could affect the answer.

## Conceptual lanes

A lane owns a separable part of the question, not a prestige class of sources.

```text
Lane
- lane_id
- subquestion
- contribution_to_answer
- scope_boundaries[]
- key_terms_or_entities[]
- query_seeds[]
- useful_evidence_types[]
- disconfirming_angle
- completion_signals[]
```

Good lane sets divide the subject by mechanism, period, stakeholder, jurisdiction,
experience, decision criterion, or disputed proposition. They minimize duplication while
allowing evidence from different kinds of sources inside each lane.

Examples:

- A product comparison might use capabilities, daily workflows, failure modes, economics,
  and community maintenance.
- A cultural history might use origins, participant practices, platform changes, creator
  perspectives, internal disagreements, and outside reception.
- A policy question might use the rule itself, implementation, affected groups, observed
  outcomes, criticism, and unresolved cases.

Require a disconfirming angle when the work is evaluative, contested, high-stakes, or likely
to inherit the framing of one source. A descriptive lane need not manufacture controversy.

## Choose sources for the claim

There is no universal source ladder. Choose evidence by what it can observe and establish.

| Claim being investigated | Often useful evidence | Scope and failure checks |
| --- | --- | --- |
| A rule, commitment, release, price, or specification | Governing text, contract, changelog, first-party announcement, archived page | Check version, jurisdiction, effective date, and whether observed behavior matches the statement |
| Measured prevalence, performance, or change | Dataset, benchmark, survey, analytics, transparent experiment, reproducible observation | Inspect definitions, sample, missing data, incentives, and whether the measure fits the claim |
| Real product behavior | Documentation, source code, issue tracker, support thread, practitioner test, review, failure report | Separate intended behavior from observed behavior; record version and environment |
| A community's norms or internal language | Participant posts, community archives, forums, creator material, moderation records, interviews | Sample more than the loudest voices; avoid turning participation into population prevalence |
| A person's or group's experience | First-person account, interview, diary, testimony, ethnography, direct observation | Attribute the experience; do not generalize beyond the evidence without broader support |
| Public reaction or sentiment | Deliberately sampled posts, comments, forums, surveys, audience analytics | State sampling limits, platform effects, deleted content, brigading, and demographic uncertainty |
| An emerging practice or trend | Practitioner reports, repositories, newsletters, social posts, podcasts, event talks, job posts, usage data | Distinguish novelty from durable adoption and repetition from independent uptake |
| Historical sequence or interpretation | Contemporary records, archives, oral histories, later accounts, specialist analysis | Separate events from later memory; surface date conflicts and retrospective framing |
| A recommendation | Evidence about the user's actual criteria: specs, practical use, costs, failure modes, community experience, alternatives | Make the value judgment explicit; do not turn popularity or one review into universal fit |
| A causal or explanatory claim | Evidence that tests alternatives, process records, experiments, longitudinal observation, informed analyses | Do not rewrite correlation, chronology, or participant belief as demonstrated causation |

Use first-party sources for what a person or organization says, publishes, or experiences.
Do not assume they independently prove impact, superiority, or reception. Conversely, do
not discard a participant account merely because it is informal when participant experience
is the subject.

Track **independence groups**, not only hostnames. Reposts, wire copies, affiliates, shared
press releases, and reports based on the same dataset may represent one evidence lineage.
Several sources can still be valuable for different observations even when they are not
independent corroboration.

## Structured records

Use stable IDs within one run. IDs need only be deterministic and unambiguous, for example
`lane-03`, `src-lane-03-02`, and `claim-lane-03-04`.

### Source record

```text
SourceRecord
- source_id
- url
- title
- publisher
- author
- published_at
- updated_at
- accessed_at
- evidence_type
- proximity: direct | participant | observer | synthesis | unclear
- fetch_status: fetched | partial | blocked | failed
- independence_group
- context
- incentives_or_perspective[]
- representativeness_notes[]
- volatility_notes[]
- caveats[]
```

Use empty values when metadata is not stated. Never infer an author or publication date from
page styling or a search snippet. Keep the URL actually fetched; store a canonical URL only
when the page establishes one or obvious tracking parameters can be removed safely.

### Evidence item

```text
EvidenceItem
- evidence_id
- source_id
- atomic_claim
- support_text
- support_kind: verified_quote | grounded_paraphrase | direct_observation
- locator
- relationship: supports | contradicts | qualifies | contextualizes
- claim_scope
- caveats[]
```

`atomic_claim` should express one proposition. Split a sentence that mixes a measured fact,
an interpretation, and a causal explanation.

Use `verified_quote` only when the wording was checked against fetched source text. A
grounded answer produced by `web_fetch` can support a paraphrase but is not automatically a
quotation. For audio, video, or interactive material, record the timestamp, section, element,
or other locator available to the acquisition tool.

### Candidate and verified claims

```text
CandidateClaim
- claim_id
- lane_id
- claim_text
- materiality: conclusion_driving | supporting | contextual
- evidence_ids[]
- known_counterevidence_ids[]
- caveats[]
```

```text
VerifiedClaim
- claim_id
- lane_id
- final_claim_text
- verdict: supported | partially_supported | contradicted | unverifiable
- approved_evidence_ids[]
- contradicting_evidence_ids[]
- required_qualification
- allowed_in_report
- verification_notes
```

Use categories rather than numeric confidence scores. A verifier should narrow a broad claim
to what the evidence establishes, not merely lower its score.

### Verified lane result

```text
VerifiedLane
- lane_id
- answer_to_subquestion
- sources[]
- evidence[]
- verified_claims[]
- rejected_claim_ids[]
- unresolved_conflicts[]
- gaps[]
- failed_acquisition[]
```

A drafting worker receives only allowed verified claims and their approved evidence. Keep
rejected items for the audit trail, not as writing material.

### Coverage result

```text
CoverageResult
- facets[]:
    facet
    status: covered | partial | missing | conflicted
    verified_claim_ids[]
    explanation
- cross_lane_conflicts[]
- source_concentration_issues[]
- perspective_gaps[]
- temporal_gaps[]
- follow_up_worthwhile
- follow_up_tasks[]:
    task_id
    priority: high | medium | low
    target_gap
    queries[]
    expected_decision_value
- stop_reason
```

Run follow-up only for high-value gaps with concrete queries whose resolution could alter
the answer. Perspective diversity is relevant when the question concerns experiences,
reception, or contested meaning; it is not a box-counting requirement for every task.

### Audit issue

```text
AuditIssue
- issue_id
- severity: critical | major | minor
- dimension:
    support | citation | provenance | freshness | source_fit |
    representativeness | completeness | contradiction |
    instruction_following | structure | repetition | readability
- section_id
- report_span
- claim_id
- source_ids[]
- finding
- required_fix
```

Critical and major evidence issues must be removed, qualified, or repaired from already
approved evidence before delivery. A minor stylistic issue does not justify another research
loop.

## Evidence interpretation

### Match language to support

- State directly observed or documented facts directly.
- Attribute participant beliefs and first-party claims.
- Label estimates, interpretations, and extrapolations.
- Say "the available accounts disagree" when conflict remains.
- Say "these examples show that this occurs" rather than "most users experience this" when
  the evidence is a collection of examples.
- Say "available evidence does not establish" rather than forcing a yes/no conclusion.

### Preserve disagreement

When sources conflict, inspect:

- whether they define the subject or metric differently;
- publication date, software version, place, population, or historical period;
- direct access versus retelling;
- sampling and missing observations;
- financial, reputational, ideological, or community incentives; and
- whether later sources copied an earlier error.

Report what is agreed, each material version of the disagreement, which evidence is better
positioned for the particular claim, and what remains unresolved. Do not average mutually
incompatible accounts into a synthetic consensus.

### Handle recency

Freshness is claim-dependent. A current price or policy may become stale in days; a
first-person historical account does not become irrelevant because it is old. Record access
dates for volatile pages and distinguish event date, publication date, update date, and
retrospective recollection.

### Avoid source laundering

Trace a claim back when many pages cite one original post, dataset, press release, or
anonymous report. Cite the original when accessible, but keep independent analysis when it
adds interpretation or testing. Do not make a claim appear corroborated by counting copies.

## Citation checks

### Mechanical checks

- Every inline URL belongs to a fetched, approved `SourceRecord`.
- No search-engine result, redirect wrapper, invented URL, or failed fetch is cited.
- Every source in the Sources section is cited in the body.
- Every cited source appears once in the Sources section.
- Duplicate URLs and obvious copies are reconciled.
- Source titles, authors, dates, and quotations are not invented.
- A verbatim quotation has a checked span and locator where available.
- Section writers cite only source IDs assigned to their sections.
- The report contains every required section exactly once.

### Semantic checks

- Every conclusion-driving externally verifiable claim has nearby support.
- The linked source supports the exact clause or sentence, not merely the topic.
- A citation group collectively supports every material assertion before it.
- Source type and representativeness match the scope of the prose.
- Correlation, sequence, or testimony is not rewritten as established causation.
- First-party claims are attributed and independently tested when the conclusion requires
  more than what the party said.
- Volatile evidence is not presented as current without a relevant date.
- Disagreement is visible rather than silently resolved.
- The strength of the conclusion matches the verified registry.

Good scoping:

```markdown
The release notes mark offline sync as experimental in version 4.2
([Project changelog](https://example.com/changelog-4-2)).
```

```markdown
Several participants in the sampled forum threads described the change as making
moderation harder; these accounts show a recurring concern in those threads, not the
prevalence of that view across the whole community
([Thread A](https://example.com/thread-a); [Thread B](https://example.com/thread-b)).
```

```markdown
In her interview, Lee remembered the 1998 meetup as the point when the name became common,
while a surviving flyer uses it several months earlier
([Interview](https://example.com/interview); [Archived flyer](https://example.com/flyer)).
```

Bad scoping:

```markdown
Users hated the change ([one forum comment](https://example.com/comment)).
```

## Section-based reporting

Use this path for reports around 2,500 words or longer, with at least five substantive
sections, or likely to exceed one response.

### Section plan

```text
SectionPlan
- section_id
- order
- kind: framing | body | conclusion | limitations | methods
- heading
- purpose
- questions_answered[]
- target_words
- assigned_claim_ids[]
- assigned_source_ids[]
- dependencies[]
- adjacent_section_purposes[]
- exclusions[]
```

Every conclusion-driving claim should have one primary home. A claim may be referenced
briefly elsewhere, but the outline must identify where it is explained and supported.

### Section draft

```text
SectionDraft
- section_id
- heading
- markdown
- abstract
- cited_source_ids[]
- used_claim_ids[]
- unresolved_gaps[]
```

Draft body sections before framing. Each writer sees the full outline but only its assigned
evidence. After the body barrier, write the executive answer, introduction, conclusion, and
takeaways from body abstracts plus the verified registry. This prevents framing from
promising conclusions that the body did not establish.

Audit every section, including late sections, for support and citation. Run a global audit
on the assembled draft for:

- missing brief requirements;
- duplicated explanations or examples;
- terms used with inconsistent meanings;
- unresolved cross-section contradictions;
- conclusion claims absent from the body;
- section order and transitions; and
- disproportionate coverage.

Assign global issues back to specific section IDs. Revise affected sections concurrently in
one coordinated phase, then assemble in numeric order. Do not give a final assembler
permission to add facts.

## Default report contract

Honor a user-provided structure. Otherwise use:

```markdown
# Specific report title

**As of:** YYYY-MM-DD
**Scope:** What was and was not researched.

## Executive answer

The direct answer, central evidence, and most important uncertainty.

## Thematic finding

Evidence-backed analysis with descriptive inline links.

## Disagreements and uncertainty

Material conflicts, perspective limits, and unresolved questions.

## Conclusion

An evidence-calibrated conclusion or recommendation.

## Limitations

Missing, inaccessible, volatile, or unrepresentative evidence and scope limits.

## Methods

A concise account of timeframe, evidence selection, and verification. Do not reveal
private chain-of-thought or worker transcripts.

## Sources

- Publisher or author. “Title.” Date if stated. URL
```

Organize the report around the user's question, not the search process or worker names.
Keep the methods note useful but short. Do not expose internal prompts, chain-of-thought,
Gigacode scripts, or audit chatter in the reader-facing report.

## Failure and degradation

### Weak or failed search

Try bounded reformulations using alternate terminology, date, place, participant language,
source type, or a disconfirming frame. Search a known relevant site directly when useful.
Stop when retries become repetitive. Record the gap instead of filling it from memory.

### Blocked, paywalled, partial, or JavaScript-only source

Prefer, in order:

1. an accessible version from the same creator or publisher;
2. an archive, transcript, repository copy, filing, dataset, abstract, or quoted primary
   passage that can be verified;
3. a different source positioned to support the same claim;
4. a narrow Browser extraction when allowed; or
5. an explicit limitation.

Do not evade authentication, payment, robots controls, or technical access restrictions.

### Volatile or deleted community material

Record access date and available locator. Use a lawful archive only when its provenance is
clear. Avoid quoting sensitive deleted material gratuitously. If context cannot be checked,
do not use the item for a conclusion-driving claim.

### User source constraints

Honor allowlists and blocklists exactly. If they prevent adequate support, explain that
before broadening. Never silently replace "only these sources" with a general web search.

### Worker or schema failure

Allow one bounded formatting repair that does not perform new research. If the result is
still invalid, reject it and continue with the remaining verified evidence. Never infer a
missing URL, quote, verdict, or source ID.

### Budget exhaustion

Preserve fetched evidence, verify conclusion-driving claims, and keep synthesis capacity.
Drop lower-priority context and narrow the report. State which facets remain incomplete.

### Unresolved evidence

Return the best supported partial answer. Distinguish:

- no evidence found;
- evidence inaccessible;
- evidence found but too weak;
- credible sources in conflict; and
- the question not answerable at the requested scope.
