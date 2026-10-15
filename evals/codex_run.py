"""Isolated Codex app-server smoke tests with native evidence; no profile installation."""

import argparse
import json
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time

from .run import ROOT, Blocked, correctness, snapshot, write_json


def resolve(models, name, effort):
    matches = [m for m in models if name in (m.get("id"), m.get("model"))]
    if len(matches) != 1 or effort not in [e["reasoningEffort"] for e in matches[0]["supportedReasoningEfforts"]]:
        raise Blocked(f"Unsupported or ambiguous Codex model/effort: {name} {effort}")
    return {"model": matches[0]["model"], "effort": effort}


class Codex:
    def __init__(self, executable):
        self.events, self.active, self.sequence = [], {}, 0
        self.inbox = queue.Queue()
        self.process = subprocess.Popen([executable, "app-server", "--stdio"], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                        text=True, encoding="utf-8")
        threading.Thread(target=self._reader, daemon=True).start()
        try:
            self.request("initialize", {"clientInfo": {"name": "oversee-harness-eval", "version": "1"},
                                       "capabilities": {"experimentalApi": True}})
            self.send({"method": "initialized"})
        except BaseException:
            self.close()
            raise

    def _reader(self):
        try:
            for line in self.process.stdout:
                self.inbox.put(json.loads(line))
        except (ValueError, OSError) as error:
            self.inbox.put(error)
        finally:
            self.inbox.put(EOFError("Codex app-server closed its output."))

    def send(self, message):
        self.events.append({"direction": "sent", "time": time.time(), "message": message})
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def receive(self, timeout=None):
        try:
            message = self.inbox.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError("Codex protocol request timed out.") from None
        if isinstance(message, Exception):
            raise message
        self.events.append({"direction": "received", "time": time.time(), "message": message})
        method, params = message.get("method"), message.get("params", {})
        if method == "turn/started":
            self.active[params["threadId"]] = params["turn"]["id"]
        elif method == "turn/completed":
            self.active.pop(params["threadId"], None)
        if method and "id" in message:
            # A noninteractive test cannot grant a surfaced permission or answer for the user.
            self.send({"id": message["id"], "error": {"code": -32601,
                       "message": "Interactive request unsupported by this test driver; no permission granted."}})
        return message

    def request(self, method, params, *, timeout=60):
        self.sequence += 1
        identifier = self.sequence
        deadline = time.monotonic() + timeout
        self.send({"id": identifier, "method": method, "params": params})
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Codex protocol request timed out.")
            message = self.receive(timeout=remaining)
            if message.get("id") == identifier and "method" not in message:
                if "error" in message:
                    raise Blocked(f"Codex {method}: {message['error'].get('message', 'Request rejected')}")
                return message["result"]

    def wait(self, thread, turn):
        # Consume completion notifications, never issue thread-status probes.
        def completed(event):
            message = event["message"]
            params = message.get("params", {})
            return (message.get("method") == "turn/completed" and params.get("threadId") == thread
                    and params.get("turn", {}).get("id") == turn)
        while not any(completed(event) for event in self.events):
            self.receive()
        event = next(e for e in reversed(self.events) if completed(e))
        if event["message"]["params"]["turn"]["status"] != "completed":
            raise Blocked("Codex turn did not complete successfully; inspect native events.")

    def close(self):
        errors = []
        attempted = set()
        deadline = time.monotonic() + 8
        while True:
            pending = [(thread, turn) for thread, turn in self.active.items()
                       if (thread, turn) not in attempted]
            if not pending:
                break
            if time.monotonic() >= deadline:
                errors.append("Cancellation deadline reached with active Codex turns remaining.")
                break
            thread, turn = pending[0]
            attempted.add((thread, turn))
            try:
                self.request("turn/interrupt", {"threadId": thread, "turnId": turn},
                             timeout=min(3, max(0.01, deadline - time.monotonic())))
            except Exception as error:
                errors.append(f"Interrupt {thread}: {error}")
        try:
            self.process.stdin.close()
        except Exception as error:
            errors.append(f"Close stdin: {error}")
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                self.process.terminate()
            except Exception as error:
                errors.append(f"Terminate process: {error}")
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    self.process.kill()
                except Exception as error:
                    errors.append(f"Kill process: {error}")
                try:
                    self.process.wait(timeout=2)
                except Exception as error:
                    errors.append(f"Wait after kill: {error}")
            except Exception as error:
                errors.append(f"Wait after terminate: {error}")
        except Exception as error:
            errors.append(f"Wait process: {error}")
        return errors


def stage(output, case):
    project = output / "project"
    shutil.copytree(ROOT / "evals/fixtures" / case["fixture"], project)
    skill = project / ".agents/skills/oversee"
    skill.mkdir(parents=True)
    shutil.copyfile(ROOT / "SKILL.md", skill / "SKILL.md")
    shutil.copytree(ROOT / "references", skill / "references")
    (project / ".gitignore").write_text("__pycache__/\n*.pyc\n.notes.json\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(project)], check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=project, check=True, capture_output=True)
    return project, skill / "SKILL.md"


def export(api, root, events=None):
    """Read only this run's root/descendants after completion, including per-turn contexts."""
    ids = [root]
    for event in api.events if events is None else events:
        msg = event["message"]
        params = msg.get("params", {})
        item = params.get("item", {})
        if params.get("threadId"):
            ids.append(params["threadId"])
        if item.get("agentThreadId"):
            ids.append(item["agentThreadId"])
        ids.extend(item.get("receiverThreadIds", []))
    records = []
    for identifier in dict.fromkeys(ids):
        thread = api.request("thread/read", {"threadId": identifier, "includeTurns": True})["thread"]
        contexts = []
        path = thread.get("path")
        if path:
            for line in Path(path).read_text(encoding="utf-8").splitlines():
                record = json.loads(line)
                if record.get("type") == "turn_context":
                    contexts.append(record)
        records.append({"thread": thread, "turn_contexts": contexts})
    return records


def run_case(executable, case, output, manager, worker):
    output.mkdir(parents=True)
    project, skill = stage(output, case)
    before = snapshot(project)
    write_json(output / "baseline.json", before)
    api, raw = Codex(executable), []
    started = time.monotonic()
    root = None
    try:
        # Discover the actual project-local payload; never substitute a global copy.
        listing = api.request("skills/list", {"cwds": [str(project)], "forceReload": True})
        matches = [s for group in listing["data"] for s in group["skills"]
                   if s["name"] == "oversee" and Path(s["path"]).resolve() == skill.resolve() and s["enabled"]]
        if len(matches) != 1:
            raise Blocked("Codex did not discover the isolated oversee payload exactly once.")
        created = api.request("thread/start", {"cwd": str(project), "model": manager["model"],
            "approvalPolicy": "never", "sandbox": "workspace-write", "allowProviderModelFallback": False,
            "historyMode": "legacy", "config": {"model_reasoning_effort": manager["effort"]}})
        root = created["thread"]["id"]
        write_json(output / "session.json", {"root": root, "manager": manager, "worker": worker,
                                               "created": created})
        prompt = case["prompt"].replace("{worker}", f"{worker['model']} {worker['effort']}")
        prompt = prompt.replace("/oversee", "$oversee")
        prompt += "\nWork only inside this fixture. No commits, pushes, installs, global changes, external services, or other projects."
        write_json(output / "prompt.json", {"text": prompt})
        input_items = [{"type": "text", "text": prompt}]
        if case["name"] != "explain":
            input_items.append({"type": "skill", "name": "oversee", "path": str(skill)})
        plan = case["name"] == "plan-handoff"
        def turn(items, planning):
            return api.request("turn/start", {"threadId": root, "input": items,
                "collaborationMode": {"mode": "plan" if planning else "default", "settings": {
                    "model": manager["model"], "reasoning_effort": manager["effort"], "developer_instructions": None}},
                "sandboxPolicy": {"type": "readOnly"} if planning else {"type": "workspaceWrite",
                    "writableRoots": [str(project)], "networkAccess": False,
                    "excludeSlashTmp": True, "excludeTmpdirEnvVar": True}})["turn"]["id"]
        identifier = turn(input_items, plan)
        api.wait(root, identifier)
        if plan:
            raw = export(api, root)
            prepared = snapshot(project)
            checks = {"unchanged": prepared == before, "no_workers": len(raw) == 1}
            write_json(output / "plan-phase.json", {"checks": checks, "snapshot": prepared, "transcripts": raw})
            if not all(checks.values()):
                raise Blocked("Plan phase changed project or spawned workers.")
            identifier = turn([{"type": "text", "text": "Plan approved. The host now enables execution in Default mode. Continue with the retained worker choice; do not invoke the skill again."}], False)
            api.wait(root, identifier)
        raw = export(api, root)
        proof = correctness(project, case["name"])
        if case["name"] == "explain":
            proof["project_unchanged"] = before == snapshot(project)
        report = {"case": case["name"], "correctness": proof,
                  "elapsed_seconds": time.monotonic() - started,
                  "orchestration": "Native evidence retained; requires Codex-specific review, not the OpenCode grader.",
                  "cost_usd": None}
        write_json(output / "result.json", report)
        return report
    finally:
        original_error = sys.exc_info()[1]
        cleanup_errors, persistence_errors = [], []
        try:
            cleanup_errors.extend(api.close() or [])
        except BaseException as error:
            cleanup_errors.append(f"Close Codex API: {error}")
        evidence = (("native.json", lambda: raw), ("events.json", lambda: api.events),
                    ("after.json", lambda: snapshot(project)))
        for name, get_value in evidence:
            try:
                write_json(output / name, get_value())
            except BaseException as error:
                persistence_errors.append(f"Persist {name}: {error}")
        issues = [*cleanup_errors, *persistence_errors]
        if issues:
            try:
                write_json(output / "cleanup-errors.json", issues)
            except BaseException as error:
                persistence_errors.append(f"Persist cleanup-errors.json: {error}")
        if persistence_errors and original_error is None:
            result_path = output / "result.json"
            try:
                result_path.unlink()
            except FileNotFoundError:
                pass
            except BaseException:
                try:
                    write_json(result_path, {"status": "evidence_incomplete", "errors": persistence_errors})
                except BaseException:
                    pass
            raise OSError("Evidence persistence failed: " + "; ".join(persistence_errors))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", default=shutil.which("codex"))
    parser.add_argument("--manager", required=True)
    parser.add_argument("--manager-effort", required=True)
    parser.add_argument("--worker", required=True)
    parser.add_argument("--worker-effort", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", action="append", choices=("parallel", "plan-handoff", "explain"))
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if not args.executable or output.exists() or output == ROOT or ROOT in output.parents:
        parser.error("Need Codex and a new output directory outside the repository.")
    api = None
    try:
        api = Codex(args.executable)
        catalog = api.request("model/list", {"includeHidden": False})["data"]
        manager, worker = resolve(catalog, args.manager, args.manager_effort), resolve(catalog, args.worker, args.worker_effort)
        api.close()
        api = None
        if args.preflight:
            print(json.dumps({"manager": manager, "worker": worker}))
            return 0
        output.mkdir(parents=True)
        write_json(output / "preflight.json", {"manager": manager, "worker": worker,
            "cli_version": subprocess.run([args.executable, "--version"], capture_output=True, text=True, check=True).stdout.strip()})
        cases = json.loads((ROOT / "evals/evals.json").read_text(encoding="utf-8"))["evals"]
        results = []
        for name in dict.fromkeys(args.case or ["explain", "parallel", "plan-handoff"]):
            case = next(c for c in cases if c["name"] == name)
            result = run_case(args.executable, case, output / name, manager, worker)
            results.append(result)
            write_json(output / "results.json", results)
            print(json.dumps({"case": name, "behavior_passed": result["correctness"]["behavior_passed"]}), flush=True)
        return 0 if all(r["correctness"]["tests_passed"] and r["correctness"]["behavior_passed"] and
                        r["correctness"].get("project_unchanged", True) for r in results) else 1
    except (Blocked, OSError, ValueError, EOFError, TimeoutError, KeyboardInterrupt) as error:
        if output.exists():
            write_json(output / "blocked.json", {"reason": str(error) or "Cancelled"})
        print("Blocked: " + (str(error) or "Cancelled"), file=sys.stderr)
        return 2
    finally:
        if api:
            api.close()


if __name__ == "__main__":
    raise SystemExit(main())
