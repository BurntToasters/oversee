import unittest

from evals.cursor_run import FORBIDDEN_FLAGS, command, grade

PROJECT = "/tmp/oversee-fixture/project"


def text(value):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": value}]}}


def tool(kind, call_id, subtype, args, result=None, started=0, ended=None):
    body = {"args": args}
    if result is not None:
        body["result"] = result
    call = {kind: body, "startedAtMs": started}
    if ended is not None:
        call["completedAtMs"] = ended
    return {"type": "tool_call", "subtype": subtype, "call_id": call_id, "tool_call": call}


def task(call_id, start, end):
    args = {"description": call_id, "model": "composer-2.5", "prompt": "brief"}
    return [tool("taskToolCall", call_id, "started", args, started=start),
            tool("taskToolCall", call_id, "completed", args, {"success": {}}, start, end)]


def shell(call_id, command_line, code=0, stdout="", rejected=False):
    args = {"command": command_line}
    result = {"rejected": {"command": command_line}} if rejected else {"success": {"exitCode": code, "stdout": stdout}}
    return [tool("shellToolCall", call_id, "started", args), tool("shellToolCall", call_id, "completed", args, result)]


def read(path):
    return tool("readToolCall", path, "started", {"path": path})


def parallel(overlap=True):
    left, right = (task("a", 0, 10), task("b", 5, 15)) if overlap else (task("a", 0, 10), task("b", 11, 20))
    return [read(PROJECT + "/.cursor/skills/oversee/references/cursor.md"),
            text("Workers: composer-2.5 (named)."), left[0], right[0], left[1], right[1],
            *shell("d", "git diff 0123abc", stdout="diff --git a/left.py b/left.py"),
            *shell("t", "python3 -m unittest discover -s tests -q"),
            text("Both changes are in; the suite passes."), {"type": "result", "subtype": "success", "usage": {}}]


class CursorTests(unittest.TestCase):
    def test_overlapping_workers_pass(self):
        graded = grade(parallel(), "parallel", "composer-2.5", PROJECT)
        self.assertTrue(graded["verified"], graded["checks"])

    def test_sequential_workers_fail_parallel_overlap(self):
        self.assertFalse(grade(parallel(overlap=False), "parallel", "composer-2.5", PROJECT)["checks"]["parallel_overlap"])

    def test_global_skill_copy_and_transcript_reads_fail(self):
        events = parallel()
        events.insert(0, read("/Users/someone/.claude/skills/oversee/SKILL.md"))
        events.insert(0, read("/Users/someone/.cursor/projects/x/agent-transcripts/a.jsonl"))
        checks = grade(events, "parallel", "composer-2.5", PROJECT)["checks"]
        self.assertFalse(checks["skill_from_fixture"])
        self.assertFalse(checks["no_transcript_reads"])

    def test_rejected_check_is_not_a_result(self):
        events = parallel()
        events[-4:-2] = shell("t", "python3 -m unittest discover -s tests -q", rejected=True)
        self.assertFalse(grade(events, "parallel", "composer-2.5", PROJECT)["checks"]["manager_runs_successful_checks"])

    def test_preamble_and_wrong_model_fail(self):
        events = parallel()
        events.insert(0, text("I'll set up the run first."))
        events[3]["tool_call"]["taskToolCall"]["args"]["model"] = "inherit"
        checks = grade(events, "parallel", "composer-2.5", PROJECT)["checks"]
        self.assertFalse(checks["worker_choice_before_dispatch"])
        self.assertFalse(checks["exact_worker_model"])

    def test_command_has_no_auto_approval_flags(self):
        args = command("agent", "/oversee composer-2.5: task", "grok-4.7-xhigh")
        self.assertFalse(set(args) & set(FORBIDDEN_FLAGS))
        self.assertIn("--trust", args)


if __name__ == "__main__":
    unittest.main()
