from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.new_skill import create_skill
from scripts.validate_skills import REPOSITORY_ROOT, validate_skill


class NewSkillTests(unittest.TestCase):
    def test_creates_valid_skill_from_template(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skills_root = Path(temporary) / "skills"
            skill = create_skill(
                name="release-notes",
                description="Draft release notes when a user provides completed changes.",
                skills_root=skills_root,
                template_path=REPOSITORY_ROOT / "template" / "SKILL.md",
                resources=["references", "scripts", "references"],
            )

            skill_md = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("name: release-notes", skill_md)
            self.assertIn("# Release Notes", skill_md)
            self.assertTrue((skill / "references").is_dir())
            self.assertTrue((skill / "scripts").is_dir())
            self.assertFalse((skill / "assets").exists())
            self.assertEqual(validate_skill(skill), [])

    def test_does_not_replace_placeholders_inside_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skills_root = Path(temporary) / "skills"
            description = (
                "Use for {{name}}, {{description}}, {{license}}, and {{title}} "
                "notes with quotes and\nUnicode: café."
            )
            skill = create_skill(
                name="placeholder-test",
                description=description,
                skills_root=skills_root,
                template_path=REPOSITORY_ROOT / "template" / "SKILL.md",
            )

            frontmatter = (skill / "SKILL.md").read_text(encoding="utf-8").split("---")[1]
            metadata = yaml.safe_load(frontmatter)
            self.assertEqual(metadata["description"], description)
            self.assertEqual(metadata["license"], "Apache-2.0")

    def test_refuses_invalid_or_existing_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skills_root = Path(temporary) / "skills"
            arguments = {
                "description": "Use this test skill for a concrete task.",
                "skills_root": skills_root,
                "template_path": REPOSITORY_ROOT / "template" / "SKILL.md",
            }
            with self.assertRaises(ValueError):
                create_skill(name="Bad_Name", **arguments)

            create_skill(name="valid-name", **arguments)
            with self.assertRaises(FileExistsError):
                create_skill(name="valid-name", **arguments)

            with self.assertRaises(ValueError):
                create_skill(
                    name="custom-license",
                    license_name="Custom",
                    **arguments,
                )

    def test_bundles_custom_license_with_resources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_license = root / "CUSTOM-LICENSE.txt"
            source_license.write_text("Custom terms\n", encoding="utf-8")

            skill = create_skill(
                name="custom-license",
                description="Use this skill to test custom licensing.",
                license_name="Custom terms in LICENSE",
                license_file=source_license,
                resources=["assets"],
                skills_root=root / "skills",
                template_path=REPOSITORY_ROOT / "template" / "SKILL.md",
            )

            self.assertEqual(
                (skill / "LICENSE").read_text(encoding="utf-8"),
                "Custom terms\n",
            )
            self.assertTrue((skill / "assets").is_dir())
            self.assertEqual(validate_skill(skill), [])


if __name__ == "__main__":
    unittest.main()
