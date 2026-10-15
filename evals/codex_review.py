"""Review completed Codex smoke runs using native events and persisted turn contexts."""

import argparse
import json
from pathlib import Path
import re

from .codex_run import Codex, export
from .run import ROOT, correctness, snapshot, write_json


def completed_items(events, root):
    return [(event["time"], event["message"]["params"]["item"])
            for event in events if event["direction"] == "received"
            and event["message"].get("method") == "item/completed"
            and event["message"]["params"].get("threadId") == root]


def grade(events, records, meta, case):
    root, manager, worker = meta["root"], meta["manager"], meta["worker"]
    items = completed_items(events, root)
    descendants = [r for r in records if r["thread"]["id"] != root]
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
        checks.update(no_workers=not descendants, no_skill_activation=not activated,
                      accurate_explanation=all(s in explanation for s in (".notes.json", "id", "title", "body")))
    else:
        checks["exact_worker_settings"] = bool(descendants) and all(exact(r, worker) for r in descendants)
        starts, ends = {}, {}
        for when, item in items:
            if item["type"] == "subAgentActivity":
                if item["kind"] == "started":
                    starts.setdefault(item["agentThreadId"], when)
                elif item["kind"] == "completed":
                    ends[item["agentThreadId"]] = when
        checks["two_workers"] = len(starts) == 2
        first, last = min(starts.values(), default=float("inf")), max(ends.values(), default=float("inf"))
        checks["announcement_before_dispatch"] = any(when <= first and item["type"] == "agentMessage" and
            worker["model"] in item["text"] and re.search(r"\b" + re.escape(worker["effort"]) + r"\b", item["text"], re.I)
            for when, item in items) and bool(starts)
        audits = [i for when, i in items if when >= last and i["type"] == "commandExecution" and i["status"] == "completed"]
        checks["manager_runs_successful_checks"] = any(re.search(r"python(?:3)?\s+(?:-B\s+)?-m\s+unittest\b", i["command"])
            and i.get("exitCode") == 0 and re.search(r"\bOK\b", i.get("aggregatedOutput", "")) for i in audits)
        checks["manager_inspects_changes"] = any("git diff" in i["command"] and
            "diff --git" in i.get("aggregatedOutput", "") for i in audits)
        checks["no_observed_status_polling"] = not any(i["type"] == "collabAgentToolCall" and
            i.get("tool") in ("list_agents", "status", "list") for _, i in items)
        notices, narration = 0, []
        for item in text:
            if item.get("phase") == "final_answer":
                continue
            content = item["text"]
            if worker["model"] in content and worker["effort"] in content.lower() and notices == 0:
                notices += 1
            elif not re.search(r"\b(blocked|permission|clarif\w*|cancel\w*|plan mode|default mode)\b", content, re.I):
                narration.append(content)
        checks["no_observed_routine_narration"] = not narration
        windows = [(a, ends[sid]) for sid, a in starts.items() if sid in ends]
        if case == "parallel":
            checks["parallel_overlap"] = len(windows) == 2 and max(a for a, _ in windows) < min(b for _, b in windows)
        else:
            windows.sort()
            checks["dependent_workers_sequenced"] = len(windows) == 2 and windows[0][1] <= windows[1][0]
            modes = [c["payload"].get("collaboration_mode", {}).get("mode") for c in root_record["turn_contexts"]]
            checks["native_mode_transition"] = modes == ["plan", "default"]
    outcomes = [e["message"]["params"]["turn"]["status"] for e in events
                if e["direction"] == "received" and e["message"].get("method") == "turn/completed"]
    checks["turns_succeeded"] = bool(outcomes) and all(x == "completed" for x in outcomes)
    return {"verified": all(v is True for v in checks.values()), "checks": checks}


def usage(events, records):
    measured = {}
    for event in events:
        message = event["message"]
        if event["direction"] == "received" and message.get("method") == "thread/tokenUsage/updated":
            params = message["params"]
            measured[params["threadId"]] = params["tokenUsage"]["total"]
    ids = {r["thread"]["id"] for r in records}
    fields = {"input": "inputTokens", "output": "outputTokens", "reasoning": "reasoningOutputTokens",
              "cache_read": "cachedInputTokens", "cache_write": "cacheWriteInputTokens"}
    result = {"sessions": len(ids), "cost_usd": None}
    for label, field in fields.items():
        values = [measured.get(sid, {}).get(field) for sid in ids]
        result[label] = sum(values) if values and all(v is not None for v in values) else None
    return result


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
                      "usage": usage(events, records), "elapsed_seconds": json.loads((folder / "result.json").read_text())["elapsed_seconds"]}
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
