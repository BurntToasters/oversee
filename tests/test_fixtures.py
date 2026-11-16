from pathlib import Path
import json
import subprocess
import tempfile
import unittest

from evals import run
from evals.codex_run import stage

ROOT = Path(__file__).resolve().parents[1]
CASE = {"name": "parallel", "fixture": "parallel"}


def git(project, *args):
    return subprocess.run(["git", *args], cwd=project, capture_output=True, text=True, check=True).stdout


class FixtureTests(unittest.TestCase):
    """Pilot fixtures must let the manager follow the skill's baseline rules."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="oversee-fixture-")
        self.addCleanup(temp.cleanup)
        self.output = Path(temp.name)

    def assert_committed_with_full_skill(self, project, skill):
        self.assertTrue(git(project, "rev-parse", "HEAD").strip())
        self.assertEqual(git(project, "status", "--porcelain"), "")
        # Clean tree: `git stash create` prints nothing, and the skill then uses the commit id.
        self.assertEqual(git(project, "stash", "create"), "")
        self.assertTrue((skill / "agents" / "openai.yaml").is_file())
        self.assertTrue((skill / "references").is_dir())

    def test_opencode_fixture_is_committed_and_allows_baseline_commands(self):
        project = run.fixture(self.output, CASE, with_skill=True)
        self.assert_committed_with_full_skill(project, project / ".opencode/skills/oversee")
        allowed = {r["resource"] for r in json.loads((project / "opencode.json").read_text())["permissions"]
                   if r["effect"] == "allow"}
        self.assertLessEqual(set(run.BASELINE_COMMANDS), allowed)
        self.assertNotIn("git stash*", allowed)

    def test_codex_stage_is_committed(self):
        project, skill_md = stage(self.output, CASE)
        self.assert_committed_with_full_skill(project, skill_md.parent)


if __name__ == "__main__":
    unittest.main()
