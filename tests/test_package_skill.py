from __future__ import annotations

import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.package_skill import ARCHIVE_TIMESTAMP, PackageError, package_skill
from tests.test_validate_skills import write_skill


class PackageSkillTests(unittest.TestCase):
    def test_builds_reproducible_archive_and_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "LICENSE").write_text("Test repository license\n", encoding="utf-8")
            skill = write_skill(root)
            references = skill / "references"
            references.mkdir()
            (references / "guide.md").write_text("# Guide\n", encoding="utf-8")
            output = root / "dist"

            archive, checksum = package_skill(skill, output)
            first_bytes = archive.read_bytes()
            archive, checksum = package_skill(skill, output)

            self.assertEqual(archive.read_bytes(), first_bytes)
            expected_hash = hashlib.sha256(first_bytes).hexdigest()
            self.assertEqual(
                checksum.read_text(encoding="utf-8"),
                f"{expected_hash}  test-skill.skill\n",
            )

            with zipfile.ZipFile(archive) as packaged:
                self.assertEqual(
                    packaged.namelist(),
                    [
                        "test-skill/LICENSE",
                        "test-skill/SKILL.md",
                        "test-skill/references/guide.md",
                    ],
                )
                self.assertTrue(
                    all(info.date_time == ARCHIVE_TIMESTAMP for info in packaged.infolist())
                )
                self.assertEqual(
                    packaged.read("test-skill/LICENSE"),
                    b"Test repository license\n",
                )

    def test_refuses_invalid_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "LICENSE").write_text("Test repository license\n", encoding="utf-8")
            skill = write_skill(root)
            (skill / "SKILL.md").unlink()

            with self.assertRaises(PackageError):
                package_skill(skill, root / "dist")

    def test_refuses_output_inside_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "LICENSE").write_text("Test repository license\n", encoding="utf-8")
            skill = write_skill(root)

            with self.assertRaises(PackageError):
                package_skill(skill, skill / "dist")

    def test_prefers_bundled_custom_license(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "LICENSE").write_text("Repository terms\n", encoding="utf-8")
            skill = write_skill(root)
            skill_md = skill / "SKILL.md"
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8").replace(
                    "license: Apache-2.0",
                    "license: Custom terms in LICENSE",
                ),
                encoding="utf-8",
            )
            (skill / "LICENSE").write_text("Custom skill terms\n", encoding="utf-8")

            archive, _ = package_skill(skill, root / "dist")
            with zipfile.ZipFile(archive) as packaged:
                self.assertEqual(
                    packaged.read("test-skill/LICENSE"),
                    b"Custom skill terms\n",
                )


if __name__ == "__main__":
    unittest.main()
