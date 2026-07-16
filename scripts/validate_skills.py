#!/usr/bin/env python3
"""Validate Agent Skills in this repository."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

import yaml
from markdown_it import MarkdownIt
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TRANSIENT_NAMES = {
    ".ds_store",
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "thumbs.db",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}
SENSITIVE_NAMES = {
    ".env",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    "id_dsa",
    "id_ed25519",
    "id_rsa",
}
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: UniqueKeyLoader, node: MappingNode, deep: bool = False
) -> dict[Any, Any]:
    if not isinstance(node, MappingNode):
        raise ConstructorError(
            None,
            None,
            f"expected a mapping node, found {node.id}",
            node.start_mark,
        )

    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@dataclass(frozen=True)
class ValidationIssue:
    path: Path
    message: str
    line: int | None = None

    def display(self, root: Path | None = None) -> str:
        try:
            path = self.path.relative_to(root) if root else self.path
        except ValueError:
            path = self.path
        location = f"{path}:{self.line}" if self.line else str(path)
        return f"{location}: {self.message}"


def sort_issues(issues: Iterable[ValidationIssue]) -> list[ValidationIssue]:
    return sorted(
        set(issues),
        key=lambda issue: (str(issue.path), issue.line or 0, issue.message),
    )


def validate_skill_name(name: str) -> str | None:
    """Return an error for an invalid spec name, otherwise None."""
    if not name:
        return "must not be empty"
    if len(name) > 64:
        return "must be at most 64 characters"
    if not NAME_PATTERN.fullmatch(name):
        return (
            "must contain only lowercase ASCII letters, digits, and single hyphens; "
            "it cannot start or end with a hyphen"
        )
    return None


def _read_frontmatter(path: Path) -> tuple[dict[str, Any] | None, str, list[ValidationIssue]]:
    issues: list[ValidationIssue] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return None, "", [ValidationIssue(path, f"must be UTF-8 ({exc})")]
    except OSError as exc:
        return None, "", [ValidationIssue(path, f"could not be read ({exc})")]

    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return (
            None,
            text,
            [ValidationIssue(path, "must begin with a YAML frontmatter delimiter (`---`)", 1)],
        )

    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.rstrip("\r\n") == "---"),
        None,
    )
    if closing_index is None:
        return (
            None,
            text,
            [ValidationIssue(path, "frontmatter is missing its closing `---` delimiter", 1)],
        )

    frontmatter_text = "".join(lines[1:closing_index])
    body = "".join(lines[closing_index + 1 :])
    try:
        data = yaml.load(frontmatter_text, Loader=UniqueKeyLoader)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        line = mark.line + 2 if mark else 1
        return None, body, [ValidationIssue(path, f"invalid YAML frontmatter ({exc})", line)]

    if not isinstance(data, dict):
        issues.append(ValidationIssue(path, "frontmatter must be a YAML mapping", 1))
        return None, body, issues

    return data, body, issues


def _validate_frontmatter(
    skill_dir: Path, data: dict[str, Any], body: str, path: Path
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    non_string_keys = [key for key in data if not isinstance(key, str)]
    if non_string_keys:
        issues.append(
            ValidationIssue(path, f"frontmatter keys must be strings: {non_string_keys!r}", 1)
        )

    unknown = sorted(key for key in data if isinstance(key, str) and key not in ALLOWED_FIELDS)
    if unknown:
        issues.append(
            ValidationIssue(path, f"unsupported frontmatter field(s): {', '.join(unknown)}", 1)
        )

    name = data.get("name")
    if not isinstance(name, str):
        issues.append(ValidationIssue(path, "`name` is required and must be a string", 1))
    else:
        name_error = validate_skill_name(name)
        if name_error:
            issues.append(ValidationIssue(path, f"`name` {name_error}", 1))
        if name != skill_dir.name:
            issues.append(
                ValidationIssue(
                    path,
                    f"`name` must match parent directory {skill_dir.name!r}",
                    1,
                )
            )

    description = data.get("description")
    if not isinstance(description, str):
        issues.append(ValidationIssue(path, "`description` is required and must be a string", 1))
    elif not description.strip():
        issues.append(ValidationIssue(path, "`description` must not be empty", 1))
    elif len(description) > 1024:
        issues.append(ValidationIssue(path, "`description` must be at most 1024 characters", 1))

    for field in ("license", "allowed-tools"):
        value = data.get(field)
        if field in data and (not isinstance(value, str) or not value.strip()):
            issues.append(ValidationIssue(path, f"`{field}` must be a non-empty string", 1))

    license_name = data.get("license")
    if (
        isinstance(license_name, str)
        and license_name.strip() != "Apache-2.0"
        and not any(
            child.is_file() and child.name.lower().startswith("license")
            for child in skill_dir.iterdir()
        )
    ):
        issues.append(
            ValidationIssue(
                path,
                "non-Apache license terms must be bundled in a top-level LICENSE file",
                1,
            )
        )

    compatibility = data.get("compatibility")
    if "compatibility" in data:
        if not isinstance(compatibility, str) or not compatibility.strip():
            issues.append(ValidationIssue(path, "`compatibility` must be a non-empty string", 1))
        elif len(compatibility) > 500:
            issues.append(
                ValidationIssue(path, "`compatibility` must be at most 500 characters", 1)
            )

    metadata = data.get("metadata")
    if "metadata" in data:
        if not isinstance(metadata, dict):
            issues.append(ValidationIssue(path, "`metadata` must be a mapping", 1))
        else:
            for key, value in metadata.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    issues.append(
                        ValidationIssue(
                            path,
                            "`metadata` keys and values must all be strings",
                            1,
                        )
                    )
                    break

    if not body.strip():
        issues.append(ValidationIssue(path, "Markdown instruction body must not be empty"))

    return issues


def _has_exact_case(root: Path, path: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False

    current = root
    for part in relative.parts:
        try:
            names = {child.name for child in current.iterdir()}
        except OSError:
            return False
        if part not in names:
            return False
        current /= part
    return True


def _validate_link_target(
    skill_dir: Path,
    markdown_path: Path,
    raw_target: str,
    line: int | None,
) -> list[ValidationIssue]:
    if not raw_target or raw_target.startswith("#"):
        return []

    parsed = urlsplit(raw_target)
    if parsed.scheme:
        if parsed.scheme.lower() not in {"http", "https", "mailto"}:
            return [
                ValidationIssue(
                    markdown_path,
                    f"link uses an unsupported URI scheme: {raw_target!r}",
                    line,
                )
            ]
        return []
    if parsed.netloc:
        return []

    target_text = unquote(parsed.path)
    if not target_text:
        return []
    if "\\" in target_text:
        return [
            ValidationIssue(
                markdown_path,
                f"local link must use forward slashes: {raw_target!r}",
                line,
            )
        ]
    if target_text.startswith("/"):
        return [
            ValidationIssue(
                markdown_path,
                f"local link must be relative to the skill root: {raw_target!r}",
                line,
            )
        ]

    root = skill_dir.resolve()
    candidate = (skill_dir / target_text).resolve()
    if not candidate.is_relative_to(root):
        return [
            ValidationIssue(
                markdown_path,
                f"local link escapes the skill directory: {raw_target!r}",
                line,
            )
        ]
    if not candidate.exists():
        return [
            ValidationIssue(
                markdown_path,
                f"local link does not exist: {raw_target!r}",
                line,
            )
        ]
    if not _has_exact_case(root, candidate):
        return [
            ValidationIssue(
                markdown_path,
                f"local link casing does not match the filesystem: {raw_target!r}",
                line,
            )
        ]
    return []


def _validate_markdown_links(skill_dir: Path, max_file_size: int) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    parser = MarkdownIt("commonmark")

    for markdown_path in sorted(skill_dir.rglob("*.md")):
        if markdown_path.is_symlink():
            continue
        try:
            if markdown_path.stat().st_size > max_file_size:
                continue
            text = markdown_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        for token in parser.parse(text):
            if token.type != "inline":
                continue
            line = token.map[0] + 1 if token.map else None
            for child in token.children or []:
                if child.type == "link_open":
                    raw_target = child.attrGet("href") or ""
                elif child.type == "image":
                    raw_target = child.attrGet("src") or ""
                else:
                    continue
                issues.extend(
                    _validate_link_target(
                        skill_dir,
                        markdown_path,
                        raw_target,
                        line,
                    )
                )

    return issues


def _validate_files(skill_dir: Path, max_file_size: int) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for path in sorted(skill_dir.rglob("*")):
        relative = path.relative_to(skill_dir)
        if path.is_symlink():
            issues.append(ValidationIssue(path, "symbolic links are not allowed in skills"))
            continue
        if any(part.lower() in TRANSIENT_NAMES for part in relative.parts):
            issues.append(
                ValidationIssue(path, "transient or generated files are not allowed in skills")
            )
            continue
        lowercase_name = path.name.lower()
        if lowercase_name in SENSITIVE_NAMES or lowercase_name.startswith(".env."):
            issues.append(
                ValidationIssue(path, "potential credential file is not allowed in a skill")
            )
        if lowercase_name.endswith(".skill") or lowercase_name.endswith(".skill.sha256"):
            issues.append(ValidationIssue(path, "generated skill packages must not be bundled"))
        if path.is_dir():
            continue
        if not path.is_file():
            issues.append(
                ValidationIssue(
                    path,
                    "only regular files and directories are allowed in skills",
                )
            )
            continue
        try:
            size = path.stat().st_size
        except OSError as exc:
            issues.append(ValidationIssue(path, f"could not inspect file ({exc})"))
            continue
        if size > max_file_size:
            issues.append(
                ValidationIssue(
                    path,
                    f"file is {size} bytes; maximum is {max_file_size} bytes",
                )
            )
    return issues


def validate_skill(
    skill_dir: Path, max_file_size: int = DEFAULT_MAX_FILE_SIZE
) -> list[ValidationIssue]:
    """Validate one skill directory."""
    skill_dir = Path(skill_dir)
    issues: list[ValidationIssue] = []

    if not skill_dir.exists():
        return [ValidationIssue(skill_dir, "skill directory does not exist")]
    if not skill_dir.is_dir():
        return [ValidationIssue(skill_dir, "skill path must be a directory")]
    if skill_dir.is_symlink():
        return [ValidationIssue(skill_dir, "skill directory cannot be a symbolic link")]

    issues.extend(_validate_files(skill_dir, max_file_size))

    name_error = validate_skill_name(skill_dir.name)
    if name_error:
        issues.append(ValidationIssue(skill_dir, f"directory name {name_error}"))

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        issues.append(ValidationIssue(skill_md, "required file is missing"))
    elif skill_md.is_symlink():
        issues.append(ValidationIssue(skill_md, "SKILL.md cannot be a symbolic link"))
    elif skill_md.stat().st_size <= max_file_size:
        data, body, frontmatter_issues = _read_frontmatter(skill_md)
        issues.extend(frontmatter_issues)
        if data is not None:
            issues.extend(_validate_frontmatter(skill_dir, data, body, skill_md))

    issues.extend(_validate_markdown_links(skill_dir, max_file_size))
    return sort_issues(issues)


def discover_skills(repository_root: Path) -> tuple[list[Path], list[ValidationIssue]]:
    """Discover immediate child directories under the repository's skills directory."""
    skills_root = Path(repository_root) / "skills"
    if not skills_root.is_dir():
        return [], [ValidationIssue(skills_root, "skills directory does not exist")]

    skills: list[Path] = []
    issues: list[ValidationIssue] = []
    for entry in sorted(skills_root.iterdir()):
        if entry.is_symlink():
            issues.append(ValidationIssue(entry, "skill entries cannot be symbolic links"))
        elif entry.is_dir():
            skills.append(entry)
        else:
            issues.append(
                ValidationIssue(
                    entry,
                    "only skill directories are allowed directly under `skills/`",
                )
            )
    if not skills:
        issues.append(ValidationIssue(skills_root, "must contain at least one skill"))
    return skills, issues


def validate_repository(
    repository_root: Path = REPOSITORY_ROOT,
    max_file_size: int = DEFAULT_MAX_FILE_SIZE,
) -> list[ValidationIssue]:
    """Discover and validate all skills in a repository."""
    skills, issues = discover_skills(Path(repository_root))
    for skill in skills:
        issues.extend(validate_skill(skill, max_file_size=max_file_size))
    return sort_issues(issues)


def _print_result(
    skills: Iterable[Path],
    issues: list[ValidationIssue],
    display_root: Path,
) -> int:
    if issues:
        print(f"Validation failed with {len(issues)} issue(s):", file=sys.stderr)
        for issue in issues:
            print(f"- {issue.display(display_root)}", file=sys.stderr)
        return 1

    skill_count = len(list(skills))
    noun = "skill" if skill_count == 1 else "skills"
    print(f"Validated {skill_count} {noun}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skill",
        nargs="*",
        type=Path,
        help="specific skill directories to validate (default: discover all skills)",
    )
    parser.add_argument(
        "--repository",
        type=Path,
        default=REPOSITORY_ROOT,
        help="repository root used for discovery and display paths",
    )
    parser.add_argument(
        "--max-file-size-mb",
        type=int,
        default=DEFAULT_MAX_FILE_SIZE // (1024 * 1024),
        help="maximum size of any bundled file (default: 10)",
    )
    args = parser.parse_args(argv)

    if args.max_file_size_mb < 1:
        parser.error("--max-file-size-mb must be at least 1")
    max_file_size = args.max_file_size_mb * 1024 * 1024
    repository = args.repository.resolve()

    if args.skill:
        skills = [path.resolve() for path in args.skill]
        issues = [
            issue
            for skill in skills
            for issue in validate_skill(skill, max_file_size=max_file_size)
        ]
    else:
        skills, discovery_issues = discover_skills(repository)
        issues = list(discovery_issues)
        for skill in skills:
            issues.extend(validate_skill(skill, max_file_size=max_file_size))

    return _print_result(skills, sort_issues(issues), repository)


if __name__ == "__main__":
    raise SystemExit(main())
