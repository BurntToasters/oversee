import unittest
from unittest.mock import patch

from evals.codex_run import Codex, export, resolve
from evals.codex_review import grade, usage
from evals.run import Blocked


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
