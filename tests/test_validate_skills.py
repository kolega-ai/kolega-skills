from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.validate_skills import validate_repository, validate_skill


def write_skill(root: Path, name: str = "test-skill", body: str = "# Test\n") -> Path:
    skill = root / "skills" / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                f"name: {name}",
                "description: Use this skill to test repository validation.",
                "license: Apache-2.0",
                "metadata:",
                "  owner: Kolega",
                "---",
                "",
                body,
            ]
        ),
        encoding="utf-8",
    )
    return skill


class ValidateSkillTests(unittest.TestCase):
    def test_accepts_valid_skill_and_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = write_skill(root)

            self.assertEqual(validate_skill(skill), [])
            self.assertEqual(validate_repository(root), [])

    def test_rejects_name_that_does_not_match_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = write_skill(root)
            skill_md = skill / "SKILL.md"
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8").replace(
                    "name: test-skill", "name: another-skill"
                ),
                encoding="utf-8",
            )

            messages = [issue.message for issue in validate_skill(skill)]
            self.assertTrue(any("must match parent directory" in message for message in messages))

    def test_rejects_duplicate_frontmatter_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = write_skill(root)
            skill_md = skill / "SKILL.md"
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8").replace(
                    "description:",
                    "name: duplicate\ndescription:",
                    1,
                ),
                encoding="utf-8",
            )

            messages = [issue.message for issue in validate_skill(skill)]
            self.assertTrue(any("duplicate key" in message for message in messages))

    def test_rejects_missing_and_escaping_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = write_skill(
                root,
                body=("# Test\n\n[Missing](references/missing.md)\n[Escape](../outside.md)\n"),
            )

            messages = [issue.message for issue in validate_skill(skill)]
            self.assertTrue(any("does not exist" in message for message in messages))
            self.assertTrue(any("escapes the skill directory" in message for message in messages))

    def test_rejects_case_mismatched_link(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = write_skill(
                root,
                body="# Test\n\n[Reference](references/guide.md)\n",
            )
            references = skill / "references"
            references.mkdir()
            (references / "Guide.md").write_text("# Guide\n", encoding="utf-8")

            messages = [issue.message for issue in validate_skill(skill)]
            self.assertTrue(
                any(
                    "does not exist" in message or "casing does not match" in message
                    for message in messages
                )
            )

    def test_resolves_reference_links_and_ignores_code_examples(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = write_skill(
                root,
                body=(
                    "# Test\n\n"
                    "```markdown\n"
                    "[Example only](missing-example.md)\n"
                    "```\n\n"
                    "[Real reference][guide]\n\n"
                    "[guide]: references/guide(1).md\n"
                ),
            )
            references = skill / "references"
            references.mkdir()
            (references / "guide(1).md").write_text("# Guide\n", encoding="utf-8")

            self.assertEqual(validate_skill(skill), [])

    def test_rejects_transient_and_sensitive_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = write_skill(root)
            (skill / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
            (skill / ".env.production").write_text("TOKEN=secret\n", encoding="utf-8")
            cache = skill / "__pycache__"
            cache.mkdir()
            (cache / "helper.pyc").write_bytes(b"cache")
            git_directory = skill / ".git"
            git_directory.mkdir()
            (git_directory / "config").write_text("[core]\n", encoding="utf-8")

            messages = [issue.message for issue in validate_skill(skill)]
            self.assertEqual(
                sum("credential file" in message for message in messages),
                2,
            )
            self.assertGreaterEqual(
                sum("transient or generated" in message for message in messages),
                2,
            )

    def test_rejects_unsafe_uri_scheme(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = write_skill(
                root,
                body="# Test\n\n[Unsupported](ftp://example.com/archive)\n",
            )

            messages = [issue.message for issue in validate_skill(skill)]
            self.assertTrue(any("unsupported URI scheme" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
