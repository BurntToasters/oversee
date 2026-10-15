import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("bump_ver", ROOT / "bump-ver.py")
bump = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bump)


class VersionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="oversee-version-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "version.txt").write_bytes(b"1.2.3\n")
        (self.root / "SKILL.md").write_bytes(b'---\nmetadata:\n  version: "1.2.3"\n---\n')
        (self.root / "README.md").write_bytes(b"Version: `1.2.3` (preview).\nHarness: v2.0.29\nHistory: 1.2.3\n")

    def contents(self):
        return {p.name: p.read_bytes() for p in self.root.iterdir()}

    def test_repository_declarations_match_canonical_version(self):
        self.assertEqual(bump.update(ROOT), (ROOT / "version.txt").read_text().strip())

    def test_bumps_update_every_declaration_and_preserve_other_versions(self):
        for part, expected in [("patch", "1.2.4"), ("minor", "1.3.0"), ("major", "2.0.0")]:
            with self.subTest(part=part):
                original = self.contents()
                bump.update(self.root, part)
                self.assertEqual(bump.update(self.root), expected)
                self.assertIn(f'  version: "{expected}"'.encode(), (self.root / "SKILL.md").read_bytes())
                readme = (self.root / "README.md").read_text()
                self.assertIn(f"Version: `{expected}`", readme)
                self.assertIn("Harness: v2.0.29\nHistory: 1.2.3", readme)
                for name, content in original.items():
                    (self.root / name).write_bytes(content)

    def test_exact_prerelease_and_build_version(self):
        bump.update(self.root, "2.0.0-rc.1+build.42")
        self.assertEqual(bump.update(self.root), "2.0.0-rc.1+build.42")
        bump.update(self.root, "patch")
        self.assertEqual(bump.update(self.root), "2.0.1")

    def test_invalid_version_cannot_change_files(self):
        before = self.contents()
        for value in ["01.2.3", "v2.0.0", "1.2", "1.2.3-01", "1.2.3+", "1.2.3\n"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                bump.update(self.root, value)
            self.assertEqual(self.contents(), before)

    def test_drift_missing_or_duplicate_declarations_cannot_change_files(self):
        path = self.root / "SKILL.md"
        for content in [b'  version: "9.9.9"\n', b"missing\n", b'  version: "1.2.3"\n' * 2]:
            path.write_bytes(content)
            before = self.contents()
            with self.assertRaises(ValueError):
                bump.update(self.root, "patch")
            self.assertEqual(self.contents(), before)

    def test_check_and_dry_run_do_not_write(self):
        before = self.contents()
        self.assertEqual(bump.update(self.root), "1.2.3")
        self.assertEqual(bump.update(self.root, "minor", dry_run=True), "1.2.3 -> 1.3.0 (dry run)")
        self.assertEqual(self.contents(), before)

    def test_preserves_crlf_and_readme_status(self):
        for path in self.root.iterdir():
            path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        readme = self.root / "README.md"
        readme.write_bytes(readme.read_bytes().replace(b"(preview)", b"(stable)"))
        bump.update(self.root, "patch")
        for path in self.root.iterdir():
            self.assertNotIn(b"\n", path.read_bytes().replace(b"\r\n", b""))
        self.assertIn(b"(stable)", readme.read_bytes())

    def test_write_failure_restores_previous_versions_and_removes_temporary_files(self):
        original, write = self.contents(), bump.atomic_write
        def fail_skill_once(path, content):
            if path.name == "SKILL.md":
                raise OSError("injected replacement failure")
            write(path, content)
        with patch.object(bump, "atomic_write", side_effect=fail_skill_once), self.assertRaises(OSError):
            bump.update(self.root, "minor")
        self.assertEqual(self.contents(), original)

    def test_cli_finds_repository_when_called_from_another_directory(self):
        result = subprocess.run([sys.executable, "-B", str(ROOT / "bump-ver.py"), "--check"],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), (ROOT / "version.txt").read_text().strip())


if __name__ == "__main__":
    unittest.main()
