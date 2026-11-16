"""Headless Cursor CLI (`agent -p`) oversee runs with native stream-json evidence; nothing installed globally."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

from .claude_run import SCOPE, WAITING, load_events, stage, workspace
from .evidence import inspects_diff, interpreter_missing, is_check_command, mentions
from .run import PYTHON, ROOT, fill_prompt, snapshot, write_json

SKILL_DIR = ".cursor/skills/oversee"
# Test runs, the notes CLI, read-only git, and the baseline commands; no `--force` or `--yolo`, ever.
ALLOW = [*[f"Shell({python}:{flags}{target}*)" for python in ("python", "python3")
           for flags in ("", "-B ") for target in ("-m unittest", "notes.py")],
         *[f"Shell(git:{command}*)" for command in ("status", "diff", "--no-pager diff", "rev-parse", "log",
                                                    "stash create", "hash-object", "ls-files")]]
DENY = ["Shell(rm)", *[f"Shell(git:{command}*)" for command in ("commit", "push", "reset", "checkout", "stash push",
                                                               "clean", "restore")]]
FORBIDDEN_FLAGS = ("--force", "--yolo", "-f")
AGENT_CONSENT = "\nYou may create a project agent profile for the worker if the Task tool cannot name it; keep it out of the deliverable."


def command(executable, prompt, manager):
    args = [executable, "-p", prompt, "--model", manager, "--output-format", "stream-json", "--trust"]
    if any(arg in FORBIDDEN_FLAGS for arg in args):
        raise ValueError("Refusing an auto-approval flag.")
    return args


def _tool(event):
    call = event.get("tool_call", {})
    kind = next((k for k in call if k.endswith("ToolCall")), "")
    return kind, call.get(kind, {}), call


def grade(events, case, worker, project):
    """Grade one run from Cursor stream-json events. `worker` is the model ID the prompt named."""
    texts, tasks, shells, reads = [], {}, [], []
    result = next((e for e in events if e.get("type") == "result"), {})
    for index, event in enumerate(events):
        if event.get("type") == "assistant":
            text = "".join(p.get("text", "") for p in event["message"].get("content", [])).strip()
            if text:
                texts.append((index, text))
        elif event.get("type") == "tool_call":
            kind, body, call = _tool(event)
            args, ident = body.get("args", {}), event.get("call_id") or call.get("toolCallId")
            if kind == "taskToolCall":
                task = tasks.setdefault(ident, {"args": args, "start": index})
                task["started_ms"] = task.get("started_ms") or call.get("startedAtMs")
                if event.get("subtype") == "completed":
                    task.update(end=index, ended_ms=call.get("completedAtMs"), ok="success" in body.get("result", {}))
            elif kind == "shellToolCall" and event.get("subtype") == "completed":
                outcome = body.get("result", {})
                success = outcome.get("success", {})
                code = success.get("exitCode") if success else None
                output = str(success.get("stdout", "")) + str(success.get("stderr", ""))
                state = None if "rejected" in outcome or interpreter_missing(code, output) else code == 0
                shells.append((index, args.get("command", ""), state, output))
            elif kind in ("readToolCall", "grepToolCall", "globToolCall") and event.get("subtype") == "started":
                reads.append(str(args.get("path") or args.get("targetDirectory") or ""))
    workers = sorted(tasks.values(), key=lambda t: t["start"])
    # Compare forward-slash forms: Cursor reports absolute paths, and Windows paths use backslashes.
    roots = tuple({str(project).replace("\\", "/"), Path(project).as_posix(), Path(project).resolve().as_posix()})
    skill_reads = [p for p in (r.replace("\\", "/") for r in reads) if "/skills/oversee/" in p]
    checks = {"skill_from_fixture": all(p.startswith(roots) for p in skill_reads),
              "no_transcript_reads": not any("agent-transcripts" in p for p in reads)}
    report = {"usage": result.get("usage"), "duration_ms": result.get("duration_ms"), "manager_model": next(
        (e.get("model") for e in events if e.get("subtype") == "init"), None), "manager_texts": [t for _, t in texts],
        "workers": [{k: w["args"].get(k) for k in ("description", "model", "subagentType")} for w in workers],
        "manager_commands": [c for _, c, _, _ in shells], "skill_reads": skill_reads}
    if case == "explain":
        checks.update(no_workers=not workers, answered=bool(texts) and result.get("subtype") == "success")
        return {"verified": all(checks.values()), "checks": checks, **report}
    first = workers[0]["start"] if workers else float("inf")
    last = max((w.get("end", float("inf")) for w in workers), default=float("inf"))
    before = [t for i, t in texts if i < first]
    final = texts[-1][0] if texts else None
    latest = {}
    for index, cmd, state, _ in shells:
        if is_check_command(cmd) and index > last and state is not None:
            latest[cmd] = state
    checks.update(
        two_workers=len(workers) >= 2,
        exact_worker_model=bool(workers) and all(w["args"].get("model") == worker for w in workers),
        worker_choice_before_dispatch=len(before) == 1 and mentions(before[0], worker),
        no_routine_narration=all(WAITING.match(t) for i, t in texts if first < i and i != final),
        manager_runs_successful_checks=bool(latest) and all(latest.values()),
        manager_inspects_changes=any(inspects_diff(cmd) and i > last and state for i, cmd, state, _ in shells),
        final_report=final is not None and final > last)
    if case == "parallel":
        spans = [(w.get("started_ms"), w.get("ended_ms")) for w in workers]
        checks["parallel_overlap"] = len(spans) >= 2 and all(s is not None for pair in spans for s in pair) and any(
            a < d and c < b for i, (a, b) in enumerate(spans) for c, d in spans[i + 1:])
    else:
        checks["dependent_workers_sequenced"] = len(workers) >= 2 and all(
            a.get("end", float("inf")) < b["start"] for a, b in zip(workers, workers[1:]))
        checks["manager_check_between_workers"] = len(workers) >= 2 and any(
            workers[0].get("end", float("inf")) < i < workers[1]["start"] and state is True
            for i, cmd, state, _ in shells if is_check_command(cmd))
    return {"verified": all(checks.values()), "checks": checks, **report}


def run_case(executable, case, output, manager, worker):
    output.mkdir(parents=True)
    project = stage(output, case, skill_dir=SKILL_DIR)
    write_json(project / ".cursor/cli.json", {"permissions": {"allow": ALLOW, "deny": DENY}})
    before, head = snapshot(project), subprocess.run(["git", "rev-parse", "HEAD"], cwd=project, capture_output=True,
                                                     text=True, check=True).stdout.strip()
    prompt = fill_prompt(case["prompt"], worker) + ("" if case["name"] == "explain" else AGENT_CONSENT) + SCOPE
    write_json(output / "prompt.json", {"text": prompt})
    started = time.monotonic()
    with (output / "events.jsonl").open("w", encoding="utf-8") as out, \
            (output / "stderr.txt").open("w", encoding="utf-8") as err:
        code = subprocess.run(command(executable, prompt, manager), cwd=project, stdout=out, stderr=err).returncode
    graded = grade(load_events(output / "events.jsonl"), case["name"], worker, project)
    proof = workspace(project, case["name"], head)
    if case["name"] == "explain":
        proof["project_unchanged"] = before == snapshot(project)
    report = {"case": case["name"], "exit": code, "elapsed_seconds": round(time.monotonic() - started, 1),
              "correctness": proof, "orchestration": graded}
    write_json(output / "result.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", default=shutil.which("agent") or shutil.which("cursor-agent"))
    parser.add_argument("--manager", required=True, help="Cursor model ID, for example grok-4.7-xhigh")
    parser.add_argument("--worker", required=True, help="Cursor model ID named in the prompt, for example composer-2.5")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", action="append", choices=("parallel", "plan-handoff", "explain"))
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if not args.executable or output.exists() or output == ROOT or ROOT in output.parents:
        parser.error("Need the Cursor CLI and a new output directory outside the repository.")
    output.mkdir(parents=True)
    version = subprocess.run([args.executable, "--version"], capture_output=True, text=True).stdout.strip()
    write_json(output / "preflight.json", {"cli_version": version, "manager": args.manager, "worker": args.worker,
                                           "python": PYTHON})
    cases = json.loads((ROOT / "evals/evals.json").read_text(encoding="utf-8"))["evals"]
    results = []
    for name in dict.fromkeys(args.case or ["explain", "parallel", "plan-handoff"]):
        case = next(c for c in cases if c["name"] == name)
        result = run_case(args.executable, case, output / name, args.manager, args.worker)
        results.append(result)
        write_json(output / "results.json", results)
        print(json.dumps({"case": name, "behavior_passed": result["correctness"]["behavior_passed"],
                          "verified": result["orchestration"]["verified"]}), flush=True)
    return 0 if all(r["correctness"]["tests_passed"] and r["correctness"]["behavior_passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
