from pathlib import Path
import subprocess
import tempfile
import unittest

from evals.claude_run import FORBIDDEN_FLAGS, NOTES_FILE, USER_NOTE, command, grade, stage


def say(text, message="m0"):
    return {"type": "assistant", "parent_tool_use_id": None,
            "message": {"id": message, "content": [{"type": "text", "text": text}]}}


def use(tool_id, name, message, **tool_input):
    return {"type": "assistant", "parent_tool_use_id": None,
            "message": {"id": message, "content": [{"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}]}}


def result(tool_id, text="", error=False):
    return {"type": "user", "parent_tool_use_id": None, "message": {"content": [
        {"type": "tool_result", "tool_use_id": tool_id, "is_error": error, "content": text}]}}


def worker(tool_id, message):
    return use(tool_id, "Agent", message, subagent_type="general-purpose", model="haiku", effort="low",
               run_in_background=False, prompt="brief")


def parallel_run(waiting=False):
    events = [say("Workers: haiku, low effort (chosen by difficulty).", "m1"),
              worker("a", "m2"), worker("b", "m2")]
    if waiting:
        events += [result("a", "Async agent launched"), result("b", "Async agent launched"),
                   say("Waiting for 2 workers.", "m3"),
                   {"type": "system", "subtype": "task_notification", "tool_use_id": "a", "status": "completed"},
                   {"type": "system", "subtype": "task_notification", "tool_use_id": "b", "status": "completed"}]
    else:
        events += [result("a", "[Subagent hand-back] done"), result("b", "[Subagent hand-back] done")]
    events += [use("d", "Bash", "m4", command="git diff 0123abc"), result("d", "diff --git a/left.py b/left.py"),
               use("t", "Bash", "m5", command="python3 -m unittest discover -s tests -q"), result("t", "Ran 6 tests\n\nOK"),
               say("Both changes are in; the suite passes.", "m6"),
               {"type": "result", "subtype": "success", "total_cost_usd": 0.25, "num_turns": 6, "modelUsage": {}}]
    return events


class ClaudeTests(unittest.TestCase):
    def test_blocking_parallel_run_passes(self):
        graded = grade(parallel_run(), "parallel", "haiku")
        self.assertTrue(graded["verified"], graded["checks"])

    def test_waiting_line_is_allowed_but_other_text_is_narration(self):
        self.assertTrue(grade(parallel_run(waiting=True), "parallel", "haiku")["verified"])
        events = parallel_run(waiting=True)
        events[5] = say("Both workers are running; I'll check back.", "m3")
        self.assertFalse(grade(events, "parallel", "haiku")["checks"]["no_routine_narration"])

    def test_host_nudge_fails_silence(self):
        events = parallel_run()
        events.insert(3, {"type": "user", "parent_tool_use_id": None, "message": {"content": [{"type": "text",
                      "text": "[Your previous response had no visible output. Please continue.]"}]}})
        self.assertFalse(grade(events, "parallel", "haiku")["checks"]["no_host_nudge"])

    def test_failed_or_missing_interpreter_check_is_not_success(self):
        events = parallel_run()
        events[8] = result("t", "FAILED (failures=1)", error=True)
        self.assertFalse(grade(events, "parallel", "haiku")["checks"]["manager_runs_successful_checks"])
        events[8] = result("t", "zsh:1: command not found: python", error=True)
        self.assertFalse(grade(events, "parallel", "haiku")["checks"]["manager_runs_successful_checks"])
        # A later working run decides; the missing-interpreter attempt ran no test.
        events[9:9] = [use("t3", "Bash", "m5b", command="python3 -m unittest tests.test_left -q"), result("t3", "OK")]
        self.assertTrue(grade(events, "parallel", "haiku")["checks"]["manager_runs_successful_checks"])
        # A failed check still fails when another command passes.
        events[8] = result("t", "FAILED (failures=1)", error=True)
        self.assertFalse(grade(events, "parallel", "haiku")["checks"]["manager_runs_successful_checks"])

    def test_wrong_model_split_batch_and_polling_fail(self):
        events = parallel_run()
        events[1]["message"]["content"][0]["input"]["model"] = "sonnet"
        events[2]["message"]["id"] = "m2b"
        events.insert(5, use("w", "ScheduleWakeup", "m3", delaySeconds=600))
        checks = grade(events, "parallel", "haiku")["checks"]
        self.assertFalse(checks["exact_worker_model"])
        self.assertFalse(checks["one_batch"])
        self.assertFalse(checks["no_polling_tools"])

    def test_dependent_workers_need_a_passing_check_between_them(self):
        events = [say("Workers: haiku, low effort.", "m1"), worker("a", "m2"), result("a", "done"),
                  use("t1", "Bash", "m3", command="python3 -m unittest tests.test_search_store -q"), result("t1", "OK"),
                  worker("b", "m4"), result("b", "done"),
                  use("d", "Bash", "m5", command="git diff 0123abc"), result("d", "diff --git"),
                  use("t2", "Bash", "m6", command="python3 -m unittest discover -s tests -q"), result("t2", "OK"),
                  say("Search is in; tests pass.", "m7"), {"type": "result", "subtype": "success"}]
        checks = grade(events, "plan-handoff", "haiku")["checks"]
        self.assertTrue(checks["dependent_workers_sequenced"])
        self.assertTrue(checks["manager_check_between_workers"])
        del events[3:5]
        self.assertFalse(grade(events, "plan-handoff", "haiku")["checks"]["manager_check_between_workers"])

    def test_explain_must_not_dispatch_or_load_the_skill(self):
        answer = [say("Notes are stored as JSON records.", "m1"), {"type": "result", "subtype": "success"}]
        self.assertTrue(grade(answer, "explain", "haiku")["verified"])
        loaded = [use("s", "Skill", "m0", skill="oversee"), *answer]
        self.assertFalse(grade(loaded, "explain", "haiku")["checks"]["no_skill_activation"])

    def test_command_has_no_auto_approval_flags(self):
        args = command("claude", "/oversee haiku: task", "claude-opus-5-5", "medium", 2)
        self.assertFalse(any(flag in arg for arg in args for flag in FORBIDDEN_FLAGS))
        self.assertEqual(args[args.index("--permission-mode") + 1], "acceptEdits")
        self.assertFalse(any(arg.startswith("Bash(python") and "unittest" not in arg and "notes.py" not in arg
                             for arg in args))

    def test_stage_commits_fixture_and_adds_user_state(self):
        with tempfile.TemporaryDirectory(prefix="oversee-claude-") as temp:
            project = stage(Path(temp), {"fixture": "parallel"})
            status = subprocess.run(["git", "status", "--short"], cwd=project, capture_output=True, text=True).stdout
            self.assertIn(" M README.md", status)
            self.assertIn("?? " + NOTES_FILE, status)
            self.assertNotIn(".claude", status)
            self.assertIn(USER_NOTE, (project / "README.md").read_text())
            self.assertTrue((project / ".claude/skills/oversee/agents/openai.yaml").is_file())


if __name__ == "__main__":
    unittest.main()
