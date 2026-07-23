#!/usr/bin/env python3
"""Materialize a deep-research workflow result as a validated Markdown report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


class MaterializationError(ValueError):
    """Raised when a workflow result cannot be materialized safely."""


def _decode_json(text: str, source: Path) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise MaterializationError(f"{source}: invalid JSON: {exc}") from exc


def _extract_json_from_markdown(text: str, source: Path) -> Any:
    heading_index = text.find("## Full return value")
    search_from = heading_index if heading_index >= 0 else 0
    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text[search_from:], re.DOTALL)
    if not match:
        raise MaterializationError(f"{source}: could not find a fenced JSON workflow return value")
    return _decode_json(match.group(1), source)


def load_workflow_result(path: Path) -> dict[str, Any]:
    """Load a persisted workflow result from JSON or the readable Markdown artifact."""
    path = Path(path)
    if not path.is_file():
        raise MaterializationError(f"{path}: workflow result does not exist")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        payload = _decode_json(text, path)
    else:
        payload = _extract_json_from_markdown(text, path)

    if isinstance(payload, dict) and isinstance(payload.get("result"), dict):
        payload = payload["result"]
    if not isinstance(payload, dict):
        raise MaterializationError(f"{path}: workflow return value must be an object")
    return payload


def validate_report_payload(payload: dict[str, Any]) -> tuple[str, str]:
    """Return normalized report Markdown and status after structural validation."""
    status = payload.get("status")
    if status not in {"complete", "partial"}:
        raise MaterializationError(
            f"workflow status is {status!r}; only complete or supported partial "
            "reports can be written"
        )

    report = payload.get("report_markdown")
    if not isinstance(report, str) or not report.strip():
        raise MaterializationError("workflow result has no nonempty report_markdown")
    report = report.strip() + "\n"

    if not report.startswith("# "):
        raise MaterializationError("report must begin with a level-one Markdown title")
    if report.count("\n## Sources\n") != 1:
        raise MaterializationError("report must contain exactly one `## Sources` section")

    body, sources = report.split("\n## Sources\n", 1)
    if not body.strip() or len(body.splitlines()) < 2:
        raise MaterializationError("report body is empty")
    source_lines = [line for line in sources.splitlines() if line.strip().startswith(("- ", "* "))]
    if not source_lines:
        raise MaterializationError("Sources section contains no source entries")
    return report, status


def collision_safe_path(path: Path) -> Path:
    """Return path or the first available numbered sibling."""
    path = Path(path)
    if not path.exists():
        return path
    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def materialize_report(
    result_path: Path,
    output_path: Path,
    *,
    overwrite: bool = False,
    collision_safe: bool = False,
) -> tuple[Path, str]:
    """Validate a workflow result and write its report, returning path and status."""
    if overwrite and collision_safe:
        raise MaterializationError("choose either overwrite or collision-safe output, not both")

    payload = load_workflow_result(result_path)
    report, status = validate_report_payload(payload)
    destination = Path(output_path)
    if destination.exists():
        if overwrite:
            pass
        elif collision_safe:
            destination = collision_safe_path(destination)
        else:
            raise MaterializationError(
                f"{destination}: output exists; use --overwrite or --collision-safe"
            )

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report, encoding="utf-8")
    if destination.stat().st_size == 0:
        raise MaterializationError(f"{destination}: report write produced an empty file")
    return destination, status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_path", type=Path, help="workflow result.md or result.json")
    parser.add_argument("output_path", type=Path, help="destination Markdown report")
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument(
        "--overwrite",
        action="store_true",
        help="replace an existing output file (only with explicit user approval)",
    )
    destination.add_argument(
        "--collision-safe",
        action="store_true",
        help="choose a numbered filename when the destination exists",
    )
    args = parser.parse_args(argv)

    try:
        path, status = materialize_report(
            args.result_path,
            args.output_path,
            overwrite=args.overwrite,
            collision_safe=args.collision_safe,
        )
    except (OSError, MaterializationError) as exc:
        print(f"Materialization failed: {exc}", file=sys.stderr)
        return 1

    print(f"Materialized {status} report: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
