import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evals.evidence import final_text, grade, skill_loaded, tools, total_usage
from evals.review import review
from evals.run import Blocked, OpenCode, main, provider_blocker, resolve, retain_interrupted, run_case, snapshot


WORKER = {"providerID": "example", "id": "worker-v4.1", "variant": "max"}


def transcript(session="root", parent=None, model=None, created=0, idle=10):
    info = {"id": session, "model": model or WORKER, "agent": "general" if parent else "build",
            "time": {"created": created, "idle": idle}, "outcome": "succeeded",
            "cost": 0, "tokens": {"input": 5, "output": 3, "reasoning": 1, "cache": {"read": 2, "write": 0}}}
    if parent:
        info["parentID"] = parent
    return {"info": info, "messages": [{"type": "assistant", "time": {"created": created},
                                       "model": model or WORKER, "content": [], "tokens": copy.deepcopy(info["tokens"])}]}


def model(provider="example", name="Example Worker V4.1", model_id="worker-v4.1", variants=("low", "max")):
    return {"providerID": provider, "id": model_id, "name": name,
            "enabled": True, "capabilities": {"tools": True}, "variants": [{"id": v} for v in variants]}


class EvidenceTests(unittest.TestCase):
    def test_completed_shell_with_failed_tests_does_not_establish_acceptance(self):
        root, child = transcript(), transcript("child", "root", created=2, idle=4)
        root["messages"][0]["content"] = [{"type": "tool", "name": "shell", "time": {"created": 5},
            "state": {"status": "completed", "input": {"command": "python -m unittest"}, "metadata": {"exit": 1}}}]
        checks = grade([root, child], "parallel", True, WORKER)["checks"]
        self.assertTrue(checks["manager_runs_checks_after_workers"])
        self.assertFalse(checks["manager_checks_succeeded"])
        root["messages"][0]["content"][0]["state"]["metadata"]["exit"] = 0
        self.assertTrue(grade([root, child], "parallel", True, WORKER)["checks"]["manager_checks_succeeded"])

    def test_passing_second_piece_does_not_erase_failed_first_piece_check(self):
        root, child = transcript(), transcript("child", "root", created=2, idle=4)
        calls = [{"type": "tool", "name": "shell", "time": {"created": 5 + index}, "state": {
            "status": "completed", "input": {"command": f"python -m unittest tests.test_{name}"}, "metadata": {"exit": code}}}
            for index, (name, code) in enumerate([("left", 1), ("right", 0)])]
        root["messages"][0]["content"] = calls
        self.assertFalse(grade([root, child], "parallel", True, WORKER)["checks"]["manager_checks_succeeded"])
        calls.append(copy.deepcopy(calls[0]))
        calls[-1]["state"]["metadata"]["exit"] = 0
        self.assertTrue(grade([root, child], "parallel", True, WORKER)["checks"]["manager_checks_succeeded"])

    def test_usage_deduplicates_sessions_not_messages(self):
        root, child = transcript(), transcript("child", "root")
        root["messages"] = [{"type": "assistant", "cost": 999, "tokens": {"input": 999}}]
        usage = total_usage([root, child, copy.deepcopy(root)])
        self.assertEqual(usage["sessions"], 2)
        self.assertEqual(usage["input"], 10)
        self.assertEqual(usage["cost_usd"], 0)

    def test_missing_usage_is_unknown(self):
        root, child = transcript(), transcript("child", "root")
        del child["info"]["tokens"]
        del child["info"]["cost"]
        usage = total_usage([root, child])
        self.assertIsNone(usage["input"])
        self.assertIsNone(usage["cost_usd"])
        self.assertIsNone(total_usage([])["output"])

    def test_authentication_defaults_are_not_measured_zero_usage(self):
        root = transcript()
        root["messages"] = [{"type": "assistant", "error": {"type": "provider.auth", "message": "Reconnect"}}]
        self.assertEqual(provider_blocker([root])["type"], "provider.auth")
        self.assertIsNone(total_usage([root])["input"])

    def test_self_report_cannot_prove_dispatch_or_audit(self):
        root = transcript()
        root["messages"] = [{"type": "assistant", "time": {"created": 1}, "content": [
            {"type": "text", "text": "Workers: exact model. I checked the diff and ran unittest. All passed."}]}]
        result = grade([root], "parallel", True, WORKER)
        self.assertFalse(result["verified"])
        self.assertFalse(result["checks"]["workers_dispatched"])
        self.assertFalse(result["checks"]["manager_runs_checks_after_workers"])

    def test_actual_child_model_mismatch_fails(self):
        root, child = transcript(), transcript("child", "root", {**WORKER, "variant": "low"}, 2, 4)
        result = grade([root, child], "parallel", True, WORKER)
        self.assertFalse(result["checks"]["exact_worker_settings"])

    def test_announcement_in_final_does_not_count(self):
        root, child = transcript(), transcript("child", "root", created=2, idle=4)
        root["messages"] = [{"type": "assistant", "time": {"created": 5}, "content": [
            {"type": "text", "text": "Workers: done."}]}]
        result = grade([root, child], "parallel", True, WORKER)
        self.assertFalse(result["checks"]["announcement_before_dispatch"])

    def test_plan_violation_cannot_pass_after_successful_execution(self):
        root, child = transcript(), transcript("child", "root", created=2, idle=4)
        result = grade([root, child], "plan-handoff", True, WORKER,
                       {"unchanged": False, "no_implementation_workers": False})
        self.assertFalse(result["verified"])
        self.assertFalse(result["checks"]["plan_phase_unchanged"])

    def test_parallel_overlap_requires_real_timestamps(self):
        root = transcript()
        sequential = [root, transcript("a", "root", created=1, idle=2), transcript("b", "root", created=3, idle=4)]
        self.assertFalse(grade(sequential, "parallel", True, WORKER)["checks"]["parallel_overlap"])
        sequential[2]["info"]["time"]["created"] = 1.5
        self.assertTrue(grade(sequential, "parallel", True, WORKER)["checks"]["parallel_overlap"])

    def test_ordinary_question_rejects_activation_and_workers(self):
        root = transcript()
        root["messages"] = [{"type": "assistant", "content": [{"type": "text", "text": ".notes.json stores id, title, body"}]}]
        self.assertTrue(grade([root], "explain", True, WORKER)["verified"])
        root["messages"].append({"type": "skill"})
        self.assertFalse(grade([root], "explain", True, WORKER)["verified"])

    def test_native_hydrated_skill_attachment_counts_as_loaded(self):
        root = transcript()
        root["messages"].insert(0, {"type": "user", "skills": [{"name": "oversee", "id": "oversee",
            "text": '<skill_content name="oversee">\nactual instructions\n</skill_content>'}]})
        self.assertTrue(skill_loaded(root))
        self.assertFalse(grade([root], "explain", True, WORKER)["checks"]["no_skill_activation"])

    def test_final_response_excludes_intermediate_narration(self):
        root = transcript()
        root["messages"] = [{"type": "assistant", "content": [{"type": "text", "text": value}]}
                            for value in ["Workers: selected", "auditing", "Done. Tests passed."]]
        self.assertEqual(final_text(root), "Done. Tests passed.")
        self.assertFalse(grade([root], "parallel", True, WORKER)["checks"]["no_observed_routine_narration"])

    def test_unlisted_progress_phrase_also_fails_silence(self):
        root = transcript()
        root["messages"] = [{"type": "assistant", "content": [{"type": "text", "text": value}]}
                            for value in ["Implementation underway.", "Done."]]
        self.assertFalse(grade([root], "parallel", True, WORKER)["checks"]["no_observed_routine_narration"])

    def test_native_code_mode_nested_tool_records_are_recognized(self):
        root, child = transcript(), transcript("child", "root", created=2, idle=4)
        root["messages"][0]["content"] = [{"type": "tool", "name": "execute", "time": {"created": 5},
            "state": {"status": "completed", "metadata": {"toolCalls": [
                {"tool": "opencode.shell", "status": "completed", "input": {"command": "python -m unittest"}},
                {"tool": "opencode.shell", "status": "completed", "input": {"command": "git diff"}},
                {"tool": "opencode.session.status", "status": "completed", "input": {"id": "child"}}]}}}]
        checks = grade([root, child], "parallel", True, WORKER)["checks"]
        self.assertTrue(checks["manager_runs_checks_after_workers"])
        self.assertTrue(checks["manager_inspects_changes"])
        self.assertFalse(checks["no_observed_status_polling"])
        self.assertEqual(len(list(tools(root))), 4)

    def test_unrecorded_code_mode_tools_leave_polling_unknown(self):
        root = transcript()
        root["messages"][0]["content"] = [{"type": "tool", "name": "execute", "state": {
            "status": "completed", "input": {"code": "claimed no polling"}}}]
        self.assertIsNone(grade([root], "parallel", True, WORKER)["checks"]["no_observed_status_polling"])

    def test_review_refuses_modified_retained_project_before_running_code(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "run"
            case = source / "parallel/with_skill"
            project = case / "project"
            project.mkdir(parents=True)
            (project / "left.py").write_text("original")
            (case / "session.json").write_text(json.dumps({"snapshot_version": 2}))
            (case / "after.json").write_text(json.dumps(snapshot(project)))
            (case / "native.json").write_text("[]")
            (project / "left.py").write_text("modified")
            output = Path(folder) / "reviewed"
            with patch("evals.review.correctness") as check, self.assertRaisesRegex(ValueError, "differs"):
                review(source, output)
            check.assert_not_called()
            self.assertFalse(output.exists())


class ResolutionTests(unittest.TestCase):
    def test_arbitrary_multiword_family_and_case_normalized_effort(self):
        self.assertEqual(resolve([model()], "Worker Example 4.1", "MAX"), WORKER)

    def test_shorthand_uses_live_catalog(self):
        self.assertEqual(resolve([model(name="LUNA 9", model_id="luna-9")], "LUNA", "MAX")["id"], "luna-9")

    def test_dotted_version_order_cannot_be_silently_substituted(self):
        with self.assertRaises(Blocked):
            resolve([model(name="Example Worker V1.4", model_id="worker-v1.4")], "Example Worker 4.1", "MAX")

    def test_catalog_variant_spelling_is_preserved(self):
        self.assertEqual(resolve([model(variants=("Low", "MAX"))], "Example Worker 4.1", "max")["variant"], "MAX")

    def test_ambiguous_version_requires_choice(self):
        with self.assertRaises(Blocked):
            resolve([model(name="LUNA 9", model_id="luna-9"), model(name="LUNA 8", model_id="luna-8")], "LUNA", "MAX")

    def test_full_ids_preserve_case(self):
        with self.assertRaises(Blocked):
            resolve([model()], "Example/worker-v4.1", "MAX")

    def test_missing_variant_never_maps_to_highest(self):
        with self.assertRaises(Blocked):
            resolve([model(variants=("low", "high"))], "Example Worker 4.1", "MAX")

    def test_same_model_provider_preference(self):
        models = [model(provider="a"), model(provider="b")]
        self.assertEqual(resolve(models, "Example Worker 4.1", "MAX", "b")["providerID"], "b")
        with self.assertRaises(Blocked):
            resolve(models, "Example Worker 4.1", "MAX")

    def test_disabled_or_non_tool_models_not_dispatched(self):
        for bad in [{**model(), "enabled": False}, {**model(), "capabilities": {"tools": False}}]:
            with self.assertRaises(Blocked):
                resolve([bad], "Example Worker 4.1", "MAX")

    def test_snapshot_includes_untracked_contents(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "new.py").write_text("old")
            before = snapshot(root)
            (root / "new.py").write_text("new")
            self.assertNotEqual(before, snapshot(root))

    def test_snapshot_covers_skill_and_permission_configuration(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / ".opencode/skills/oversee").mkdir(parents=True)
            (root / ".opencode/skills/oversee/SKILL.md").write_text("original")
            before = snapshot(root)
            (root / ".opencode/skills/oversee/SKILL.md").write_text("changed")
            self.assertNotEqual(before, snapshot(root))
            self.assertEqual(snapshot(root, legacy=True), {})

    def test_preflight_cannot_create_sessions_or_output(self):
        class FakeAPI:
            version = "2-test"
            def __init__(self, service):
                pass
            def catalog(self, directory):
                return [model()]
            def operation(self, *args, **kwargs):
                raise AssertionError("Preflight called a session/model operation")
        with tempfile.TemporaryDirectory() as folder, patch("evals.run.OpenCode", FakeAPI), contextlib.redirect_stdout(io.StringIO()):
            output = Path(folder) / "results"
            result = main(["--manager", "Example Worker 4.1", "--manager-effort", "max", "--worker",
                           "Example Worker 4.1", "--worker-effort", "max", "--output", str(output), "--preflight"])
            self.assertEqual(result, 0)
            self.assertFalse(output.exists())

    def test_provider_failure_stops_before_next_pilot_session(self):
        class FakeAPI:
            version = "2-test"
            def __init__(self, service):
                pass
            def catalog(self, directory):
                return [model()]
        with tempfile.TemporaryDirectory() as folder, patch("evals.run.OpenCode", FakeAPI), \
                patch("evals.run.run_case", side_effect=Blocked("provider.auth: Reconnect")) as run, \
                contextlib.redirect_stderr(io.StringIO()):
            output = Path(folder) / "results"
            result = main(["--manager", "Example Worker 4.1", "--manager-effort", "max", "--worker",
                           "Example Worker 4.1", "--worker-effort", "max", "--output", str(output)])
            self.assertEqual(result, 2)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(json.loads((output / "blocked.json").read_text())["status"], "blocked")

    def test_focused_rerun_does_not_launch_other_cases_or_baselines(self):
        class FakeAPI:
            version = "2-test"
            def __init__(self, service):
                pass
            def catalog(self, directory):
                return [model()]
        report = {"correctness": {"tests_passed": True, "behavior_passed": True},
                  "orchestration": {"verified": True}}
        with tempfile.TemporaryDirectory() as folder, patch("evals.run.OpenCode", FakeAPI), \
                patch("evals.run.run_case", return_value=report) as run, contextlib.redirect_stdout(io.StringIO()):
            output = Path(folder) / "results"
            result = main(["--manager", "Example Worker 4.1", "--manager-effort", "max", "--worker",
                           "Example Worker 4.1", "--worker-effort", "max", "--output", str(output),
                           "--case", "parallel", "--case", "parallel", "--arm", "with-skill"])
            self.assertEqual(result, 0)
            run.assert_called_once()
            self.assertEqual(run.call_args.args[1]["name"], "parallel")
            self.assertIs(run.call_args.args[3], True)
            benchmark = json.loads((output / "benchmark.json").read_text())
            self.assertFalse(benchmark["paired"])
            self.assertEqual(benchmark["planned_sessions"], 1)

    def test_transport_timeout_reconnects_blocking_wait(self):
        api = object.__new__(OpenCode)
        with patch.object(api, "operation", side_effect=[TimeoutError(), None]) as operation:
            api.wait("session")
        self.assertEqual(operation.call_count, 2)
        self.assertTrue(all("wait" in call.args[0] for call in operation.call_args_list))

    def test_expired_deadline_does_not_retry(self):
        api = object.__new__(OpenCode)
        with patch.object(api, "operation") as operation, self.assertRaises(TimeoutError):
            api.wait("session", deadline=0)
        operation.assert_not_called()

    def test_deadline_expiry_after_plan_does_not_dispatch_implementation(self):
        clock, calls = [0], []
        class FakeAPI:
            version = "test"
            def catalog(self, directory):
                return [model()]
            def operation(self, name, *args, **kwargs):
                calls.append(name)
                return {"data": {"id": "root"}} if name == "session.create" else None
            def collect(self, session, deadline):
                clock[0] = 2
                return [transcript()]
        with tempfile.TemporaryDirectory() as folder:
            output, project = Path(folder) / "run", Path(folder) / "project"
            project.mkdir()
            with patch("evals.run.fixture", return_value=project), patch("evals.run.subprocess.run") as shell, \
                    patch("evals.run.time.monotonic", side_effect=lambda: clock[0]), \
                    patch("evals.run.retain_interrupted") as recovery:
                shell.return_value.stdout = ""
                with self.assertRaisesRegex(TimeoutError, "deadline"):
                    run_case(FakeAPI(), {"name": "plan-handoff", "prompt": "ready plan"}, output, False,
                             WORKER, WORKER, deadline_seconds=1)
                recovery.assert_called_once()
        self.assertEqual(calls.count("session.prompt"), 1)
        self.assertNotIn("session.switchAgent", calls)

    def test_cancellation_stops_dispatcher_before_children(self):
        api = object.__new__(OpenCode)
        with patch.object(api, "children", side_effect=lambda sid: [{"id": "child"}] if sid == "root" else []), patch.object(api, "operation") as operation:
            api.cancel("root")
        self.assertEqual([call.args[1] for call in operation.call_args_list], ["root", "child"])

    def test_parent_cancellation_failure_still_interrupts_children(self):
        api = object.__new__(OpenCode)
        with patch.object(api, "children", side_effect=lambda sid: [{"id": "child"}] if sid == "root" else []), \
                patch.object(api, "operation", side_effect=[Blocked("parent unavailable"), None]) as operation:
            errors = api.cancel("root")
        self.assertEqual([call.args[1] for call in operation.call_args_list], ["root", "child"])
        self.assertEqual(errors[0]["session"], "root")

    def test_partial_recovery_keeps_known_root_and_exports_grandchildren(self):
        api = object.__new__(OpenCode)
        def export(names, sid):
            if sid == "root":
                raise Blocked("root export unavailable")
            return {"data": transcript(sid, "root")}
        def children(sid):
            return [{"id": "child"}] if sid == "root" else [{"id": "grandchild"}] if sid == "child" else []
        with tempfile.TemporaryDirectory() as folder, patch.object(api, "cancel", return_value=[]), \
                patch.object(api, "operation", side_effect=export), patch.object(api, "children", side_effect=children):
            retain_interrupted(api, "root", Path(folder), [transcript()])
            raw = json.loads((Path(folder) / "native.json").read_text())
            self.assertEqual([t["info"]["id"] for t in raw], ["root", "child", "grandchild"])
            self.assertEqual(json.loads((Path(folder) / "interruption.json").read_text())["errors"][0]["operation"], "export")
