import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASH = next((str(p) for p in [Path(r"C:\Program Files\Git\bin\bash.exe")]
             if p.exists()), None) or (shutil.which("bash") if os.name != "nt" else None)
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")
TARGETS = [".agents/skills/oversee", ".claude/skills/oversee", ".gemini/config/skills/oversee",
           ".gemini/antigravity-cli/skills/oversee"]


class Installers(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="oversee-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "source with spaces"
        self.source.mkdir()
        for name in ["install.sh", "install.bat", "uninstall.sh", "uninstall.bat", "remote-install.ps1", "SKILL.md"]:
            shutil.copyfile(ROOT / name, self.source / name)
        shutil.copytree(ROOT / "references", self.source / "references")
        self.profile = self.root / "profile with spaces"
        self.profile.mkdir()
        self.downloads = self.root / "downloads"
        self.downloads.mkdir()
        self.env = dict(os.environ, HOME=self.profile.as_posix(), USERPROFILE=str(self.profile),
                        TMPDIR=self.downloads.as_posix(), TEMP=str(self.downloads), TMP=str(self.downloads))
        self.targets = [self.profile / p for p in TARGETS]
        assert all(t.resolve().is_relative_to(self.root) for t in self.targets)

    def run_script(self, platform, command):
        if platform == "bash":
            if not BASH:
                self.skipTest("Bash not available")
            args = [BASH, str(self.source / (command + ".sh"))]
        else:
            if os.name != "nt":
                self.skipTest("Windows cmd required")
            args = ["cmd.exe", "/d", "/c", str(self.source / (command + ".bat"))]
        return subprocess.run(args, env=self.env, cwd=self.source, input="\n", capture_output=True, text=True, timeout=30)

    def lifecycle(self, platform):
        installed = self.run_script(platform, "install")
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        for target in self.targets:
            self.assertEqual((target / "SKILL.md").read_bytes(), (ROOT / "SKILL.md").read_bytes())
            self.assertEqual(sorted(p.name for p in target.iterdir()), ["SKILL.md", "references"])
            (target / "keep.txt").write_text("user file")
            (target / "references/obsolete.md").write_text("old instruction")
        updated = self.run_script(platform, "install")
        self.assertEqual(updated.returncode, 0, updated.stdout + updated.stderr)
        for target in self.targets:
            self.assertFalse((target / "references/obsolete.md").exists())
            self.assertEqual((target / "keep.txt").read_text(), "user file")
        neighbor = self.profile / ".agents/skills/other/keep.txt"
        neighbor.parent.mkdir()
        neighbor.write_text("keep")
        removed = self.run_script(platform, "uninstall")
        self.assertEqual(removed.returncode, 0, removed.stdout + removed.stderr)
        self.assertTrue(all(not target.exists() for target in self.targets))
        self.assertTrue(neighbor.exists())
        self.assertEqual(self.run_script(platform, "uninstall").returncode, 0)

    def test_windows_lifecycle(self):
        self.lifecycle("windows")

    def test_bash_lifecycle(self):
        self.lifecycle("bash")

    def incomplete(self, platform):
        (self.source / "references/harnesses.md").unlink()
        result = self.run_script(platform, "install")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(all(not target.exists() for target in self.targets))

    def test_windows_incomplete_payload(self):
        self.incomplete("windows")

    def test_bash_incomplete_payload(self):
        self.incomplete("bash")

    def rollback(self, platform):
        target = self.targets[0]
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("old skill")
        (target / "references").write_text("user file blocks directory replacement")
        result = self.run_script(platform, "install")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((target / "SKILL.md").read_text(), "old skill")
        self.assertEqual((target / "references").read_text(), "user file blocks directory replacement")
        self.assertEqual(list(target.parent.glob("*stage*")), [])

    def test_windows_replacement_failure_restores_payload(self):
        self.rollback("windows")

    def test_bash_replacement_failure_restores_payload(self):
        self.rollback("bash")

    def self_protection(self, platform):
        self.assertEqual(self.run_script(platform, "install").returncode, 0)
        installed = self.targets[0]
        suffix = ".sh" if platform == "bash" else ".bat"
        for name in ["install", "uninstall"]:
            shutil.copyfile(self.source / (name + suffix), installed / (name + suffix))
        self.source = installed
        result = self.run_script(platform, "install")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Skipped:", result.stdout)
        self.assertNotEqual(self.run_script(platform, "uninstall").returncode, 0)
        self.assertTrue(all((t / "SKILL.md").exists() for t in self.targets))

    def test_windows_self_install_and_uninstall_protection(self):
        self.self_protection("windows")

    def test_bash_self_install_and_uninstall_protection(self):
        self.self_protection("bash")

    @unittest.skipUnless(BASH, "Bash not available")
    def test_bash_failed_final_move_restores_both_items(self):
        target = self.targets[0]
        (target / "references").mkdir(parents=True)
        (target / "SKILL.md").write_text("old")
        (target / "references/old.md").write_text("old refs")
        shim = self.root / "bash-env"
        shim.write_text('mv() { if [[ "$1" == *stage*/references && "$2" == */oversee/references ]]; then return 1; fi; command mv "$@"; }\n', encoding="utf-8")
        self.env["BASH_ENV"] = shim.as_posix()
        self.assertNotEqual(self.run_script("bash", "install").returncode, 0)
        self.assertEqual((target / "SKILL.md").read_text(), "old")
        self.assertEqual((target / "references/old.md").read_text(), "old refs")
        self.assertFalse((target / "references/harnesses.md").exists())

    def archive(self):
        archive = self.root / "mock.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(self.source, arcname="oversee-main")
        return archive

    @unittest.skipUnless(BASH, "Bash not available")
    def remote_bash(self, curl_exit=0, corrupt=False, interrupt=False):
        archive = self.archive()
        if corrupt:
            archive.write_text("not an archive")
        self.env.update(AUDIT_ARCHIVE=archive.as_posix(), AUDIT_SOURCE=(self.source / "install.sh").as_posix(),
                        AUDIT_CURL_EXIT=str(curl_exit))
        mock = 'curl() { cat "$AUDIT_ARCHIVE"; return "$AUDIT_CURL_EXIT"; }; export -f curl; cat "$AUDIT_SOURCE" | bash'
        if interrupt:
            mock = 'curl() { kill -TERM "$BASHPID"; }; export -f curl; cat "$AUDIT_SOURCE" | bash'
        result = subprocess.run([BASH, "-c", mock], env=self.env, cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(list(self.downloads.iterdir()), [])
        return result

    def test_remote_bash_success_cleans_fetch(self):
        result = self.remote_bash()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(all((t / "SKILL.md").exists() for t in self.targets))

    def test_remote_bash_curl_failure_despite_valid_archive(self):
        self.assertNotEqual(self.remote_bash(curl_exit=22).returncode, 0)
        self.assertTrue(all(not t.exists() for t in self.targets))

    def test_remote_bash_corrupt_archive_cleans_fetch(self):
        self.assertNotEqual(self.remote_bash(corrupt=True).returncode, 0)

    def test_remote_bash_interrupted_fetch_cleans(self):
        self.assertNotEqual(self.remote_bash(interrupt=True).returncode, 0)

    @unittest.skipUnless(POWERSHELL and os.name == "nt", "Windows PowerShell required")
    def remote_powershell(self, mode):
        self.env.update(AUDIT_ARCHIVE=str(self.archive()), AUDIT_SOURCE=str(self.source), AUDIT_MODE=mode)
        script = self.root / "remote-test.ps1"
        script.write_text("""
$ErrorActionPreference = 'Stop'
function Invoke-WebRequest {
    param($Uri, $OutFile)
    if ($env:AUDIT_MODE -eq 'download-failure') { throw 'injected download failure' }
    if ($Uri.EndsWith('.zip')) {
        Compress-Archive -LiteralPath $env:AUDIT_SOURCE -DestinationPath $OutFile
    } else { Copy-Item -LiteralPath $env:AUDIT_ARCHIVE -Destination $OutFile }
}
if ($env:AUDIT_MODE -eq 'tar-failure') {
    function tar {
        $folder = $args[[Array]::IndexOf($args, '-C') + 1]
        Copy-Item -Path (Join-Path $env:AUDIT_SOURCE '*') -Destination $folder -Recurse
        $global:LASTEXITCODE = 7
    }
}
if ($env:AUDIT_MODE -eq 'zip') {
    function Get-Command { param($Name, $ErrorAction) return $null }
}
& (Join-Path $env:AUDIT_SOURCE 'remote-install.ps1')
""", encoding="utf-8")
        result = subprocess.run([POWERSHELL, "-NoProfile", "-File", str(script)], env=self.env,
                                capture_output=True, input="\n", text=True, timeout=30)
        self.assertFalse(any(self.downloads.glob("oversee-*")))
        return result

    def test_powershell_remote_success(self):
        result = self.remote_powershell("success")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(all((t / "references/harnesses.md").exists() for t in self.targets))

    def test_powershell_remote_tar_failure_with_partial_payload(self):
        result = self.remote_powershell("tar-failure")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Archive extraction failed", result.stderr)
        self.assertTrue(all(not t.exists() for t in self.targets))

    def test_powershell_remote_download_failure(self):
        self.assertNotEqual(self.remote_powershell("download-failure").returncode, 0)

    def test_powershell_remote_zip_fallback(self):
        result = self.remote_powershell("zip")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_line_endings(self):
        for path in ROOT.glob("*.bat"):
            data = path.read_bytes()
            self.assertNotIn(b"\n", data.replace(b"\r\n", b""), path.name)
        for path in ROOT.glob("*.sh"):
            self.assertNotIn(b"\r", path.read_bytes(), path.name)
