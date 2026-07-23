meta = {
    "name": "deep-research",
    "description": "Research disjoint lanes, adaptively verify claims, and produce a compact cited report",
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
                    "claim_type": {"type": "string"},
                    "verification_triggers": {"type": "array", "items": {"type": "string"}},
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
                    "status": {
                        "type": "string",
                        "enum": ["supported", "qualified", "unsupported", "unresolved"],
                    },
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

# Claim-type classification constants (optional fields; absent = legacy conservative mode)
EXTERNALLY_CHECKABLE_TYPES = {"external_fact", "quantitative", "causal", "comparative"}
TESTIMONY_TYPES = {"attributed_report", "interpretation"}
RISK_TRIGGERS = {"high_stakes", "known_dispute"}
SCOPE_TRIGGERS = {"cross_source_conflict", "scope_risk", "source_access_uncertain"}

# Stage-plan mode constants
VALID_VERIFICATION_MODES = {"risk_only", "selective", "required"}
VALID_FOLLOWUP_MODES = {"off", "thesis_changing"}
VALID_AUDIT_MODES = {"deterministic", "combined", "dual"}


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
        scout = (record or {}).get("scout") or {}
        for failure in scout.get("failures", []):
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


def is_eligible_for_verification(claim, mode):
    """Determine whether a claim should be sent to the verifier under the given mode.

    Claims with an explicit claim_type use the full classification matrix.
    Legacy claims (no claim_type) use a conservative heuristic.
    """
    claim_type = str(claim.get("claim_type", "")).strip()
    triggers = set(claim.get("verification_triggers") or [])
    importance = str(claim.get("importance", ""))
    disputed = bool(claim.get("disputed", False))

    if claim_type in TESTIMONY_TYPES:
        return False

    if claim_type not in EXTERNALLY_CHECKABLE_TYPES and claim_type:
        # Unknown explicit type — treat as not checkable
        return False
    if not claim_type:
        # Legacy: no claim_type; apply conservative heuristics
        if mode == "risk_only":
            return disputed
        return importance == "conclusion-driving" or disputed

    # Explicit externally-checkable type
    if mode == "risk_only":
        return bool(triggers & RISK_TRIGGERS)
    if mode in ("selective", "required"):
        return (
            importance == "conclusion-driving"
            or disputed
            or claim_type in ("quantitative", "causal", "comparative")
            or bool(triggers & (RISK_TRIGGERS | SCOPE_TRIGGERS))
        )
    return False


def claim_priority_key(claim):
    """Lower value = higher verification priority."""
    triggers = set(claim.get("verification_triggers") or [])
    importance = str(claim.get("importance", ""))
    claim_type = str(claim.get("claim_type", ""))
    if triggers & RISK_TRIGGERS:
        return 0
    if importance == "conclusion-driving" or claim_type in (
        "causal",
        "quantitative",
        "comparative",
    ):
        return 1
    return 2


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
        "\n\nFor each candidate claim include optional claim_type (attributed_report, "
        "external_fact, quantitative, causal, comparative, or interpretation) and "
        "verification_triggers (known_dispute, source_access_uncertain, "
        "cross_source_conflict, scope_risk, high_stakes) where applicable."
    )


def verification_prompt(scout, selected_claims, failed_ledger):
    return (
        "Verify only the selected candidate claims listed below. "
        "Do not re-research background claims or broadly re-fetch the scout's "
        "sources. Return a delta; never echo the scout record.\n\nBRIEF: "
        + repr(brief)
        + "\nSCOUT RECORD: "
        + repr(scout)
        + "\nSELECTED CLAIMS: "
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
        "qualified, unsupported, or unresolved. New records contain only genuinely "
        "new evidence tied to a verdict."
    )


def budget_allows_optional(extra=0):
    if budget.total is None:
        return True
    return budget.remaining() > writing_reserve + extra


def build_registry(records):
    """Build the source registry and supported-claim list from all research records.

    Every schema-valid scout source is preserved.  Verifier-added sources are
    admitted only when they are referenced by evidence tied to a valid verdict.
    Claims are assigned statuses: direct, supported, qualified, unsupported,
    unresolved, or deferred.  Lanes are never dropped due to verifier failure.
    """
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
        # Admit verifier-added sources only when evidence is approved by a valid
        # verdict for the same claim.
        valid_verifier_statuses = {
            "supported",
            "qualified",
            "unsupported",
            "unresolved",
        }
        selected_claim_ids = set(str(claim_id) for claim_id in record.get("selected_claim_ids", []))
        approved_new_evidence_ids = set()
        verdicts = verifier.get("verdicts", [])
        new_evidence = verifier.get("new_evidence", [])
        for verdict in verdicts:
            if verdict.get("status") not in valid_verifier_statuses:
                continue
            verdict_claim_id = str(verdict.get("claim_id", ""))
            if verdict_claim_id not in selected_claim_ids:
                continue
            approved_ids = set(str(eid) for eid in verdict.get("approved_evidence_ids", []))
            for evidence_item in new_evidence:
                evidence_id = str(evidence_item.get("id", ""))
                if (
                    evidence_id in approved_ids
                    and str(evidence_item.get("claim_id", "")) == verdict_claim_id
                ):
                    approved_new_evidence_ids.add(evidence_id)
        new_ev_by_source = {}
        for ev in new_evidence:
            sid = str(ev.get("source_id", ""))
            if sid:
                new_ev_by_source.setdefault(sid, set()).add(str(ev.get("id", "")))
        for source in verifier.get("new_sources", []):
            src_id = str(source.get("id", ""))
            ev_ids_for_source = new_ev_by_source.get(src_id, set())
            if ev_ids_for_source & approved_new_evidence_ids:
                key = canonical_url(source.get("url"))
                if key:
                    raw_sources.append((key, lane_id, source))
                    source_keys[(lane_id, src_id)] = key

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

    supported_claims = []
    lane_summaries = []
    all_gaps = []
    valid_statuses = {"supported", "qualified", "unsupported", "unresolved"}

    for record in records:
        scout = record.get("scout") or {}
        verifier = record.get("verification") or {}
        lane_id = str(scout.get("lane_id", "lane"))
        selected_ids = set(record.get("selected_claim_ids") or [])
        deferred_ids = set(record.get("deferred_claim_ids") or [])
        verifier_failed = bool(record.get("verifier_failed", False))

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
            claim_id = str(claim.get("id", ""))
            verdict = verdicts.get(claim_id)

            if claim_id in deferred_ids:
                status = "deferred"
                qualification = ""
            elif claim_id in selected_ids:
                if verifier_failed:
                    status = "unresolved"
                    qualification = ""
                elif verdict:
                    raw_status = str(verdict.get("status", "unresolved"))
                    status = raw_status if raw_status in valid_statuses else "unresolved"
                    qualification = str(verdict.get("qualification", ""))
                else:
                    # Verifier ran but omitted this claim
                    status = "unresolved"
                    qualification = ""
            else:
                # Not sent for verification — usable as directly attributed
                status = "direct"
                qualification = ""

            # Use approved evidence or fall back to all evidence IDs for direct claims
            if verdict and verdict.get("approved_evidence_ids"):
                approved_eids = verdict.get("approved_evidence_ids")
            else:
                approved_eids = claim.get("evidence_ids", [])

            source_ids = []
            excerpts = []
            for eid in approved_eids:
                ev_item = evidence.get(eid) or {}
                source_key = source_keys.get((lane_id, str(ev_item.get("source_id", ""))))
                if source_key and source_key in registry_ids:
                    source_ids.append(registry_ids[source_key])
                excerpt = ev_item.get("quote_or_paraphrase")
                if excerpt:
                    excerpts.append(str(excerpt))

            if source_ids:
                supported_claims.append(
                    {
                        "id": lane_id + "/" + claim_id,
                        "text": claim.get("text", ""),
                        "status": status,
                        "qualification": qualification,
                        "source_ids": sorted(set(source_ids)),
                        "evidence": excerpts,
                    }
                )

    return (
        registry,
        supported_claims,
        lane_summaries,
        sorted(set(str(gap) for gap in all_gaps if gap)),
    )


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
        source_lines.append(
            "- [" + source.get("title", key) + "](" + source.get("url", key) + ")" + suffix
        )
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


# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------
validation_errors = []
if not isinstance(args, dict):
    validation_errors.append("args must be an object")
brief = args.get("brief", {}) if isinstance(args, dict) else {}
tier = args.get("tier", "") if isinstance(args, dict) else ""
lanes = args.get("lanes", []) if isinstance(args, dict) else []
acquisition = args.get("acquisition", {}) if isinstance(args, dict) else {}
report_profile = args.get("report_profile", {}) if isinstance(args, dict) else {}
routes = args.get("routes", {}) if isinstance(args, dict) else {}
intake = args.get("intake", {}) if isinstance(args, dict) else {}

lane_ranges = {"focused": (2, 2), "standard": (3, 4), "extended": (5, 6)}
tier_caps = {"focused": (4, 6), "standard": (6, 8), "extended": (8, 12)}
if not isinstance(brief, dict) or not str(brief.get("question", "")).strip():
    validation_errors.append("brief.question is required")
if not isinstance(brief, dict) or not str(brief.get("audience", "")).strip():
    validation_errors.append("brief.audience is required")
if not isinstance(brief, dict) or not str(brief.get("scope", "")).strip():
    validation_errors.append("brief.scope is required")
if tier not in lane_ranges:
    validation_errors.append("tier must be focused, standard, or extended")
if not isinstance(lanes, list):
    validation_errors.append("lanes must be an array")
elif tier in lane_ranges:
    minimum, maximum = lane_ranges[tier]
    if len(lanes) < minimum or len(lanes) > maximum:
        validation_errors.append(
            tier
            + " requires "
            + str(minimum)
            + ("-" + str(maximum) if minimum != maximum else "")
            + " lanes"
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
length_preset = report_profile.get("length", "") if isinstance(report_profile, dict) else ""
target_words = report_profile.get("target_words") if isinstance(report_profile, dict) else None
length_targets = {"concise": 1500, "standard": 3000, "detailed": 6000}
if length_preset not in ("concise", "standard", "detailed", "long", "custom"):
    validation_errors.append(
        "report_profile.length must be concise, standard, detailed, long, or custom"
    )
if not isinstance(target_words, int) or isinstance(target_words, bool) or target_words < 500:
    validation_errors.append("report_profile.target_words must be an integer of at least 500")
elif length_preset in length_targets and target_words != length_targets[length_preset]:
    validation_errors.append(
        "report_profile.target_words does not match the selected length preset"
    )
elif length_preset == "long" and target_words < 10000:
    validation_errors.append("report_profile.long requires at least 10000 target words")

required_intake_fields = {"length", "audience_use", "scope", "delivery"}
if not isinstance(intake, dict):
    validation_errors.append("intake must be an object")
else:
    intake_mode = intake.get("mode")
    intake_confirmed = intake.get("confirmed")
    resolved_fields = intake.get("resolved_fields")
    topic_questions_asked = intake.get("topic_questions_asked")
    if intake_mode not in ("interactive", "user_directed_defaults"):
        validation_errors.append("intake.mode must be interactive or user_directed_defaults")
    if intake_mode == "interactive" and intake_confirmed is not True:
        validation_errors.append("interactive intake must be confirmed")
    if not isinstance(resolved_fields, list) or not required_intake_fields.issubset(
        set(str(field) for field in resolved_fields)
    ):
        validation_errors.append(
            "intake.resolved_fields must include length, audience_use, scope, and delivery"
        )
    if (
        not isinstance(topic_questions_asked, int)
        or isinstance(topic_questions_asked, bool)
        or (intake_mode == "interactive" and not 1 <= topic_questions_asked <= 3)
        or (intake_mode == "user_directed_defaults" and topic_questions_asked != 0)
    ):
        validation_errors.append(
            "intake.topic_questions_asked must be 1-3 for interactive intake "
            "or 0 for user_directed_defaults"
        )

writing_reserve = args.get("writing_reserve_tokens", 18000) if isinstance(args, dict) else 18000
batch_size = args.get("research_batch_size", 2) if isinstance(args, dict) else 2
if not isinstance(writing_reserve, int) or writing_reserve < 0:
    validation_errors.append("writing_reserve_tokens must be a nonnegative integer")
if (
    not isinstance(batch_size, int)
    or batch_size < 1
    or batch_size > (3 if tier == "extended" else 2)
):
    validation_errors.append("research_batch_size exceeds the tier concurrency limit")

# ---------------------------------------------------------------------------
# Stage-plan parsing (optional; defaults: selective + thesis_changing + combined)
# ---------------------------------------------------------------------------
stage_plan_arg = args.get("stage_plan", {}) if isinstance(args, dict) else {}
if not isinstance(stage_plan_arg, dict):
    stage_plan_arg = {}

verification_mode = str(stage_plan_arg.get("verification", "selective")).strip() or "selective"
followup_mode = str(stage_plan_arg.get("followup", "thesis_changing")).strip() or "thesis_changing"
audit_mode = str(stage_plan_arg.get("audit", "combined")).strip() or "combined"
plan_reason = str(stage_plan_arg.get("reason", "")).strip()

if verification_mode not in VALID_VERIFICATION_MODES:
    validation_errors.append("stage_plan.verification must be risk_only, selective, or required")
    verification_mode = "selective"
if followup_mode not in VALID_FOLLOWUP_MODES:
    validation_errors.append("stage_plan.followup must be off or thesis_changing")
    followup_mode = "thesis_changing"
if audit_mode not in VALID_AUDIT_MODES:
    validation_errors.append("stage_plan.audit must be deterministic, combined, or dual")
    audit_mode = "combined"

resolved_plan = {
    "verification": verification_mode,
    "followup": followup_mode,
    "audit": audit_mode,
    "reason": plan_reason,
}

if validation_errors:
    return {
        "status": "failed",
        "report_markdown": "",
        "cited_sources": [],
        "gaps": validation_errors,
        "run_summary": {
            "stage_plan": resolved_plan,
            "stages_run": [],
            "stages_skipped": [],
            "eligible_claims": 0,
            "selected_claims": 0,
            "deferred_claims": 0,
            "verifier_calls": 0,
            "lanes_skipped_no_eligible": 0,
            "verifier_verdict_counts": {},
            "tier": tier or "unknown",
            "base_lanes_requested": len(lanes) if isinstance(lanes, list) else 0,
            "base_lanes_completed": 0,
            "followups_run": 0,
            "escalations_run": 0,
            "draft_mode": "single",
        },
    }

# ---------------------------------------------------------------------------
# Telemetry accumulators
# ---------------------------------------------------------------------------
stages_run = []
stages_skipped = []
verifier_calls_made = 0
draft_mode = "single"

# ---------------------------------------------------------------------------
# Research phase
# ---------------------------------------------------------------------------
phase("Research")
stages_run.append("Research")
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
            research_records.append(
                {
                    "scout": scout,
                    "verification": None,
                    "eligible_claim_ids": [],
                    "selected_claim_ids": [],
                    "deferred_claim_ids": [],
                    "verifier_failed": False,
                }
            )

# ---------------------------------------------------------------------------
# Deterministic claim selection
# ---------------------------------------------------------------------------
# Compute eligible claims per lane
for record in research_records:
    eligible = [
        c
        for c in record["scout"].get("candidate_claims", [])
        if is_eligible_for_verification(c, verification_mode)
    ]
    record["eligible_claim_ids"] = [c["id"] for c in eligible]

lanes_skipped_no_eligible_count = sum(1 for r in research_records if not r["eligible_claim_ids"])

# Global verifier-call cap
if verification_mode == "risk_only":
    max_verifier_calls = 1
elif verification_mode == "selective":
    max_verifier_calls = 3 if tier == "extended" else 2
else:
    # required: one per successful lane, capped at six
    max_verifier_calls = min(len(research_records), 6)

# Selective verification prioritizes a thesis-changing follow-up over the
# lowest-priority eligible main lane. Reserve one call only when a follow-up
# was actually requested and could consume it; unused capacity is otherwise
# available to main-lane verification.
reserve_followup_verifier = (
    verification_mode == "selective"
    and followup_mode == "thesis_changing"
    and tier != "focused"
    and max_verifier_calls > 0
)
main_lane_verifier_cap = max_verifier_calls - (1 if reserve_followup_verifier else 0)

# Sort eligible lanes by priority of their best-priority eligible claim
records_with_eligible = [r for r in research_records if r["eligible_claim_ids"]]


def lane_priority_sort_key(record):
    eids = set(record["eligible_claim_ids"])
    eligible_claims = [
        c for c in record["scout"].get("candidate_claims", []) if c.get("id") in eids
    ]
    if not eligible_claims:
        return (999,)
    return (min(claim_priority_key(c) for c in eligible_claims),)


records_sorted_by_priority = sorted(records_with_eligible, key=lane_priority_sort_key)
records_to_verify = records_sorted_by_priority[:main_lane_verifier_cap]
selected_lane_ids = set(str(r["scout"].get("lane_id", "")) for r in records_to_verify)

# Assign selected / deferred claim IDs per lane
for record in records_with_eligible:
    lane_id_key = str(record["scout"].get("lane_id", ""))
    eid_set = set(record["eligible_claim_ids"])
    eligible_claims = [
        c for c in record["scout"].get("candidate_claims", []) if c.get("id") in eid_set
    ]
    if lane_id_key in selected_lane_ids:
        sorted_claims = sorted(eligible_claims, key=claim_priority_key)
        record["selected_claim_ids"] = [c["id"] for c in sorted_claims[:8]]
        record["deferred_claim_ids"] = [c["id"] for c in sorted_claims[8:]]
    else:
        # Lane cut by global cap — all eligible claims deferred
        record["deferred_claim_ids"] = list(record["eligible_claim_ids"])

# ---------------------------------------------------------------------------
# Verify phase (conditional — only when there are selected claims)
# ---------------------------------------------------------------------------
if records_to_verify:
    phase("Verify")
    stages_run.append("Verify")
    failed_ledger = compact_failed_ledger(research_records)
    for start in range(0, len(records_to_verify), batch_size):
        batch = records_to_verify[start : start + batch_size]
        results = await parallel(
            [
                (
                    lambda record=record: dispatch(
                        verification_prompt(
                            record["scout"],
                            [
                                c
                                for c in record["scout"].get("candidate_claims", [])
                                if c.get("id") in set(record["selected_claim_ids"])
                            ],
                            failed_ledger,
                        ),
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
            verifier_calls_made += 1
            if verification is None:
                # Failed optional stage — keep lane, mark claims unresolved
                record["verifier_failed"] = True
            else:
                record["verification"] = verification
else:
    stages_skipped.append("Verify")
    failed_ledger = compact_failed_ledger(research_records)

# Count of lanes that contributed usable scout results
base_lanes_completed = len(research_records)

# ---------------------------------------------------------------------------
# Acquisition escalation (optional, applies remaining verifier cap)
# ---------------------------------------------------------------------------
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
    esc_scout = await dispatch(
        escalation_prompt,
        "escalation:" + str(kind),
        "Research",
        SCOUT_SCHEMA,
        "acquisition",
        "browser" if kind == "browser" else "investigation",
    )
    escalations_run = 1
    if esc_scout is None:
        partial_reasons.append("the single acquisition escalation failed")
    else:
        esc_record = {
            "scout": esc_scout,
            "verification": None,
            "eligible_claim_ids": [],
            "selected_claim_ids": [],
            "deferred_claim_ids": [],
            "verifier_failed": False,
        }
        esc_eligible = [
            c
            for c in esc_scout.get("candidate_claims", [])
            if is_eligible_for_verification(c, verification_mode)
        ]
        esc_record["eligible_claim_ids"] = [c["id"] for c in esc_eligible]

        esc_cap_limit = (
            1
            if verification_mode == "risk_only"
            else main_lane_verifier_cap
            if verification_mode == "selective"
            else 6
        )
        if esc_eligible and verifier_calls_made < esc_cap_limit:
            sorted_esc = sorted(esc_eligible, key=claim_priority_key)
            esc_record["selected_claim_ids"] = [c["id"] for c in sorted_esc[:8]]
            esc_record["deferred_claim_ids"] = [c["id"] for c in sorted_esc[8:]]
            esc_failed_ledger = compact_failed_ledger(research_records + [esc_record])
            esc_selected_claims = [
                c
                for c in esc_scout.get("candidate_claims", [])
                if c.get("id") in set(esc_record["selected_claim_ids"])
            ]
            esc_verification = await dispatch(
                verification_prompt(esc_scout, esc_selected_claims, esc_failed_ledger)
                + "\nDo not reacquire the escalation target; assess the returned "
                "evidence and seek ordinary independent support only if essential.",
                "verify:acquisition-escalation",
                "Verify",
                VERIFIER_SCHEMA,
                "verification",
            )
            verifier_calls_made += 1
            if esc_verification is None:
                partial_reasons.append("the acquisition escalation could not be verified")
                esc_record["verifier_failed"] = True
            else:
                esc_record["verification"] = esc_verification
        elif esc_eligible:
            esc_record["deferred_claim_ids"] = list(esc_record["eligible_claim_ids"])

        research_records.append(esc_record)

# First registry build (for coverage's lane summaries and claim index)
registry, supported_claims, lane_summaries, evidence_gaps = build_registry(research_records)

# ---------------------------------------------------------------------------
# Coverage phase (conditional)
# ---------------------------------------------------------------------------
required_structure = (
    report_profile.get("required_structure", []) if isinstance(report_profile, dict) else []
)
run_coverage = (
    followup_mode == "thesis_changing"
    or target_words >= 5000
    or (isinstance(required_structure, list) and len(required_structure) >= 2)
)

coverage = None
if run_coverage and research_records:
    phase("Coverage")
    stages_run.append("Coverage")
    coverage = await dispatch(
        "Assess whether one bounded follow-up could change the thesis or recommendation. "
        "Do not research. Focused work must not request a follow-up. A Standard or "
        "Extended follow-up must identify the exact decision affected and one narrow, "
        "non-overlapping lane. Return followup_needed=false for merely useful context. "
        "Also decide the reader-facing drafting shape. Section drafting is warranted "
        "for a target of roughly 5000 words or more, or for a shorter report only when "
        "at least two genuinely independent sections have distinct supported claim sets. "
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
        + "\nSUPPORTED LANE SUMMARIES: "
        + repr(lane_summaries)
        + "\nSUPPORTED CLAIMS: "
        + repr(supported_claims)
        + "\nGAPS: "
        + repr(evidence_gaps)
        + "\nFAILED ACQUISITIONS: "
        + repr(compact_failed_ledger(research_records)),
        "coverage",
        "Coverage",
        COVERAGE_SCHEMA,
        "audit",
    )
else:
    stages_skipped.append("Coverage")

# ---------------------------------------------------------------------------
# Follow-up lane (conditional on followup_mode and coverage recommendation)
# ---------------------------------------------------------------------------
followups_run = 0
if (
    followup_mode == "thesis_changing"
    and tier != "focused"
    and coverage
    and coverage.get("followup_needed")
    and str(coverage.get("decision_affected", "")).strip()
    and isinstance(coverage.get("followup_lane"), dict)
    and budget_allows_optional(verification_fetches * 250)
):
    followup_lane = coverage["followup_lane"]
    followup_scout_result = await dispatch(
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

    if followup_scout_result is not None:
        followup_record = {
            "scout": followup_scout_result,
            "verification": None,
            "eligible_claim_ids": [],
            "selected_claim_ids": [],
            "deferred_claim_ids": [],
            "verifier_failed": False,
        }
        fu_eligible = [
            c
            for c in followup_scout_result.get("candidate_claims", [])
            if is_eligible_for_verification(c, verification_mode)
        ]
        followup_record["eligible_claim_ids"] = [c["id"] for c in fu_eligible]

        fu_cap_limit = (
            1
            if verification_mode == "risk_only"
            else max_verifier_calls
            if verification_mode == "selective"
            else 6
        )
        if fu_eligible and verifier_calls_made < fu_cap_limit:
            sorted_fu = sorted(fu_eligible, key=claim_priority_key)
            followup_record["selected_claim_ids"] = [c["id"] for c in sorted_fu[:8]]
            followup_record["deferred_claim_ids"] = [c["id"] for c in sorted_fu[8:]]
            fu_failed_ledger = compact_failed_ledger(research_records)
            fu_selected_claims = [
                c
                for c in followup_scout_result.get("candidate_claims", [])
                if c.get("id") in set(followup_record["selected_claim_ids"])
            ]
            fu_verification = await dispatch(
                verification_prompt(followup_scout_result, fu_selected_claims, fu_failed_ledger)
                + "\nDo not reacquire the follow-up target; assess the returned "
                "evidence and seek ordinary independent support only if essential.",
                "followup:verify",
                "Verify",
                VERIFIER_SCHEMA,
                "verification",
            )
            verifier_calls_made += 1
            if fu_verification is None:
                followup_record["verifier_failed"] = True
            else:
                followup_record["verification"] = fu_verification
        elif fu_eligible:
            followup_record["deferred_claim_ids"] = list(followup_record["eligible_claim_ids"])

        research_records.append(followup_record)
        followups_run = 1
    else:
        partial_reasons.append("the single decision-changing follow-up failed")

# Final registry build (includes follow-up lane if present)
registry, supported_claims, lane_summaries, evidence_gaps = build_registry(research_records)
all_gaps = sorted(set(partial_reasons + evidence_gaps + ((coverage or {}).get("gaps", []))))

# ---------------------------------------------------------------------------
# Additive telemetry counts (computed once; reused in all return paths)
# ---------------------------------------------------------------------------
total_eligible = sum(len(r.get("eligible_claim_ids", [])) for r in research_records)
total_selected = sum(len(r.get("selected_claim_ids", [])) for r in research_records)
total_deferred = sum(len(r.get("deferred_claim_ids", [])) for r in research_records)

verifier_verdict_counts = {}
for record in research_records:
    for verdict in (record.get("verification") or {}).get("verdicts", []):
        vs = str(verdict.get("status", "unknown"))
        verifier_verdict_counts[vs] = verifier_verdict_counts.get(vs, 0) + 1

# Claims usable for drafting (all statuses except unsupported)
citable_claims = [c for c in supported_claims if c.get("status") != "unsupported"]

if not citable_claims or not registry:
    return {
        "status": "failed",
        "report_markdown": "",
        "cited_sources": [],
        "gaps": all_gaps + ["no supported claim set was sufficient to draft a cited report"],
        "run_summary": {
            "stage_plan": resolved_plan,
            "stages_run": stages_run,
            "stages_skipped": stages_skipped,
            "eligible_claims": total_eligible,
            "selected_claims": total_selected,
            "deferred_claims": total_deferred,
            "verifier_calls": verifier_calls_made,
            "lanes_skipped_no_eligible": lanes_skipped_no_eligible_count,
            "verifier_verdict_counts": verifier_verdict_counts,
            "tier": tier,
            "base_lanes_requested": len(lanes),
            "base_lanes_completed": base_lanes_completed,
            "followups_run": followups_run,
            "escalations_run": escalations_run,
            "draft_mode": draft_mode,
        },
    }

# ---------------------------------------------------------------------------
# Draft phase
# ---------------------------------------------------------------------------
STATUS_USE_MATRIX = (
    "Status-use matrix:\n"
    "direct – cite and attribute; do not describe as independently verified.\n"
    "supported – may support a factual conclusion.\n"
    "qualified – preserve the qualification near the affected claim.\n"
    "unresolved/deferred – omit from decisive conclusions; may include only as "
    "clearly attributed testimony with explicit scope limits."
)

phase("Draft")
stages_run.append("Draft")
single_draft_prompt = (
    "Write the complete reader-facing report from the supported-claim registry below. "
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
    + "\nSUPPORTED CLAIMS: "
    + repr(citable_claims)
    + "\nSOURCE REGISTRY: "
    + repr(registry)
    + "\nCONSEQUENTIAL GAPS: "
    + repr(all_gaps)
    + "\n\n"
    + STATUS_USE_MATRIX
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
    claims_by_id = {claim.get("id"): claim for claim in citable_claims}
    section_target = max(500, target_words // len(section_outline))
    section_results = await parallel(
        [
            (
                lambda section=section, section_index=section_index: dispatch(
                    "Draft one bounded report section. Use only the assigned supported "
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
                    + "\nASSIGNED SUPPORTED CLAIMS: "
                    + repr(
                        [
                            claims_by_id[claim_id]
                            for claim_id in section.get("claim_ids", [])
                            if claim_id in claims_by_id
                        ]
                    )
                    + "\nSOURCE REGISTRY: "
                    + repr(registry)
                    + "\n\n"
                    + STATUS_USE_MATRIX,
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
            + "\nSUPPORTED CLAIMS: "
            + repr(citable_claims)
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
            "stage_plan": resolved_plan,
            "stages_run": stages_run,
            "stages_skipped": stages_skipped,
            "eligible_claims": total_eligible,
            "selected_claims": total_selected,
            "deferred_claims": total_deferred,
            "verifier_calls": verifier_calls_made,
            "lanes_skipped_no_eligible": lanes_skipped_no_eligible_count,
            "verifier_verdict_counts": verifier_verdict_counts,
            "tier": tier,
            "base_lanes_requested": len(lanes),
            "base_lanes_completed": base_lanes_completed,
            "followups_run": followups_run,
            "escalations_run": escalations_run,
            "draft_mode": draft_mode,
        },
    }

report, cited_sources, deterministic_issues = assemble_report(draft, registry)

# ---------------------------------------------------------------------------
# Audit phase (conditional on audit_mode)
# ---------------------------------------------------------------------------
if audit_mode == "dual":
    audit_roles = ["evidence", "editorial"]
elif audit_mode == "combined":
    audit_roles = ["combined"]
else:
    audit_roles = []  # deterministic — no agent audit

material_issues = list(deterministic_issues)

if audit_roles:
    phase("Audit")
    stages_run.append("Audit")
    audit_prompt = (
        "Audit this report against the brief, report profile, supported claims, and "
        "source registry. Check support for material claims, calibrated certainty, "
        "fair scope, reader fit, structure, and voice. Be compact. A revision is "
        "needed only for a material issue, not optional polish. "
        "Treat deterministic issues as material. "
        "For experiential and testimony-based reports focus on attribution, "
        "overgeneralization, sample limits, and separation of testimony from "
        "inference — not relitigating whether the reported experience occurred.\n\n"
        "BRIEF: "
        + repr(brief)
        + "\nREPORT PROFILE: "
        + repr(report_profile)
        + "\nREPORT: "
        + report
        + "\nSUPPORTED CLAIMS: "
        + repr(citable_claims)
        + "\nDETERMINISTIC ISSUES: "
        + repr(deterministic_issues)
    )
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
    for audit in audits:
        material_issues.extend(audit.get("material_issues", []))
    if not audits:
        partial_reasons.append("the report audit failed")
else:
    stages_skipped.append("Audit")
    audits = []

# ---------------------------------------------------------------------------
# Revision (at most one, only when material issues exist)
# ---------------------------------------------------------------------------
remaining_material_issues = []
if material_issues or any(audit.get("revision_needed") for audit in audits):
    phase("Revise")
    stages_run.append("Revise")
    revision = await dispatch(
        "Revise the report only to fix the material issues below. Preserve the "
        "reader-fit voice and supported useful detail. Use only exact registry URLs "
        "for citations. Return title and body without a Sources section. If an issue "
        "cannot be fixed from supported evidence, remove or narrow the claim and list "
        "the remaining issue.\n\nBRIEF: "
        + repr(brief)
        + "\nREPORT PROFILE: "
        + repr(report_profile)
        + "\nCURRENT REPORT: "
        + report
        + "\nMATERIAL ISSUES: "
        + repr(sorted(set(str(issue) for issue in material_issues if issue)))
        + "\nSUPPORTED CLAIMS: "
        + repr(citable_claims)
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

# ---------------------------------------------------------------------------
# High-stakes closure check (retained)
# ---------------------------------------------------------------------------
if high_stakes and remaining_material_issues:
    closure = await dispatch(
        "Perform a final evidence closure check only on the unresolved material "
        "issues. Do not edit prose and do not report formatting defects.\n\nREPORT: "
        + report
        + "\nUNRESOLVED MATERIAL ISSUES: "
        + repr(remaining_material_issues)
        + "\nSUPPORTED CLAIMS: "
        + repr(citable_claims),
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

# ---------------------------------------------------------------------------
# Deterministic final structural check (always runs)
# ---------------------------------------------------------------------------
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
            "stage_plan": resolved_plan,
            "stages_run": stages_run,
            "stages_skipped": stages_skipped,
            "eligible_claims": total_eligible,
            "selected_claims": total_selected,
            "deferred_claims": total_deferred,
            "verifier_calls": verifier_calls_made,
            "lanes_skipped_no_eligible": lanes_skipped_no_eligible_count,
            "verifier_verdict_counts": verifier_verdict_counts,
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
        "stage_plan": resolved_plan,
        "stages_run": stages_run,
        "stages_skipped": stages_skipped,
        "eligible_claims": total_eligible,
        "selected_claims": total_selected,
        "deferred_claims": total_deferred,
        "verifier_calls": verifier_calls_made,
        "lanes_skipped_no_eligible": lanes_skipped_no_eligible_count,
        "verifier_verdict_counts": verifier_verdict_counts,
        "tier": tier,
        "base_lanes_requested": len(lanes),
        "base_lanes_completed": base_lanes_completed,
        "followups_run": followups_run,
        "escalations_run": escalations_run,
        "draft_mode": draft_mode,
    },
}
