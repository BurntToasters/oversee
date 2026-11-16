"""Grade retained native OpenCode transcripts; missing evidence stays unknown."""

import re

FIELDS = ("input", "output", "reasoning", "cache_read", "cache_write", "cost_usd")
# Host helper agents (OpenCode v1/v2); every other child agent is a worker.
HELPER_AGENTS = {"explore", "plan", "scout"}
_QUOTED = re.compile(r"'[^']*'|\"(?:\\.|[^\"\\])*\"")
_WRAPPERS = (
    re.compile(r"""\s*(?:"[^"]*(?:powershell|pwsh)(?:\.exe)?"|'[^']*(?:powershell|pwsh)(?:\.exe)?'|"""
               r"""(?:\S*[/\\])?(?:powershell|pwsh)(?:\.exe)?)\s+(?:-NoProfile\s+)?-Command\s+(['"])""", re.I),
    re.compile(r"""\s*(?:/\S*/)?(?:bash|sh|zsh)\s+-l?c\s+(['"])"""))
_CHECK = re.compile(r"^(?:\S*[/\\])?(?:python(?:3(?:\.\d+)?)?|py)(?:\.exe)?"
                    r"(?:\s+(?:-[XW]\s*\S+|-[bBdEiIOqsSuvR]+))*\s+-m\s+unittest(?=\s|$)", re.I)
_GIT_DIFF = re.compile(r"\s*git(?:\.exe)?(?:\s+(?:--no-pager|-P|--paginate|-p|--no-optional-locks|"
                       r"--literal-pathspecs|--no-replace-objects|-[Cc]\s+\S+|--(?:git-dir|work-tree)(?:=|\s+)\S+))*"
                       r"\s+diff(?=\s|$)")
_NO_CONTENT = re.compile(r"\s--(?:stat|shortstat|numstat|dirstat|summary|name-only|name-status|quiet|"
                         r"exit-code|no-patch)\b|\s-s(?=\s|$)")


def _blank_quotes(command):
    return _QUOTED.sub("''", command)


def unwrap_shell(command):
    """Return the body of a PowerShell -Command or POSIX `sh -c`/`-lc` wrapper, else the command."""
    for pattern in _WRAPPERS:
        match = pattern.match(command)
        if not match:
            continue
        quote, body = match.group(1), command[match.end():].rstrip()
        if not body.endswith(quote):
            return command
        body = body[:-1]
        # A quote inside the body means text outside the wrapper; leave it wrapped.
        if (quote == "'" and "'" in body) or (quote == '"' and re.search(r'(?<!\\)"', body)):
            return command
        return body
    return command


def is_check_command(command):
    """One unittest run per command: no pipes, chains, or redirection outside quotes."""
    flat = _blank_quotes(unwrap_shell(str(command or "")).strip())
    if re.search(r"[|;&<>\n\r`]|\$\(", flat):
        return False
    return bool(_CHECK.match(flat))


def mentions(text, token):
    """Whole-token, case-insensitive mention of a model id or effort."""
    return bool(token) and re.search(r"(?<![\w.-])" + re.escape(token) + r"(?![\w-]|\.\w)", text, re.I) is not None


def changed_paths(before, after):
    if before is None or after is None:
        return None
    return {p for p in set(before) | set(after) if before.get(p) != after.get(p)}


def _root_id(transcripts, root_id=None):
    ids = [t["info"]["id"] for t in transcripts]
    if root_id in ids:
        return root_id
    # Old evidence lacks a stored root: use the first parentless, else first, transcript.
    return next((t["info"]["id"] for t in transcripts if not t["info"].get("parentID")), ids[0] if ids else None)


def root_transcript(transcripts, root_id=None):
    rid = _root_id(transcripts, root_id)
    return next((t for t in transcripts if t["info"]["id"] == rid), None)


def is_helper(transcript):
    return transcript["info"].get("agent") in HELPER_AGENTS


def total_usage(transcripts):
    sessions = {t["info"]["id"]: t for t in transcripts}
    fields = FIELDS
    totals = dict.fromkeys(fields, 0)
    for transcript in sessions.values():
        info = transcript["info"]
        # Session counters start at zero even when authentication prevents inference.
        measured = any(m.get("type") == "assistant" and "tokens" in m for m in transcript["messages"])
        usage = info.get("tokens") if measured else None
        values = {k: usage.get(k) if usage else None for k in fields[:3]}
        values.update({"cache_read": (usage or {}).get("cache", {}).get("read"),
                       "cache_write": (usage or {}).get("cache", {}).get("write"),
                       "cost_usd": info.get("cost") if measured else None})
        for key, value in values.items():
            if value is None or totals[key] is None:
                totals[key] = None
            else:
                totals[key] += value
    if not sessions:
        totals = dict.fromkeys(fields, None)
    return {"sessions": len(sessions), **totals}


def usage_by_role(transcripts, root_id=None):
    """Split total_usage: root session is the manager; children split into workers and host helpers."""
    if not transcripts:
        empty = total_usage([])
        return {"manager": empty, "children": empty, "workers": empty, "helpers": empty, "manager_turns": None}
    root_id = _root_id(transcripts, root_id)
    roots = [t for t in transcripts if t["info"]["id"] == root_id]
    others = [t for t in transcripts if t["info"]["id"] != root_id]
    group = lambda items: total_usage(items) if items else {"sessions": 0, **dict.fromkeys(FIELDS, 0)}
    # total_usage keeps the last transcript for a duplicated session id; count turns from the same one.
    turns = sum(1 for m in roots[-1]["messages"] if m.get("type") == "assistant" and "tokens" in m)
    return {"manager": total_usage(roots), "children": group(others),
            "workers": group([t for t in others if not is_helper(t)]),
            "helpers": group([t for t in others if is_helper(t)]), "manager_turns": turns or None}


def inspects_diff(command):
    """True when a segment of a (possibly wrapped) chain is a content diff not piped or redirected."""
    flat = _blank_quotes(unwrap_shell(str(command or "")))
    return any(_GIT_DIFF.match(segment) and not re.search(r"[|<>]", segment) and not _NO_CONTENT.search(segment)
               for segment in re.split(r"&&|\|\||;|\n", flat))


def tools(transcript):
    def nested(value, parent_time):
        if isinstance(value, dict):
            if value.get("type") == "tool" and "state" in value and "name" in value:
                yield {**value, "time": value.get("time", parent_time)}
            elif isinstance(value.get("tool"), str) and "status" in value:
                # OpenCode v2 Code Mode records tools without the outer part schema.
                yield {"name": value["tool"].removeprefix("opencode."),
                       "time": value.get("time", parent_time),
                       "state": {"status": value["status"], "input": value.get("input", {}),
                                 "metadata": value.get("metadata", {})}}
            else:
                for item in value.values():
                    yield from nested(item, parent_time)
        elif isinstance(value, list):
            for item in value:
                yield from nested(item, parent_time)

    for message in transcript.get("messages", []):
        if message.get("type") == "assistant":
            for item in message.get("content", []):
                if item.get("type") == "tool":
                    yield item
                    yield from nested(item.get("state", {}).get("metadata", {}), item.get("time", {}))


def completed_between(calls, start, end, matches):
    selected, unknown_end, late = [], False, False
    for tool in calls:
        if not matches(tool):
            continue
        times = tool.get("time", {})
        created, completed = times.get("created"), times.get("completed")
        if completed is None:
            if created is None or created < end:
                unknown_end = True
        elif start <= completed < end:
            selected.append(tool)
        elif created is not None and created < end and completed >= end:
            late = True
    return selected, unknown_end, late


def text_content(transcript):
    return "\n".join(part.get("text", "")
                     for msg in transcript.get("messages", []) if msg.get("type") == "assistant"
                     for part in msg.get("content", []) if part.get("type") == "text")


def final_text(transcript):
    for message in reversed(transcript.get("messages", [])):
        if message.get("type") == "assistant":
            text = "\n".join(p.get("text", "") for p in message.get("content", []) if p.get("type") == "text")
            if text:
                return text
    return ""


def skill_loaded(transcript):
    return any(m.get("type") == "skill" and m.get("name", "oversee") == "oversee" or
               any(s.get("name") == "oversee" and s.get("text", "").startswith('<skill_content name="oversee">')
                   for s in m.get("skills", [])) for m in transcript.get("messages", [])) or any(
        t.get("name") == "skill" and t.get("state", {}).get("status") == "completed" and
        "oversee" in str(t.get("state", {}).get("input", {})) for t in tools(transcript))


def plan_phase_checks(transcripts, unchanged, worker, manager, root_id=None):
    rid = _root_id(transcripts, root_id) if transcripts else None
    children = [t for t in transcripts if t["info"]["id"] != rid]
    uses = lambda t: t["info"].get("model") == worker or any(
        m.get("model") == worker for m in t.get("messages", []) if m.get("type") == "assistant")
    # Host planning helpers may explore, but the worker choice is reserved for implementation.
    return {"unchanged": unchanged,
            "no_implementation_workers": not any(not is_helper(t) for t in children),
            "no_worker_choice_in_plan": None if worker == manager else not any(uses(t) for t in children)}


def _read_path(tool):
    data = tool.get("state", {}).get("input", {})
    path = next((data[k] for k in ("filePath", "file_path", "path") if isinstance(data.get(k), str)), "")
    return path.replace("\\", "/")


def silence(root, worker, last_idle=None):
    """Narration check: per user turn only the last text (after that turn's last tool) is exempt,
    plus one single-line worker-choice notice; the run's final text must also follow the last idle."""
    turns, current = [], []
    for message in root.get("messages", []):
        if message.get("type") == "user":
            turns.append(current)
            current = []
        elif message.get("type") == "assistant":
            current.append(message)
    turns.append(current)
    turns = [t for t in turns if t]
    narration, notices, final_ok = [], 0, False
    for number, turn in enumerate(turns):
        parts = [(i, p) for i, m in enumerate(turn) for p in m.get("content", [])]
        texts = [k for k, (_, p) in enumerate(parts) if p.get("type") == "text" and p.get("text")]
        end = None
        if texts and not any(p.get("type") == "tool" for _, p in parts[texts[-1] + 1:]):
            end = parts[texts[-1]][0]
        if end is not None and number == len(turns) - 1:
            created = turn[end].get("time", {}).get("created")
            if last_idle is not None and created is not None and created < last_idle:
                end = None
            final_ok = end is not None
        for i, message in enumerate(turn):
            text = "\n".join(p.get("text", "") for p in message.get("content", []) if p.get("type") == "text")
            if i == end or not text:
                continue
            # Blocker/clarification text is exempt only as a turn end (awaiting the user), handled above.
            if (mentions(text, worker["id"]) and mentions(text, worker["variant"])
                    and len(text.splitlines()) == 1 and notices == 0):
                notices += 1
                continue
            narration.append(text)
    return not narration and final_ok


def grade(transcripts, case, with_skill, worker, phase=None, root_id=None, changed=None):
    if not transcripts:
        return {"verified": False, "checks": {"native_transcript": None}}
    rid = _root_id(transcripts, root_id)
    root = root_transcript(transcripts, rid)
    children = [t for t in transcripts if t["info"]["id"] != rid]
    calls = list(tools(root))
    checks = {"native_transcript": True}
    worker_calls = [t for t in children if not is_helper(t)]
    if case == "explain":
        explanation = text_content(root).lower()
        checks.update(no_workers=not children,
                      no_skill_activation=not skill_loaded(root),
                      accurate_explanation=all(s in explanation for s in [".notes.json", "id", "title", "body"]))
    elif with_skill:
        checks["workers_dispatched"] = bool(worker_calls)
        checks["exact_worker_settings"] = bool(worker_calls) and all(
            t["info"].get("model") == worker and any(m.get("type") == "assistant" for m in t["messages"])
            and all(m.get("model") == worker for m in t["messages"] if m.get("type") == "assistant")
            for t in worker_calls)
        checks["skill_loaded"] = skill_loaded(root)
        earliest = min((t["info"]["time"]["created"] for t in worker_calls), default=None)
        announced = False
        for message in root["messages"]:
            if message.get("type") != "assistant":
                continue
            for part in message.get("content", []):
                if (part.get("type") == "text" and worker["id"] in part.get("text", "")
                        and re.search(r"\b" + re.escape(worker["variant"]) + r"\b", part.get("text", ""), re.I)):
                    # A later text block in a launch message is not an announcement.
                    announced = earliest is not None and message["time"]["created"] <= earliest
                if part.get("type") == "tool" and part.get("time", {}).get("created", float("inf")) >= (earliest or float("inf")):
                    break
            if announced:
                break
        checks["announcement_before_dispatch"] = announced
        finished = max((float("inf") if t["info"]["time"].get("idle") is None else t["info"]["time"]["idle"]
                        for t in worker_calls), default=float("inf"))
        post = [t for t in calls if t.get("time", {}).get("created", 0) >= finished
                and t.get("state", {}).get("status") == "completed"]
        # Read tool INPUT, not prose claiming checks ran. execute can contain nested shell calls.
        commands = [t.get("state", {}).get("input", {}).get("command", "") for t in post
                    if t.get("name", "").lower() in ("shell", "bash", "powershell")]
        checks["manager_runs_checks_after_workers"] = any(is_check_command(s) for s in commands)
        test_calls = [t for t in post if t.get("name", "").lower() in ("shell", "bash", "powershell")
                      and is_check_command(t.get("state", {}).get("input", {}).get("command", ""))]
        # A completed shell tool can still contain a failed test process.
        latest_checks = {t["state"]["input"]["command"]: t["state"].get("metadata", {}).get("exit") for t in test_calls}
        exits = list(latest_checks.values())
        checks["manager_checks_succeeded"] = (False if any(code is not None and code != 0 for code in exits)
            else None if not exits or any(code is None for code in exits) else True)
        # A read counts only for a path that actually changed (unknown baseline: reads never count).
        checks["manager_inspects_changes"] = any(inspects_diff(s) for s in commands) or any(
            t.get("name") in ("read", "read_file") and _read_path(t) and
            any(_read_path(t) == p or _read_path(t).endswith("/" + p) for p in changed or ()) for t in post)
        if not commands and any(t.get("name") == "execute" for t in post):
            checks["manager_runs_checks_after_workers"] = None
            checks["manager_inspects_changes"] = None
        # Unknown nested schemas must not be promoted to a no-polling success.
        checks["no_observed_status_polling"] = not any(
            re.search(r"(list_agents|session[._](?:status|list)|/api/session\?|how.s it going)",
                      t.get("name", "") + " " + str(t.get("state", {}).get("input", {})), re.I)
            for t in calls)
        if checks["no_observed_status_polling"] and any(
                t.get("name") == "execute" and not t.get("state", {}).get("metadata", {}).get("toolCalls")
                for t in calls):
            checks["no_observed_status_polling"] = None
        last_idle = max((t["info"]["time"].get("idle") for t in children
                         if t["info"]["time"].get("idle") is not None), default=None)
        checks["no_observed_routine_narration"] = silence(root, worker, last_idle)
        if case == "parallel":
            windows = [(t["info"]["time"]["created"], t["info"]["time"].get("idle")) for t in worker_calls]
            checks["parallel_overlap"] = any(a < d and c < b for i, (a, b) in enumerate(windows)
                                             for c, d in windows[i + 1:] if b is not None and d is not None)
        if case == "plan-handoff":
            checks["plan_phase_unchanged"] = (phase or {}).get("unchanged")
            checks["no_implementation_in_plan"] = (phase or {}).get("no_implementation_workers")
            checks["no_worker_choice_in_plan"] = (phase or {}).get("no_worker_choice_in_plan")
            checks["native_mode_transition"] = any(m.get("type") == "agent-switched" and
                                                      m.get("agent") == "build" for m in root["messages"])
            windows = sorted(((t["info"]["time"].get("created"), t["info"]["time"].get("idle")) for t in worker_calls),
                             key=lambda w: (w[0] is None, w[0] or 0))
            checks["dependent_workers_sequenced"] = len(windows) >= 2 and all(
                b is not None and b <= c for (_, b), (c, _) in zip(windows, windows[1:]))
            if len(windows) >= 2 and windows[0][1] is not None:
                start, end = windows[0][1], windows[1][0]
                shell = lambda t: t.get("name", "").lower() in ("shell", "bash", "powershell")
                tests_between, tests_unknown, tests_late = completed_between(calls, start, end, lambda t: shell(t) and
                    is_check_command(t.get("state", {}).get("input", {}).get("command", "")))
                latest_between = {}
                for tool in sorted(tests_between, key=lambda t: t.get("time", {}).get("completed", float("-inf"))):
                    latest_between[tool["state"]["input"]["command"]] = tool
                diff_tools, diff_unknown, diff_late = completed_between(calls, start, end, lambda t: shell(t) and
                    inspects_diff(t.get("state", {}).get("input", {}).get("command", "")))
                diff_between = any(t.get("state", {}).get("status") == "completed" for t in diff_tools)
                exits_between = list(latest_between.values())
                codes_between = [t.get("state", {}).get("metadata", {}).get("exit") for t in exits_between]
                if tests_late or any(t.get("state", {}).get("status") != "completed" for t in exits_between) \
                        or any(code is not None and code != 0 for code in codes_between):
                    passed_between = False
                elif tests_unknown:
                    passed_between = None
                elif not exits_between:
                    passed_between = False
                elif any(code is None for code in codes_between):
                    passed_between = None
                else:
                    passed_between = True
                checks["dependent_manager_acceptance_between_workers"] = (
                    False if passed_between is False or diff_late or (diff_tools and not diff_between) else
                    None if passed_between is None or diff_unknown else diff_between)
            else:
                checks["dependent_manager_acceptance_between_workers"] = False
    else:
        checks["direct_baseline"] = not children
    checks["sessions_succeeded"] = all(t["info"].get("outcome") == "succeeded" for t in transcripts)
    return {"verified": bool(checks) and all(v is True for v in checks.values()), "checks": checks}
