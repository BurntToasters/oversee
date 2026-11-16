"""Review completed Codex smoke runs using native events and persisted turn contexts."""

import argparse
import json
from pathlib import Path
import re

from .codex_run import Codex, export
from .evidence import inspects_diff, is_check_command, mentions
from .run import ROOT, correctness, snapshot, write_json

HELPER_TYPES = {"explorer"}
# Items that are neither tools nor worker activity; a turn's final text may follow them.
PASSIVE_ITEMS = {"agentMessage", "userMessage", "reasoning", "plan"}


def completed_items(events, root):
    return [(event["time"], event["message"]["params"]["item"])
            for event in events if event["direction"] == "received"
            and event["message"].get("method") == "item/completed"
            and event["message"]["params"].get("threadId") == root]


# Shared with the OpenCode grader: one unittest run, wrappers unwrapped, no chains/pipes/redirects.
_unittest_invocation = is_check_command


def _agent_types(events, records):
    """Best-effort agent type per thread from thread records, turn contexts, or spawn items."""
    keys = ("agentRole", "agentType", "agent_role", "agent_type")
    found = {}
    def pick(data):
        return next((data[k] for k in keys if isinstance(data.get(k), str)), None)
    for record in records:
        sources = [record.get("thread", {})] + [c.get("payload", {}) for c in record.get("turn_contexts", [])]
        kind = next((pick(s) for s in sources if pick(s)), None)
        if kind:
            found[record["thread"]["id"]] = kind.lower()
    for event in events:
        item = event.get("message", {}).get("params", {}).get("item", {})
        kind = pick(item)
        if not kind and isinstance(item.get("arguments"), str):
            try:
                kind = pick(json.loads(item["arguments"]))
            except (ValueError, AttributeError):
                kind = None
        for sid in [item.get("agentThreadId"), *item.get("receiverThreadIds", [])]:
            if kind and sid:
                found.setdefault(sid, kind.lower())
    return found


def _silence(events, root, worker):
    """Per turn only the last text, after the turn's last tool/worker item, is exempt; plus one notice."""
    turns, current = [], []
    for event in events:
        message = event.get("message", {})
        params = message.get("params", {})
        if event.get("direction") != "received" or params.get("threadId") != root:
            continue
        if message.get("method") == "item/completed":
            current.append(params["item"])
        elif message.get("method") == "turn/completed":
            turns.append(current)
            current = []
    turns = [t for t in [*turns, current] if t]
    narration, notices, final_ok = [], 0, False
    for number, turn in enumerate(turns):
        texts = [i for i, item in enumerate(turn) if item.get("type") == "agentMessage"]
        end = texts[-1] if texts and all(i.get("type") in PASSIVE_ITEMS for i in turn[texts[-1] + 1:]) else None
        if number == len(turns) - 1:
            final_ok = end is not None
        for index in texts:
            content = turn[index].get("text", "")
            if index == end:
                continue
            if (mentions(content, worker["model"]) and mentions(content, worker["effort"])
                    and len(content.strip().splitlines()) == 1 and notices == 0):
                notices += 1
            else:
                narration.append(content)
    return not narration and final_ok


def _unittest_success_output(output):
    output = str(output or "")
    ran = re.search(r"(?m)^Ran\s+(\d+)\s+tests?\s+in\s+[\d.]+s\s*$", output)
    passed = re.search(r"(?m)^OK(?:\s+\([^\r\n]*\))?\s*$", output)
    return bool(ran and int(ran.group(1)) > 0 and passed)


def _latest_checks(items):
    checks = {}
    for item in items:
        command = item.get("command", "")
        if _unittest_invocation(command):
            checks[command] = item
    if not checks:
        return False
    outcomes = []
    for item in checks.values():
        code = item.get("exitCode")
        if item.get("status") in ("failed", "interrupted") or (code is not None and code != 0):
            outcomes.append(False)
        elif code is None:
            outcomes.append(None)
        elif _unittest_success_output(item.get("aggregatedOutput", "")):
            outcomes.append(True)
        elif re.search(r"(?m)^FAILED\s*\(", str(item.get("aggregatedOutput") or "")):
            outcomes.append(False)
        else:
            outcomes.append(None)
    return False if False in outcomes else None if None in outcomes else True


def _shows_diff(item):
    return (item.get("status") == "completed" and inspects_diff(item.get("command", ""))
            and "diff --git" in str(item.get("aggregatedOutput") or ""))


def _command_items(items, after=float("-inf"), before=float("inf")):
    return [(when, item) for when, item in items if after <= when < before
            and item.get("type") == "commandExecution"]


def grade(events, records, meta, case):
    root, manager, worker = meta["root"], meta["manager"], meta["worker"]
    items = completed_items(events, root)
    types = _agent_types(events, records)
    helper = lambda sid: types.get(sid) in HELPER_TYPES
    descendants = [r for r in records if r["thread"]["id"] != root and not helper(r["thread"]["id"])]
    def exact(record, setting):
        contexts = record["turn_contexts"]
        return bool(contexts) and all(c["payload"].get("model") == setting["model"] and
                                     c["payload"].get("effort") == setting["effort"] for c in contexts)
    root_record = next(r for r in records if r["thread"]["id"] == root)
    checks = {"exact_manager_settings": exact(root_record, manager)}
    text = [i for _, i in items if i["type"] == "agentMessage"]
    if case == "explain":
        explanation = "\n".join(i["text"] for i in text).lower()
        activated = any(i["type"] == "userMessage" and any(c.get("type") == "skill" and
            c.get("name") == "oversee" for c in i.get("content", [])) for _, i in items)
        checks.update(no_workers=not [r for r in records if r["thread"]["id"] != root], no_skill_activation=not activated,
                      accurate_explanation=all(s in explanation for s in (".notes.json", "id", "title", "body")))
    else:
        checks["exact_worker_settings"] = bool(descendants) and all(exact(r, worker) for r in descendants)
        starts, ends = {}, {}
        for when, item in items:
            if item["type"] == "subAgentActivity" and not helper(item.get("agentThreadId")):
                if item["kind"] == "started":
                    starts.setdefault(item["agentThreadId"], when)
                elif item["kind"] == "completed":
                    ends[item["agentThreadId"]] = when
        # Extra spawns are retries of a failed piece; two pieces need at least two worker spawns.
        checks["two_workers"] = len(starts) >= 2
        first, last = min(starts.values(), default=float("inf")), max(ends.values(), default=float("inf"))
        checks["announcement_before_dispatch"] = any(when <= first and item["type"] == "agentMessage" and
            worker["model"] in item["text"] and re.search(r"\b" + re.escape(worker["effort"]) + r"\b", item["text"], re.I)
            for when, item in items) and bool(starts)
        audits = [i for _, i in _command_items(items, after=last)]
        checks["manager_runs_successful_checks"] = _latest_checks(audits)
        checks["manager_inspects_changes"] = any(_shows_diff(i) for i in audits)
        checks["no_observed_status_polling"] = not any(i["type"] == "collabAgentToolCall" and
            i.get("tool") in ("list_agents", "status", "list") for _, i in items)
        checks["no_observed_routine_narration"] = _silence(events, root, worker)
        windows = sorted((a, ends[sid]) for sid, a in starts.items() if sid in ends)
        if case == "parallel":
            checks["parallel_overlap"] = any(a < d and c < b for i, (a, b) in enumerate(windows)
                                             for c, d in windows[i + 1:])
        else:
            checks["dependent_workers_sequenced"] = len(windows) >= 2 and all(
                b <= c for (_, b), (c, _) in zip(windows, windows[1:]))
            # With retries, acceptance holds when some gap between consecutive spawns shows it.
            outcomes = []
            for (_, end), (start, _) in zip(windows, windows[1:]):
                between = [i for _, i in _command_items(items, after=end, before=start)]
                passed = _latest_checks(between)
                inspected = any(_shows_diff(i) for i in between)
                outcomes.append(False if passed is False or not inspected else None if passed is None else True)
            checks["dependent_manager_acceptance_between_workers"] = (
                True if True in outcomes else None if None in outcomes else False)
            modes = [c["payload"].get("collaboration_mode", {}).get("mode") for c in root_record["turn_contexts"]]
            checks["native_mode_transition"] = modes == ["plan", "default"]
    outcomes = [e["message"]["params"]["turn"]["status"] for e in events
                if e["direction"] == "received" and e["message"].get("method") == "turn/completed"]
    checks["turns_succeeded"] = bool(outcomes) and all(x == "completed" for x in outcomes)
    return {"verified": all(v is True for v in checks.values()), "checks": checks}


# cacheWriteInputTokens may be absent from Codex token totals; a missing field stays None, never a failure.
FIELDS = {"input": "inputTokens", "output": "outputTokens", "reasoning": "reasoningOutputTokens",
          "cache_read": "cachedInputTokens", "cache_write": "cacheWriteInputTokens"}


def _measured(events):
    measured = {}
    for event in events:
        message = event["message"]
        if event["direction"] == "received" and message.get("method") == "thread/tokenUsage/updated":
            params = message["params"]
            measured[params["threadId"]] = params["tokenUsage"]["total"]
    return measured


def _totals(measured, ids):
    result = {"sessions": len(ids), "cost_usd": None}
    for label, field in FIELDS.items():
        values = [measured.get(sid, {}).get(field) for sid in ids]
        result[label] = sum(values) if values and all(v is not None for v in values) else None
    return result


def usage(events, records):
    return _totals(_measured(events), {r["thread"]["id"] for r in records})


def usage_by_role(events, records, root):
    """Split usage into root, worker, and helper (explorer) threads; events hold cumulative totals."""
    measured = _measured(events)
    types = _agent_types(events, records)
    others = {r["thread"]["id"] for r in records} - {root}
    helpers = {sid for sid in others if types.get(sid) in HELPER_TYPES}
    # Codex reports no cost, so cost stays None even for an empty group.
    group = lambda ids: _totals(measured, ids) if ids else {"sessions": 0, "cost_usd": None, **dict.fromkeys(FIELDS, 0)}
    return {"manager": _totals(measured, {root}), "children": group(others), "workers": group(others - helpers),
            "helpers": group(helpers), "manager_turns": None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--executable", default="codex")
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if not source.is_dir() or output.exists() or output == ROOT or ROOT in output.parents or source in output.parents:
        parser.error("Need an existing smoke run and new output outside source and repository.")
    cases = sorted(source.glob("*/session.json"))
    if not cases:
        parser.error("No Codex case sessions found.")
    for session in cases:
        if snapshot(session.parent / "project") != json.loads((session.parent / "after.json").read_text()):
            parser.error(f"Retained project changed: {session.parent}")
    api = Codex(args.executable)
    try:
        output.mkdir(parents=True)
        results = []
        for session in cases:
            folder = session.parent
            meta = json.loads(session.read_text())
            events = json.loads((folder / "events.json").read_text())
            records = export(api, meta["root"], events)
            proof = correctness(folder / "project", folder.name)
            if folder.name == "explain":
                proof["project_unchanged"] = json.loads((folder / "baseline.json").read_text()) == json.loads((folder / "after.json").read_text())
            orchestration = grade(events, records, meta, folder.name)
            if folder.name == "plan-handoff":
                phase = json.loads((folder / "plan-phase.json").read_text())
                orchestration["checks"]["plan_phase_unchanged"] = (
                    phase["snapshot"] == json.loads((folder / "baseline.json").read_text())
                    if "snapshot" in phase else phase["checks"]["unchanged"])
                first_execution = next((i for i, e in enumerate(events) if e["message"].get("method") == "turn/start"
                    and e["message"].get("params", {}).get("collaborationMode", {}).get("mode") == "default"), len(events))
                orchestration["checks"]["plan_phase_no_workers"] = not any(
                    e["message"].get("params", {}).get("item", {}).get("type") in ("subAgentActivity", "collabAgentToolCall")
                    for e in events[:first_execution])
                orchestration["verified"] = all(v is True for v in orchestration["checks"].values())
            report = {"case": folder.name, "correctness": proof, "orchestration": orchestration,
                      "usage": usage(events, records),
                      "usage_by_role": usage_by_role(events, records, meta["root"]), "elapsed_seconds": json.loads((folder / "result.json").read_text())["elapsed_seconds"]}
            destination = output / folder.name
            destination.mkdir()
            write_json(destination / "native.json", records)
            write_json(destination / "result.json", report)
            finals = [i["text"] for _, i in completed_items(events, meta["root"]) if i["type"] == "agentMessage" and i.get("phase") == "final_answer"]
            (destination / "final_response.md").write_text(finals[-1] + "\n" if finals else "", encoding="utf-8")
            results.append(report)
            print(json.dumps({"case": folder.name, "behavior_passed": proof["behavior_passed"],
                              "orchestration_verified": orchestration["verified"]}), flush=True)
        write_json(output / "results.json", results)
    finally:
        api.close()


if __name__ == "__main__":
    main()
