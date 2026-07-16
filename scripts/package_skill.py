#!/usr/bin/env python3
"""Build validated, reproducible .skill archives."""

from __future__ import annotations

import argparse
import hashlib
import stat
import sys
import zipfile
from pathlib import Path

try:
    from scripts.validate_skills import (
        REPOSITORY_ROOT,
        ValidationIssue,
        discover_skills,
        validate_skill,
    )
except ModuleNotFoundError:
    from validate_skills import (  # type: ignore[no-redef]
        REPOSITORY_ROOT,
        ValidationIssue,
        discover_skills,
        validate_skill,
    )


ARCHIVE_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class PackageError(Exception):
    """Raised when a skill cannot be packaged safely."""


def _format_issues(issues: list[ValidationIssue]) -> str:
    return "\n".join(f"- {issue.display()}" for issue in issues)


def _archive_info(archive_path: str, executable: bool) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(archive_path, date_time=ARCHIVE_TIMESTAMP)
    info.create_system = 3
    mode = 0o755 if executable else 0o644
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_skill(
    skill_dir: Path,
    output_dir: Path,
    repository_root: Path | None = None,
) -> tuple[Path, Path]:
    """Validate and package one skill, returning archive and checksum paths."""
    skill_dir = Path(skill_dir).resolve()
    output_dir = Path(output_dir).resolve()
    if output_dir == skill_dir or output_dir.is_relative_to(skill_dir):
        raise PackageError("output directory must be outside the source skill")

    if repository_root is None:
        if skill_dir.parent.name != "skills":
            raise PackageError(
                "repository root is required when the skill is not inside a `skills/` directory"
            )
        repository_root = skill_dir.parent.parent
    repository_root = Path(repository_root).resolve()

    issues = validate_skill(skill_dir)
    if issues:
        raise PackageError(f"{skill_dir.name} failed validation:\n{_format_issues(issues)}")

    files = sorted(path for path in skill_dir.rglob("*") if path.is_file())
    if not files:
        raise PackageError(f"{skill_dir} contains no files")

    archive_sources = [
        ((Path(skill_dir.name) / source.relative_to(skill_dir)).as_posix(), source)
        for source in files
    ]
    if not any(
        source.parent == skill_dir and source.name.lower().startswith("license") for source in files
    ):
        root_license = repository_root / "LICENSE"
        if not root_license.is_file():
            raise PackageError(
                "skill has no bundled license and repository LICENSE could not be found"
            )
        archive_sources.append(((Path(skill_dir.name) / "LICENSE").as_posix(), root_license))

    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"{skill_dir.name}.skill"
    temporary_path = output_dir / f".{skill_dir.name}.skill.tmp"

    try:
        with zipfile.ZipFile(
            temporary_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for archive_name, source in sorted(archive_sources):
                executable = bool(source.stat().st_mode & 0o111)
                archive.writestr(
                    _archive_info(archive_name, executable),
                    source.read_bytes(),
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )
        temporary_path.replace(archive_path)
    finally:
        temporary_path.unlink(missing_ok=True)

    checksum_path = archive_path.with_suffix(f"{archive_path.suffix}.sha256")
    checksum_path.write_text(
        f"{_sha256(archive_path)}  {archive_path.name}\n",
        encoding="utf-8",
    )
    return archive_path, checksum_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", nargs="?", type=Path, help="skill directory to package")
    parser.add_argument(
        "--all",
        action="store_true",
        help="discover and package every skill in the repository",
    )
    parser.add_argument(
        "--repository",
        type=Path,
        default=REPOSITORY_ROOT,
        help="repository root used with --all",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPOSITORY_ROOT / "dist",
        help="package output directory (default: dist/)",
    )
    args = parser.parse_args(argv)

    if args.all == (args.skill is not None):
        parser.error("provide exactly one skill directory or use --all")

    if args.all:
        skills, discovery_issues = discover_skills(args.repository)
        if discovery_issues:
            print("Could not discover skills:", file=sys.stderr)
            print(_format_issues(discovery_issues), file=sys.stderr)
            return 1
    else:
        skills = [args.skill]

    try:
        for skill in skills:
            repository_root = args.repository if args.all else None
            archive, checksum = package_skill(skill, args.output, repository_root)
            print(f"Packaged {skill.name}: {archive} ({checksum.name})")
    except (OSError, PackageError) as exc:
        print(f"Packaging failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
