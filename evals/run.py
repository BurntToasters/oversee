"""Reproducible paired OpenCode v2 pilot. No credentials enter output artifacts."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

if __package__:
    from .evidence import final_text, grade, plan_phase_checks, total_usage
else:
    from evidence import final_text, grade, plan_phase_checks, total_usage

ROOT = Path(__file__).resolve().parents[1]


class Blocked(Exception):
    pass


def provider_blocker(transcripts):
    for transcript in transcripts:
        for message in transcript.get("messages", []):
            error = message.get("error", {})
            if error.get("type", "").startswith("provider."):
                return {"type": error["type"], "message": error.get("message", "Provider rejected the request.")}
    return None


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def words(value):
    return sorted(re.findall(r"[a-z]+|\d+(?:\.\d+)*", re.sub(r"\bv(?=\d)", "", value.lower())))


def resolve(models, name, effort, provider=None):
    available = [m for m in models if m.get("enabled") is True and m.get("capabilities", {}).get("tools") is True]
    if "/" in name:
        matches = [m for m in available if m["providerID"] + "/" + m["id"] == name]
    else:
        exact = [m for m in available if name == m["id"] or words(name) == words(m.get("name", ""))]
        matches = exact or [m for m in available if set(words(name)) <= set(words(m.get("name", "")))]
    if provider and any(m["providerID"] == provider for m in matches):
        matches = [m for m in matches if m["providerID"] == provider]
    if len(matches) != 1:
        raise Blocked(f"Model {name!r}: expected one live match, found {len(matches)}; supply a full provider/model ID.")
    model = matches[0]
    variants = [v["id"] for v in model.get("variants", [])]
    matching = [v for v in variants if v == effort] or [v for v in variants if v.casefold() == effort.casefold()]
    if len(matching) != 1:
        raise Blocked(f"Model {name!r} does not offer requested effort {effort!r}.")
    return {"providerID": model["providerID"], "id": model["id"], "variant": matching[0]}


def selector(model):
    return f"{model['providerID']}/{model['id']}#{model['variant']}"


def execution_timeout(deadline):
    remaining = 60 if deadline is None else min(60, deadline - time.monotonic())
    if remaining <= 0:
        raise TimeoutError("Pilot deadline expired.")
    return remaining


class OpenCode:
    def __init__(self, service_file):
        service = json.loads(service_file.read_text(encoding="utf-8"))
        self.url = service["url"].rstrip("/")
        parsed = urllib.parse.urlparse(self.url)
        if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
            raise Blocked("Service discovery must point to a local OpenCode service.")
        self.auth = "Basic " + base64.b64encode(("opencode:" + service["password"]).encode()).decode()
        self.version = service["version"]
        schema = self.request("GET", "/openapi.json")
        self.operations = {op["operationId"]: (method.upper(), path)
                           for path, methods in schema["paths"].items() for method, op in methods.items()
                           if isinstance(op, dict) and "operationId" in op}

    def request(self, method, path, data=None, query=None, timeout=60):
        if query:
            path += "?" + urllib.parse.urlencode(query)
        request = urllib.request.Request(self.url + path, method=method,
                                        data=None if data is None else json.dumps(data).encode(),
                                        headers={"Authorization": self.auth, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read()
                return json.loads(body) if body else None
        except urllib.error.HTTPError as error:
            # Never include headers, service-file contents, or arbitrary remote error bodies.
            raise Blocked(f"OpenCode {method} {path.split('?')[0]} returned HTTP {error.code}.") from None

    def operation(self, names, session=None, data=None, query=None, timeout=60):
        name = next((n for n in names.split("|") if n in self.operations), None)
        if name is None:
            raise Blocked(f"OpenCode {self.version} lacks required operation: {names}")
        method, path = self.operations[name]
        if session:
            path = path.replace("{sessionID}", session)
        return self.request(method, path, data, query, timeout)

    def catalog(self, directory):
        return self.operation("model.list", query={"location[directory]": str(directory)})["data"]

    def wait(self, session, deadline=None):
        # Reconnect a blocking wait if its transport times out; never query session status.
        while True:
            remaining = None if deadline is None else deadline - time.monotonic()
            if remaining is not None and remaining <= 0:
                raise TimeoutError("Pilot deadline expired.")
            try:
                self.operation("experimental.session.wait|session.wait", session,
                               timeout=60 if remaining is None else min(60, remaining))
                return
            except (TimeoutError, socket.timeout):
                if deadline is not None and time.monotonic() >= deadline:
                    raise TimeoutError("Pilot deadline expired.") from None

    def children(self, session):
        query = {"parentID": session, "limit": "100", "order": "asc"}
        children = []
        while True:
            page = self.operation("session.list", query=query)
            children.extend(page["data"])
            cursor = page.get("cursor", {}).get("next")
            if not cursor:
                return children
            query = {"parentID": session, "limit": "100", "cursor": cursor}

    def collect(self, session, deadline=None):
        self.wait(session, deadline)
        descendants = []
        for child in self.children(session):
            descendants.extend(self.collect(child["id"], deadline))
        if descendants:
            self.wait(session, deadline)
        root = self.operation("experimental.session.export|session.export", session)["data"]
        return [root, *descendants]

    def cancel(self, session):
        errors, seen = [], set()

        def interrupt(sid):
            if sid in seen:
                return
            seen.add(sid)
            # Stop the dispatcher before discovering and interrupting its descendants.
            try:
                self.operation("session.interrupt", sid)
            except (Blocked, OSError) as error:
                errors.append({"session": sid, "operation": "interrupt", "error": str(error)})
            try:
                for child in self.children(sid):
                    interrupt(child["id"])
            except (Blocked, OSError) as error:
                errors.append({"session": sid, "operation": "children", "error": str(error)})

        interrupt(session)
        return errors


def retain_interrupted(api, session, output, retained):
    """Best-effort cleanup must not replace the original failure or lose known evidence."""
    errors = api.cancel(session)
    transcripts = {t["info"]["id"]: t for t in retained}
    seen = set()

    def capture(sid):
        if sid in seen:
            return
        seen.add(sid)
        try:
            transcripts[sid] = api.operation("experimental.session.export|session.export", sid)["data"]
        except (Blocked, OSError) as error:
            errors.append({"session": sid, "operation": "export", "error": str(error)})
        try:
            children = api.children(sid)
        except (Blocked, OSError) as error:
            errors.append({"session": sid, "operation": "children", "error": str(error)})
            return
        for child in children:
            capture(child["id"])

    capture(session)
    write_json(output / "native.json", list(transcripts.values()))
    write_json(output / "interruption.json", {"interruption_requested": True, "errors": errors,
               "limitation": "Interruption requests do not prove every worker has stopped."})


def snapshot(directory, *, legacy=False):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob("*") if p.is_file()
            and not any(s in ((".git", ".opencode", "__pycache__") if legacy else (".git", "__pycache__"))
                        for s in p.relative_to(directory).parts)}


def fixture(output, case, with_skill):
    project = output / "project"
    shutil.copytree(ROOT / "evals" / "fixtures" / case["fixture"], project)
    (project / ".gitignore").write_text("__pycache__/\n*.pyc\n.notes.json\n.opencode/\nopencode.json\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(project)], check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=project, check=True, capture_output=True)
    if with_skill:
        skill = project / ".opencode/skills/oversee"
        skill.mkdir(parents=True)
        shutil.copyfile(ROOT / "SKILL.md", skill / "SKILL.md")
        shutil.copytree(ROOT / "references", skill / "references")
    # Same explicit permissions in both arms; no --auto or changes to the real profile.
    rules = [{"action": action, "resource": "*", "effect": "deny"}
             for action in ["external_directory", "webfetch", "websearch", "shell"]]
    rules += [{"action": "shell", "resource": command, "effect": "allow"}
              for command in ["python *", "python3 *", "git status*", "git diff*", "git ls-files*"]]
    config = {"$schema": "https://opencode.ai/config.json", "permissions": rules,
              "agents": {"general": {"permissions": rules}, "build": {"permissions": rules}}}
    write_json(project / "opencode.json", config)
    return project


def correctness(project, case):
    tests = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
                           cwd=project, capture_output=True, text=True, timeout=60)
    if case == "parallel":
        probe = "from left import normalize_tag; from right import parse_limit; assert normalize_tag('  AbC  ') == 'abc'\nfor x in ['0','-1']:\n try: parse_limit(x)\n except ValueError: pass\n else: raise AssertionError(x)\nassert parse_limit('2') == 2"
    elif case == "plan-handoff":
        probe = "import store,tempfile,subprocess,sys; from pathlib import Path\nwith tempfile.TemporaryDirectory() as t:\n p=Path(t)/'n.json'; store.add_note('Milk','body',p); store.add_note('Bread','body',p); assert [n['title'] for n in store.find_notes('MIL',p)] == ['Milk']; assert len(store.find_notes('',p)) == 2; r=subprocess.run([sys.executable,'notes.py','--file',str(p),'search','MIL'],capture_output=True,text=True); assert r.returncode == 0 and r.stdout.strip() == '1: Milk'"
    else:
        probe = "import store; assert store.DEFAULT_PATH.name == '.notes.json'"
    behavior = subprocess.run([sys.executable, "-B", "-c", probe], cwd=project, capture_output=True, text=True, timeout=60)
    return {"tests_passed": tests.returncode == 0, "behavior_passed": behavior.returncode == 0,
            "test_output": tests.stdout + tests.stderr, "behavior_output": behavior.stdout + behavior.stderr}


def run_case(api, case, output, with_skill, manager, worker, deadline_seconds=None):
    output.mkdir(parents=True)
    project = fixture(output, case, with_skill)
    # Verify catalog at the actual isolated location, not only the source repository.
    for setting in [manager, worker]:
        resolve(api.catalog(project), f"{setting['providerID']}/{setting['id']}", setting["variant"])
    before = snapshot(project)
    write_json(output / "baseline.json", before)
    write_json(output / "baseline-git.json", {
        name: subprocess.run(["git", *args], cwd=project, capture_output=True, text=True, check=True).stdout
        for name, args in {"status": ["status", "--porcelain=v1", "-uall"],
                           "staged": ["diff", "--cached"], "unstaged": ["diff"],
                           "untracked": ["ls-files", "--others", "--exclude-standard"]}.items()})
    phase = None
    agent = "plan" if case["name"] == "plan-handoff" else "build"
    session = api.operation("session.create", data={"location": {"directory": str(project)},
                            "title": "oversee-eval " + case["name"] + (" with skill" if with_skill else " baseline"),
                            "agent": agent, "model": manager})["data"]["id"]
    write_json(output / "session.json", {"id": session, "manager": manager, "worker": worker,
                                        "version": api.version, "with_skill": with_skill, "snapshot_version": 2})
    started = time.monotonic()
    deadline = None if deadline_seconds is None else started + deadline_seconds
    raw = []
    try:
        prompt = case["prompt"].replace("{worker}", selector(worker))
        if not with_skill:
            prompt = prompt.replace("/oversee " + selector(worker) + ":", "").replace("/oversee " + selector(worker), "")
            prompt += ("\nDo not delegate." if case["name"] == "explain" else
                       "\nImplement directly yourself after execution is enabled. Do not delegate.")
        prompt += "\nWork only in this fixture. Do not commit, push, install dependencies, change global settings, or access other projects."
        write_json(output / "prompt.json", {"text": prompt})
        attachment = []
        if with_skill and case["name"] != "explain":
            available = api.operation("skill.list", query={"location[directory]": str(project)})["data"]
            skill = next((s for s in available if s.get("name") == "oversee" and
                          str(project).replace("\\", "/").lower() in json.dumps(s).replace("\\\\", "/").lower()), None)
            if skill is None:
                raise Blocked("Isolated oversee skill was not discovered; refusing a global substitute.")
            attachment = [{"id": skill["id"]}]
        api.operation("session.prompt", session, data={"text": prompt, "skills": attachment},
                      timeout=execution_timeout(deadline))
        raw = api.collect(session, deadline)
        failure = provider_blocker(raw)
        if failure:
            raise Blocked(f"{failure['type']}: {failure['message']}")
        if case["name"] == "plan-handoff":
            phase = plan_phase_checks(raw, snapshot(project) == before, worker, manager)
            write_json(output / "plan-phase.json", {"checks": phase, "transcripts": raw})
            if any(v is False for v in phase.values()):
                raise Blocked("Plan phase modified project files, started implementing workers, or used the worker choice.")
            api.operation("session.switchAgent", session, data={"agent": "build"}, timeout=execution_timeout(deadline))
            api.operation("session.prompt", session, data={"text": "Plan approved. The host is now in Build mode. Continue the prepared implementation with the retained worker choice; do not invoke the skill again."},
                          timeout=execution_timeout(deadline))
            raw = api.collect(session, deadline)
            failure = provider_blocker(raw)
            if failure:
                raise Blocked(f"{failure['type']}: {failure['message']}")
    except (KeyboardInterrupt, TimeoutError, Blocked, OSError):
        try:
            retain_interrupted(api, session, output, raw)
        except (Blocked, OSError) as cleanup_error:
            print("Partial evidence recovery failed: " + str(cleanup_error), file=sys.stderr)
        raise
    write_json(output / "native.json", raw)
    (output / "final_response.md").write_text(final_text(raw[0]) + "\n", encoding="utf-8")
    after = snapshot(project)
    write_json(output / "after.json", after)
    proof = correctness(project, case["name"])
    if case["name"] == "explain":
        proof["project_unchanged"] = before == after
    report = {"case": case["name"], "with_skill": with_skill,
              "correctness": proof, "orchestration": grade(raw, case["name"], with_skill, worker, phase),
              "elapsed_seconds": time.monotonic() - started, "usage": total_usage(raw)}
    report["orchestration"]["checks"]["exact_manager_settings"] = any(
        m.get("type") == "assistant" for m in raw[0]["messages"]) and all(
        m.get("model") == manager for m in raw[0]["messages"] if m.get("type") == "assistant")
    report["orchestration"]["verified"] = all(v is True for v in report["orchestration"]["checks"].values())
    write_json(output / "result.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service-file", type=Path, default=Path.home() / ".local/state/opencode/service.json")
    parser.add_argument("--manager", required=True)
    parser.add_argument("--manager-effort", required=True)
    parser.add_argument("--worker", required=True)
    parser.add_argument("--worker-effort", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight", action="store_true", help="Resolve live settings without creating sessions or calling models")
    parser.add_argument("--case", action="append", choices=("parallel", "plan-handoff", "explain"),
                        help="Select pilot cases for a focused rerun; default is all three")
    parser.add_argument("--arm", choices=("both", "with-skill", "without-skill"), default="both",
                        help="Default is paired runs; a single arm is a follow-up, not a paired benchmark")
    parser.add_argument("--deadline-seconds", type=float, help="Explicit per-session pilot deadline; none by default")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error("Run output must be outside the repository.")
    if output.exists():
        parser.error("Use a new output directory; existing evidence is never overwritten.")
    if args.deadline_seconds is not None and args.deadline_seconds <= 0:
        parser.error("Deadline must be positive.")
    try:
        api = OpenCode(args.service_file)
        models = api.catalog(ROOT)
        manager = resolve(models, args.manager, args.manager_effort)
        worker = resolve(models, args.worker, args.worker_effort, manager["providerID"])
        preflight = {"version": api.version, "manager": manager, "worker": worker}
        if args.preflight:
            print(json.dumps(preflight, indent=2))
            return 0
        output.mkdir(parents=True)
        write_json(output / "preflight.json", preflight)
        cases = json.loads((ROOT / "evals/evals.json").read_text(encoding="utf-8"))
        results = []
        selected = list(dict.fromkeys(args.case or cases["pilot"]))
        arms = [False, True] if args.arm == "both" else [args.arm == "with-skill"]
        for name in selected:
            case = next(c for c in cases["evals"] if c["name"] == name)
            for enabled in arms:
                folder = output / name / ("with_skill" if enabled else "without_skill")
                results.append(run_case(api, case, folder, enabled, manager, worker, args.deadline_seconds))
                print(json.dumps({"case": name, "with_skill": enabled, "complete": True}), flush=True)
                write_json(output / "benchmark.json", {"runs": results, "repeats": 1,
                           "planned_sessions": len(selected) * len(arms), "paired": args.arm == "both",
                           "limitation": "Small pilot; no general savings guarantee. Single-arm reruns cannot establish a comparison. Unknown metrics remain null."})
        return 0 if all(r["correctness"]["tests_passed"] and r["correctness"]["behavior_passed"] and
                        r["correctness"].get("project_unchanged", True) and r["orchestration"]["verified"] for r in results) else 1
    except (Blocked, OSError, TimeoutError, KeyboardInterrupt) as error:
        message = str(error) or "Pilot cancelled."
        if output.exists():
            write_json(output / "blocked.json", {"status": "blocked", "reason": message})
        print("Blocked: " + message, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
