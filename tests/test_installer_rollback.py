import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_installers as ti  # noqa: E402

CLAUDE = 1  # index of the second target; faults fire only here
WINDOWS_POINTS = {
    "publish-skill": rb'move "%STAGE%\SKILL.md" "%DEST%\SKILL.md" >nul',
    "publish-references": rb'move "%STAGE%\references" "%DEST%\references" >nul',
    "restore-skill": rb'move "%STAGE%\old-skill" "%DEST%\SKILL.md" >nul',
    "restore-references": rb'move "%STAGE%\old-references" "%DEST%\references" >nul',
}
BASH_SUFFIXES = {
    "publish-skill": "/SKILL.md",
    "publish-references": "/references",
    "restore-skill": "/old-skill",
    "restore-references": "/old-references",
}


def tree(path):
    return {p.relative_to(path).as_posix(): p.read_bytes() for p in path.rglob("*") if p.is_file()}


def holds(path, data):
    return path.is_file() and path.read_bytes() == data


class RollbackFaults(unittest.TestCase):
    run_script = ti.Installers.run_script

    def setUp(self):
        ti.Installers.setUp(self)
        for target in self.targets:
            (target / "references").mkdir(parents=True)
            (target / "SKILL.md").write_text("old skill")
            (target / "references" / "old.md").write_text("old refs")
            (target / "keep.txt").write_text("user file")
        self.neighbor = self.profile / ".agents/skills/other/keep.txt"
        self.neighbor.parent.mkdir(parents=True)
        self.neighbor.write_text("keep")

    def new_tree(self):
        expected = {"SKILL.md": (self.source / "SKILL.md").read_bytes(), "keep.txt": b"user file"}
        for rel, data in tree(self.source / "references").items():
            expected["references/" + rel] = data
        return expected

    def stage_leftovers(self):
        return sorted(p for t in self.targets for p in t.parent.glob("*stage*"))

    def inject(self, platform, points):
        if platform == "windows":
            path = self.source / "install.bat"
            data = path.read_bytes()
            for point in points:
                original = WINDOWS_POINTS[point]
                self.assertEqual(data.count(original), 1, point)
                wrapped = b'if /i "%DEST%"=="%AUDIT_FAIL_DEST%" (call :fail_move) else (' + original + b")"
                data = data.replace(original, wrapped)
            self.assertIn(b"\r\n:recovery\r\n", data)
            data = data.replace(b"\r\n:recovery\r\n", b"\r\n:fail_move\r\nexit /b 1\r\n\r\n:recovery\r\n", 1)
            path.write_bytes(data)
            self.env["AUDIT_FAIL_DEST"] = str(self.targets[CLAUDE])
        else:
            shim = self.root / "bash-env-faults.sh"
            suffixes = [BASH_SUFFIXES[p] for p in points]
            shim.write_text(
                'mv() { if [[ "$2" == */.claude/skills/oversee/* && ( "$1" == *"$AUDIT_FAIL_SRC" '
                '|| ( -n "$AUDIT_FAIL_SRC2" && "$1" == *"$AUDIT_FAIL_SRC2" ) ) ]]; then return 1; fi; '
                'command mv "$@"; }\n', encoding="utf-8")
            self.env.update(BASH_ENV=shim.as_posix(), AUDIT_FAIL_SRC=suffixes[0],
                            AUDIT_FAIL_SRC2=suffixes[1] if len(suffixes) > 1 else "")

    def run_fault(self, platform, points):
        self.inject(platform, points)
        result = self.run_script(platform, "install")
        return result, result.stdout + result.stderr

    def publish_fault(self, platform, point):
        before = {t: tree(t) for t in self.targets}
        result, output = self.run_fault(platform, [point])
        self.assertNotEqual(result.returncode, 0, output)
        self.assertEqual(tree(self.targets[0]), self.new_tree(), output)
        self.assertEqual(tree(self.targets[CLAUDE]), before[self.targets[CLAUDE]], output)
        for target in self.targets[2:]:
            self.assertEqual(tree(target), before[target], output)
        self.assertEqual(self.stage_leftovers(), [], output)
        self.assertEqual(self.neighbor.read_text(), "keep")

    def recovery_fault(self, platform, points):
        before = {t: tree(t) for t in self.targets}
        result, output = self.run_fault(platform, points)
        self.assertNotEqual(result.returncode, 0, output)
        target = self.targets[CLAUDE]
        backups = list(target.parent.glob("*stage*"))
        self.assertEqual(len(backups), 1, output)
        backup = backups[0]
        retained = [line for line in output.splitlines() if "recovery files retained at" in line]
        self.assertEqual(len(retained), 1, output)
        reported = retained[0].split("recovery files retained at", 1)[1].strip().strip('"')
        self.assertTrue(reported.endswith("/.claude/skills/" + backup.name)
                        or reported.endswith("\\.claude\\skills\\" + backup.name), output)
        self.assertEqual(self.stage_leftovers(), backups, output)
        # Every old item is either back in place or still retained in the backup.
        self.assertTrue(holds(target / "SKILL.md", b"old skill") or holds(backup / "old-skill", b"old skill"), output)
        self.assertTrue(holds(target / "references/old.md", b"old refs")
                        or holds(backup / "old-references/old.md", b"old refs"), output)
        self.assertEqual((target / "keep.txt").read_text(), "user file")
        self.assertEqual(tree(self.targets[0]), self.new_tree(), output)
        for other in self.targets[2:]:
            self.assertEqual(tree(other), before[other], output)
        self.assertEqual(self.neighbor.read_text(), "keep")

    @unittest.skipUnless(os.name == "nt", "install.bat requires Windows cmd.exe")
    def test_windows_publish_skill_fault_restores_target(self):
        self.publish_fault("windows", "publish-skill")

    @unittest.skipUnless(os.name == "nt", "install.bat requires Windows cmd.exe")
    def test_windows_publish_references_fault_restores_target(self):
        self.publish_fault("windows", "publish-references")

    @unittest.skipUnless(os.name == "nt", "install.bat requires Windows cmd.exe")
    def test_windows_recovery_restore_references_fault_retains_backup(self):
        self.recovery_fault("windows", ["publish-references", "restore-references"])

    @unittest.skipUnless(os.name == "nt", "install.bat requires Windows cmd.exe")
    def test_windows_recovery_restore_skill_fault_retains_backup(self):
        self.recovery_fault("windows", ["publish-references", "restore-skill"])

    @unittest.skipUnless(ti.BASH, "Bash not available")
    def test_bash_publish_skill_fault_restores_target(self):
        self.publish_fault("bash", "publish-skill")

    @unittest.skipUnless(ti.BASH, "Bash not available")
    def test_bash_publish_references_fault_restores_target(self):
        self.publish_fault("bash", "publish-references")

    @unittest.skipUnless(ti.BASH, "Bash not available")
    def test_bash_recovery_restore_references_fault_retains_backup(self):
        self.recovery_fault("bash", ["publish-references", "restore-references"])

    @unittest.skipUnless(ti.BASH, "Bash not available")
    def test_bash_recovery_restore_skill_fault_retains_backup(self):
        self.recovery_fault("bash", ["publish-references", "restore-skill"])


if __name__ == "__main__":
    unittest.main()
