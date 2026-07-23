from __future__ import annotations

import ast
import asyncio
import json
import tempfile
import types
import unittest
from pathlib import Path
from typing import Any

from scripts.package_skill import package_skill

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "deep-research"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
WORKFLOW_PATH = SKILL_ROOT / "scripts" / "deep-research.workflow"
MATERIALIZER_PATH = SKILL_ROOT / "scripts" / "materialize_report.py"


def load_materializer() -> Any:
    namespace: dict[str, Any] = {
        "__name__": "deep_research_materializer",
        "__file__": str(MATERIALIZER_PATH),
    }
    source = MATERIALIZER_PATH.read_text(encoding="utf-8")
    exec(compile(source, str(MATERIALIZER_PATH), "exec"), namespace)  # noqa: S102
    return types.SimpleNamespace(**namespace)


MATERIALIZER = load_materializer()


# ---------------------------------------------------------------------------
# Scout / verifier helper factories for custom claim scenarios
# ---------------------------------------------------------------------------


def _make_scout(
    lane_id: str,
    claim_type: str | None = None,
    *,
    disputed: bool = False,
    triggers: list[str] | None = None,
    importance: str = "conclusion-driving",
) -> dict[str, Any]:
    """Return a minimal valid scout record for use in scout_overrides."""
    claim: dict[str, Any] = {
        "id": "C1",
        "text": f"Material claim for {lane_id}.",
        "evidence_ids": ["E1"],
        "importance": importance,
        "disputed": disputed,
    }
    if claim_type is not None:
        claim["claim_type"] = claim_type
    if triggers is not None:
        claim["verification_triggers"] = triggers
    return {
        "lane_id": lane_id,
        "summary": f"Summary for {lane_id}.",
        "sources": [
            {
                "id": "SRC1",
                "title": f"Source for {lane_id}",
                "url": f"https://example.test/{lane_id}",
                "publisher": "Example",
                "date": "2025",
                "source_type": "primary",
            }
        ],
        "evidence": [
            {
                "id": "E1",
                "claim": f"Material claim for {lane_id}.",
                "source_id": "SRC1",
                "quote_or_paraphrase": "A supporting passage.",
            }
        ],
        "candidate_claims": [claim],
        "failures": [],
        "gaps": [],
    }


def _make_scout_with_many_claims(
    lane_id: str,
    count: int,
    claim_type: str,
    triggers: list[str] | None = None,
) -> dict[str, Any]:
    """Return a scout record with `count` claims, all conclusion-driving."""
    claims: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for i in range(1, count + 1):
        c: dict[str, Any] = {
            "id": f"C{i}",
            "text": f"Claim {i} for {lane_id}.",
            "evidence_ids": [f"E{i}"],
            "importance": "conclusion-driving",
            "disputed": False,
            "claim_type": claim_type,
        }
        if triggers is not None:
            c["verification_triggers"] = triggers
        claims.append(c)
        evidence.append(
            {
                "id": f"E{i}",
                "claim": f"Claim {i} for {lane_id}.",
                "source_id": "SRC1",
                "quote_or_paraphrase": f"Passage {i}.",
            }
        )
    return {
        "lane_id": lane_id,
        "summary": f"Summary for {lane_id} ({count} claims).",
        "sources": [
            {
                "id": "SRC1",
                "title": f"Source for {lane_id}",
                "url": f"https://example.test/{lane_id}",
                "publisher": "Example",
                "date": "2025",
                "source_type": "primary",
            }
        ],
        "evidence": evidence,
        "candidate_claims": claims,
        "failures": [],
        "gaps": [],
    }


class DeepResearchSkillContractTests(unittest.TestCase):
    def test_briefing_precedes_gigacode_and_sequential_fallback(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")
        guide = (SKILL_ROOT / "references" / "gigacode-workflow.md").read_text(encoding="utf-8")
        normalized_skill = " ".join(skill.split())

        briefing = skill.index("## Brief the report with the user")
        preflight = skill.index("## Check Gigacode before research")
        apply_brief = skill.index("## 1. Apply the confirmed brief")
        self.assertLess(briefing, preflight)
        self.assertLess(preflight, apply_brief)
        self.assertIn("Explicitly ask the user to confirm or correct\nthe brief, and wait.", skill)
        self.assertIn(
            "After the brief is confirmed, check whether `run_workflow` is available",
            normalized_skill,
        )
        self.assertIn("Run `/gigacode on`", skill)
        self.assertIn("Do not start the\nsequential fallback until the user chooses it.", skill)
        self.assertIn("do not ask again during that research request", skill)
        self.assertIn(
            "absence of `list_subagent_models` alone does\nnot mean Gigacode is off", skill
        )
        self.assertIn("do not silently fall back", guide)

    def test_briefing_contract_requires_core_and_topic_specific_questions(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")
        guide = (SKILL_ROOT / "references" / "gigacode-workflow.md").read_text(encoding="utf-8")
        normalized_skill = " ".join(skill.split())
        normalized_guide = " ".join(guide.split())

        for core_field in ("Length", "Audience and use", "Scope", "Delivery"):
            self.assertIn(f"**{core_field}**", skill)
        self.assertIn("Ask only what remains unresolved", skill)
        self.assertIn("ask 1–3 concise questions", normalized_skill)
        self.assertIn(
            "Do not ask generic questions that merely restate the title", normalized_skill
        )
        self.assertIn(
            "tier, lanes, models, verification, audit, or drafting mode",
            normalized_skill,
        )
        self.assertIn("**Proposed research brief**", skill)
        self.assertIn("Record this as a user-directed exception", normalized_skill)
        self.assertIn("reopens only the affected part of the brief", normalized_skill)
        self.assertIn("Bypassing Gigacode does not bypass intake", normalized_skill)

        expected_lengths = {
            "concise": "1,500",
            "standard": "3,000",
            "detailed": "6,000",
            "long": "10,000",
        }
        for preset, words in expected_lengths.items():
            self.assertIn(f"`{preset}`", skill)
            self.assertIn(words, skill)
        self.assertIn("custom word target", normalized_skill)
        self.assertIn("There is no silent default for `target_words`", normalized_guide)

    def test_briefing_examples_cover_sparse_and_detailed_requests(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn('**Underspecified request — "Research the history', skill)
        self.assertIn("Ask all four plus a topic question in one batch", skill)
        self.assertIn("**Detailed initial request", skill)
        self.assertIn("Skip those questions and ask only what remains", skill)

    def test_prefers_same_model_family_for_stage_routes(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")
        guide = (SKILL_ROOT / "references" / "gigacode-workflow.md").read_text(encoding="utf-8")
        normalized_skill = " ".join(skill.split())
        normalized_guide = " ".join(guide.split())

        self.assertIn("anchor routing to the effective Investigation default", normalized_skill)
        self.assertIn("same exact model with lower effort", normalized_skill)
        self.assertIn("clearly related faster sibling", normalized_skill)
        self.assertIn("Do not assemble a sampler of unrelated providers", normalized_skill)
        self.assertIn("only when the user directs it", normalized_skill)
        self.assertIn("Sharing a provider is not enough", normalized_guide)
        self.assertIn("Keep a capability-driven exception to the affected role", normalized_guide)


class FakeBudget:
    def __init__(self, total: int | None = None, spent_per_agent: int = 100) -> None:
        self.total = total
        self._spent = 0
        self.spent_per_agent = spent_per_agent

    def spent(self) -> int:
        return self._spent

    def remaining(self) -> float | int:
        if self.total is None:
            return float("inf")
        return max(0, self.total - self._spent)

    def charge(self) -> None:
        self._spent += self.spent_per_agent


class FakeWorkflowHarness:
    def __init__(
        self,
        args: dict[str, Any],
        *,
        followup_needed: bool = False,
        section_drafting_needed: bool | None = None,
        fail_labels: set[str] | None = None,
        budget: FakeBudget | None = None,
        default_claim_type: str | None = None,
        scout_overrides: dict[str, dict[str, Any]] | None = None,
        verifier_overrides: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.args = args
        self.followup_needed = followup_needed
        self.section_drafting_needed = section_drafting_needed
        self.fail_labels = fail_labels or set()
        self.budget = budget or FakeBudget()
        self.default_claim_type = default_claim_type
        self.scout_overrides = scout_overrides or {}
        self.verifier_overrides = verifier_overrides or {}
        self.calls: list[dict[str, Any]] = []
        self.phases: list[str] = []

    async def agent(self, prompt: str, **options: Any) -> dict[str, Any] | None:
        label = options.get("label", "")
        self.calls.append({"prompt": prompt, **options})
        self.budget.charge()
        if label in self.fail_labels:
            return None

        if label.startswith("scout:") or label == "followup:scout":
            lane_id = label.split(":", 1)[1]
            if lane_id in self.scout_overrides:
                return self.scout_overrides[lane_id]
            return self._scout(lane_id)
        if label.startswith("escalation:"):
            return self._scout("acquisition-escalation")
        if label.startswith("verify:") or label == "followup:verify":
            lane_id = label.split(":", 1)[1]
            if lane_id in self.verifier_overrides:
                return self.verifier_overrides[lane_id]
            return self._verification(lane_id)
        if label == "coverage":
            target_words = self.args["report_profile"]["target_words"]
            section_needed = (
                target_words >= 5_000
                if self.section_drafting_needed is None
                else self.section_drafting_needed
            )
            return {
                "summary": "The supported lanes answer the main question.",
                "followup_needed": self.followup_needed,
                "decision_affected": (
                    "The central recommendation could change." if self.followup_needed else ""
                ),
                "followup_lane": {
                    "id": "followup",
                    "title": "One narrow gap",
                    "question": "Resolve the one decision-changing gap.",
                    "source_classes": ["official record"],
                },
                "gaps": [],
                "section_drafting_needed": section_needed,
                "section_drafting_reason": (
                    "The requested report is long." if section_needed else ""
                ),
                "section_outline": (
                    [
                        {
                            "heading": "First movement",
                            "purpose": "Establish the first part.",
                            "claim_ids": ["lane-1/C1"],
                        },
                        {
                            "heading": "Second movement",
                            "purpose": "Develop the second part.",
                            "claim_ids": ["lane-2/C1"],
                        },
                    ]
                    if section_needed
                    else []
                ),
            }
        if label.startswith("section-draft:"):
            section_number = label.rsplit(":", 1)[1]
            lane_id = f"lane-{section_number}"
            return {
                "heading": f"Movement {section_number}",
                "body_markdown": (
                    f"A section supported by a [primary source](https://example.test/{lane_id})."
                ),
                "used_claim_ids": [f"{lane_id}/C1"],
                "gaps": [],
            }
        if label == "draft-assembly":
            first_lane = self.args["lanes"][0]["id"]
            url = f"https://example.test/{first_lane}"
            return {
                "title": "A Long, Unified Report",
                "body_markdown": (
                    f"The assembled opening cites a [primary source]({url}).\n\n"
                    "## First movement\n\n"
                    "The sections now form one argument.\n\n"
                    "## Second movement\n\n"
                    "The conclusion follows without repetition."
                ),
                "gaps": [],
            }
        if label == "draft":
            first_lane = self.args["lanes"][0]["id"]
            url = f"https://example.test/{first_lane}"
            return {
                "title": "A Specific Reader-Fit Report",
                "body_markdown": (
                    f"The evidence establishes the main answer through a "
                    f"[primary source]({url}).\n\n"
                    "## What changed\n\n"
                    "The supported record supports a concise conclusion."
                ),
                "gaps": [],
            }
        if label.startswith("audit:"):
            return {
                "revision_needed": False,
                "material_issues": [],
                "minor_issues": [],
                "summary": "No material issue.",
            }
        if label == "revision":
            first_lane = self.args["lanes"][0]["id"]
            url = f"https://example.test/{first_lane}"
            return {
                "title": "A Specific Reader-Fit Report",
                "body_markdown": (
                    f"The revised answer cites a [primary source]({url}).\n\n"
                    "## What changed\n\nThe supported conclusion remains."
                ),
                "remaining_material_issues": [],
            }
        if label == "closure":
            return {"supported": True, "unresolved_material_issues": []}
        raise AssertionError(f"Unexpected worker label: {label}")

    async def parallel(self, thunks: list[Any]) -> list[Any]:
        return list(await asyncio.gather(*(thunk() for thunk in thunks)))

    async def pipeline(self, items: list[Any], *stages: Any) -> list[Any]:
        outputs = []
        for index, item in enumerate(items):
            value = item
            for stage in stages:
                value = await stage(value, item, index)
                if value is None:
                    break
            outputs.append(value)
        return outputs

    def phase(self, title: str) -> None:
        self.phases.append(title)

    def log(self, message: str) -> None:
        del message
        return None

    def _scout(self, lane_id: str) -> dict[str, Any]:
        claim: dict[str, Any] = {
            "id": "C1",
            "text": f"Material claim for {lane_id}.",
            "evidence_ids": ["E1"],
            "importance": "conclusion-driving",
            "disputed": False,
        }
        if self.default_claim_type is not None:
            claim["claim_type"] = self.default_claim_type
        return {
            "lane_id": lane_id,
            "summary": f"Verified-looking summary for {lane_id}.",
            "sources": [
                {
                    "id": "SRC1",
                    "title": f"Primary source for {lane_id}",
                    "url": f"https://example.test/{lane_id}",
                    "publisher": "Example Archive",
                    "date": "2025",
                    "source_type": "primary",
                }
            ],
            "evidence": [
                {
                    "id": "E1",
                    "claim": f"Material claim for {lane_id}.",
                    "source_id": "SRC1",
                    "quote_or_paraphrase": "A compact supporting passage.",
                }
            ],
            "candidate_claims": [claim],
            "failures": [
                {
                    "url": f"https://blocked.test/{lane_id}?download=1",
                    "reason": "403 access denied",
                    "terminal": True,
                }
            ],
            "gaps": [],
        }

    def _verification(self, lane_id: str) -> dict[str, Any]:
        return {
            "lane_id": lane_id,
            "summary": f"Selective verification for {lane_id}.",
            "verdicts": [
                {
                    "claim_id": "C1",
                    "status": "supported",
                    "approved_evidence_ids": ["E1"],
                    "qualification": "",
                }
            ],
            "rejected_evidence_ids": [],
            "new_sources": [],
            "new_evidence": [],
            "new_failures": [],
            "gaps": [],
        }


def workflow_args(
    tier: str = "standard",
    *,
    route: bool = False,
    writing_reserve_tokens: int = 1_000,
) -> dict[str, Any]:
    counts = {"focused": 2, "standard": 3, "extended": 5}
    ceilings = {
        "focused": (4, 6),
        "standard": (6, 8),
        "extended": (8, 12),
    }
    searches, fetches = ceilings[tier]
    routes: dict[str, Any] = {}
    if route:
        routes = {
            role: {
                "provider": "fixture-provider",
                "model": "fixture-model",
                "effort": None,
            }
            for role in ("discovery", "verification", "synthesis", "audit")
        }
    return {
        "intake": {
            "mode": "interactive",
            "confirmed": True,
            "resolved_fields": ["length", "audience_use", "scope", "delivery"],
            "topic_questions_asked": 2,
        },
        "brief": {
            "question": "What does the evidence support?",
            "audience": "General readers",
            "scope": "A bounded test",
            "high_stakes": False,
        },
        "tier": tier,
        "lanes": [
            {
                "id": f"lane-{index}",
                "title": f"Lane {index}",
                "question": f"Establish boundary {index}.",
                "source_classes": ["primary records"],
            }
            for index in range(1, counts[tier] + 1)
        ],
        "acquisition": {
            "searches_per_lane": searches,
            "fetches_per_lane": fetches,
            "verification_searches": 2,
            "verification_fetches": 4,
        },
        "report_profile": {
            "kind": "historical-cultural",
            "voice": "Engaging and precise",
            "length": "standard",
            "target_words": 3_000,
            "required_structure": [],
            "avoid_structure": ["Executive answer", "Methods", "Limitations"],
        },
        "writing_reserve_tokens": writing_reserve_tokens,
        "research_batch_size": 2,
        "allow_acquisition_escalation": False,
        "escalation": None,
        "routes": routes,
    }


async def execute_workflow(harness: FakeWorkflowHarness) -> dict[str, Any]:
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = ast.AsyncFunctionDef(
        name="__workflow_main__",
        args=ast.arguments(
            posonlyargs=[],
            args=[],
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[],
        ),
        body=tree.body,
        decorator_list=[],
    )
    module = ast.Module(body=[function], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "args": harness.args,
        "agent": harness.agent,
        "parallel": harness.parallel,
        "pipeline": harness.pipeline,
        "phase": harness.phase,
        "log": harness.log,
        "budget": harness.budget,
    }
    exec(compile(module, str(WORKFLOW_PATH), "exec"), namespace)  # noqa: S102
    return await namespace["__workflow_main__"]()


class DeepResearchWorkflowTests(unittest.TestCase):
    def test_workflow_is_static_safe_and_model_agnostic(self) -> None:
        source = WORKFLOW_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        meta_assignment = next(
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "meta" for target in node.targets)
        )
        meta = ast.literal_eval(meta_assignment.value)

        self.assertEqual(meta["name"], "deep-research")
        self.assertEqual(meta["max_agent_depth"], 1)
        self.assertGreaterEqual(len(meta["phases"]), 6)
        self.assertFalse(
            any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(tree))
        )
        self.assertNotRegex(source, r"\bopen\s*\(")
        self.assertNotRegex(source, r"model_override\s*=\s*\{")

        shipped_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in SKILL_ROOT.rglob("*")
            if path.is_file() and path.suffix in {".md", ".py", ".workflow"}
        )
        self.assertNotRegex(shipped_text, r'"provider"\s*:\s*"[A-Za-z0-9]')
        self.assertNotRegex(shipped_text, r'"model"\s*:\s*"[A-Za-z0-9]')

    def test_standard_run_is_bounded_and_routes_by_stage(self) -> None:
        # Default stage_plan: selective + thesis_changing + combined
        # selective/standard cap = 2, with one call reserved for a possible
        # thesis-changing follow-up.
        args = workflow_args(route=True)
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["run_summary"]["base_lanes_requested"], 3)
        self.assertEqual(result["run_summary"]["base_lanes_completed"], 3)
        self.assertEqual(result["run_summary"]["followups_run"], 0)
        self.assertEqual(result["run_summary"]["draft_mode"], "single")
        scout_calls = [call for call in harness.calls if call["label"].startswith("scout:")]
        verify_calls = [call for call in harness.calls if call["label"].startswith("verify:")]
        self.assertEqual(len(scout_calls), 3)
        # One main lane is verified; the second call remains available to the
        # conditional follow-up.
        self.assertEqual(len(verify_calls), 1)
        self.assertLessEqual(len(harness.calls), 9)
        self.assertTrue(
            all(
                call.get("model_override") == args["routes"]["discovery"]
                for call in harness.calls
                if call["label"].startswith("scout:")
            )
        )
        self.assertEqual(result["report_markdown"].count("\n## Sources\n"), 1)
        self.assertEqual(len(result["cited_sources"]), 1)
        # Failed URL from lane-1 scout appears in the verification prompts
        self.assertIn("https://blocked.test/lane-1", self._verification_prompts(harness))
        self.assertIn("Do not retry any terminal URL", self._verification_prompts(harness))

    def test_focused_run_uses_two_lanes_and_inherits_without_routes(self) -> None:
        args = workflow_args("focused")
        harness = FakeWorkflowHarness(args, followup_needed=True)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["run_summary"]["base_lanes_requested"], 2)
        self.assertEqual(result["run_summary"]["followups_run"], 0)
        self.assertFalse(any("model_override" in call for call in harness.calls))
        self.assertFalse(any(call["label"].startswith("followup:") for call in harness.calls))

    def test_skill_selects_section_drafting_for_long_report(self) -> None:
        args = workflow_args()
        args["report_profile"]["length"] = "detailed"
        args["report_profile"]["target_words"] = 6_000
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["run_summary"]["draft_mode"], "sections")
        self.assertEqual(
            len([call for call in harness.calls if call["label"].startswith("section-draft:")]),
            2,
        )
        self.assertEqual([call["label"] for call in harness.calls].count("draft-assembly"), 1)
        self.assertFalse(any(call["label"] == "draft" for call in harness.calls))

    def test_skill_can_select_sections_for_exceptional_shorter_structure(self) -> None:
        args = workflow_args()
        harness = FakeWorkflowHarness(args, section_drafting_needed=True)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["run_summary"]["draft_mode"], "sections")
        self.assertEqual(
            len([call for call in harness.calls if call["label"].startswith("section-draft:")]),
            2,
        )

    def test_standard_runs_at_most_one_followup(self) -> None:
        # Use required mode so the follow-up lane also gets a verifier
        # (required cap=6 > 3 main calls → follow-up still within cap)
        args = workflow_args()
        args["stage_plan"] = {
            "verification": "required",
            "followup": "thesis_changing",
            "audit": "combined",
        }
        harness = FakeWorkflowHarness(args, followup_needed=True)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["run_summary"]["followups_run"], 1)
        self.assertEqual(
            [call["label"] for call in harness.calls].count("followup:scout"),
            1,
        )
        self.assertEqual(
            [call["label"] for call in harness.calls].count("followup:verify"),
            1,
        )

    def test_selective_standard_reserves_one_verifier_call_for_followup(self) -> None:
        args = workflow_args()
        harness = FakeWorkflowHarness(args, followup_needed=True)
        result = asyncio.run(execute_workflow(harness))

        main_verify_calls = [call for call in harness.calls if call["label"].startswith("verify:")]
        self.assertEqual(len(main_verify_calls), 1)
        self.assertEqual(
            [call["label"] for call in harness.calls].count("followup:verify"),
            1,
        )
        self.assertEqual(result["run_summary"]["verifier_calls"], 2)

    def test_selective_escalation_cannot_consume_reserved_followup_verifier(self) -> None:
        args = workflow_args()
        args["brief"]["high_stakes"] = True
        args["allow_acquisition_escalation"] = True
        args["escalation"] = {
            "kind": "local",
            "target": "irreplaceable-source.pdf",
            "question": "What conclusion-changing fact does the source establish?",
        }
        harness = FakeWorkflowHarness(args, followup_needed=True)
        result = asyncio.run(execute_workflow(harness))

        labels = [call["label"] for call in harness.calls]
        self.assertIn("escalation:local", labels)
        self.assertNotIn("verify:acquisition-escalation", labels)
        self.assertIn("followup:verify", labels)
        self.assertEqual(result["run_summary"]["verifier_calls"], 2)

    def test_writing_reserve_suppresses_followup(self) -> None:
        args = workflow_args(writing_reserve_tokens=9_000)
        budget = FakeBudget(total=10_000, spent_per_agent=100)
        harness = FakeWorkflowHarness(args, followup_needed=True, budget=budget)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["run_summary"]["base_lanes_completed"], 3)
        self.assertEqual(result["run_summary"]["followups_run"], 0)
        self.assertFalse(any(call["label"].startswith("followup:") for call in harness.calls))

    def test_failed_worker_produces_supported_partial_and_none_is_filtered(self) -> None:
        args = workflow_args()
        harness = FakeWorkflowHarness(args, fail_labels={"scout:lane-3"})
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["run_summary"]["base_lanes_completed"], 2)
        self.assertTrue(any("lane-3" in gap for gap in result["gaps"]))
        self.assertNotIn("None", result["report_markdown"])

    def test_invalid_args_fail_before_dispatch(self) -> None:
        args = workflow_args()
        args["lanes"] = args["lanes"][:2]
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "failed")
        self.assertFalse(harness.calls)
        self.assertTrue(any("standard requires 3-4 lanes" in gap for gap in result["gaps"]))

    def test_incomplete_intake_fails_before_dispatch(self) -> None:
        invalid_cases: list[tuple[str, dict[str, Any], str]] = []

        args = workflow_args()
        args.pop("intake")
        invalid_cases.append(("missing intake", args, "intake.mode"))

        args = workflow_args()
        args["intake"] = "confirmed"  # type: ignore[assignment]
        invalid_cases.append(("non-object intake", args, "intake must be an object"))

        args = workflow_args()
        args["intake"]["confirmed"] = False
        invalid_cases.append(
            ("unconfirmed interactive", args, "interactive intake must be confirmed")
        )

        args = workflow_args()
        args["intake"]["resolved_fields"].remove("delivery")
        invalid_cases.append(("missing core field", args, "intake.resolved_fields"))

        for count in (0, 4, True):
            args = workflow_args()
            args["intake"]["topic_questions_asked"] = count
            invalid_cases.append(
                (
                    f"invalid interactive topic count {count!r}",
                    args,
                    "intake.topic_questions_asked",
                )
            )

        args = workflow_args()
        args["brief"]["audience"] = ""
        invalid_cases.append(("missing audience", args, "brief.audience is required"))

        args = workflow_args()
        args["brief"]["scope"] = ""
        invalid_cases.append(("missing scope", args, "brief.scope is required"))

        args = workflow_args()
        args["report_profile"].pop("length")
        invalid_cases.append(("missing length", args, "report_profile.length"))

        args = workflow_args()
        args["report_profile"].pop("target_words")
        invalid_cases.append(("missing target", args, "report_profile.target_words"))

        for name, invalid_args, expected_gap in invalid_cases:
            with self.subTest(name=name):
                harness = FakeWorkflowHarness(invalid_args)
                result = asyncio.run(execute_workflow(harness))

                self.assertEqual(result["status"], "failed")
                self.assertFalse(harness.calls)
                self.assertTrue(
                    any(expected_gap in gap for gap in result["gaps"]),
                    result["gaps"],
                )

    def test_length_presets_and_custom_targets_are_enforced(self) -> None:
        valid_lengths = [
            ("concise", 1_500),
            ("standard", 3_000),
            ("detailed", 6_000),
            ("long", 10_000),
            ("long", 12_000),
            ("custom", 750),
        ]
        for length, target_words in valid_lengths:
            with self.subTest(length=length, target_words=target_words):
                args = workflow_args()
                args["report_profile"]["length"] = length
                args["report_profile"]["target_words"] = target_words
                harness = FakeWorkflowHarness(args)
                result = asyncio.run(execute_workflow(harness))

                self.assertIn(result["status"], {"complete", "partial"})
                self.assertTrue(harness.calls)

        invalid_lengths = [
            ("concise", 1_501, "does not match"),
            ("standard", 2_999, "does not match"),
            ("detailed", 5_999, "does not match"),
            ("long", 9_999, "requires at least 10000"),
            ("custom", 499, "at least 500"),
        ]
        for length, target_words, expected_gap in invalid_lengths:
            with self.subTest(length=length, target_words=target_words):
                args = workflow_args()
                args["report_profile"]["length"] = length
                args["report_profile"]["target_words"] = target_words
                harness = FakeWorkflowHarness(args)
                result = asyncio.run(execute_workflow(harness))

                self.assertEqual(result["status"], "failed")
                self.assertFalse(harness.calls)
                self.assertTrue(
                    any(expected_gap in gap for gap in result["gaps"]),
                    result["gaps"],
                )

    def test_user_directed_defaults_can_skip_topic_questions(self) -> None:
        args = workflow_args()
        args["intake"] = {
            "mode": "user_directed_defaults",
            "confirmed": False,
            "resolved_fields": ["length", "audience_use", "scope", "delivery"],
            "topic_questions_asked": 0,
        }
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "complete")
        self.assertNotIn("intake", result["run_summary"])
        self.assertNotIn("user_directed_defaults", result["report_markdown"])

    # -----------------------------------------------------------------------
    # Acceptance scenario 1: experiential risk_only — zero verifiers
    # -----------------------------------------------------------------------

    def test_risk_only_experiential_zero_verifiers_no_coverage_combined_audit(self) -> None:
        """Four-lane attributed-testimony plan: risk_only → 0 verifiers; followup=off
        → Coverage skipped; combined audit runs; complete report with one Sources section."""
        args = workflow_args("standard")
        # Add a 4th lane (standard allows up to 4)
        args["lanes"].append(
            {
                "id": "lane-4",
                "title": "Lane 4",
                "question": "Establish boundary 4.",
                "source_classes": ["primary records"],
            }
        )
        args["stage_plan"] = {
            "verification": "risk_only",
            "followup": "off",
            "audit": "combined",
            "reason": "experiential_accounts",
        }
        # All claims are attributed_report — ineligible for risk_only (no risk triggers)
        harness = FakeWorkflowHarness(args, default_claim_type="attributed_report")
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["run_summary"]["base_lanes_completed"], 4)
        self.assertEqual(result["run_summary"]["verifier_calls"], 0)
        self.assertEqual(result["run_summary"]["selected_claims"], 0)
        self.assertEqual(result["run_summary"]["eligible_claims"], 0)
        # No Coverage (followup=off, target<5000, no required_structure)
        self.assertNotIn("coverage", [c["label"] for c in harness.calls])
        self.assertIn("Coverage", result["run_summary"]["stages_skipped"])
        self.assertNotIn("Coverage", result["run_summary"]["stages_run"])
        # Verify stage skipped
        self.assertIn("Verify", result["run_summary"]["stages_skipped"])
        self.assertNotIn("Verify", result["run_summary"]["stages_run"])
        # One combined audit
        audit_calls = [c for c in harness.calls if c["label"].startswith("audit:")]
        self.assertEqual(len(audit_calls), 1)
        self.assertEqual(audit_calls[0]["label"], "audit:combined")
        self.assertIn("Audit", result["run_summary"]["stages_run"])
        # Stage plan preserved in telemetry
        plan = result["run_summary"]["stage_plan"]
        self.assertEqual(plan["verification"], "risk_only")
        self.assertEqual(plan["followup"], "off")
        self.assertEqual(plan["audit"], "combined")
        self.assertEqual(plan["reason"], "experiential_accounts")
        # Exactly one Sources section in the complete report
        self.assertEqual(result["report_markdown"].count("\n## Sources\n"), 1)

    # -----------------------------------------------------------------------
    # Acceptance scenario 2: mixed selective — only eligible lane verified
    # -----------------------------------------------------------------------

    def test_selective_only_eligible_lane_gets_verifier(self) -> None:
        """Lane-3 (causal) is the only one eligible under selective; lanes 1 & 2
        (attributed_report) are skipped as having no eligible claims."""
        args = workflow_args("standard")  # 3 lanes
        args["stage_plan"] = {
            "verification": "selective",
            "followup": "off",
            "audit": "deterministic",
        }
        harness = FakeWorkflowHarness(
            args,
            default_claim_type="attributed_report",
            scout_overrides={"lane-3": _make_scout("lane-3", claim_type="causal")},
        )
        result = asyncio.run(execute_workflow(harness))

        self.assertIn(result["status"], ("complete", "partial"))
        verify_calls = [c for c in harness.calls if c["label"].startswith("verify:")]
        self.assertEqual(len(verify_calls), 1)
        self.assertEqual(verify_calls[0]["label"], "verify:lane-3")
        self.assertEqual(result["run_summary"]["verifier_calls"], 1)
        self.assertEqual(result["run_summary"]["eligible_claims"], 1)
        self.assertEqual(result["run_summary"]["lanes_skipped_no_eligible"], 2)
        # Deterministic mode: no agent audit
        audit_calls = [c for c in harness.calls if c["label"].startswith("audit:")]
        self.assertEqual(len(audit_calls), 0)
        self.assertIn("Audit", result["run_summary"]["stages_skipped"])
        self.assertNotIn("Audit", result["run_summary"]["stages_run"])
        # Report is still generated from direct + supported claims
        self.assertGreater(len(result["report_markdown"]), 50)

    # -----------------------------------------------------------------------
    # Acceptance scenario 3: no-op suppression
    # -----------------------------------------------------------------------

    def test_no_eligible_claims_suppresses_all_verifiers(self) -> None:
        """All lanes have attributed_report claims → zero eligible → zero verifiers."""
        args = workflow_args()
        args["stage_plan"] = {
            "verification": "selective",
            "followup": "off",
            "audit": "deterministic",
        }
        harness = FakeWorkflowHarness(args, default_claim_type="attributed_report")
        result = asyncio.run(execute_workflow(harness))

        verify_calls = [c for c in harness.calls if c["label"].startswith("verify:")]
        self.assertEqual(len(verify_calls), 0)
        self.assertEqual(result["run_summary"]["verifier_calls"], 0)
        self.assertEqual(result["run_summary"]["selected_claims"], 0)
        self.assertNotIn("Verify", result["run_summary"]["stages_run"])
        self.assertIn("Verify", result["run_summary"]["stages_skipped"])
        # Report is still generated from direct-status claims
        self.assertGreater(len(result["report_markdown"]), 50)

    # -----------------------------------------------------------------------
    # Acceptance scenario 4: verifier failure / empty / partial
    # -----------------------------------------------------------------------

    def test_verifier_failure_preserves_lane_and_generates_report(self) -> None:
        """Verifier returns None: the scout lane is kept (claims get unresolved status)
        and the report is still generated.  Status is not 'failed'."""
        args = workflow_args()
        args["stage_plan"] = {
            "verification": "selective",
            "followup": "off",
            "audit": "combined",
        }
        # With selective/standard cap=2, lanes 1 and 2 are selected; lane-1 verifier fails.
        harness = FakeWorkflowHarness(args, fail_labels={"verify:lane-1"})
        result = asyncio.run(execute_workflow(harness))

        # Lane was not dropped — report is produced
        self.assertNotEqual(result["status"], "failed")
        self.assertGreater(len(result["report_markdown"]), 50)
        # Scout for lane-1 still ran
        scout_labels = [c["label"] for c in harness.calls]
        self.assertIn("scout:lane-1", scout_labels)
        # Verifier for lane-1 was attempted
        self.assertIn("verify:lane-1", scout_labels)
        # Telemetry records the call
        self.assertGreaterEqual(result["run_summary"]["verifier_calls"], 1)
        self.assertEqual(result["run_summary"]["base_lanes_completed"], 3)

    def test_verifier_empty_delta_preserves_lane(self) -> None:
        """Verifier returns empty verdicts: claims are unresolved but lane is kept."""
        args = workflow_args()
        args["stage_plan"] = {
            "verification": "selective",
            "followup": "off",
            "audit": "combined",
        }
        empty_delta: dict[str, Any] = {
            "lane_id": "lane-1",
            "summary": "Empty delta.",
            "verdicts": [],
            "rejected_evidence_ids": [],
            "new_sources": [],
            "new_evidence": [],
            "new_failures": [],
            "gaps": [],
        }
        harness = FakeWorkflowHarness(args, verifier_overrides={"lane-1": empty_delta})
        result = asyncio.run(execute_workflow(harness))

        self.assertNotEqual(result["status"], "failed")
        self.assertGreater(len(result["report_markdown"]), 50)
        # Verifier was called for lane-1
        self.assertGreaterEqual(result["run_summary"]["verifier_calls"], 1)
        draft_prompt = next(c["prompt"] for c in harness.calls if c["label"] == "draft")
        lane_claim = draft_prompt.index("'id': 'lane-1/C1'")
        self.assertIn("'status': 'unresolved'", draft_prompt[lane_claim : lane_claim + 300])

    def test_verifier_sources_require_same_claim_approved_evidence(self) -> None:
        args = workflow_args()
        args["stage_plan"] = {
            "verification": "selective",
            "followup": "off",
            "audit": "deterministic",
        }
        verifier_delta = {
            "lane_id": "lane-1",
            "summary": "One corroborating source was admitted.",
            "verdicts": [
                {
                    "claim_id": "C1",
                    "status": "supported",
                    "approved_evidence_ids": ["VE1"],
                    "qualification": "",
                },
                {
                    "claim_id": "C999",
                    "status": "supported",
                    "approved_evidence_ids": ["VE2"],
                    "qualification": "",
                },
            ],
            "rejected_evidence_ids": [],
            "new_sources": [
                {
                    "id": "VS1",
                    "title": "Approved corroboration",
                    "url": "https://corroboration.test/approved",
                },
                {
                    "id": "VS2",
                    "title": "Orphan source",
                    "url": "https://corroboration.test/orphan",
                },
            ],
            "new_evidence": [
                {
                    "id": "VE1",
                    "claim_id": "C1",
                    "claim": "Corroboration for C1.",
                    "source_id": "VS1",
                    "quote_or_paraphrase": "Independent support.",
                },
                {
                    "id": "VE2",
                    "claim_id": "C999",
                    "claim": "Unrelated evidence.",
                    "source_id": "VS2",
                    "quote_or_paraphrase": "Not tied to the verdict.",
                },
            ],
            "new_failures": [],
            "gaps": [],
        }
        harness = FakeWorkflowHarness(
            args,
            verifier_overrides={"lane-1": verifier_delta},
        )
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "complete")
        draft_prompt = next(c["prompt"] for c in harness.calls if c["label"] == "draft")
        self.assertIn("https://corroboration.test/approved", draft_prompt)
        self.assertNotIn("https://corroboration.test/orphan", draft_prompt)

    # -----------------------------------------------------------------------
    # Acceptance scenario 5: required mode + dual audit + caps
    # -----------------------------------------------------------------------

    def test_required_dual_audit_all_lanes_verified_and_caps_hold(self) -> None:
        """required mode with dual audit: all 5 extended lanes verified (≤6 cap);
        dual audit runs; unresolved claims do not appear as settled conclusions."""
        args = workflow_args("extended")
        args["stage_plan"] = {
            "verification": "required",
            "followup": "off",
            "audit": "dual",
        }
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["run_summary"]["base_lanes_completed"], 5)
        # required cap = min(5, 6) = 5; all 5 lanes are verified
        verify_calls = [c for c in harness.calls if c["label"].startswith("verify:")]
        self.assertEqual(len(verify_calls), 5)
        self.assertEqual(result["run_summary"]["verifier_calls"], 5)
        # Dual audit
        audit_calls = [c for c in harness.calls if c["label"].startswith("audit:")]
        self.assertEqual(len(audit_calls), 2)
        audit_labels = sorted(c["label"] for c in audit_calls)
        self.assertEqual(audit_labels, ["audit:editorial", "audit:evidence"])
        self.assertIn("Audit", result["run_summary"]["stages_run"])
        self.assertNotIn("Audit", result["run_summary"]["stages_skipped"])
        self.assertEqual(result["report_markdown"].count("\n## Sources\n"), 1)

    def test_required_mode_includes_selective_claim_types(self) -> None:
        args = workflow_args()
        args["stage_plan"] = {
            "verification": "required",
            "followup": "off",
            "audit": "deterministic",
        }
        harness = FakeWorkflowHarness(
            args,
            default_claim_type="attributed_report",
            scout_overrides={
                "lane-2": _make_scout(
                    "lane-2",
                    claim_type="causal",
                    importance="supporting",
                )
            },
        )
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "complete")
        verify_labels = [c["label"] for c in harness.calls if c["label"].startswith("verify:")]
        self.assertEqual(verify_labels, ["verify:lane-2"])

    def test_required_extended_escalation_uses_remaining_verifier_call(self) -> None:
        args = workflow_args("extended")
        args["stage_plan"] = {
            "verification": "required",
            "followup": "off",
            "audit": "deterministic",
        }
        args["allow_acquisition_escalation"] = True
        args["escalation"] = {
            "kind": "local",
            "target": "irreplaceable-source.pdf",
            "question": "What conclusion-changing fact does the source establish?",
        }
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "complete")
        labels = [c["label"] for c in harness.calls]
        self.assertIn("escalation:local", labels)
        self.assertIn("verify:acquisition-escalation", labels)
        self.assertEqual(result["run_summary"]["escalations_run"], 1)
        self.assertEqual(result["run_summary"]["verifier_calls"], 6)
        self.assertEqual(result["report_markdown"].count("\n## Sources\n"), 1)

    # -----------------------------------------------------------------------
    # Acceptance scenario 6: bound enforcement — max 8 claims per verifier call
    # -----------------------------------------------------------------------

    def test_max_8_claims_per_verifier_call_excess_deferred(self) -> None:
        """Lane-1 has 10 eligible claims; only 8 are sent to the verifier, 2 deferred.
        Lane-2 (attributed_report) has no eligible claims under risk_only."""
        args = workflow_args("focused")  # 2 lanes
        args["stage_plan"] = {
            "verification": "risk_only",
            "followup": "off",
            "audit": "deterministic",
        }
        lane1_scout = _make_scout_with_many_claims(
            "lane-1",
            count=10,
            claim_type="external_fact",
            triggers=["known_dispute"],
        )
        lane2_scout = _make_scout("lane-2", claim_type="attributed_report")
        harness = FakeWorkflowHarness(
            args,
            scout_overrides={"lane-1": lane1_scout, "lane-2": lane2_scout},
        )
        result = asyncio.run(execute_workflow(harness))

        self.assertIn(result["status"], ("complete", "partial"))
        self.assertEqual(result["run_summary"]["eligible_claims"], 10)
        self.assertEqual(result["run_summary"]["selected_claims"], 8)
        self.assertEqual(result["run_summary"]["deferred_claims"], 2)
        self.assertEqual(result["run_summary"]["verifier_calls"], 1)
        self.assertEqual(result["run_summary"]["lanes_skipped_no_eligible"], 1)
        # Exactly one verify:lane-1 call
        verify_calls = [c for c in harness.calls if c["label"] == "verify:lane-1"]
        self.assertEqual(len(verify_calls), 1)
        # SELECTED CLAIMS key appears in the prompt
        self.assertIn("SELECTED CLAIMS:", verify_calls[0]["prompt"])

    # -----------------------------------------------------------------------
    # Acceptance scenario 7: conditional Coverage / audit
    # -----------------------------------------------------------------------

    def test_coverage_skipped_when_followup_off_and_short_target(self) -> None:
        """followup=off, target_words<5000, no required_structure → Coverage skipped."""
        args = workflow_args()
        args["stage_plan"] = {
            "verification": "selective",
            "followup": "off",
            "audit": "combined",
        }
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        self.assertNotIn("coverage", [c["label"] for c in harness.calls])
        self.assertIn("Coverage", result["run_summary"]["stages_skipped"])
        self.assertNotIn("Coverage", result["run_summary"]["stages_run"])
        self.assertEqual(result["run_summary"]["followups_run"], 0)

    def test_coverage_runs_when_followup_thesis_changing(self) -> None:
        """Coverage runs whenever followup=thesis_changing."""
        args = workflow_args()
        args["stage_plan"] = {
            "verification": "selective",
            "followup": "thesis_changing",
            "audit": "combined",
        }
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        self.assertIn("coverage", [c["label"] for c in harness.calls])
        self.assertIn("Coverage", result["run_summary"]["stages_run"])

    def test_coverage_runs_for_long_target_even_with_followup_off(self) -> None:
        """Coverage runs when target_words >= 5000 regardless of followup mode."""
        args = workflow_args()
        args["report_profile"]["length"] = "detailed"
        args["report_profile"]["target_words"] = 6_000
        args["stage_plan"] = {
            "verification": "selective",
            "followup": "off",
            "audit": "combined",
        }
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        self.assertIn("coverage", [c["label"] for c in harness.calls])
        self.assertIn("Coverage", result["run_summary"]["stages_run"])
        self.assertEqual(result["run_summary"]["draft_mode"], "sections")

    def test_required_structure_can_trigger_coverage(self) -> None:
        args = workflow_args()
        args["report_profile"]["required_structure"] = ["Findings", "Recommendations"]
        args["stage_plan"] = {
            "verification": "selective",
            "followup": "off",
            "audit": "deterministic",
        }
        harness = FakeWorkflowHarness(args, section_drafting_needed=False)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "complete")
        self.assertIn("coverage", [c["label"] for c in harness.calls])
        self.assertIn("Coverage", result["run_summary"]["stages_run"])

    def test_deterministic_audit_skips_agent_audit(self) -> None:
        """audit=deterministic → no audit: label calls; structural checks still run."""
        args = workflow_args()
        args["stage_plan"] = {
            "verification": "selective",
            "followup": "off",
            "audit": "deterministic",
        }
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        audit_calls = [c for c in harness.calls if c["label"].startswith("audit:")]
        self.assertEqual(len(audit_calls), 0)
        self.assertIn("Audit", result["run_summary"]["stages_skipped"])
        # Report is still complete (deterministic structural checks passed)
        self.assertIn(result["status"], ("complete", "partial"))
        self.assertEqual(result["report_markdown"].count("\n## Sources\n"), 1)

    # -----------------------------------------------------------------------
    # Acceptance scenario 8: omitted stage_plan defaults
    # -----------------------------------------------------------------------

    def test_omitted_stage_plan_defaults_to_selective_thesis_changing_combined(self) -> None:
        """Omitted stage_plan resolves to selective + thesis_changing + combined,
        preserving the prior ordinary intent while gaining adaptive verification."""
        args = workflow_args()
        # Deliberately omit stage_plan from args
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        plan = result["run_summary"]["stage_plan"]
        self.assertEqual(plan["verification"], "selective")
        self.assertEqual(plan["followup"], "thesis_changing")
        self.assertEqual(plan["audit"], "combined")
        self.assertEqual(plan.get("reason", ""), "")
        # Coverage runs (thesis_changing default)
        self.assertIn("Coverage", result["run_summary"]["stages_run"])
        # Combined audit
        audit_calls = [c for c in harness.calls if c["label"].startswith("audit:")]
        self.assertEqual(len(audit_calls), 1)
        self.assertEqual(audit_calls[0]["label"], "audit:combined")

    # -----------------------------------------------------------------------
    # Acceptance scenario 9: telemetry accurate and additive
    # -----------------------------------------------------------------------

    def test_telemetry_accurate_and_additive(self) -> None:
        """All telemetry fields are present; counts are deterministic and accurate."""
        # Default stage_plan: selective + thesis_changing + combined
        # 3 lanes, all legacy (no claim_type) → eligible for selective
        # selective/standard cap = 2, with one reserved for a possible follow-up.
        args = workflow_args()
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        rs = result["run_summary"]
        for key in (
            "stage_plan",
            "stages_run",
            "stages_skipped",
            "eligible_claims",
            "selected_claims",
            "deferred_claims",
            "verifier_calls",
            "lanes_skipped_no_eligible",
            "verifier_verdict_counts",
            "tier",
            "base_lanes_requested",
            "base_lanes_completed",
            "followups_run",
            "escalations_run",
            "draft_mode",
        ):
            self.assertIn(key, rs, f"missing telemetry key: {key}")

        # All 3 legacy claims are eligible for selective (conclusion-driving)
        self.assertEqual(rs["eligible_claims"], 3)
        # One main-lane slot is available and two eligible lanes are deferred.
        self.assertEqual(rs["selected_claims"], 1)
        self.assertEqual(rs["deferred_claims"], 2)
        self.assertEqual(rs["verifier_calls"], 1)
        self.assertEqual(rs["lanes_skipped_no_eligible"], 0)
        self.assertEqual(rs["verifier_verdict_counts"].get("supported", 0), 1)
        # Stage tracking
        self.assertIn("Research", rs["stages_run"])
        self.assertIn("Verify", rs["stages_run"])
        self.assertIn("Coverage", rs["stages_run"])
        self.assertIn("Draft", rs["stages_run"])
        self.assertIn("Audit", rs["stages_run"])

    def test_telemetry_present_in_validation_failure_return(self) -> None:
        """Even a validation failure return includes telemetry with stage_plan."""
        args = workflow_args()
        args["lanes"] = args["lanes"][:1]  # too few for standard → validation error
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "failed")
        self.assertIn("stage_plan", result["run_summary"])
        self.assertEqual(result["run_summary"]["verifier_calls"], 0)
        self.assertEqual(result["run_summary"]["stages_run"], [])

    @staticmethod
    def _verification_prompts(harness: FakeWorkflowHarness) -> str:
        return "\n".join(
            call["prompt"] for call in harness.calls if call["label"].startswith("verify:")
        )


class MaterializeReportTests(unittest.TestCase):
    def payload(self, status: str = "complete") -> dict[str, Any]:
        return {
            "status": status,
            "report_markdown": (
                "# Test report\n\n"
                "A supported [claim](https://example.test/source).\n\n"
                "## Sources\n\n"
                "- [Source](https://example.test/source)\n"
            ),
            "cited_sources": [],
            "gaps": [],
        }

    def test_materializes_json_and_creates_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = root / "result.json"
            result.write_text(json.dumps(self.payload()), encoding="utf-8")
            output = root / "reports" / "report.md"

            path, status = MATERIALIZER.materialize_report(result, output)

            self.assertEqual(path, output)
            self.assertEqual(status, "complete")
            self.assertTrue(output.read_text(encoding="utf-8").endswith("\n"))

    def test_materializes_markdown_result_and_supported_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = self.payload("partial")
            result = root / "result.md"
            result.write_text(
                "# Workflow result\n\n"
                "## Full return value\n\n"
                f"```json\n{json.dumps(payload)}\n```\n",
                encoding="utf-8",
            )

            _, status = MATERIALIZER.materialize_report(result, root / "partial.md")

            self.assertEqual(status, "partial")

    def test_refuses_collision_and_supports_numbered_or_explicit_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = root / "result.json"
            result.write_text(json.dumps(self.payload()), encoding="utf-8")
            output = root / "report.md"
            output.write_text("existing\n", encoding="utf-8")

            with self.assertRaises(MATERIALIZER.MaterializationError):
                MATERIALIZER.materialize_report(result, output)

            numbered, _ = MATERIALIZER.materialize_report(
                result,
                output,
                collision_safe=True,
            )
            self.assertEqual(numbered.name, "report-2.md")
            overwritten, _ = MATERIALIZER.materialize_report(
                result,
                output,
                overwrite=True,
            )
            self.assertEqual(overwritten, output)
            self.assertTrue(output.read_text(encoding="utf-8").startswith("# Test report"))

    def test_rejects_failed_malformed_or_empty_report_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cases = [
                ("failed.json", {"status": "failed", "report_markdown": ""}),
                ("missing.json", {"status": "complete"}),
                (
                    "malformed.json",
                    {"status": "complete", "report_markdown": "# Title\n\nNo sources.\n"},
                ),
            ]
            for filename, payload in cases:
                with self.subTest(filename=filename):
                    result = root / filename
                    result.write_text(json.dumps(payload), encoding="utf-8")
                    output = root / f"{filename}.md"
                    with self.assertRaises(MATERIALIZER.MaterializationError):
                        MATERIALIZER.materialize_report(result, output)
                    self.assertFalse(output.exists())

    def test_rejects_invalid_json_and_conflicting_collision_modes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            invalid = root / "result.json"
            invalid.write_text("{", encoding="utf-8")
            with self.assertRaises(MATERIALIZER.MaterializationError):
                MATERIALIZER.load_workflow_result(invalid)

            valid = root / "valid.json"
            valid.write_text(json.dumps(self.payload()), encoding="utf-8")
            with self.assertRaises(MATERIALIZER.MaterializationError):
                MATERIALIZER.materialize_report(
                    valid,
                    root / "report.md",
                    overwrite=True,
                    collision_safe=True,
                )


class DeepResearchPackagingTests(unittest.TestCase):
    def test_package_contains_workflow_and_materializer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive, _ = package_skill(
                SKILL_ROOT,
                Path(temporary),
                repository_root=REPOSITORY_ROOT,
            )
            import zipfile

            with zipfile.ZipFile(archive) as packaged:
                names = packaged.namelist()
            self.assertIn("deep-research/scripts/deep-research.workflow", names)
            self.assertIn("deep-research/scripts/materialize_report.py", names)


if __name__ == "__main__":
    unittest.main()
