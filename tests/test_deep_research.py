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


def load_workflow_helpers() -> dict[str, Any]:
    """Execute only the workflow's module-level helpers, outside the async wrapper."""
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    wanted = {
        "canonical_url",
        "strip_fenced_code",
        "strip_inline_code",
        "matching_bracket",
        "link_destination",
        "markdown_urls",
        "strip_sources",
        "structural_issues",
        "slugify",
    }
    body: list[ast.stmt] = [
        node
        for node in tree.body
        if (isinstance(node, ast.FunctionDef) and node.name in wanted)
        or (
            isinstance(node, ast.Assign)
            and any(getattr(target, "id", "") == "TRACKING_PARAMS" for target in node.targets)
        )
    ]
    module = ast.Module(body=body, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace: dict[str, Any] = {}
    exec(compile(module, str(WORKFLOW_PATH), "exec"), namespace)  # noqa: S102
    return namespace


WORKFLOW_HELPERS = load_workflow_helpers()

# Shared corpus for the workflow/materializer parity contract.
LINK_FIXTURES = [
    "[Saturn](https://en.wikipedia.org/wiki/Saturn_(mythology)) shaped the tradition.",
    "[Spec](https://example.com/doc \"The Title\") and [b](https://example.com/b 't')",
    "![diagram](https://example.com/img.png) beside [text](https://example.com/a)",
    "inline `[a](b)` plus [real](https://example.com/real)",
    "[reference style][1] and [inline](https://example.com/ok)",
    "[angle](<https://example.com/ok2>) end",
    "[anchor](#part) [mail](mailto:a@b.c) [rel](./x.md) [plain](http://example.com/h)",
    "```\n[fenced](https://example.com/no)\n```\n[after](https://example.com/yes)",
    "~~~text\n[tilde](https://example.com/no2)\n~~~\n[y](https://example.com/y2)",
    "[nested [brackets] label](https://example.com/n)",
    "[trailing parens](https://example.com/a(b)c) tail",
    "no links at all",
    "",
]
URL_FIXTURES = [
    "https://www.jstor.org/stable/2860993?seq=3",
    "https://www.jstor.org/stable/2860993?seq=41",
    "https://example.gov/data?report=2019",
    "https://example.gov/data?report=2024",
    "https://Example.COM/Path/",
    "https://example.com/p?utm_source=x&utm_medium=y&id=7",
    "https://example.com/p?id=7",
    "https://example.com/p?b=2&a=1",
    "https://example.com/p?a=1&b=2",
    "https://example.com/x#fragment",
    "HTTPS://EXAMPLE.com/A?ref=twitter",
    "https://example.com",
    "",
]


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
        section_word_count: int = 900,
        assembled_word_counts: list[int] | None = None,
        audit_material_issues: list[str] | None = None,
        revision_remaining_issues: list[str] | None = None,
        omit_dossier_paths: bool = False,
        omit_section_paths: bool = False,
        coverage_override: dict[str, Any] | None = None,
        draft_word_padding: int = 0,
        revision_keeps_padding: bool = False,
    ) -> None:
        self.args = args
        self.followup_needed = followup_needed
        self.section_drafting_needed = section_drafting_needed
        self.fail_labels = fail_labels or set()
        self.budget = budget or FakeBudget()
        self.default_claim_type = default_claim_type
        self.scout_overrides = scout_overrides or {}
        self.verifier_overrides = verifier_overrides or {}
        self.section_word_count = section_word_count
        self.assembled_word_counts = list(assembled_word_counts or [])
        self.audit_material_issues = list(audit_material_issues or [])
        self.revision_remaining_issues = list(revision_remaining_issues or [])
        self.omit_dossier_paths = omit_dossier_paths
        self.omit_section_paths = omit_section_paths
        self.coverage_override = coverage_override
        self.draft_word_padding = draft_word_padding
        self.revision_keeps_padding = revision_keeps_padding
        self.calls: list[dict[str, Any]] = []
        self.phases: list[str] = []

    # -- scratchpad helpers -------------------------------------------------
    def workspace_root(self) -> str:
        workspace = self.args.get("workspace")
        if not isinstance(workspace, dict):
            return ""
        directory = str(workspace.get("scratchpad_dir", "")).rstrip("/")
        slug = str(workspace.get("run_slug", ""))
        if not directory or not slug:
            return ""
        return f"{directory}/deep-research/{slug}"

    @staticmethod
    def _path_from_prompt(prompt: str, marker: str) -> str:
        index = prompt.find(marker)
        if index < 0:
            return ""
        return prompt[index:].split()[0].rstrip(",.")

    def _next_assembled_word_count(self) -> int:
        if not self.assembled_word_counts:
            target = self.args.get("report_profile", {}).get("target_words", 3_000)
            return int(target)
        if len(self.assembled_word_counts) == 1:
            return self.assembled_word_counts[0]
        return self.assembled_word_counts.pop(0)

    async def agent(self, prompt: str, **options: Any) -> dict[str, Any] | None:
        label = options.get("label", "")
        self.calls.append({"prompt": prompt, **options})
        self.budget.charge()
        if label in self.fail_labels:
            return None
        root = self.workspace_root()

        if label.startswith("scout:") or label == "followup:scout":
            lane_id = label.split(":", 1)[1]
            scout = self.scout_overrides.get(lane_id) or self._scout(lane_id)
            if root and not self.omit_dossier_paths:
                scout = dict(scout)
                scout["dossier_path"] = self._path_from_prompt(prompt, f"{root}/lanes/")
            return scout
        if label.startswith("escalation:"):
            scout = self._scout("acquisition-escalation")
            if root and not self.omit_dossier_paths:
                scout["dossier_path"] = self._path_from_prompt(prompt, f"{root}/lanes/")
            return scout
        if label.startswith("verify:") or label == "followup:verify":
            lane_id = label.split(":", 1)[1]
            if lane_id in self.verifier_overrides:
                return self.verifier_overrides[lane_id]
            return self._verification(lane_id)
        if label == "coverage":
            if self.coverage_override is not None:
                return self.coverage_override
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
        if label.startswith("section-draft:") or label.startswith("section-expand:"):
            section_number = label.rsplit(":", 1)[1]
            lane_id = f"lane-{section_number}"
            url = f"https://example.test/{lane_id}"
            if root:
                expanding = label.startswith("section-expand:")
                path = self._path_from_prompt(prompt, f"{root}/sections/")
                return {
                    "heading": f"Movement {section_number}",
                    "section_path": "" if self.omit_section_paths else path,
                    "word_count": self.section_word_count * (2 if expanding else 1),
                    "cited_urls": [url],
                    "used_claim_ids": [f"{lane_id}/C1"],
                    "gaps": [],
                }
            return {
                "heading": f"Movement {section_number}",
                "body_markdown": f"A section supported by a [primary source]({url}).",
                "used_claim_ids": [f"{lane_id}/C1"],
                "gaps": [],
            }
        if label.startswith("draft-assembly") and root:
            first_lane = self.args["lanes"][0]["id"]
            return {
                "title": "A Long, Unified Report",
                "body_path": self._path_from_prompt(prompt, f"{root}/report/"),
                "assembled_word_count": self._next_assembled_word_count(),
                "cited_urls": [f"https://example.test/{first_lane}"],
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
            padding = ("filler " * self.draft_word_padding).strip()
            return {
                "title": "A Specific Reader-Fit Report",
                "body_markdown": (
                    f"The evidence establishes the main answer through a "
                    f"[primary source]({url}).\n\n"
                    "## What changed\n\n"
                    f"The supported record supports a concise conclusion. {padding}".strip()
                ),
                "gaps": [],
            }
        if label.startswith("audit:"):
            return {
                "revision_needed": bool(self.audit_material_issues),
                "material_issues": list(self.audit_material_issues),
                "minor_issues": [],
                "summary": "No material issue.",
            }
        if label == "revision" and root:
            return {
                "title": "A Long, Unified Report",
                "body_path": self._path_from_prompt(prompt, f"{root}/report/"),
                "assembled_word_count": self._next_assembled_word_count(),
                "remaining_material_issues": list(self.revision_remaining_issues),
            }
        if label == "revision":
            first_lane = self.args["lanes"][0]["id"]
            url = f"https://example.test/{first_lane}"
            # A revision tightens by default; revision_keeps_padding models one
            # that fails to.
            padding = (
                ("filler " * self.draft_word_padding).strip() if self.revision_keeps_padding else ""
            )
            return {
                "title": "A Specific Reader-Fit Report",
                "body_markdown": (
                    f"The revised answer cites a [primary source]({url}).\n\n"
                    f"## What changed\n\nThe supported conclusion remains. {padding}".strip()
                ),
                "remaining_material_issues": list(self.revision_remaining_issues),
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
    writing_reserve_tokens: int | None = None,
    workspace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    counts = {"focused": 2, "standard": 3, "extended": 5}
    ceilings = {
        "focused": (4, 6),
        "standard": (6, 8),
        "extended": (8, 12),
    }
    searches, fetches = ceilings[tier]
    payload: dict[str, Any]
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
    payload = {
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
            "current_as_of": "2026-07-28",
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
        "allow_acquisition_escalation": False,
        "escalation": None,
        "routes": routes,
    }
    if writing_reserve_tokens is not None:
        payload["writing_reserve_tokens"] = writing_reserve_tokens
    if workspace is not None:
        payload["workspace"] = workspace
    return payload


def scratchpad_workspace(run_slug: str = "bounded-test") -> dict[str, str]:
    """A valid workspace argument pointing at an absolute scratchpad path."""
    return {"scratchpad_dir": "/tmp/kolega-scratchpad-fixture", "run_slug": run_slug}


# Mirrors the curated __builtins__ in kolega-code's workflow executor. Running the
# workflow under this mapping catches any reliance on a builtin the real sandbox
# withholds (import, open, eval, and the time/random surface are all absent).
SANDBOX_BUILTIN_NAMES = (
    "abs",
    "all",
    "any",
    "ascii",
    "bin",
    "bool",
    "bytearray",
    "bytes",
    "callable",
    "chr",
    "dict",
    "divmod",
    "enumerate",
    "filter",
    "float",
    "format",
    "frozenset",
    "getattr",
    "hasattr",
    "hash",
    "hex",
    "int",
    "isinstance",
    "issubclass",
    "iter",
    "len",
    "list",
    "map",
    "max",
    "min",
    "next",
    "oct",
    "ord",
    "pow",
    "range",
    "repr",
    "reversed",
    "round",
    "set",
    "setattr",
    "slice",
    "sorted",
    "str",
    "sum",
    "tuple",
    "type",
    "zip",
    "Exception",
    "ValueError",
    "KeyError",
    "IndexError",
    "TypeError",
    "RuntimeError",
    "StopIteration",
    "StopAsyncIteration",
    "ArithmeticError",
    "ZeroDivisionError",
    "AttributeError",
    "NotImplementedError",
    "AssertionError",
    "__build_class__",
)


def sandbox_builtins() -> dict[str, Any]:
    """The restricted builtins mapping the workflow must run under."""
    import builtins

    table: dict[str, Any] = {
        name: getattr(builtins, name) for name in SANDBOX_BUILTIN_NAMES if hasattr(builtins, name)
    }
    table["True"] = True
    table["False"] = False
    table["None"] = None
    return table


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
        "__builtins__": sandbox_builtins(),
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
        # Default stage_plan: selective + thesis_changing + combined. Every lane
        # holding eligible claims is verified; no capacity is held back.
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
        self.assertEqual(result["run_summary"]["deferred_claims"], 0)
        self.assertLessEqual(len(harness.calls), 11)
        self.assertTrue(
            all(
                call.get("model_override") == args["routes"]["discovery"]
                for call in harness.calls
                if call["label"].startswith("scout:")
            )
        )
        self.assertEqual(result["report_markdown"].count("\n## Sources\n"), 1)
        self.assertEqual(len(result["cited_sources"]), 1)
        self.assertEqual(len(result["source_registry"]), 3)
        # Each lane's own failed URL reaches its verifier prompt.
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

    def test_no_verifier_capacity_is_reserved_before_coverage(self) -> None:
        """Every eligible lane is verified whether or not a follow-up happens."""
        without_followup = FakeWorkflowHarness(workflow_args(), followup_needed=False)
        asyncio.run(execute_workflow(without_followup))
        with_followup = FakeWorkflowHarness(workflow_args(), followup_needed=True)
        followup_result = asyncio.run(execute_workflow(with_followup))

        def main_verifies(harness: FakeWorkflowHarness) -> int:
            return len([c for c in harness.calls if c["label"].startswith("verify:lane-")])

        self.assertEqual(main_verifies(without_followup), 3)
        self.assertEqual(main_verifies(with_followup), 3)
        self.assertIn("followup:verify", [c["label"] for c in with_followup.calls])
        self.assertEqual(followup_result["run_summary"]["verifier_calls"], 4)
        self.assertEqual(followup_result["run_summary"]["deferred_claims"], 0)

    def test_escalation_is_verified_alongside_the_followup(self) -> None:
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
        self.assertIn("verify:acquisition-escalation", labels)
        self.assertIn("followup:verify", labels)
        # Three lanes, the escalation, and the follow-up are each verified once.
        self.assertEqual(result["run_summary"]["verifier_calls"], 5)

    def test_writing_reserve_suppresses_followup(self) -> None:
        # The reserve floor for a 3,000-word target is 18,000 tokens; a budget
        # only slightly above it admits research but not optional follow-up work.
        args = workflow_args(writing_reserve_tokens=18_000)
        budget = FakeBudget(total=18_900, spent_per_agent=100)
        harness = FakeWorkflowHarness(args, followup_needed=True, budget=budget)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["run_summary"]["base_lanes_completed"], 3)
        self.assertEqual(result["run_summary"]["followups_run"], 0)
        self.assertFalse(any(call["label"].startswith("followup:") for call in harness.calls))

    def test_exhausted_reserve_stops_before_any_worker(self) -> None:
        args = workflow_args(writing_reserve_tokens=18_000)
        budget = FakeBudget(total=18_000, spent_per_agent=100)
        harness = FakeWorkflowHarness(args, budget=budget)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "failed")
        self.assertFalse(harness.calls)
        self.assertTrue(
            any("research did not start" in gap for gap in result["gaps"]), result["gaps"]
        )
        # Lanes that never ran are not reported as failed workers.
        self.assertFalse(any("research worker failed" in gap for gap in result["gaps"]))

    def test_writing_reserve_floor_scales_with_target_length(self) -> None:
        args = workflow_args()
        args["report_profile"]["length"] = "long"
        args["report_profile"]["target_words"] = 12_000
        args["writing_reserve_tokens"] = 18_000
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "failed")
        self.assertFalse(harness.calls)
        self.assertTrue(
            any("writing_reserve_tokens must be at least 33600" in gap for gap in result["gaps"]),
            result["gaps"],
        )

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

        for count in (-1, True, "two"):
            args = workflow_args()
            args["intake"]["topic_questions_asked"] = count
            invalid_cases.append(
                (
                    f"invalid topic count {count!r}",
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
        args["brief"].pop("current_as_of")
        invalid_cases.append(("missing as-of date", args, "brief.current_as_of is required"))

        args = workflow_args()
        args["research_batch_size"] = 2
        invalid_cases.append(
            ("legacy batch size", args, "research_batch_size is no longer supported")
        )

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

    def test_topic_question_count_is_telemetry_not_a_gate(self) -> None:
        """A caller-asserted question count never aborts an otherwise valid run."""
        for count in (0, 7):
            with self.subTest(count=count):
                args = workflow_args()
                args["intake"]["topic_questions_asked"] = count
                harness = FakeWorkflowHarness(args)
                result = asyncio.run(execute_workflow(harness))

                self.assertEqual(result["status"], "complete")
                self.assertEqual(result["run_summary"]["topic_questions_asked"], count)

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
        """Lane-3 (causal) is the only one eligible under selective; lanes 1 & 2 hold
        background testimony and are skipped as having no eligible claims."""
        args = workflow_args("standard")  # 3 lanes
        args["stage_plan"] = {
            "verification": "selective",
            "followup": "off",
            "audit": "deterministic",
        }
        harness = FakeWorkflowHarness(
            args,
            scout_overrides={
                "lane-1": _make_scout(
                    "lane-1", claim_type="attributed_report", importance="background"
                ),
                "lane-2": _make_scout(
                    "lane-2", claim_type="attributed_report", importance="background"
                ),
                "lane-3": _make_scout("lane-3", claim_type="causal"),
            },
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
        # The report still draws on attributed and single-source claims.
        self.assertGreater(len(result["report_markdown"]), 50)

    # -----------------------------------------------------------------------
    # Acceptance scenario 3: no-op suppression
    # -----------------------------------------------------------------------

    def test_no_eligible_claims_suppresses_all_verifiers(self) -> None:
        """Background testimony in every lane → zero eligible → zero verifiers."""
        args = workflow_args()
        args["stage_plan"] = {
            "verification": "selective",
            "followup": "off",
            "audit": "deterministic",
        }
        harness = FakeWorkflowHarness(
            args,
            scout_overrides={
                f"lane-{index}": _make_scout(
                    f"lane-{index}", claim_type="attributed_report", importance="background"
                )
                for index in (1, 2, 3)
            },
        )
        result = asyncio.run(execute_workflow(harness))

        verify_calls = [c for c in harness.calls if c["label"].startswith("verify:")]
        self.assertEqual(len(verify_calls), 0)
        self.assertEqual(result["run_summary"]["verifier_calls"], 0)
        self.assertEqual(result["run_summary"]["selected_claims"], 0)
        self.assertNotIn("Verify", result["run_summary"]["stages_run"])
        self.assertIn("Verify", result["run_summary"]["stages_skipped"])
        # Testimony claims remain citable as attributed material.
        self.assertGreater(len(result["report_markdown"]), 50)
        draft_prompt = next(c["prompt"] for c in harness.calls if c["label"] == "draft")
        self.assertIn("'status': 'attributed'", draft_prompt)

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
        self.assertIn("'status': 'unverified'", draft_prompt[lane_claim : lane_claim + 300])

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
            scout_overrides={
                "lane-1": _make_scout(
                    "lane-1", claim_type="attributed_report", importance="background"
                ),
                "lane-2": _make_scout("lane-2", claim_type="causal", importance="supporting"),
                "lane-3": _make_scout(
                    "lane-3", claim_type="attributed_report", importance="background"
                ),
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
            "topic_questions_asked",
            "target_words",
            "assembled_word_count",
            "expansion_passes",
            "dossiers",
            "workspace_enabled",
        ):
            self.assertIn(key, rs, f"missing telemetry key: {key}")

        # All 3 legacy claims are eligible for selective (conclusion-driving) and
        # every eligible lane is verified — nothing is deferred by a global cap.
        self.assertEqual(rs["eligible_claims"], 3)
        self.assertEqual(rs["selected_claims"], 3)
        self.assertEqual(rs["deferred_claims"], 0)
        self.assertEqual(rs["verifier_calls"], 3)
        self.assertEqual(rs["lanes_skipped_no_eligible"], 0)
        self.assertEqual(rs["verifier_verdict_counts"].get("supported", 0), 3)
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


class DeterministicHelperParityTests(unittest.TestCase):
    """The workflow's in-sandbox copies must not drift from the authoritative ones."""

    def test_link_extraction_matches_between_implementations(self) -> None:
        for fixture in LINK_FIXTURES:
            with self.subTest(fixture=fixture[:40]):
                self.assertEqual(
                    WORKFLOW_HELPERS["markdown_urls"](fixture),
                    MATERIALIZER.markdown_urls(fixture),
                )

    def test_url_identity_matches_between_implementations(self) -> None:
        for fixture in URL_FIXTURES:
            with self.subTest(fixture=fixture):
                self.assertEqual(
                    WORKFLOW_HELPERS["canonical_url"](fixture),
                    MATERIALIZER.canonical_url(fixture),
                )

    def test_link_edge_cases_resolve_correctly(self) -> None:
        extract = MATERIALIZER.markdown_urls
        # Balanced parentheses survive: the flagship Wikipedia case.
        self.assertEqual(
            extract("[Saturn](https://en.wikipedia.org/wiki/Saturn_(mythology)) x"),
            ["https://en.wikipedia.org/wiki/Saturn_(mythology)"],
        )
        # An optional title is not part of the destination.
        self.assertEqual(
            extract('[Spec](https://example.com/doc "Title")'),
            ["https://example.com/doc"],
        )
        # Images, inline code, fenced blocks, and reference links are not citations.
        self.assertEqual(extract("![i](https://example.com/img.png)"), [])
        self.assertEqual(extract("`[a](https://example.com/no)`"), [])
        self.assertEqual(extract("```\n[a](https://example.com/no)\n```"), [])
        self.assertEqual(extract("[label][ref]"), [])
        # Anchors, mail links, and relative paths are ignored, not "unknown".
        self.assertEqual(extract("[a](#x) [b](mailto:a@b.c) [c](./d.md)"), [])

    def test_url_identity_preserves_meaningful_query_parameters(self) -> None:
        canonical = MATERIALIZER.canonical_url
        self.assertNotEqual(
            canonical("https://example.gov/data?report=2019"),
            canonical("https://example.gov/data?report=2024"),
        )
        self.assertNotEqual(
            canonical("https://www.jstor.org/stable/2860993?seq=3"),
            canonical("https://www.jstor.org/stable/2860993?seq=41"),
        )
        # Tracking-only differences and parameter order collapse.
        self.assertEqual(
            canonical("https://example.com/p?utm_source=x&id=7"),
            canonical("https://example.com/p?id=7"),
        )
        self.assertEqual(
            canonical("https://example.com/p?b=2&a=1"),
            canonical("https://example.com/p?a=1&b=2"),
        )
        self.assertEqual(
            canonical("https://Example.COM/Path/"),
            canonical("https://example.com/Path"),
        )

    def test_registry_keeps_query_distinct_sources_apart(self) -> None:
        """Two query-differentiated sources must not collapse into one registry card."""
        args = workflow_args()
        overrides = {}
        for index, year in ((1, "2019"), (2, "2024")):
            scout = _make_scout(f"lane-{index}")
            scout["sources"][0]["url"] = f"https://example.gov/data?report={year}"
            scout["sources"][0]["title"] = f"Report {year}"
            overrides[f"lane-{index}"] = scout
        harness = FakeWorkflowHarness(args, scout_overrides=overrides)
        result = asyncio.run(execute_workflow(harness))

        urls = sorted(source["url"] for source in result["source_registry"])
        self.assertIn("https://example.gov/data?report=2019", urls)
        self.assertIn("https://example.gov/data?report=2024", urls)


class ReportPreservationTests(unittest.TestCase):
    """A drafted report is never discarded for a residual defect."""

    def test_residual_material_issue_returns_partial_with_the_report(self) -> None:
        args = workflow_args()
        harness = FakeWorkflowHarness(
            args,
            audit_material_issues=["a material claim is unsupported"],
            revision_remaining_issues=["the gap could not be closed from evidence"],
        )
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "partial")
        self.assertGreater(len(result["report_markdown"]), 50)
        self.assertEqual(result["report_markdown"].count("\n## Sources\n"), 1)
        self.assertIn("the gap could not be closed from evidence", result["gaps"])
        self.assertIn("Revise", result["run_summary"]["stages_run"])

    def test_unknown_citation_url_does_not_discard_the_report(self) -> None:
        args = workflow_args()
        harness = FakeWorkflowHarness(
            args,
            audit_material_issues=["citation cannot be resolved"],
            revision_remaining_issues=["unknown citation URL remains"],
        )
        result = asyncio.run(execute_workflow(harness))

        self.assertNotEqual(result["status"], "failed")
        self.assertTrue(result["report_markdown"].startswith("# "))

    def test_failed_only_when_no_report_exists(self) -> None:
        with self.subTest(case="drafting worker fails"):
            harness = FakeWorkflowHarness(workflow_args(), fail_labels={"draft"})
            result = asyncio.run(execute_workflow(harness))
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["report_markdown"], "")
            self.assertIn("drafting worker failed", result["gaps"])

        with self.subTest(case="every claim refuted"):
            args = workflow_args()
            refuted = {
                "lane_id": "lane",
                "summary": "Nothing survived verification.",
                "verdicts": [
                    {
                        "claim_id": "C1",
                        "status": "unsupported",
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
            harness = FakeWorkflowHarness(
                args,
                verifier_overrides={f"lane-{index}": dict(refuted) for index in (1, 2, 3)},
            )
            result = asyncio.run(execute_workflow(harness))
            self.assertEqual(result["status"], "failed")
            self.assertTrue(
                any("no supported claim set" in gap for gap in result["gaps"]), result["gaps"]
            )

    def test_status_matrix_governs_claim_use(self) -> None:
        args = workflow_args()
        harness = FakeWorkflowHarness(args)
        asyncio.run(execute_workflow(harness))
        draft_prompt = next(c["prompt"] for c in harness.calls if c["label"] == "draft")

        self.assertIn("verified – independently checked", draft_prompt)
        self.assertIn("unverified – not independently checked", draft_prompt)
        self.assertIn("not describe it as independently corroborated", draft_prompt)
        # The retired vocabulary is gone.
        self.assertNotIn("direct – cite and attribute", draft_prompt)
        self.assertNotIn("deferred", draft_prompt)


class ClaimTypeEligibilityTests(unittest.TestCase):
    """A self-reported claim type can never switch verification off."""

    def test_unrecognized_claim_types_still_get_verified(self) -> None:
        for claim_type in ("statistical", "numeric_fact", "QUANTITATIVE", "Quantitative"):
            with self.subTest(claim_type=claim_type):
                args = workflow_args()
                overrides = {
                    f"lane-{index}": _make_scout(
                        f"lane-{index}", claim_type=claim_type, disputed=True
                    )
                    for index in (1, 2, 3)
                }
                harness = FakeWorkflowHarness(args, scout_overrides=overrides)
                result = asyncio.run(execute_workflow(harness))

                self.assertEqual(result["run_summary"]["eligible_claims"], 3)
                self.assertEqual(result["run_summary"]["verifier_calls"], 3)

    def test_background_testimony_still_opts_out(self) -> None:
        args = workflow_args()
        overrides = {
            f"lane-{index}": _make_scout(
                f"lane-{index}", claim_type="attributed_report", importance="background"
            )
            for index in (1, 2, 3)
        }
        harness = FakeWorkflowHarness(args, scout_overrides=overrides)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["run_summary"]["eligible_claims"], 0)
        self.assertEqual(result["run_summary"]["verifier_calls"], 0)

    def test_conclusion_driving_testimony_is_verified(self) -> None:
        args = workflow_args()
        overrides = {
            f"lane-{index}": _make_scout(
                f"lane-{index}", claim_type="interpretation", importance="conclusion-driving"
            )
            for index in (1, 2, 3)
        }
        harness = FakeWorkflowHarness(args, scout_overrides=overrides)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["run_summary"]["verifier_calls"], 3)

    def test_claim_type_and_trigger_enums_are_declared_in_the_schema(self) -> None:
        source = WORKFLOW_PATH.read_text(encoding="utf-8")
        for value in (
            "attributed_report",
            "external_fact",
            "quantitative",
            "causal",
            "comparative",
            "interpretation",
        ):
            self.assertIn(f'"{value}"', source)
        self.assertIn('"claim_type": {"type": "string", "enum": CLAIM_TYPES}', source)


class ScratchpadEvidenceTests(unittest.TestCase):
    """Evidence depth lives in scratchpad dossiers, not in the return channel."""

    def test_workspace_turns_on_dossiers_and_path_based_handoffs(self) -> None:
        args = workflow_args(workspace=scratchpad_workspace())
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))
        root = harness.workspace_root()

        self.assertEqual(result["status"], "complete")
        self.assertTrue(result["run_summary"]["workspace_enabled"])
        self.assertEqual(result["run_summary"]["dossiers"], 3)

        scout_prompt = next(c["prompt"] for c in harness.calls if c["label"] == "scout:lane-1")
        self.assertIn(f"{root}/lanes/lane-1.md", scout_prompt)
        self.assertIn("EVIDENCE DOSSIER (required)", scout_prompt)
        self.assertIn("verbatim quotations", scout_prompt)

        verify_prompt = next(c["prompt"] for c in harness.calls if c["label"] == "verify:lane-1")
        self.assertIn(f"{root}/lanes/lane-1.md", verify_prompt)
        self.assertIn(f"{root}/lanes/lane-1.verify.md", verify_prompt)
        self.assertIn("SELECTED CLAIMS:", verify_prompt)
        # The verifier is not handed the whole scout record any more.
        self.assertNotIn("SCOUT RECORD:", verify_prompt)
        self.assertNotIn("candidate_claims", verify_prompt)

    def test_coverage_and_audit_receive_a_claim_index_without_excerpts(self) -> None:
        args = workflow_args(workspace=scratchpad_workspace())
        harness = FakeWorkflowHarness(args)
        asyncio.run(execute_workflow(harness))

        for label in ("coverage", "audit:combined"):
            with self.subTest(label=label):
                prompt = next(c["prompt"] for c in harness.calls if c["label"] == label)
                self.assertIn("CLAIM INDEX:", prompt)
                self.assertNotIn("A compact supporting passage.", prompt)

    def test_absent_workspace_keeps_inline_only_behaviour(self) -> None:
        harness = FakeWorkflowHarness(workflow_args())
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "complete")
        self.assertFalse(result["run_summary"]["workspace_enabled"])
        self.assertEqual(result["run_summary"]["dossiers"], 0)
        scout_prompt = next(c["prompt"] for c in harness.calls if c["label"] == "scout:lane-1")
        self.assertNotIn("EVIDENCE DOSSIER", scout_prompt)
        self.assertNotIn("deep-research/", scout_prompt)

    def test_scout_that_cannot_persist_a_dossier_still_produces_a_report(self) -> None:
        args = workflow_args(workspace=scratchpad_workspace())
        harness = FakeWorkflowHarness(args, omit_dossier_paths=True)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["run_summary"]["dossiers"], 0)
        self.assertGreater(len(result["report_markdown"]), 50)
        verify_prompt = next(c["prompt"] for c in harness.calls if c["label"] == "verify:lane-1")
        self.assertNotIn("LANE DOSSIER:", verify_prompt)

    def test_invalid_workspace_fails_before_dispatch(self) -> None:
        cases = [
            ("relative path", {"scratchpad_dir": "tmp/pad", "run_slug": "ok"}, "absolute path"),
            ("empty path", {"scratchpad_dir": "", "run_slug": "ok"}, "absolute path"),
            ("bad slug", {"scratchpad_dir": "/tmp/pad", "run_slug": "Bad Slug"}, "run_slug"),
            ("slug leading dash", {"scratchpad_dir": "/tmp/pad", "run_slug": "-x"}, "run_slug"),
            ("empty slug", {"scratchpad_dir": "/tmp/pad", "run_slug": ""}, "run_slug"),
        ]
        for name, workspace, expected in cases:
            with self.subTest(name=name):
                harness = FakeWorkflowHarness(workflow_args(workspace=workspace))
                result = asyncio.run(execute_workflow(harness))

                self.assertEqual(result["status"], "failed")
                self.assertFalse(harness.calls)
                self.assertTrue(
                    any(expected in gap for gap in result["gaps"]),
                    result["gaps"],
                )


class LongReportAssemblyTests(unittest.TestCase):
    """Long reports are assembled from files, not one giant JSON string."""

    @staticmethod
    def long_args() -> dict[str, Any]:
        args = workflow_args(workspace=scratchpad_workspace("long-report"))
        args["report_profile"]["length"] = "detailed"
        args["report_profile"]["target_words"] = 6_000
        args["writing_reserve_tokens"] = 18_000
        return args

    def test_section_files_and_report_plan_replace_inline_body(self) -> None:
        harness = FakeWorkflowHarness(self.long_args(), section_word_count=3_000)
        result = asyncio.run(execute_workflow(harness))
        root = harness.workspace_root()

        self.assertEqual(result["run_summary"]["draft_mode"], "sections")
        self.assertEqual(result["report_markdown"], "")
        plan = result["report_plan"]
        self.assertEqual(plan["body_path"], f"{root}/report/body.md")
        self.assertEqual(len(plan["section_paths"]), 2)
        self.assertTrue(plan["section_paths"][0].startswith(f"{root}/sections/01-"))
        self.assertEqual(plan["assembled_word_count"], 6_000)
        self.assertEqual(result["run_summary"]["expansion_passes"], 0)
        self.assertTrue(result["source_registry"])

        section_prompt = next(c["prompt"] for c in harness.calls if c["label"] == "section-draft:1")
        self.assertIn(f"{root}/sections/01-", section_prompt)
        self.assertIn("Do not return the body text", section_prompt)

        audit_prompt = next(c["prompt"] for c in harness.calls if c["label"] == "audit:combined")
        self.assertIn("REPORT FILE:", audit_prompt)
        self.assertNotIn("\nREPORT: ", audit_prompt)

    def test_short_assembly_triggers_exactly_one_expansion_pass(self) -> None:
        harness = FakeWorkflowHarness(
            self.long_args(),
            section_word_count=500,
            assembled_word_counts=[1_000, 5_400],
        )
        result = asyncio.run(execute_workflow(harness))

        labels = [c["label"] for c in harness.calls]
        self.assertEqual(result["run_summary"]["expansion_passes"], 1)
        self.assertEqual(labels.count("draft-assembly"), 1)
        self.assertEqual(labels.count("draft-assembly:2"), 1)
        expansions = [label for label in labels if label.startswith("section-expand:")]
        self.assertTrue(1 <= len(expansions) <= 3)
        self.assertEqual(result["report_plan"]["assembled_word_count"], 5_400)

    def test_persistent_shortfall_is_reported_but_still_delivered(self) -> None:
        harness = FakeWorkflowHarness(
            self.long_args(),
            section_word_count=200,
            assembled_word_counts=[900],
        )
        result = asyncio.run(execute_workflow(harness))

        self.assertNotEqual(result["status"], "failed")
        self.assertIsNotNone(result["report_plan"])
        self.assertTrue(
            any("materially shorter than the requested length" in gap for gap in result["gaps"]),
            result["gaps"],
        )

    def test_missing_section_files_fall_back_to_one_bounded_draft(self) -> None:
        harness = FakeWorkflowHarness(self.long_args(), omit_section_paths=True)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["run_summary"]["draft_mode"], "single")
        self.assertIsNone(result["report_plan"])
        self.assertTrue(result["report_markdown"].startswith("# "))
        self.assertTrue(
            any("did not persist enough section files" in gap for gap in result["gaps"]),
            result["gaps"],
        )

    def test_inline_section_drafting_without_a_workspace(self) -> None:
        args = workflow_args()
        args["report_profile"]["length"] = "detailed"
        args["report_profile"]["target_words"] = 6_000
        args["writing_reserve_tokens"] = 18_000
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["run_summary"]["draft_mode"], "sections")
        self.assertIsNone(result["report_plan"])
        self.assertEqual(result["report_markdown"].count("\n## Sources\n"), 1)


class DegradedStageTests(unittest.TestCase):
    """A stage whose structured output degenerates must fail loudly, not quietly."""

    @staticmethod
    def degenerate_coverage() -> dict[str, Any]:
        """Reproduces an observed failure: later fields packed into `summary`."""
        return {
            "summary": (
                "At 6000 words with independent periods, section drafting is warranted."
                "\n<followup_needed>true</followup_needed>"
                '\n<section_outline>[{"heading": "One", "purpose": "p", "claim_ids": []}]'
                "</section_outline>"
            )
        }

    def long_args(self) -> dict[str, Any]:
        args = workflow_args()
        args["report_profile"]["length"] = "detailed"
        args["report_profile"]["target_words"] = 6_000
        args["writing_reserve_tokens"] = 18_000
        return args

    def test_unusable_coverage_is_reported_and_its_decisions_discarded(self) -> None:
        harness = FakeWorkflowHarness(self.long_args(), followup_needed=True)
        harness.coverage_override = self.degenerate_coverage()
        result = asyncio.run(execute_workflow(harness))

        rs = result["run_summary"]
        self.assertIn("Coverage", rs["degraded_stages"])
        self.assertEqual(result["status"], "partial")
        self.assertTrue(
            any("coverage stage returned an unusable record" in gap for gap in result["gaps"]),
            result["gaps"],
        )
        # The follow-up it asked for is not silently performed.
        self.assertEqual(rs["followups_run"], 0)
        self.assertFalse(any(c["label"].startswith("followup:") for c in harness.calls))

    def test_long_report_still_gets_sections_from_a_derived_outline(self) -> None:
        args = self.long_args()
        args["workspace"] = scratchpad_workspace("derived-outline")
        harness = FakeWorkflowHarness(args, section_word_count=1_500)
        harness.coverage_override = self.degenerate_coverage()
        result = asyncio.run(execute_workflow(harness))

        rs = result["run_summary"]
        self.assertEqual(rs["section_outline_source"], "derived")
        self.assertEqual(rs["draft_mode"], "sections")
        self.assertIsNotNone(result["report_plan"])
        # One section per lane that produced citable claims.
        self.assertEqual(len(result["report_plan"]["section_paths"]), 3)
        seams = next(c["prompt"] for c in harness.calls if c["label"] == "draft-assembly")
        self.assertIn("derived from research lanes", seams)

    def test_healthy_coverage_is_not_flagged_and_owns_the_outline(self) -> None:
        args = self.long_args()
        args["workspace"] = scratchpad_workspace("healthy-coverage")
        harness = FakeWorkflowHarness(args, section_word_count=1_500)
        result = asyncio.run(execute_workflow(harness))

        rs = result["run_summary"]
        self.assertEqual(rs["degraded_stages"], [])
        self.assertEqual(rs["section_outline_source"], "coverage")
        self.assertEqual(rs["draft_mode"], "sections")

    def test_short_report_does_not_derive_an_outline(self) -> None:
        harness = FakeWorkflowHarness(workflow_args())
        harness.coverage_override = self.degenerate_coverage()
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["run_summary"]["section_outline_source"], "none")
        self.assertEqual(result["run_summary"]["draft_mode"], "single")

    def test_workers_are_told_to_write_reader_facing_gaps(self) -> None:
        harness = FakeWorkflowHarness(workflow_args())
        asyncio.run(execute_workflow(harness))
        for label in ("scout:lane-1", "verify:lane-1", "coverage"):
            with self.subTest(label=label):
                prompt = next(c["prompt"] for c in harness.calls if c["label"] == label)
                self.assertIn("State every gap in reader-facing language", prompt)


class LengthBudgetTests(unittest.TestCase):
    """Both directions of the confirmed word target are enforced."""

    def test_overlong_draft_is_sent_to_revision_to_be_tightened(self) -> None:
        args = workflow_args()  # target 3000 -> overlength threshold 4050
        harness = FakeWorkflowHarness(args, draft_word_padding=6_000)
        result = asyncio.run(execute_workflow(harness))

        revision = [c for c in harness.calls if c["label"] == "revision"]
        self.assertEqual(len(revision), 1)
        self.assertIn("far longer than the requested length", revision[0]["prompt"])
        self.assertIn("words against a target of about 3000", revision[0]["prompt"])
        # The revision tightened it, so no overlength gap survives.
        self.assertFalse(any("materially longer" in gap for gap in result["gaps"]))

    def test_overlength_survives_as_a_gap_when_revision_does_not_tighten(self) -> None:
        args = workflow_args()
        harness = FakeWorkflowHarness(args, draft_word_padding=6_000, revision_keeps_padding=True)
        result = asyncio.run(execute_workflow(harness))

        self.assertTrue(
            any("materially longer than the requested length" in gap for gap in result["gaps"]),
            result["gaps"],
        )
        self.assertEqual(result["status"], "partial")

    def test_on_target_report_triggers_no_revision(self) -> None:
        args = workflow_args()
        harness = FakeWorkflowHarness(args, draft_word_padding=2_900)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "complete")
        self.assertFalse(any(c["label"] == "revision" for c in harness.calls))
        self.assertFalse(any("longer than the requested" in gap for gap in result["gaps"]))


class ReaderFacingGapsTests(unittest.TestCase):
    """Operator-facing gaps are sanitised before reaching a reader."""

    def test_internal_identifiers_are_stripped_or_dropped(self) -> None:
        raw = [
            "lane-1/C11's second half requires evidence from the later lanes.",
            "Klibansky, Panofsky and Saxl's Saturn and Melancholy was reached only at "
            "second hand, through two summarising sources.",
            "C6's self-dating rests on a single tertiary source (lane-2/C6).",
            "   ",
            "Short.",
        ]
        cleaned = MATERIALIZER.reader_facing_gaps(raw)

        joined = " ".join(cleaned)
        self.assertNotIn("lane-", joined)
        self.assertNotIn("C11", joined)
        self.assertNotIn("C6", joined)
        # The genuine, reader-useful disclosure survives intact.
        self.assertTrue(any("Saturn and Melancholy" in gap for gap in cleaned))
        # Entries that were only about research machinery are dropped.
        self.assertFalse(any("later lanes" in gap for gap in cleaned))

    def test_near_duplicate_gaps_collapse_to_the_fullest_wording(self) -> None:
        raw = [
            "Agrippa's table of Saturn is quoted from a page fragment, so the spirit "
            "names and metal are incompletely attested.",
            "Agrippa's table of Saturn survives here only as a page fragment: the spirit "
            "names, the metal, and the promised effects are incompletely attested, and "
            "whether he later retracted the material was never established.",
            "Engraved gems and curse tablets naming Kronos were never surveyed because "
            "the searches failed.",
        ]
        cleaned = MATERIALIZER.reader_facing_gaps(raw)

        self.assertEqual(len(cleaned), 2)
        # The fuller Agrippa phrasing wins.
        agrippa = next(gap for gap in cleaned if "Agrippa" in gap)
        self.assertIn("whether he later retracted", agrippa)
        self.assertTrue(any("Engraved gems" in gap for gap in cleaned))

    def test_distinct_gaps_are_not_collapsed(self) -> None:
        raw = [
            "Ficino's chapters on engraved images could not be read directly.",
            "The Golden Dawn's Saturn ritual was never located in a primary text.",
            "Segal remains the only witness for the Harranian temple description.",
        ]
        self.assertEqual(len(MATERIALIZER.reader_facing_gaps(raw)), 3)

    def test_long_gap_lists_are_capped_with_an_overflow_note(self) -> None:
        subjects = [
            "Ptolemy's Tetrabiblos death attributions",
            "Vettius Valens on Saturn significations",
            "Firmicus Maternus on planetary temperament",
            "the Harranian temple architecture",
            "Ibn Wahshiyya's agronomy digressions",
            "the Castilian intermediary manuscript",
            "Albertus Magnus on permitted images",
            "Ficino's Apologia of 1489",
            "Agrippa's retraction in De vanitate",
            "Duerer's engraving iconography",
            "Barrett's Magus and its plates",
            "Levi's astral light doctrine",
            "the Sprengel correspondence forgery case",
            "Crowley's Liber 777 tables",
            "the Berlin lodge initiation grades",
        ]
        raw = [f"Scholarship on {subject} could not be consulted." for subject in subjects]
        cleaned = MATERIALIZER.reader_facing_gaps(raw)

        self.assertEqual(len(cleaned), MATERIALIZER.MAX_READER_FACING_GAPS + 1)
        self.assertRegex(cleaned[-1], r"^\d+ further sourcing gaps are recorded")
        # Shared boilerplate must not merge gaps about different subjects.
        self.assertGreaterEqual(len(MATERIALIZER.reader_facing_gaps(raw, limit=99)), 13)

    def test_reworded_variants_of_one_gap_collapse(self) -> None:
        """The same gap reported by a scout and a verifier appears once."""
        raw = [
            "Ficino's own chapters on engraved images in Book III of De vita were "
            "unreadable, so whether he prescribed a Saturn talisman cannot be settled.",
            "Ficino's own chapters on engraved images in the third book of De vita — the "
            "passages where he sets out what figures astrologers carve, and whether he "
            "endorses them — could not be read directly.",
        ]
        cleaned = MATERIALIZER.reader_facing_gaps(raw)
        self.assertEqual(len(cleaned), 1)

    def test_partial_report_gaps_section_is_reader_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = {
                "status": "partial",
                "report_markdown": (
                    "# T\n\nBody with a [claim](https://example.test/s).\n\n"
                    "## Sources\n\n- [S](https://example.test/s)\n"
                ),
                "cited_sources": [],
                "gaps": [
                    "lane-3/C4 could not be corroborated by any second source.",
                    "Ellic Howe's documentary case that the correspondence was fabricated "
                    "was never obtained.",
                ],
            }
            result = root / "result.json"
            result.write_text(json.dumps(payload), encoding="utf-8")
            output = root / "partial.md"

            MATERIALIZER.materialize_report(result, output)
            written = output.read_text(encoding="utf-8")

            self.assertIn("## Scope and gaps", written)
            self.assertIn("Ellic Howe", written)
            self.assertNotIn("lane-3", written)
            self.assertNotIn("C4", written)

    def test_degraded_stage_produces_a_materializer_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = {
                "status": "partial",
                "report_markdown": (
                    "# T\n\nBody with a [claim](https://example.test/s).\n\n"
                    "## Sources\n\n- [S](https://example.test/s)\n"
                ),
                "cited_sources": [],
                "gaps": [],
                "run_summary": {"degraded_stages": ["Coverage"]},
            }
            result = root / "result.json"
            result.write_text(json.dumps(payload), encoding="utf-8")

            _, _, warnings = MATERIALIZER.materialize_report(result, root / "out.md")

            self.assertTrue(any("unusable record" in w for w in warnings), warnings)


class RouteAndIdentityContractTests(unittest.TestCase):
    def test_malformed_routes_fail_before_dispatch(self) -> None:
        cases = [
            ("missing effort", {"provider": "p", "model": "m"}, "exactly provider, model"),
            (
                "extra key",
                {"provider": "p", "model": "m", "effort": None, "extra": 1},
                "exactly provider, model",
            ),
            ("empty model", {"provider": "p", "model": "", "effort": None}, "non-empty provider"),
            ("not an object", "fixture-route", "complete route object"),
        ]
        for name, route, expected in cases:
            with self.subTest(name=name):
                args = workflow_args()
                args["routes"] = {"discovery": route}
                harness = FakeWorkflowHarness(args)
                result = asyncio.run(execute_workflow(harness))

                self.assertEqual(result["status"], "failed")
                self.assertFalse(harness.calls)
                self.assertTrue(
                    any(expected in gap for gap in result["gaps"]),
                    result["gaps"],
                )

    def test_unknown_route_role_is_rejected(self) -> None:
        args = workflow_args()
        args["routes"] = {"drafting": {"provider": "p", "model": "m", "effort": None}}
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "failed")
        self.assertTrue(
            any("not a recognized stage role" in gap for gap in result["gaps"]), result["gaps"]
        )

    def test_absent_route_roles_inherit_silently(self) -> None:
        args = workflow_args()
        args["routes"] = {"discovery": {"provider": "p", "model": "m", "effort": "high"}}
        harness = FakeWorkflowHarness(args)
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["status"], "complete")
        scout = next(c for c in harness.calls if c["label"] == "scout:lane-1")
        draft = next(c for c in harness.calls if c["label"] == "draft")
        self.assertEqual(scout["model_override"], args["routes"]["discovery"])
        self.assertNotIn("model_override", draft)

    def test_reused_lane_id_cannot_cross_wire_evidence(self) -> None:
        """A follow-up scout reusing 'lane-1' keeps its own sources and claims."""
        args = workflow_args()
        colliding = _make_scout("lane-1")
        colliding["sources"][0]["url"] = "https://example.test/followup-source"
        colliding["sources"][0]["title"] = "Follow-up source"
        harness = FakeWorkflowHarness(
            args,
            followup_needed=True,
            scout_overrides={"scout": colliding},
        )
        result = asyncio.run(execute_workflow(harness))

        self.assertEqual(result["run_summary"]["followups_run"], 1)
        urls = sorted(source["url"] for source in result["source_registry"])
        self.assertIn("https://example.test/lane-1", urls)
        self.assertIn("https://example.test/followup-source", urls)

        draft_prompt = next(c["prompt"] for c in harness.calls if c["label"] == "draft")
        self.assertIn("'id': 'lane-1/C1'", draft_prompt)
        self.assertIn("'id': 'followup-1/C1'", draft_prompt)


class DocumentedBehaviourTests(unittest.TestCase):
    """Documented behaviour must be reachable through the documented API."""

    def setUp(self) -> None:
        self.skill = SKILL_PATH.read_text(encoding="utf-8")
        self.workflow_guide = (SKILL_ROOT / "references" / "gigacode-workflow.md").read_text(
            encoding="utf-8"
        )
        self.evidence_guide = (SKILL_ROOT / "references" / "evidence-and-reporting.md").read_text(
            encoding="utf-8"
        )

    def test_stage_plan_is_documented_with_its_audit_mapping(self) -> None:
        self.assertIn("stage_plan", self.workflow_guide)
        self.assertIn("stage_plan", self.skill)
        for value in ("risk_only", "selective", "required", "deterministic", "combined", "dual"):
            self.assertIn(value, self.workflow_guide)
        self.assertIn('stage_plan.audit: "dual"', self.skill)

    def test_claim_type_and_trigger_enums_are_documented(self) -> None:
        for value in (
            "attributed_report",
            "external_fact",
            "quantitative",
            "causal",
            "comparative",
            "interpretation",
        ):
            self.assertIn(value, self.evidence_guide)
        for trigger in (
            "known_dispute",
            "cross_source_conflict",
            "scope_risk",
            "source_access_uncertain",
            "high_stakes",
        ):
            self.assertIn(trigger, self.evidence_guide)

    def test_script_path_invocation_is_documented(self) -> None:
        self.assertIn("script_path", self.skill)
        self.assertIn("script_path", self.workflow_guide)
        self.assertIn("takes precedence", self.workflow_guide)

    def test_workspace_and_current_as_of_are_documented(self) -> None:
        self.assertIn("workspace", self.skill)
        self.assertIn("scratchpad_dir", self.workflow_guide)
        self.assertIn("run_slug", self.workflow_guide)
        self.assertIn("current_as_of", self.workflow_guide)
        self.assertIn("current_as_of", self.skill)

    def test_claim_statuses_are_documented(self) -> None:
        for status in (
            "verified",
            "qualified",
            "contested",
            "refuted",
            "attributed",
            "single-source",
            "unverified",
        ):
            self.assertIn(status, self.evidence_guide)

    def test_degradation_and_length_behaviour_are_documented(self) -> None:
        self.assertIn("degraded_stages", self.workflow_guide)
        self.assertIn("degraded_stages", self.skill)
        self.assertIn("section_outline_source", self.workflow_guide)
        self.assertIn("1.35", self.workflow_guide)
        # Gaps must be reader-facing, and that rule is written down.
        self.assertIn("leaked machinery", self.evidence_guide)
        self.assertIn("Scope and gaps", self.workflow_guide)

    def test_sequential_fallback_uses_scratchpad_files(self) -> None:
        fallback = self.skill.split("### Sequential fallback", 1)[1]
        self.assertIn("scratchpad", fallback)
        self.assertIn("registry.json", fallback)
        self.assertIn("not in conversation context", fallback)


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
            "source_registry": [
                {
                    "id": "S001",
                    "title": "Source",
                    "url": "https://example.test/source",
                    "publisher": "Example",
                    "date": "2025",
                    "source_type": "primary",
                }
            ],
            "gaps": [],
        }

    def test_materializes_json_and_creates_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = root / "result.json"
            result.write_text(json.dumps(self.payload()), encoding="utf-8")
            output = root / "reports" / "report.md"

            path, status, warnings = MATERIALIZER.materialize_report(result, output)

            self.assertEqual(path, output)
            self.assertEqual(status, "complete")
            self.assertEqual(warnings, [])
            self.assertTrue(output.read_text(encoding="utf-8").endswith("\n"))

    def test_materializes_markdown_result_and_supported_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = self.payload("partial")
            payload["gaps"] = ["One archival series stayed inaccessible."]
            result = root / "result.md"
            result.write_text(
                "# Workflow result\n\n"
                "## Full return value\n\n"
                f"```json\n{json.dumps(payload)}\n```\n",
                encoding="utf-8",
            )
            output = root / "partial.md"

            _, status, _ = MATERIALIZER.materialize_report(result, output)

            self.assertEqual(status, "partial")
            written = output.read_text(encoding="utf-8")
            self.assertIn("## Scope and gaps", written)
            self.assertIn("One archival series stayed inaccessible.", written)
            # The gaps note precedes the bibliography.
            self.assertLess(written.index("## Scope and gaps"), written.index("## Sources"))

    def test_complete_report_has_no_gaps_section(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = self.payload("complete")
            payload["gaps"] = ["A minor note."]
            result = root / "result.json"
            result.write_text(json.dumps(payload), encoding="utf-8")
            output = root / "complete.md"

            MATERIALIZER.materialize_report(result, output)

            self.assertNotIn("## Scope and gaps", output.read_text(encoding="utf-8"))

    def test_assembles_report_plan_from_the_body_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            body = root / "body.md"
            body.write_text(
                "# A Long, Unified Report\n\n"
                "The opening cites [Saturn](https://en.wikipedia.org/wiki/Saturn_(mythology)) "
                "and a [dated series](https://example.gov/data?report=2024).\n\n"
                "## First movement\n\n"
                "Body prose with an image ![chart](https://example.test/chart.png) and "
                "`[code](nope)`.\n",
                encoding="utf-8",
            )
            payload = {
                "status": "complete",
                "report_markdown": "",
                "report_plan": {
                    "title": "A Long, Unified Report",
                    "body_path": str(body),
                    "section_paths": [str(root / "01-first.md")],
                    "assembled_word_count": 11_000,
                },
                "cited_sources": [],
                "source_registry": [
                    {
                        "id": "S001",
                        "title": "Saturn (mythology)",
                        "url": "https://en.wikipedia.org/wiki/Saturn_(mythology)",
                        "publisher": "Wikipedia",
                        "date": "",
                        "source_type": "reference",
                    },
                    {
                        "id": "S002",
                        "title": "Report 2024",
                        "url": "https://example.gov/data?report=2024",
                        "publisher": "Example Agency",
                        "date": "2024",
                        "source_type": "official",
                    },
                    {
                        "id": "S003",
                        "title": "Report 2019",
                        "url": "https://example.gov/data?report=2019",
                        "publisher": "Example Agency",
                        "date": "2019",
                        "source_type": "official",
                    },
                ],
                "gaps": [],
            }
            result = root / "result.json"
            result.write_text(json.dumps(payload), encoding="utf-8")
            output = root / "long.md"

            path, status, warnings = MATERIALIZER.materialize_report(result, output)

            written = path.read_text(encoding="utf-8")
            self.assertEqual(status, "complete")
            self.assertEqual(warnings, [])
            self.assertEqual(written.count("\n## Sources\n"), 1)
            # Parenthesised and query-bearing URLs both resolve to their own source.
            self.assertIn("[Saturn (mythology)](https://en.wikipedia.org/wiki/Saturn_", written)
            self.assertIn("https://example.gov/data?report=2024", written)
            # The uncited 2019 series is not smuggled into the bibliography.
            self.assertNotIn("report=2019", written)
            # Images and inline code are not citations.
            self.assertNotIn("chart.png", written.split("## Sources")[1])

    def test_report_plan_requires_a_readable_body_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = {
                "status": "complete",
                "report_markdown": "",
                "report_plan": {"title": "T", "body_path": str(root / "missing.md")},
                "source_registry": [],
                "gaps": [],
            }
            result = root / "result.json"
            result.write_text(json.dumps(payload), encoding="utf-8")
            output = root / "out.md"

            with self.assertRaises(MATERIALIZER.MaterializationError):
                MATERIALIZER.materialize_report(result, output)
            self.assertFalse(output.exists())

    def test_short_report_is_delivered_with_a_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = self.payload()
            payload["run_summary"] = {"target_words": 6_000}
            result = root / "result.json"
            result.write_text(json.dumps(payload), encoding="utf-8")
            output = root / "short.md"

            path, _, warnings = MATERIALIZER.materialize_report(result, output)

            self.assertTrue(path.exists())
            self.assertEqual(len(warnings), 1)
            self.assertIn("requested target of about 6000", warnings[0])

    def test_refuses_collision_and_supports_numbered_or_explicit_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = root / "result.json"
            result.write_text(json.dumps(self.payload()), encoding="utf-8")
            output = root / "report.md"
            output.write_text("existing\n", encoding="utf-8")

            with self.assertRaises(MATERIALIZER.MaterializationError):
                MATERIALIZER.materialize_report(result, output)

            numbered, _, _ = MATERIALIZER.materialize_report(
                result,
                output,
                collision_safe=True,
            )
            self.assertEqual(numbered.name, "report-2.md")
            overwritten, _, _ = MATERIALIZER.materialize_report(
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
                (
                    "bodyless.json",
                    {
                        "status": "complete",
                        "report_markdown": "# Title\n\n## Sources\n\n- [S](https://e.test/s)\n",
                    },
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
