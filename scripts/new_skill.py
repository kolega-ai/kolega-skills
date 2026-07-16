#!/usr/bin/env python3
"""Create a new Agent Skill from the repository template."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

try:
    from scripts.validate_skills import REPOSITORY_ROOT, validate_skill, validate_skill_name
except ModuleNotFoundError:
    from validate_skills import (  # type: ignore[no-redef]
        REPOSITORY_ROOT,
        validate_skill,
        validate_skill_name,
    )


RESOURCE_DIRECTORIES = ("scripts", "references", "assets")
REQUIRED_PLACEHOLDERS = ("{{name}}", "{{description}}", "{{license}}", "{{title}}")
PLACEHOLDER_PATTERN = re.compile(
    "|".join(re.escape(placeholder) for placeholder in REQUIRED_PLACEHOLDERS)
)


def _yaml_string(value: str) -> str:
    """Serialize a string using JSON syntax, which is valid YAML."""
    return json.dumps(value, ensure_ascii=False)


def create_skill(
    name: str,
    description: str,
    skills_root: Path,
    template_path: Path,
    resources: list[str] | tuple[str, ...] = (),
    license_name: str = "Apache-2.0",
    license_file: Path | None = None,
) -> Path:
    """Create and return a new skill directory."""
    name_error = validate_skill_name(name)
    if name_error:
        raise ValueError(f"invalid skill name: {name_error}")
    if not description.strip():
        raise ValueError("description must not be empty")
    if len(description) > 1024:
        raise ValueError("description must be at most 1024 characters")
    if not license_name.strip():
        raise ValueError("license must not be empty")
    if license_name.strip() != "Apache-2.0" and license_file is None:
        raise ValueError("non-Apache skills must provide a license file")
    if license_file is not None and not Path(license_file).is_file():
        raise ValueError(f"license file does not exist: {license_file}")

    invalid_resources = sorted(set(resources) - set(RESOURCE_DIRECTORIES))
    if invalid_resources:
        raise ValueError(f"unsupported resource directories: {', '.join(invalid_resources)}")

    skills_root = Path(skills_root)
    template_path = Path(template_path)
    target = skills_root / name
    if target.exists():
        raise FileExistsError(f"skill already exists: {target}")

    template = template_path.read_text(encoding="utf-8")
    missing = [placeholder for placeholder in REQUIRED_PLACEHOLDERS if placeholder not in template]
    if missing:
        raise ValueError(f"template is missing placeholder(s): {', '.join(missing)}")

    replacements = {
        "{{name}}": name,
        "{{description}}": _yaml_string(description.strip()),
        "{{license}}": _yaml_string(license_name.strip()),
        "{{title}}": name.replace("-", " ").title(),
    }
    rendered = PLACEHOLDER_PATTERN.sub(
        lambda match: replacements[match.group(0)],
        template,
    )

    skills_root.mkdir(parents=True, exist_ok=True)
    target.mkdir()
    try:
        (target / "SKILL.md").write_text(rendered, encoding="utf-8")
        if license_file is not None:
            shutil.copyfile(license_file, target / "LICENSE")
        for resource in dict.fromkeys(resources):
            (target / resource).mkdir()
        issues = validate_skill(target)
        if issues:
            details = "; ".join(issue.message for issue in issues)
            raise ValueError(f"generated skill did not validate: {details}")
    except Exception:
        shutil.rmtree(target)
        raise

    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="lowercase kebab-case skill name")
    parser.add_argument(
        "--description",
        required=True,
        help="what the skill does and when an agent should use it",
    )
    parser.add_argument(
        "--skills-root",
        type=Path,
        default=REPOSITORY_ROOT / "skills",
        help="directory that contains skills (default: skills/)",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=REPOSITORY_ROOT / "template" / "SKILL.md",
        help="SKILL.md template path",
    )
    parser.add_argument(
        "--resource",
        action="append",
        choices=RESOURCE_DIRECTORIES,
        default=[],
        help="optional resource directory to create; repeat as needed",
    )
    parser.add_argument(
        "--license",
        dest="license_name",
        default="Apache-2.0",
        help="license frontmatter value (default: Apache-2.0)",
    )
    parser.add_argument(
        "--license-file",
        type=Path,
        help="terms to bundle as LICENSE (required for non-Apache licenses)",
    )
    args = parser.parse_args(argv)

    try:
        target = create_skill(
            name=args.name,
            description=args.description,
            skills_root=args.skills_root,
            template_path=args.template,
            resources=args.resource,
            license_name=args.license_name,
            license_file=args.license_file,
        )
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Could not create skill: {exc}\n")

    print(f"Created {target}")
    print("Next: replace the template body, add only necessary resources, and validate it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
