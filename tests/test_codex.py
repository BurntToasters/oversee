import unittest
import io
import queue
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from evals.codex_run import Codex, export, resolve, run_case
from evals.codex_review import grade, usage
from evals.run import Blocked


def item_event(when, item):
    return {"direction": "received", "time": when, "message": {"method": "item/completed",
            "params": {"threadId": "root", "item": item}}}


def audit_item(command, code=0, output="", status="completed"):
    return {"type": "commandExecution", "status": status, "command": command,
            "exitCode": code, "aggregatedOutput": output}


def unittest_output(count=1):
    noun = "test" if count == 1 else "tests"
    return f"Ran {count} {noun} in 0.001s\n\nOK\n"


def orchestration_records(modes=("default",)):
    manager, worker = {"model": "manager", "effort": "high"}, {"model": "worker", "effort": "max"}
    root = {"thread": {"id": "root"}, "turn_contexts": [{"payload": {**manager,
            "collaboration_mode": {"mode": mode}}} for mode in modes]}
    children = [{"thread": {"id": name}, "turn_contexts": [{"payload": worker}]}
                for name in ("left", "right")]
    return [root, *children], {"root": "root", "manager": manager, "worker": worker}


def parallel_events(left_code=1):
    events = [item_event(0, {"type": "agentMessage", "text": "Using worker max"}),
              item_event(1, {"type": "subAgentActivity", "kind": "started", "agentThreadId": "left"}),
              item_event(2, {"type": "subAgentActivity", "kind": "started", "agentThreadId": "right"}),
              item_event(3, {"type": "subAgentActivity", "kind": "completed", "agentThreadId": "left"}),
              item_event(4, {"type": "subAgentActivity", "kind": "completed", "agentThreadId": "right"}),
              item_event(5, audit_item("python -m unittest tests.test_left", left_code, unittest_output())),
              item_event(6, audit_item("python -m unittest tests.test_right", 0, unittest_output())),
              item_event(7, audit_item("git diff", 0, "diff --git a/left.py b/left.py")),
              item_event(8, {"type": "agentMessage", "phase": "final_answer", "text": "Done."})]
    events.append({"direction": "received", "message": {"method": "turn/completed",
                   "params": {"threadId": "root", "turn": {"id": "turn", "status": "completed"}}}})
    return events


class CodexTests(unittest.TestCase):
    def test_success_prose_cannot_establish_codex_dispatch_or_audit(self):
        settings = {"model": "model", "effort": "max"}
        meta = {"root": "root", "manager": settings, "worker": settings}
        record = {"thread": {"id": "root"}, "turn_contexts": [{"payload": settings}]}
        events = [{"direction": "received", "time": 1, "message": {"method": "item/completed", "params": {
            "threadId": "root", "item": {"type": "agentMessage", "phase": "final_answer",
            "text": "Two model max workers completed. I audited every change and all tests passed."}}}}]
        result = grade(events, [record], meta, "parallel")
        self.assertFalse(result["verified"])
        self.assertFalse(result["checks"]["exact_worker_settings"])
        self.assertFalse(result["checks"]["manager_runs_successful_checks"])

    def test_usage_sums_unique_threads_using_latest_native_counters(self):
        def event(thread, tokens):
            return {"direction": "received", "message": {"method": "thread/tokenUsage/updated", "params": {
                "threadId": thread, "tokenUsage": {"total": {"inputTokens": tokens, "outputTokens": 2}}}}}
        records = [{"thread": {"id": "root"}}, {"thread": {"id": "child"}}, {"thread": {"id": "root"}}]
        result = usage([event("root", 1), event("root", 3), event("child", 5)], records)
        self.assertEqual(result["input"], 8)
        self.assertEqual(result["sessions"], 2)
        self.assertIsNone(result["reasoning"])
        self.assertIsNone(result["cost_usd"])
        self.assertIsNone(usage([event("root", 3)], records)["input"])

    def test_configured_thread_model_cannot_replace_execution_context_proof(self):
        settings = {"model": "arbitrary-model", "effort": "max"}
        meta = {"root": "root", "manager": settings, "worker": settings}
        record = {"thread": {"id": "root", "model": "arbitrary-model"}, "turn_contexts": []}
        self.assertFalse(grade([], [record], meta, "explain")["checks"]["exact_manager_settings"])
        record["turn_contexts"] = [{"payload": settings}]
        self.assertTrue(grade([], [record], meta, "explain")["checks"]["exact_manager_settings"])

    def test_export_includes_current_and_legacy_descendant_event_schemas(self):
        api = object.__new__(Codex)
        api.events = [
            {"message": {"params": {"threadId": "root", "item": {
                "type": "subAgentActivity", "agentThreadId": "child"}}}},
            {"message": {"params": {"threadId": "child", "item": {
                "type": "collabAgentToolCall", "receiverThreadIds": ["grandchild"]}}}}]
        with patch.object(api, "request", side_effect=lambda method, p: {"thread": {"id": p["threadId"]}}) as request:
            records = export(api, "root")
        self.assertEqual([r["thread"]["id"] for r in records], ["root", "child", "grandchild"])
        self.assertEqual(request.call_count, 3)

    def test_models_and_efforts_come_from_the_live_catalog(self):
        models = [{"id": "example-v1.4", "model": "example-v1.4",
                   "supportedReasoningEfforts": [{"reasoningEffort": "medium"}]}]
        self.assertEqual(resolve(models, "example-v1.4", "medium"), {"model": "example-v1.4", "effort": "medium"})
        for name, effort in [("example-v4.1", "medium"), ("example-v1.4", "max")]:
            with self.assertRaises(Blocked):
                resolve(models, name, effort)
        with self.assertRaises(Blocked):
            resolve(models * 2, "example-v1.4", "medium")

    def test_wait_consumes_notifications_without_status_requests(self):
        api = object.__new__(Codex)
        api.events = []
        def completion():
            api.events.append({"message": {"method": "turn/completed", "params": {
                "threadId": "root", "turn": {"id": "turn", "status": "completed"}}}})
        with patch.object(api, "receive", side_effect=completion) as receive, patch.object(api, "request") as request:
            api.wait("root", "turn")
        receive.assert_called_once_with()
        request.assert_not_called()

    def test_protocol_timeout_is_total_across_unrelated_notifications(self):
        api = object.__new__(Codex)
        api.sequence, api.events = 0, []
        api.process = SimpleNamespace(stdin=SimpleNamespace(write=Mock(), flush=Mock()))
        clock, waits = [0.0], []

        def monotonic():
            return clock[0]

        def unrelated(timeout):
            waits.append(timeout)
            clock[0] += 0.4
            return {"method": "unrelated/event", "params": {}}

        with patch("evals.codex_run.time.monotonic", side_effect=monotonic), \
                patch.object(api, "receive", side_effect=unrelated), self.assertRaisesRegex(TimeoutError, "timed out"):
            api.request("turn/interrupt", {}, timeout=1)
        self.assertEqual(len(waits), 3)
        self.assertGreater(waits[0], waits[1])
        self.assertGreater(waits[1], waits[2])

    def test_completion_before_wait_is_not_lost(self):
        api = object.__new__(Codex)
        api.events = [{"message": {"method": "turn/completed", "params": {
            "threadId": "root", "turn": {"id": "turn", "status": "completed"}}}}]
        with patch.object(api, "receive") as receive:
            api.wait("root", "turn")
        receive.assert_not_called()

    def test_failed_turn_does_not_count_as_completed_success(self):
        api = object.__new__(Codex)
        api.events = [{"message": {"method": "turn/completed", "params": {
            "threadId": "root", "turn": {"id": "turn", "status": "failed"}}}}]
        with self.assertRaises(Blocked):
            api.wait("root", "turn")

    def test_failed_distinct_unittest_command_cannot_be_masked_by_another_pass(self):
        records, meta = orchestration_records()
        result = grade(parallel_events(), records, meta, "parallel")
        self.assertFalse(result["checks"]["manager_runs_successful_checks"])
        self.assertFalse(result["verified"])

    def test_latest_result_for_each_codex_check_command_controls_acceptance(self):
        records, meta = orchestration_records()
        events = parallel_events(left_code=0)
        # A later failure of the same command supersedes its earlier successful result.
        events.insert(-2, item_event(6.5, audit_item("python -m unittest tests.test_left", 1, "FAILED (failures=1)\n")))
        self.assertFalse(grade(events, records, meta, "parallel")["checks"]["manager_runs_successful_checks"])
        events.insert(-2, item_event(6.7, audit_item("python -m unittest tests.test_left", 0, unittest_output())))
        self.assertTrue(grade(events, records, meta, "parallel")["checks"]["manager_runs_successful_checks"])

    def test_missing_codex_test_exit_code_stays_unknown(self):
        records, meta = orchestration_records()
        events = parallel_events(left_code=None)
        self.assertIsNone(grade(events, records, meta, "parallel")["checks"]["manager_runs_successful_checks"])

    def test_exit_zero_without_unittest_result_output_stays_unknown(self):
        records, meta = orchestration_records()
        events = parallel_events(left_code=0)
        events[5]["message"]["params"]["item"]["aggregatedOutput"] = ""
        self.assertIsNone(grade(events, records, meta, "parallel")["checks"]["manager_runs_successful_checks"])

    def test_echoed_or_chained_unittest_command_does_not_count(self):
        records, meta = orchestration_records()
        events = parallel_events(left_code=0)
        for index in (5, 6):
            item = events[index]["message"]["params"]["item"]
            item["command"] = "echo 'python -m unittest'; true"
            item["aggregatedOutput"] = unittest_output()
        self.assertFalse(grade(events, records, meta, "parallel")["checks"]["manager_runs_successful_checks"])

    def test_powershell_check_chain_counts_only_final_unittest_output(self):
        records, meta = orchestration_records()
        events = parallel_events(left_code=0)
        command = ('"C:\\\\Program Files\\\\PowerShell\\\\7\\\\pwsh.exe" -Command '
                   "'git diff; git status --short; python -B -m unittest discover -s tests -v'")
        events[5]["message"]["params"]["item"]["command"] = command
        events[5]["message"]["params"]["item"]["aggregatedOutput"] = (
            "diff --git a/left.py b/left.py\n" + unittest_output(4))
        self.assertTrue(grade(events, records, meta, "parallel")["checks"]["manager_runs_successful_checks"])

    def test_dependent_codex_requires_diff_and_passing_check_before_next_dispatch(self):
        records, meta = orchestration_records(("plan", "default"))
        events = [item_event(0, {"type": "agentMessage", "text": "Using worker max"}),
                  item_event(1, {"type": "subAgentActivity", "kind": "started", "agentThreadId": "left"}),
                  item_event(2, {"type": "subAgentActivity", "kind": "completed", "agentThreadId": "left"}),
                  item_event(2.5, audit_item("python -m unittest tests.test_left", 0, unittest_output())),
                  item_event(2.6, audit_item("git diff", 0, "diff --git a/left.py b/left.py")),
                  item_event(3, {"type": "subAgentActivity", "kind": "started", "agentThreadId": "right"}),
                  item_event(4, {"type": "subAgentActivity", "kind": "completed", "agentThreadId": "right"}),
                  item_event(5, audit_item("python -m unittest", 0, unittest_output())),
                  item_event(5.5, audit_item("git diff", 0, "diff --git a/right.py b/right.py"))]
        result = grade(events, records, meta, "plan-handoff")
        self.assertTrue(result["checks"]["dependent_manager_acceptance_between_workers"])
        events[3]["time"], events[4]["time"] = 3.5, 3.6
        events[5]["time"] = 3
        result = grade(events, records, meta, "plan-handoff")
        self.assertFalse(result["checks"]["dependent_manager_acceptance_between_workers"])

    def test_close_interrupts_children_discovered_while_interrupting_root(self):
        api = object.__new__(Codex)
        api.active = {"root": "root-turn"}
        api.events = []
        api.inbox = queue.Queue()
        api.process = SimpleNamespace(stdin=io.StringIO(), wait=Mock(return_value=0))
        calls = []

        def request(method, params, *, timeout):
            calls.append((method, params["threadId"]))
            if params["threadId"] == "root":
                api.inbox.put({"method": "turn/started", "params": {
                    "threadId": "child", "turn": {"id": "child-turn"}}})
                api.receive(timeout=0)
            else:
                api.active.pop("child", None)

        with patch.object(api, "request", side_effect=request):
            errors = api.close()
        self.assertEqual(calls, [("turn/interrupt", "root"), ("turn/interrupt", "child")])
        self.assertEqual(errors, [])

    def test_close_records_broken_pipe_and_escalates_process_shutdown_with_timeouts(self):
        stdin = SimpleNamespace(close=Mock(side_effect=BrokenPipeError("closed")))
        process = SimpleNamespace(stdin=stdin, wait=Mock(side_effect=[subprocess.TimeoutExpired("codex", 2),
                            subprocess.TimeoutExpired("codex", 2), 0]), terminate=Mock(), kill=Mock())
        api = object.__new__(Codex)
        api.active, api.process = {}, process
        errors = api.close()
        self.assertTrue(any("Close stdin" in error for error in errors))
        process.terminate.assert_called_once()
        process.kill.assert_called_once()
        self.assertEqual([call.kwargs["timeout"] for call in process.wait.call_args_list], [2, 2, 2])

    def test_run_case_persists_evidence_when_cleanup_fails_without_masking_original_error(self):
        class FailedAPI:
            events = [{"message": {"method": "session/list"}}]
            def request(self, *args, **kwargs):
                raise ValueError("original run failure")
            def close(self):
                raise BrokenPipeError("cleanup failure")

        with tempfile.TemporaryDirectory() as folder, patch("evals.codex_run.Codex", return_value=FailedAPI()):
            output = Path(folder) / "case"
            case = {"fixture": "parallel", "name": "parallel", "prompt": "prompt"}
            with self.assertRaisesRegex(ValueError, "original run failure"):
                run_case("codex", case, output, {"model": "manager", "effort": "high"},
                         {"model": "worker", "effort": "max"})
            self.assertTrue((output / "native.json").exists())
            self.assertTrue((output / "events.json").exists())
            self.assertTrue((output / "after.json").exists())
            self.assertIn("cleanup failure", (output / "cleanup-errors.json").read_text())

    def test_run_case_reports_successful_run_as_failed_when_evidence_cannot_persist(self):
        state = {}

        def prepare(folder, case):
            project = folder / "project"
            project.mkdir(parents=True)
            (project / "file.py").write_text("value = 1\n")
            skill = project / ".agents" / "skills" / "oversee" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("skill\n")
            state["skill"] = skill
            return project, skill

        class SuccessfulAPI:
            def __init__(self):
                self.events = []
            def request(self, method, params):
                if method == "skills/list":
                    return {"data": [{"skills": [{"name": "oversee", "path": str(state["skill"]), "enabled": True}]}]}
                if method == "thread/start":
                    return {"thread": {"id": "root"}}
                if method == "turn/start":
                    return {"turn": {"id": "turn"}}
                if method == "thread/read":
                    return {"thread": {"id": params["threadId"]}}
                raise AssertionError(method)
            def wait(self, *args):
                return None
            def close(self):
                return []

        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "case"
            api = SuccessfulAPI()
            writer = __import__("evals.codex_run", fromlist=["write_json"]).write_json

            def write(path, value):
                if path.name == "events.json":
                    raise OSError("disk full")
                return writer(path, value)

            with patch("evals.codex_run.stage", side_effect=prepare), \
                    patch("evals.codex_run.Codex", return_value=api), \
                    patch("evals.codex_run.correctness", return_value={"tests_passed": True, "behavior_passed": True}), \
                    patch("evals.codex_run.write_json", side_effect=write):
                with self.assertRaisesRegex(OSError, "Evidence persistence failed"):
                    run_case("codex", {"name": "parallel", "fixture": "parallel", "prompt": "prompt"},
                             output, {"model": "manager", "effort": "high"},
                             {"model": "worker", "effort": "max"})
            self.assertTrue((output / "native.json").exists())
            self.assertTrue((output / "after.json").exists())
            self.assertFalse((output / "events.json").exists())
            self.assertFalse((output / "result.json").exists())
            self.assertIn("disk full", (output / "cleanup-errors.json").read_text())
