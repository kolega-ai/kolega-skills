meta = {
    "name": "bounded-deep-research",
    "description": "Research disjoint lanes, selectively verify claims, and produce a compact cited report",
    "max_agent_depth": 1,
    "phases": [
        {"title": "Research"},
        {"title": "Verify"},
        {"title": "Coverage"},
        {"title": "Draft"},
        {"title": "Audit"},
        {"title": "Revise"},
    ],
}

SCOUT_SCHEMA = {
    "type": "object",
    "properties": {
        "lane_id": {"type": "string"},
        "summary": {"type": "string"},
        "sources": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "publisher": {"type": "string"},
                    "date": {"type": "string"},
                    "source_type": {"type": "string"},
                },
                "required": ["id", "title", "url"],
            },
        },
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "claim": {"type": "string"},
                    "source_id": {"type": "string"},
                    "quote_or_paraphrase": {"type": "string"},
                },
                "required": ["id", "claim", "source_id", "quote_or_paraphrase"],
            },
        },
        "candidate_claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "text": {"type": "string"},
                    "evidence_ids": {"type": "array", "items": {"type": "string"}},
                    "importance": {"type": "string"},
                    "disputed": {"type": "boolean"},
                },
                "required": ["id", "text", "evidence_ids", "importance", "disputed"],
            },
        },
        "failures": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "reason": {"type": "string"},
                    "terminal": {"type": "boolean"},
                },
                "required": ["url", "reason", "terminal"],
            },
        },
        "gaps": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "lane_id",
        "summary",
        "sources",
        "evidence",
        "candidate_claims",
        "failures",
        "gaps",
    ],
}

VERIFIER_SCHEMA = {
    "type": "object",
    "properties": {
        "lane_id": {"type": "string"},
        "summary": {"type": "string"},
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string"},
                    "status": {"type": "string"},
                    "approved_evidence_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "qualification": {"type": "string"},
                },
                "required": [
                    "claim_id",
                    "status",
                    "approved_evidence_ids",
                    "qualification",
                ],
            },
        },
        "rejected_evidence_ids": {"type": "array", "items": {"type": "string"}},
        "new_sources": SCOUT_SCHEMA["properties"]["sources"],
        "new_evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "claim_id": {"type": "string"},
                    "claim": {"type": "string"},
                    "source_id": {"type": "string"},
                    "quote_or_paraphrase": {"type": "string"},
                },
                "required": [
                    "id",
                    "claim_id",
                    "claim",
                    "source_id",
                    "quote_or_paraphrase",
                ],
            },
        },
        "new_failures": SCOUT_SCHEMA["properties"]["failures"],
        "gaps": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "lane_id",
        "summary",
        "verdicts",
        "rejected_evidence_ids",
        "new_sources",
        "new_evidence",
        "new_failures",
        "gaps",
    ],
}

COVERAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "followup_needed": {"type": "boolean"},
        "decision_affected": {"type": "string"},
        "followup_lane": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "question": {"type": "string"},
                "source_classes": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["id", "title", "question", "source_classes"],
        },
        "gaps": {"type": "array", "items": {"type": "string"}},
        "section_drafting_needed": {"type": "boolean"},
        "section_drafting_reason": {"type": "string"},
        "section_outline": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "purpose": {"type": "string"},
                    "claim_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["heading", "purpose", "claim_ids"],
            },
        },
    },
    "required": [
        "summary",
        "followup_needed",
        "decision_affected",
        "gaps",
        "section_drafting_needed",
        "section_drafting_reason",
        "section_outline",
    ],
}

DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "body_markdown": {"type": "string"},
        "gaps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "body_markdown", "gaps"],
}

SECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "heading": {"type": "string"},
        "body_markdown": {"type": "string"},
        "used_claim_ids": {"type": "array", "items": {"type": "string"}},
        "gaps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["heading", "body_markdown", "used_claim_ids", "gaps"],
}

AUDIT_SCHEMA = {
    "type": "object",
    "properties": {
        "revision_needed": {"type": "boolean"},
        "material_issues": {"type": "array", "items": {"type": "string"}},
        "minor_issues": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": ["revision_needed", "material_issues", "minor_issues", "summary"],
}

REVISION_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "body_markdown": {"type": "string"},
        "remaining_material_issues": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "body_markdown", "remaining_material_issues"],
}

CLOSURE_SCHEMA = {
    "type": "object",
    "properties": {
        "supported": {"type": "boolean"},
        "unresolved_material_issues": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["supported", "unresolved_material_issues"],
}


def canonical_url(value):
    text = str(value or "").strip()
    text = text.split("#", 1)[0]
    text = text.split("?", 1)[0]
    return text.rstrip("/")


def route_for(role):
    value = routes.get(role)
    if not isinstance(value, dict):
        return None
    if set(value.keys()) != {"provider", "model", "effort"}:
        return None
    if not value.get("provider") or not value.get("model"):
        return None
    return value


async def dispatch(prompt, label, phase_name, schema, role, agent_type="investigation"):
    override = route_for(role)
    if override is None:
        return await agent(
            prompt,
            label=label,
            phase=phase_name,
            schema=schema,
            agent_type=agent_type,
        )
    return await agent(
        prompt,
        label=label,
        phase=phase_name,
        schema=schema,
        model_override=override,
        agent_type=agent_type,
    )


def compact_failed_ledger(records):
    ledger = {}
    for record in records:
        for failure in (record or {}).get("failures", []):
            key = canonical_url(failure.get("url"))
            if key and key not in ledger:
                ledger[key] = {
                    "url": failure.get("url", ""),
                    "reason": failure.get("reason", ""),
                    "terminal": bool(failure.get("terminal", False)),
                }
        verifier = (record or {}).get("verification") or {}
        for failure in verifier.get("new_failures", []):
            key = canonical_url(failure.get("url"))
            if key and key not in ledger:
                ledger[key] = {
                    "url": failure.get("url", ""),
                    "reason": failure.get("reason", ""),
                    "terminal": bool(failure.get("terminal", False)),
                }
    return [ledger[key] for key in sorted(ledger.keys())]


def research_prompt(lane, searches, fetches, special_instruction=""):
    return (
        "Research only this disjoint lane for the settled brief.\n\n"
        "BRIEF: "
        + repr(brief)
        + "\nLANE: "
        + repr(lane)
        + "\nREPORT PROFILE: "
        + repr(report_profile)
        + "\n\nACQUISITION CEILING: at most "
        + str(searches)
        + " materially different searches and "
        + str(fetches)
        + " fetches. These are ceilings, not quotas; stop as soon as material "
        "claims are adequately supported. Never repeat a query. Retry a transient "
        "timeout once only. Treat access denial, 403/404, login/paywall, robots, "
        "certificate failure, unsupported/oversized content, and scanned/no-text "
        "content as terminal for that URL. Do not vary URL syntax to retry. Try at "
        "most one obvious accessible equivalent for a conclusion-driving source. "
        "Do not use browser automation, downloading, conversion, or OCR. "
        + special_instruction
        + "\n\nReturn a compact record only. Use atomic evidence and lane-local IDs. "
        "Do not include fetched full text, search transcripts, prose bibliography, "
        "or process narration."
    )


def verification_prompt(scout, failed_ledger):
    selected_claims = []
    for claim in scout.get("candidate_claims", []):
        if claim.get("importance") == "conclusion-driving" or claim.get("disputed"):
            selected_claims.append(claim)
    return (
        "Selectively verify only the conclusion-driving or disputed claims below. "
        "Do not re-research background claims or broadly re-fetch the scout's "
        "sources. Return a delta; never echo the scout record.\n\nBRIEF: "
        + repr(brief)
        + "\nSCOUT RECORD: "
        + repr(scout)
        + "\nCLAIMS SELECTED: "
        + repr(selected_claims)
        + "\nKNOWN FAILED ACQUISITIONS: "
        + repr(failed_ledger)
        + "\n\nDo not retry any terminal URL or equivalent access strategy in the "
        "failed ledger. Use at most "
        + str(verification_searches)
        + " materially different searches and "
        + str(verification_fetches)
        + " fetches. Never use OCR or conversion. Seek independent support only "
        "where it can affect the answer. Verdict status must be supported, "
        "qualified, unsupported, or disputed. New records contain only genuinely "
        "new evidence."
    )


def budget_allows_optional(extra=0):
    if budget.total is None:
        return True
    return budget.remaining() > writing_reserve + extra


def build_registry(records):
    raw_sources = []
    source_keys = {}
    for record in records:
        scout = record.get("scout") or {}
        lane_id = str(scout.get("lane_id", "lane"))
        for source in scout.get("sources", []):
            key = canonical_url(source.get("url"))
            if key:
                raw_sources.append((key, lane_id, source))
                source_keys[(lane_id, str(source.get("id", "")))] = key
        verifier = record.get("verification") or {}
        for source in verifier.get("new_sources", []):
            key = canonical_url(source.get("url"))
            if key:
                raw_sources.append((key, lane_id, source))
                source_keys[(lane_id, str(source.get("id", "")))] = key

    by_url = {}
    for key, lane_id, source in sorted(raw_sources, key=lambda item: (item[0], item[1])):
        if key not in by_url:
            by_url[key] = {
                "title": str(source.get("title", "")).strip() or key,
                "url": str(source.get("url", "")).strip(),
                "publisher": str(source.get("publisher", "")).strip(),
                "date": str(source.get("date", "")).strip(),
                "source_type": str(source.get("source_type", "")).strip(),
            }

    registry = []
    registry_ids = {}
    for index, key in enumerate(sorted(by_url.keys()), 1):
        card = dict(by_url[key])
        card["id"] = "S" + str(index).zfill(3)
        registry.append(card)
        registry_ids[key] = card["id"]

    claims = []
    lane_summaries = []
    all_gaps = []
    for record in records:
        scout = record.get("scout") or {}
        verifier = record.get("verification") or {}
        lane_id = str(scout.get("lane_id", "lane"))
        lane_summaries.append(
            {
                "lane_id": lane_id,
                "summary": verifier.get("summary") or scout.get("summary", ""),
            }
        )
        all_gaps.extend(scout.get("gaps", []))
        all_gaps.extend(verifier.get("gaps", []))
        verdicts = {item.get("claim_id"): item for item in verifier.get("verdicts", [])}
        evidence = {item.get("id"): item for item in scout.get("evidence", [])}
        for item in verifier.get("new_evidence", []):
            evidence[item.get("id")] = item
        for claim in scout.get("candidate_claims", []):
            verdict = verdicts.get(claim.get("id"))
            if not verdict or verdict.get("status") == "unsupported":
                continue
            approved = verdict.get("approved_evidence_ids") or claim.get("evidence_ids", [])
            source_ids = []
            excerpts = []
            for evidence_id in approved:
                evidence_item = evidence.get(evidence_id) or {}
                source_key = source_keys.get((lane_id, str(evidence_item.get("source_id", ""))))
                if source_key and source_key in registry_ids:
                    source_ids.append(registry_ids[source_key])
                excerpt = evidence_item.get("quote_or_paraphrase")
                if excerpt:
                    excerpts.append(str(excerpt))
            if source_ids:
                claims.append(
                    {
                        "id": lane_id + "/" + str(claim.get("id", "")),
                        "text": claim.get("text", ""),
                        "status": verdict.get("status", ""),
                        "qualification": verdict.get("qualification", ""),
                        "source_ids": sorted(set(source_ids)),
                        "evidence": excerpts,
                    }
                )
    return registry, claims, lane_summaries, sorted(set(str(gap) for gap in all_gaps if gap))


def strip_sources(markdown):
    lines = str(markdown or "").strip().splitlines()
    kept = []
    for line in lines:
        if line.strip().lower() == "## sources":
            break
        kept.append(line)
    if kept and kept[0].startswith("# "):
        kept = kept[1:]
    return "\n".join(kept).strip()


def markdown_urls(markdown):
    urls = []
    cursor = 0
    text = str(markdown or "")
    while True:
        marker = text.find("](", cursor)
        if marker < 0:
            break
        end = text.find(")", marker + 2)
        if end < 0:
            break
        url = text[marker + 2 : end].strip().strip("<>")
        if url and url not in urls:
            urls.append(url)
        cursor = end + 1
    return urls


def structural_issues(markdown):
    issues = []
    text = str(markdown or "").strip()
    if not text.startswith("# "):
        issues.append("missing level-one title")
    if text.count("\n## Sources\n") != 1:
        issues.append("report must contain exactly one Sources section")
    lines = text.splitlines()
    headings = []
    for index, line in enumerate(lines):
        if line.startswith("## "):
            key = line.strip().lower()
            if key in headings:
                issues.append("duplicate heading: " + line.strip())
            headings.append(key)
            next_index = index + 1
            has_content = False
            while next_index < len(lines) and not lines[next_index].startswith("## "):
                if lines[next_index].strip():
                    has_content = True
                    break
                next_index += 1
            if not has_content:
                issues.append("empty section: " + line.strip())
    return issues


def assemble_report(draft, registry):
    title = str((draft or {}).get("title", "")).strip().lstrip("#").strip()
    body = strip_sources((draft or {}).get("body_markdown", ""))
    by_url = {canonical_url(source.get("url")): source for source in registry}
    cited = []
    unknown = []
    for url in markdown_urls(body):
        key = canonical_url(url)
        if key in by_url and key not in cited:
            cited.append(key)
        elif key not in by_url:
            unknown.append(url)
    source_lines = []
    cited_sources = []
    for key in cited:
        source = by_url[key]
        detail = source.get("publisher") or source.get("source_type") or ""
        if source.get("date"):
            detail = (detail + ", " + source.get("date")).strip(", ")
        suffix = " — " + detail if detail else ""
        source_lines.append("- [" + source.get("title", key) + "](" + source.get("url", key) + ")" + suffix)
        cited_sources.append(source)
    report = "# " + title + "\n\n" + body + "\n\n## Sources\n\n" + "\n".join(source_lines)
    issues = []
    if not title:
        issues.append("missing report title")
    if not body:
        issues.append("missing report body")
    if not cited_sources:
        issues.append("report body cites no registry source")
    if unknown:
        issues.append("unknown citation URLs: " + repr(unknown))
    issues.extend(structural_issues(report))
    return report.strip() + "\n", cited_sources, issues


validation_errors = []
if not isinstance(args, dict):
    validation_errors.append("args must be an object")
brief = args.get("brief", {}) if isinstance(args, dict) else {}
tier = args.get("tier", "") if isinstance(args, dict) else ""
lanes = args.get("lanes", []) if isinstance(args, dict) else []
acquisition = args.get("acquisition", {}) if isinstance(args, dict) else {}
report_profile = args.get("report_profile", {}) if isinstance(args, dict) else {}
routes = args.get("routes", {}) if isinstance(args, dict) else {}

lane_ranges = {"focused": (2, 2), "standard": (3, 4), "extended": (5, 6)}
tier_caps = {"focused": (4, 6), "standard": (6, 8), "extended": (8, 12)}
if not isinstance(brief, dict) or not str(brief.get("question", "")).strip():
    validation_errors.append("brief.question is required")
if tier not in lane_ranges:
    validation_errors.append("tier must be focused, standard, or extended")
if not isinstance(lanes, list):
    validation_errors.append("lanes must be an array")
elif tier in lane_ranges:
    minimum, maximum = lane_ranges[tier]
    if len(lanes) < minimum or len(lanes) > maximum:
        validation_errors.append(
            tier + " requires " + str(minimum) + ("-" + str(maximum) if minimum != maximum else "") + " lanes"
        )
lane_ids = []
for lane in lanes if isinstance(lanes, list) else []:
    if not isinstance(lane, dict):
        validation_errors.append("every lane must be an object")
        continue
    lane_id = str(lane.get("id", "")).strip()
    if not lane_id or not str(lane.get("question", "")).strip():
        validation_errors.append("every lane requires id and question")
    if lane_id in lane_ids:
        validation_errors.append("lane ids must be unique")
    lane_ids.append(lane_id)

default_searches, default_fetches = tier_caps.get(tier, (0, 0))
searches_per_lane = acquisition.get("searches_per_lane", default_searches)
fetches_per_lane = acquisition.get("fetches_per_lane", default_fetches)
verification_searches = acquisition.get("verification_searches", 2)
verification_fetches = acquisition.get("verification_fetches", 4)
if (
    not isinstance(searches_per_lane, int)
    or searches_per_lane < 0
    or searches_per_lane > default_searches
):
    validation_errors.append("searches_per_lane exceeds the tier ceiling")
if (
    not isinstance(fetches_per_lane, int)
    or fetches_per_lane < 0
    or fetches_per_lane > default_fetches
):
    validation_errors.append("fetches_per_lane exceeds the tier ceiling")
if not isinstance(verification_searches, int) or verification_searches < 0:
    validation_errors.append("verification_searches must be a nonnegative integer")
if not isinstance(verification_fetches, int) or verification_fetches < 0:
    validation_errors.append("verification_fetches must be a nonnegative integer")
target_words = report_profile.get("target_words", 3000) if isinstance(report_profile, dict) else 3000
if not isinstance(target_words, int) or target_words < 500:
    validation_errors.append("report_profile.target_words must be an integer of at least 500")

writing_reserve = args.get("writing_reserve_tokens", 18000) if isinstance(args, dict) else 18000
batch_size = args.get("research_batch_size", 2) if isinstance(args, dict) else 2
if not isinstance(writing_reserve, int) or writing_reserve < 0:
    validation_errors.append("writing_reserve_tokens must be a nonnegative integer")
if not isinstance(batch_size, int) or batch_size < 1 or batch_size > (3 if tier == "extended" else 2):
    validation_errors.append("research_batch_size exceeds the tier concurrency limit")

if validation_errors:
    return {
        "status": "failed",
        "report_markdown": "",
        "cited_sources": [],
        "gaps": validation_errors,
        "run_summary": {
            "tier": tier or "unknown",
            "base_lanes_requested": len(lanes) if isinstance(lanes, list) else 0,
            "base_lanes_completed": 0,
            "followups_run": 0,
            "escalations_run": 0,
            "draft_mode": "single",
        },
    }

phase("Research")
research_records = []
partial_reasons = []
for start in range(0, len(lanes), batch_size):
    if not budget_allows_optional():
        partial_reasons.append("research stopped to preserve the writing and audit reserve")
        break
    batch = lanes[start : start + batch_size]
    results = await parallel(
        [
            (
                lambda lane=lane: dispatch(
                    research_prompt(lane, searches_per_lane, fetches_per_lane),
                    "scout:" + str(lane.get("id")),
                    "Research",
                    SCOUT_SCHEMA,
                    "discovery",
                )
            )
            for lane in batch
        ]
    )
    for lane, scout in zip(batch, results):
        if scout is None:
            partial_reasons.append("research worker failed for " + str(lane.get("id")))
        else:
            research_records.append({"scout": scout, "verification": None})

phase("Verify")
failed_ledger = compact_failed_ledger(research_records)
for start in range(0, len(research_records), batch_size):
    batch = research_records[start : start + batch_size]
    results = await parallel(
        [
            (
                lambda record=record: dispatch(
                    verification_prompt(record["scout"], failed_ledger),
                    "verify:" + str(record["scout"].get("lane_id")),
                    "Verify",
                    VERIFIER_SCHEMA,
                    "verification",
                )
            )
            for record in batch
        ]
    )
    for record, verification in zip(batch, results):
        if verification is None:
            partial_reasons.append(
                "verification worker failed for " + str(record["scout"].get("lane_id"))
            )
        else:
            record["verification"] = verification

research_records = [record for record in research_records if record.get("verification") is not None]
base_lanes_completed = len(research_records)

escalations_run = 0
escalation = args.get("escalation")
allow_escalation = bool(args.get("allow_acquisition_escalation", False))
high_stakes = bool(brief.get("high_stakes", False))
if (
    allow_escalation
    and (tier == "extended" or high_stakes)
    and isinstance(escalation, dict)
    and escalation.get("kind") in ("browser", "local")
    and escalation.get("target")
    and escalation.get("question")
    and budget_allows_optional()
):
    escalation_lane = {
        "id": "acquisition-escalation",
        "title": "One bounded acquisition escalation",
        "question": escalation.get("question"),
        "source_classes": ["irreplaceable target source"],
    }
    kind = escalation.get("kind")
    escalation_prompt = (
        "Perform one bounded acquisition escalation for an irreplaceable source. "
        "Make exactly one "
        + str(kind)
        + " attempt against "
        + str(escalation.get("target"))
        + ". Answer only this question: "
        + str(escalation.get("question"))
        + ". Do not try another URL, mirror, method, conversion, browser path, or OCR "
        "engine. Stop after success or failure. Return the same compact source, atomic "
        "evidence, candidate-claim, failure, and gap record used by a research lane. "
        "Do not include full fetched text, a search transcript, or process narration."
    )
    scout = await dispatch(
        escalation_prompt,
        "escalation:" + str(kind),
        "Research",
        SCOUT_SCHEMA,
        "acquisition",
        "browser" if kind == "browser" else "investigation",
    )
    escalations_run = 1
    if scout is None:
        partial_reasons.append("the single acquisition escalation failed")
    else:
        failed_ledger = compact_failed_ledger(research_records + [{"scout": scout}])
        verification = await dispatch(
            verification_prompt(scout, failed_ledger)
            + "\nDo not reacquire the escalation target; assess the returned evidence and seek "
            "ordinary independent support only if essential.",
            "verify:acquisition-escalation",
            "Verify",
            VERIFIER_SCHEMA,
            "verification",
        )
        if verification is None:
            partial_reasons.append("the acquisition escalation could not be verified")
        else:
            research_records.append({"scout": scout, "verification": verification})

registry, verified_claims, lane_summaries, evidence_gaps = build_registry(research_records)

phase("Coverage")
coverage = None
if research_records:
    coverage = await dispatch(
        "Assess whether one bounded follow-up could change the thesis or recommendation. "
        "Do not research. Focused work must not request a follow-up. A Standard or "
        "Extended follow-up must identify the exact decision affected and one narrow, "
        "non-overlapping lane. Return followup_needed=false for merely useful context. "
        "Also decide the reader-facing drafting shape. Section drafting is warranted "
        "for a target of roughly 5000 words or more, or for a shorter report only when "
        "at least two genuinely independent sections have distinct verified claim sets. "
        "Research lanes alone are not a reason. Return a compact section outline with "
        "purpose and claim IDs when sections are warranted; otherwise return an empty "
        "outline.\n\n"
        "BRIEF: "
        + repr(brief)
        + "\nTIER: "
        + tier
        + "\nTARGET WORDS: "
        + str(target_words)
        + "\nREPORT PROFILE: "
        + repr(report_profile)
        + "\nVERIFIED LANE SUMMARIES: "
        + repr(lane_summaries)
        + "\nVERIFIED CLAIM INDEX: "
        + repr(verified_claims)
        + "\nGAPS: "
        + repr(evidence_gaps)
        + "\nFAILED ACQUISITIONS: "
        + repr(compact_failed_ledger(research_records)),
        "coverage",
        "Coverage",
        COVERAGE_SCHEMA,
        "audit",
    )

followups_run = 0
if (
    tier != "focused"
    and coverage
    and coverage.get("followup_needed")
    and str(coverage.get("decision_affected", "")).strip()
    and isinstance(coverage.get("followup_lane"), dict)
    and budget_allows_optional(verification_fetches * 250)
):
    failed_ledger = compact_failed_ledger(research_records)
    followup_lane = coverage.get("followup_lane")

    async def followup_scout(_lane, _original, _index):
        return await dispatch(
            research_prompt(
                followup_lane,
                searches_per_lane,
                fetches_per_lane,
                "This is the only follow-up. Research only the decision-changing gap: "
                + str(coverage.get("decision_affected")),
            ),
            "followup:scout",
            "Research",
            SCOUT_SCHEMA,
            "discovery",
        )

    async def followup_verify(scout, _original, _index):
        if scout is None:
            return None
        verification = await dispatch(
            verification_prompt(scout, failed_ledger),
            "followup:verify",
            "Verify",
            VERIFIER_SCHEMA,
            "verification",
        )
        if verification is None:
            return None
        return {"scout": scout, "verification": verification}

    followup_results = await pipeline([followup_lane], followup_scout, followup_verify)
    followup_records = [record for record in followup_results if record is not None]
    if followup_records:
        research_records.extend(followup_records[:1])
        followups_run = 1
    else:
        partial_reasons.append("the single decision-changing follow-up failed")

registry, verified_claims, lane_summaries, evidence_gaps = build_registry(research_records)
all_gaps = sorted(set(partial_reasons + evidence_gaps + ((coverage or {}).get("gaps", []))))

if not verified_claims or not registry:
    return {
        "status": "failed",
        "report_markdown": "",
        "cited_sources": [],
        "gaps": all_gaps + ["no verified claim set was sufficient to draft a cited report"],
        "run_summary": {
            "tier": tier,
            "base_lanes_requested": len(lanes),
            "base_lanes_completed": base_lanes_completed,
            "followups_run": followups_run,
            "escalations_run": escalations_run,
            "draft_mode": "single",
        },
    }

phase("Draft")
single_draft_prompt = (
    "Write the complete reader-facing report from the verified registry below. "
    "Answer the question early. Match the report profile rather than using a fixed "
    "institutional template. Cite material factual claims with descriptive Markdown "
    "links using only exact URLs from the registry. Use a smaller set of strong "
    "representative citations; do not force every source into the prose. Keep material "
    "uncertainty near the affected claim without repeating boilerplate caveats. Do not "
    "mention workers, lanes, evidence IDs, audits, or retry history. Return title and "
    "body only: do not write a Sources section because it is built deterministically.\n\n"
    "BRIEF: "
    + repr(brief)
    + "\nREPORT PROFILE: "
    + repr(report_profile)
    + "\nVERIFIED CLAIMS: "
    + repr(verified_claims)
    + "\nSOURCE REGISTRY: "
    + repr(registry)
    + "\nCONSEQUENTIAL GAPS: "
    + repr(all_gaps)
)
section_outline = (coverage or {}).get("section_outline", [])
section_outline = [
    section
    for section in section_outline
    if isinstance(section, dict)
    and str(section.get("heading", "")).strip()
    and str(section.get("purpose", "")).strip()
]
section_decision = bool((coverage or {}).get("section_drafting_needed", False))
use_section_drafting = len(section_outline) >= 2 and (target_words >= 5000 or section_decision)
draft_mode = "sections" if use_section_drafting else "single"

draft = None
if use_section_drafting:
    claims_by_id = {claim.get("id"): claim for claim in verified_claims}
    section_target = max(500, target_words // len(section_outline))
    section_results = await parallel(
        [
            (
                lambda section=section, section_index=section_index: dispatch(
                    "Draft one bounded report section. Use only the assigned verified "
                    "claims and exact registry URLs. Write the section heading and body, "
                    "not a title, introduction, conclusion, or Sources section. Avoid "
                    "repeating general context that belongs elsewhere. Target about "
                    + str(section_target)
                    + " words.\n\nBRIEF: "
                    + repr(brief)
                    + "\nREPORT PROFILE: "
                    + repr(report_profile)
                    + "\nSECTION: "
                    + repr(section)
                    + "\nASSIGNED VERIFIED CLAIMS: "
                    + repr(
                        [
                            claims_by_id[claim_id]
                            for claim_id in section.get("claim_ids", [])
                            if claim_id in claims_by_id
                        ]
                    )
                    + "\nSOURCE REGISTRY: "
                    + repr(registry),
                    "section-draft:" + str(section_index + 1),
                    "Draft",
                    SECTION_SCHEMA,
                    "synthesis",
                )
            )
            for section_index, section in enumerate(section_outline)
        ]
    )
    section_results = [section for section in section_results if section is not None]
    if len(section_results) >= 2:
        draft = await dispatch(
            "Synthesize the independently drafted sections into one coherent report. "
            "Write a specific title, an opening that answers the question early, smooth "
            "transitions, and an evidence-calibrated conclusion. Remove repetition and "
            "normalize voice without flattening subject-specific texture. Preserve only "
            "supported citations and use exact registry URLs. Return title and body "
            "without a Sources section.\n\nBRIEF: "
            + repr(brief)
            + "\nREPORT PROFILE: "
            + repr(report_profile)
            + "\nSECTION DRAFTS: "
            + repr(section_results)
            + "\nVERIFIED CLAIMS: "
            + repr(verified_claims)
            + "\nSOURCE REGISTRY: "
            + repr(registry)
            + "\nCONSEQUENTIAL GAPS: "
            + repr(all_gaps),
            "draft-assembly",
            "Draft",
            DRAFT_SCHEMA,
            "synthesis",
        )
    else:
        partial_reasons.append(
            "section drafting did not produce enough usable sections; used one bounded draft"
        )
        draft_mode = "single"

if draft is None:
    draft = await dispatch(
        single_draft_prompt,
        "draft",
        "Draft",
        DRAFT_SCHEMA,
        "synthesis",
    )

if draft is None:
    return {
        "status": "failed",
        "report_markdown": "",
        "cited_sources": [],
        "gaps": all_gaps + ["drafting worker failed"],
        "run_summary": {
            "tier": tier,
            "base_lanes_requested": len(lanes),
            "base_lanes_completed": base_lanes_completed,
            "followups_run": followups_run,
            "escalations_run": escalations_run,
            "draft_mode": draft_mode,
        },
    }

report, cited_sources, deterministic_issues = assemble_report(draft, registry)

phase("Audit")
audit_prompt = (
    "Audit this report against the brief, report profile, verified claims, and source "
    "registry. Check support for material claims, calibrated certainty, fair scope, "
    "reader fit, structure, and voice. Be compact. A revision is needed only for a "
    "material issue, not optional polish. Treat deterministic issues as material.\n\n"
    "BRIEF: "
    + repr(brief)
    + "\nREPORT PROFILE: "
    + repr(report_profile)
    + "\nREPORT: "
    + report
    + "\nVERIFIED CLAIMS: "
    + repr(verified_claims)
    + "\nDETERMINISTIC ISSUES: "
    + repr(deterministic_issues)
)
audit_roles = ["evidence", "editorial"] if tier == "extended" or high_stakes else ["combined"]
audits = await parallel(
    [
        (
            lambda audit_role=audit_role: dispatch(
                audit_prompt + "\nAUDIT ROLE: " + audit_role,
                "audit:" + audit_role,
                "Audit",
                AUDIT_SCHEMA,
                "audit",
            )
        )
        for audit_role in audit_roles
    ]
)
audits = [audit for audit in audits if audit is not None]
material_issues = list(deterministic_issues)
for audit in audits:
    material_issues.extend(audit.get("material_issues", []))
if not audits:
    partial_reasons.append("the report audit failed")

remaining_material_issues = []
if material_issues or any(audit.get("revision_needed") for audit in audits):
    phase("Revise")
    revision = await dispatch(
        "Revise the report only to fix the material issues below. Preserve the "
        "reader-fit voice and supported useful detail. Use only exact registry URLs "
        "for citations. Return title and body without a Sources section. If an issue "
        "cannot be fixed from verified evidence, remove or narrow the claim and list "
        "the remaining issue.\n\nBRIEF: "
        + repr(brief)
        + "\nREPORT PROFILE: "
        + repr(report_profile)
        + "\nCURRENT REPORT: "
        + report
        + "\nMATERIAL ISSUES: "
        + repr(sorted(set(str(issue) for issue in material_issues if issue)))
        + "\nVERIFIED CLAIMS: "
        + repr(verified_claims)
        + "\nSOURCE REGISTRY: "
        + repr(registry),
        "revision",
        "Revise",
        REVISION_SCHEMA,
        "synthesis",
    )
    if revision is None:
        partial_reasons.append("material revision failed")
        remaining_material_issues = material_issues
    else:
        report, cited_sources, deterministic_issues = assemble_report(revision, registry)
        remaining_material_issues = list(revision.get("remaining_material_issues", []))
        remaining_material_issues.extend(deterministic_issues)

if high_stakes and remaining_material_issues:
    closure = await dispatch(
        "Perform a final evidence closure check only on the unresolved material "
        "issues. Do not edit prose and do not report formatting defects.\n\nREPORT: "
        + report
        + "\nUNRESOLVED MATERIAL ISSUES: "
        + repr(remaining_material_issues)
        + "\nVERIFIED CLAIMS: "
        + repr(verified_claims),
        "closure",
        "Audit",
        CLOSURE_SCHEMA,
        "verification",
    )
    if closure is None or not closure.get("supported"):
        remaining_material_issues = (
            closure.get("unresolved_material_issues", remaining_material_issues)
            if closure
            else remaining_material_issues
        )
    else:
        remaining_material_issues = []

final_structural_issues = structural_issues(report)
if final_structural_issues or remaining_material_issues:
    return {
        "status": "failed",
        "report_markdown": "",
        "cited_sources": [],
        "gaps": sorted(
            set(
                all_gaps
                + partial_reasons
                + final_structural_issues
                + [str(issue) for issue in remaining_material_issues]
            )
        ),
        "run_summary": {
            "tier": tier,
            "base_lanes_requested": len(lanes),
            "base_lanes_completed": base_lanes_completed,
            "followups_run": followups_run,
            "escalations_run": escalations_run,
            "draft_mode": draft_mode,
        },
    }

status = "partial" if partial_reasons or base_lanes_completed < len(lanes) else "complete"
return {
    "status": status,
    "report_markdown": report,
    "cited_sources": cited_sources,
    "gaps": sorted(set(all_gaps + partial_reasons)),
    "run_summary": {
        "tier": tier,
        "base_lanes_requested": len(lanes),
        "base_lanes_completed": base_lanes_completed,
        "followups_run": followups_run,
        "escalations_run": escalations_run,
        "draft_mode": draft_mode,
    },
}
