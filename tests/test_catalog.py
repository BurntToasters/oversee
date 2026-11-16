import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
EVALS = CATALOG["evals"]
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class CatalogTests(unittest.TestCase):
    def test_ids_and_names_unique_and_kebab(self):
        ids = [e["id"] for e in EVALS]
        names = [e["name"] for e in EVALS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            self.assertRegex(name, KEBAB)

    def test_fixtures_exist(self):
        for entry in EVALS:
            self.assertTrue((ROOT / "evals" / "fixtures" / entry["fixture"]).is_dir(), entry["name"])

    def test_pilot_names_exist_and_are_pilot_entries(self):
        by_name = {e["name"]: e for e in EVALS}
        for name in CATALOG["pilot"]:
            self.assertIn(name, by_name)
            self.assertEqual(by_name[name]["execution"], "pilot", name)

    def test_pilot_prompts_request_no_verbose_checks(self):
        by_name = {e["name"]: e for e in EVALS}
        for name in CATALOG["pilot"]:
            self.assertNotRegex(by_name[name]["prompt"], r"(?<!\S)-v(?!\S)", name)

    def test_only_pilot_or_scenario_execution(self):
        for entry in EVALS:
            self.assertIn(entry["execution"], {"pilot", "scenario"}, entry["name"])

    def test_prompts_and_expectations_present(self):
        for entry in EVALS:
            self.assertTrue(entry["prompt"].strip(), entry["name"])
            self.assertTrue(entry["expectations"], entry["name"])
            for item in entry["expectations"]:
                self.assertTrue(item.strip(), entry["name"])

    def test_only_worker_placeholder_used(self):
        for entry in EVALS:
            self.assertEqual(set(re.findall(r"\{[^}]*\}", entry["prompt"])) - {"{worker}"}, set(), entry["name"])

    def test_negative_cases_present(self):
        negatives = [e["name"] for e in EVALS if e["name"].startswith("negative-") or e["name"] == "quoted-trigger"]
        self.assertGreaterEqual(len(negatives), 4)
        self.assertIn("host-parser-limit", {e["name"] for e in EVALS})

    def test_planning_scope_cases_present(self):
        names = {e["name"] for e in EVALS}
        for name in ["plan-mode-task-then-invoke", "plan-mode-host-helpers", "normal-mode-task-then-invoke",
                     "research-request-stays-with-manager", "plan-mode-research-request", "plan-fresh-context"]:
            self.assertIn(name, names)

    def test_implementation_only_cases_present(self):
        names = {e["name"] for e in EVALS}
        for name in ["post-run-audit-request", "audit-only-invocation", "repo-map-invocation",
                     "post-run-coding-request", "post-run-findings-then-invoke"]:
            self.assertIn(name, names)


    def test_context_economy_cases_present(self):
        by_id = {e["id"]: e for e in EVALS}
        for number, name in [(45, "ready-plan-not-reexplored"), (46, "lean-baseline"),
                             (47, "brief-pointers-and-report-fields"), (48, "quiet-checks-real-exit-code"),
                             (49, "staggered-completion-silence")]:
            self.assertEqual(by_id[number]["name"], name)
            self.assertEqual(by_id[number]["execution"], "scenario", name)
            self.assertEqual(by_id[number]["fixture"], "notes-cli", name)

if __name__ == "__main__":
    unittest.main()
