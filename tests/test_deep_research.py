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
    ) -> None:
        self.args = args
        self.followup_needed = followup_needed
        self.section_drafting_needed = section_drafting_needed
        self.fail_labels = fail_labels or set()
        self.budget = budget or FakeBudget()
        self.calls: list[dict[str, Any]] = []
        self.phases: list[str] = []

    async def agent(self, prompt: str, **options: Any) -> dict[str, Any] | None:
        label = options.get("label", "")
        self.calls.append({"prompt": prompt, **options})
        self.budget.charge()
        if label in self.fail_labels:
            return None

        if label.startswith("scout:") or label in {"followup:scout"}:
            lane_id = label.split(":", 1)[1]
            return self._scout(lane_id)
        if label.startswith("escalation:"):
            return self._scout("acquisition-escalation")
        if label.startswith("verify:") or label == "followup:verify":
            lane_id = label.split(":", 1)[1]
            return self._verification(lane_id)
        if label == "coverage":
            target_words = self.args["report_profile"]["target_words"]
            section_needed = (
                target_words >= 5_000
                if self.section_drafting_needed is None
                else self.section_drafting_needed
            )
            return {
                "summary": "The verified lanes answer the main question.",
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
                    "The verified record supports a concise conclusion."
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

    @staticmethod
    def _scout(lane_id: str) -> dict[str, Any]:
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
            "candidate_claims": [
                {
                    "id": "C1",
                    "text": f"Material claim for {lane_id}.",
                    "evidence_ids": ["E1"],
                    "importance": "conclusion-driving",
                    "disputed": False,
                }
            ],
            "failures": [
                {
                    "url": f"https://blocked.test/{lane_id}?download=1",
                    "reason": "403 access denied",
                    "terminal": True,
                }
            ],
            "gaps": [],
        }

    @staticmethod
    def _verification(lane_id: str) -> dict[str, Any]:
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
        self.assertEqual(len(verify_calls), 3)
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
        args["report_profile"]["target_words"] = 5_500
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
        args = workflow_args()
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
