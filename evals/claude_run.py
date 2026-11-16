"""Headless Claude Code (`claude -p`) oversee runs with native stream-json evidence; nothing installed globally."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from .evidence import inspects_diff, interpreter_missing, is_check_command, mentions
from .run import PYTHON, ROOT, correctness, fill_prompt, init_repo, snapshot, write_json

USER_NOTE = "User note: keep this line."
NOTES_FILE = "notes.txt"
NUDGE = "no visible output"
WAITING = re.compile(r"^Waiting for \d+ workers?\.$")
# Tools that emulate a wait or read worker progress; the skill forbids them.
POLLING_TOOLS = {"ScheduleWakeup", "Monitor", "TaskOutput", "BashOutput", "AgentOutput", "CronCreate"}
# Read-only git, the baseline commands, and the test runner; no auto-approval flags, ever.
ALLOWED_TOOLS = ["Agent", "Read", "Edit", "Write", "Glob", "Grep",
                 *[f"Bash({python}{flags} {target}:*)" for python in ("python", "python3")
                   for flags in ("", " -B") for target in ("-m unittest", "notes.py")],
                 *[f"Bash(git {command}:*)" for command in ("status", "diff", "--no-pager diff", "rev-parse", "log",
                                                            "stash create", "hash-object", "ls-files")]]
FORBIDDEN_FLAGS = ("--dangerously-skip-permissions", "bypassPermissions", "--allow-dangerously-skip-permissions")
SCOPE = "\nWork only in this fixture. Do not commit, push, install dependencies, change global settings, or access other projects."


def stage(output, case, dirty=True, skill_dir=".claude/skills/oversee"):
    """Committed fixture with the skill in the host's project folder (ignored), plus a user edit and an untracked file."""
    project = output / "project"
    shutil.copytree(ROOT / "evals/fixtures" / case["fixture"], project)
    host_dir = Path(skill_dir).parts[0]
    (project / ".gitignore").write_text(f"__pycache__/\n*.pyc\n.notes.json\n{host_dir}/\n", encoding="utf-8")
    init_repo(project)
    shutil.copytree(ROOT / "skills/oversee", project / skill_dir)
    if dirty:
        with (project / "README.md").open("a", encoding="utf-8") as readme:
            readme.write("\n" + USER_NOTE + "\n")
        (project / NOTES_FILE).write_text("user scratch, keep\n", encoding="utf-8")
    return project


def command(executable, prompt, manager_model, manager_effort, budget):
    args = [executable, "-p", prompt, "--model", manager_model, "--effort", manager_effort,
            "--setting-sources", "project", "--no-session-persistence", "--permission-mode", "acceptEdits",
            "--allowedTools", *ALLOWED_TOOLS, "--output-format", "stream-json", "--verbose",
            "--max-budget-usd", str(budget)]
    if any(flag in arg for arg in args for flag in FORBIDDEN_FLAGS):
        raise ValueError("Refusing an auto-approval flag.")
    return args


def load_events(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("{")]


def _text(content):
    if isinstance(content, str):
        return content
    return "".join(part.get("text", "") for part in content or [] if isinstance(part, dict))


def grade(events, case, worker):
    """Grade one run from its stream-json events. `worker` is the per-call model alias the prompt named."""
    texts, uses, results, notices, nudges, denials = [], [], {}, {}, 0, []
    result = next((e for e in events if e.get("type") == "result"), {})
    for index, event in enumerate(events):
        kind, main = event.get("type"), not event.get("parent_tool_use_id")
        if kind == "assistant" and main:
            for part in event["message"].get("content", []):
                if part.get("type") == "text" and part["text"].strip():
                    texts.append((index, part["text"].strip()))
                elif part.get("type") == "tool_use":
                    uses.append((index, event["message"].get("id"), part))
        elif kind == "user" and main:
            content = event["message"].get("content")
            if NUDGE in _text(content if isinstance(content, list) else [{"text": content or ""}]):
                nudges += 1
            for part in content if isinstance(content, list) else []:
                if part.get("type") == "tool_result":
                    results[part.get("tool_use_id")] = (index, part)
        elif kind == "system" and event.get("subtype") == "task_notification" and event.get("status") == "completed":
            notices[event.get("tool_use_id")] = index
        elif kind == "system" and event.get("subtype") == "permission_denied":
            denials.append(event.get("agent_id") or "manager")
    agents = [(i, mid, u) for i, mid, u in uses if u["name"] in ("Agent", "Task")]
    bash = [(i, u) for i, _, u in uses if u["name"] == "Bash"]
    skill_used = any(u["name"] == "Skill" and "oversee" in json.dumps(u.get("input", {})) for _, _, u in uses)
    checks = {"no_host_nudge": nudges == 0,
              "no_polling_tools": not any(u["name"] in POLLING_TOOLS for _, _, u in uses)}
    report = {"cost_usd": result.get("total_cost_usd"), "turns": result.get("num_turns"),
              "cost_by_model": {m: u.get("costUSD") for m, u in (result.get("modelUsage") or {}).items()},
              "manager_texts": [t for _, t in texts], "denials": denials, "nudges": nudges,
              "workers": [{k: u["input"].get(k) for k in ("subagent_type", "model", "effort", "run_in_background",
                                                            "isolation", "name")} for _, _, u in agents],
              "manager_commands": [u["input"].get("command") for _, u in bash]}
    if case == "explain":
        checks.update(no_workers=not agents, no_skill_activation=not skill_used,
                      answered=bool(texts) and result.get("subtype") == "success")
        return {"verified": all(checks.values()), "checks": checks, **report}

    def finished(use):
        return notices.get(use["id"], results.get(use["id"], (float("inf"),))[0])
    first_dispatch = agents[0][0] if agents else float("inf")
    last_finish = max((finished(u) for _, _, u in agents), default=float("inf"))
    final = texts[-1][0] if texts else None
    before = [t for i, t in texts if i < first_dispatch]
    choice = before[0] if len(before) == 1 else None
    between = [t for i, t in texts if i > first_dispatch and i != final]
    # The latest run of each check command decides; a command the shell could not start ran no test.
    latest = {}
    for i, u in bash:
        state = _check_state(results.get(u["id"]))
        if is_check_command(u["input"].get("command")) and i > last_finish and state is not None:
            latest[u["input"]["command"]] = state
    checks.update(
        two_workers=len(agents) >= 2,
        exact_worker_model=bool(agents) and all(u["input"].get("model") == worker for _, _, u in agents),
        no_isolation_or_name=not any(u["input"].get(k) for _, _, u in agents for k in ("isolation", "name")),
        worker_choice_before_dispatch=bool(choice) and mentions(choice, worker),
        no_routine_narration=all(WAITING.match(t) for t in between),
        manager_runs_successful_checks=bool(latest) and all(latest.values()),
        manager_inspects_changes=any(inspects_diff(u["input"].get("command", "")) and i > last_finish
                                     for i, u in bash),
        final_report=final is not None and final > last_finish)
    if case == "parallel":
        checks["one_batch"] = len({mid for _, mid, _ in agents}) == 1
    else:
        ordered = sorted(agents, key=lambda a: a[0])
        checks["dependent_workers_sequenced"] = len(ordered) >= 2 and all(
            finished(a[2]) < b[0] for a, b in zip(ordered, ordered[1:]))
        checks["manager_check_between_workers"] = len(ordered) >= 2 and any(
            finished(ordered[0][2]) < i < ordered[1][0] and _check_state(results.get(u["id"])) is True
            for i, u in bash if is_check_command(u["input"].get("command")))
    return {"verified": all(checks.values()), "checks": checks, **report}


def _check_state(result):
    """True passed, False failed, None when the shell could not start it."""
    if not result:
        return False
    part = result[1]
    output = _text(part.get("content") if isinstance(part.get("content"), list) else [{"text": part.get("content") or ""}])
    return None if interpreter_missing(None, output) else not part.get("is_error")


def workspace(project, case, before_head):
    def git(*args):
        return subprocess.run(["git", *args], cwd=project, capture_output=True, text=True).stdout.strip()
    proof = correctness(project, case)
    proof.update(head_unchanged=git("rev-parse", "HEAD") == before_head, stash_list_empty=git("stash", "list") == "",
                 user_edit_kept=USER_NOTE in (project / "README.md").read_text(encoding="utf-8"),
                 untracked_kept=(project / NOTES_FILE).is_file())
    return proof


def run_case(executable, case, output, manager_model, manager_effort, worker, budget, fork):
    output.mkdir(parents=True)
    project = stage(output, case)
    before, head = snapshot(project), subprocess.run(["git", "rev-parse", "HEAD"], cwd=project, capture_output=True,
                                                     text=True, check=True).stdout.strip()
    prompt = fill_prompt(case["prompt"], worker) + SCOPE
    write_json(output / "prompt.json", {"text": prompt, "fork_mode": fork})
    env = dict(os.environ)
    if fork != "default":
        env["CLAUDE_CODE_FORK_SUBAGENT"] = "1" if fork == "on" else "0"
    started = time.monotonic()
    with (output / "events.jsonl").open("w", encoding="utf-8") as out, \
            (output / "stderr.txt").open("w", encoding="utf-8") as err:
        code = subprocess.run(command(executable, prompt, manager_model, manager_effort, budget),
                              cwd=project, env=env, stdout=out, stderr=err).returncode
    graded = grade(load_events(output / "events.jsonl"), case["name"], worker)
    proof = workspace(project, case["name"], head)
    if case["name"] == "explain":
        proof["project_unchanged"] = before == snapshot(project)
    report = {"case": case["name"], "exit": code, "elapsed_seconds": round(time.monotonic() - started, 1),
              "correctness": proof, "orchestration": graded}
    write_json(output / "result.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", default=shutil.which("claude"))
    parser.add_argument("--manager-model", required=True, help="for example claude-opus-5-5")
    parser.add_argument("--manager-effort", required=True)
    parser.add_argument("--worker", required=True, help="per-call model alias named in the prompt, for example haiku")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", action="append", choices=("parallel", "plan-handoff", "explain"))
    parser.add_argument("--fork-mode", choices=("default", "on", "off"), default="default",
                        help="on removes `run_in_background`, as in interactive sessions")
    parser.add_argument("--max-budget-usd", type=float, default=2.0)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if not args.executable or output.exists() or output == ROOT or ROOT in output.parents:
        parser.error("Need Claude Code and a new output directory outside the repository.")
    output.mkdir(parents=True)
    version = subprocess.run([args.executable, "--version"], capture_output=True, text=True).stdout.strip()
    write_json(output / "preflight.json", {"cli_version": version, "manager": [args.manager_model, args.manager_effort],
                                           "worker": args.worker, "fork_mode": args.fork_mode, "python": PYTHON})
    cases = json.loads((ROOT / "evals/evals.json").read_text(encoding="utf-8"))["evals"]
    results = []
    for name in dict.fromkeys(args.case or ["explain", "parallel", "plan-handoff"]):
        case = next(c for c in cases if c["name"] == name)
        result = run_case(args.executable, case, output / name, args.manager_model, args.manager_effort,
                          args.worker, args.max_budget_usd, args.fork_mode)
        results.append(result)
        write_json(output / "results.json", results)
        print(json.dumps({"case": name, "behavior_passed": result["correctness"]["behavior_passed"],
                          "verified": result["orchestration"]["verified"],
                          "cost_usd": result["orchestration"]["cost_usd"]}), flush=True)
    return 0 if all(r["correctness"]["tests_passed"] and r["correctness"]["behavior_passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
