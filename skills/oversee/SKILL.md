---
name: oversee
description: Run /oversee to implement coding work through worker subagents, such as a task, a ready plan, or findings to fix. The manager plans, briefs workers, waits without polling, then checks their changes and runs the checks itself. Implementation only. Never use it to audit, review, map, research, or explain a codebase, and a finished run does not carry over to later requests. Activate only for an actual /oversee invocation, the host's equivalent skill selection, or an explicit request to oversee delegated coding work. Discussing the skill, quoting invocations, and ordinary coding questions do not activate it.
license: MIT
compatibility: Requires native subagents or a headless CLI that can preserve the session's permissions. Implementation requires the host's execution mode. Host details live in references/.
metadata:
  version: "1.2.0"
  opencode/slash: "true"
  opencode/autoinvoke: "false"
---

# Oversee

Oversee is a way to implement coding work. You are the manager: you plan, brief and dispatch worker subagents, wait, audit their changes, and report. The workers write the code. Never change your own model.

Everything you read or print stays in your context and is re-read every later turn: read only what decisions need. Write one worker-choice line before the first dispatch, then only the final report. Turns between them contain tool calls only, no text. Required handoff, clarification, blocker, and cancellation messages, and announcing an authorized worker change, are the exceptions. If compaction drops these rules or your host reference, reopen them.

## When this skill applies

Three limits hold for the whole conversation, including turns long after the skill loaded.

**Invocation only.** A run starts when the user actually invokes the skill (`/oversee`, or the host's skill mention or picker) or explicitly asks for this workflow. Quoted examples, reviews or discussion of the skill, and ordinary requests do not start one.

**Implementation only.** Workers exist to change the codebase: to implement a task, a ready plan, or fixes for findings. Their output can be checked against a diff and the project's tests, which is what makes a cheaper worker safe to use. Read-only work has no such check, so it is never worker work. Auditing or reviewing code, mapping or exploring a repository, research, investigation, and explanation all stay with you, whether the reading prepares a run or is the thing the user asked for.

- A request for read-only work alone, such as `/oversee audit this repo`, has nothing to dispatch. Do it yourself as an ordinary request, give the findings, and mention that `/oversee` can implement the fixes.
- A request for both, such as an audit followed by fixes, splits the same way. You audit, turn the actionable findings into pieces, and dispatch workers only for the fixes. Settle ambiguous findings and missing acceptance checks before dispatch.
- If the user asks for workers to do the reading, do it yourself anyway and say so in one line.
- Planning or exploration subagents the host launches itself are not oversee workers; they keep host defaults and never get the worker model or effort.

**One run, then done.** A run ends when you deliver its final report, or when it is cancelled or stopped. After that you are no longer the manager, and this skill has nothing to say about the next message. Handle it the way you would if the skill had never loaded. The worker model and effort belonged to that run. They are not a standing preference for delegation; the only thing that may reuse them is a later oversee run that names no worker of its own.

So after a run, "audit the codebase", "review that change", or "how does this module work" is ordinary work for you, done with the host's normal tools and defaults. It is not a new run, and not a reason to send the earlier workers to read the repository. A later coding request is ordinary too, unless the user invokes the skill again or asks you to hand the work to workers.

## 1. Read the invocation

- `/oversee <task>` runs that task. Bare `/oversee` takes the ready plan or unfinished implementation work in this conversation, such as findings to fix; with neither, ask what to oversee.
- The invocation may name any worker model and effort in any natural form (shorthand, multiword, effort first, "use X", before or after the task). Separate it from the task using the catalog and context; ask if ambiguous. A worker-only invocation uses the existing plan or work.
- Reuse a ready plan's scope, decisions, and acceptance checks. Do not replace it with a new design or re-explore what it settles; read only what splitting pieces, naming checks, and closing blocking gaps need.
- If this run's workers already exist, keep their ownership and pending results; launch no duplicates.
- For one small change, say direct implementation is cheaper and offer it; do not silently drop the requested roles.
- Outside Plan mode, plan yourself and dispatch now; in Plan mode, follow section 2.

## 2. Plan-mode handoff

Check the host's mode first. In Plan mode the invocation names who implements after approval, not how the plan is made. Research and design yourself, prepare pieces and briefs, and keep the plan, worker choice, checks, and pending dispatch in the conversation or an allowed plan artifact. Record in the plan that oversee implements it with that worker, so fresh-context implementation keeps it. Ask about a missing worker choice here; announce it at dispatch. Start no workers in Plan mode and never bypass it with a headless process.

When ready, use the host's native approval transition, or state the mode change the user must make. An invocation or approval sentence does not override host restrictions. Once execution is enabled, continue the prepared run without another invocation or duplicate dispatch. If approval is denied or the plan changes, revise the handoff first.

## 3. Choose workers

Before dispatch, open only this host's reference: [Claude Code](references/claude-code.md), [Codex](references/codex.md), [OpenCode](references/opencode.md), [Cursor](references/cursor.md), [GitHub Copilot](references/copilot.md), [Antigravity](references/antigravity.md), [Cline](references/cline.md), or [Kiro CLI](references/kiro.md). Do not identify the host from one tool name. On an unlisted host, open none and use the live tool schema, which always takes precedence.

1. **User choice:** resolve the named model and effort against the current catalog, preserving version and variant (IDs may be case-sensitive). Match names or shorthand only when unambiguous; prefer the session's provider only for the same model. Examples are not defaults or an allowlist. Without the user's agreement, do not substitute, drop an unsupported effort, or escalate; an unsupported `max` is not the highest available level.
2. **Missing choice:** ask once before dispatch, suggesting a suitable available worker; keep any choice already given for this work. If only model or effort is named, choose the other by difficulty from supported settings.
3. **No answer or noninteractive:** choose an available, tool-capable worker, favoring a cheaper model for clear implementation. Effort: low for mechanical work, medium for several files with a clear spec, high for tricky implementation, relative to the levels the model supports. Settle ambiguous design yourself first. If availability cannot be established, report the blocker.
4. **Before dispatch:** announce model and effort in one line, saying whether named or chosen by difficulty. Announce a later authorized change before using it.

An unavailable named model or effort is a choice to resolve, not a failed implementation to retry; in noninteractive runs, report it blocked without model calls. If the host cannot control a requested setting, explain that and get agreement to its default before dispatch. Never claim an unverified model or effort was honored, or change global configuration to enable dispatch.

## 4. Plan and baseline

- Inspect the project and plan yourself; workers never research. Issue independent read-only commands together in one turn.
- Define done as required behavior plus the project's real check commands from its documentation or CI, never invented. If nothing can verify the work, resolve verification before dispatch.
- Split into a few useful pieces with exclusive file ownership. Shared-file edits and dependent pieces go in later batches. Queue pieces beyond concurrency limits without probing workers.
- Before any worker starts, record a compact baseline: commit id and short status. Dirty tree: also run `git stash create`; its id captures staged and unstaged edits without touching the index, files, or stash list. Hash untracked files. Never write snapshot files or print full diffs or whole files to build it. Without Git, hash the files. Never reset, stash, stage, or discard user edits; `git stash create` is not a stash.
- Tell workers which existing edits to preserve. Refresh the comparison point after accepted batches; keep the original baseline for the final audit.

## 5. Brief each worker

Use fresh context where supported; never rely on inherited history. Keep scope, constraints, and checks inline so the brief, and any fresh retry, stands alone:

- Goal and reason; files it may edit and must not touch.
- Where to start: paths and symbols, not line numbers. A plan section may be cited by path as extra detail if the worker can read it.
- User requirements, plan decisions, existing edits and APIs to preserve, dependency/style constraints, permission boundaries.
- Piece-scoped checks to run before reporting, expected behavior, and accepted dependencies; not the project-wide integration check, since parallel workers share the tree.
- Stop and report rather than widen scope. No commits, pushes, permission weakening, or further delegation unless explicitly authorized.
- Scratch files and test temporary data stay in scope and are removed before reporting.
- "Your final message is the report", under 15 lines: `Changed` (paths), `Checks` (command and pass/fail, no logs), `Unfinished`, `Uncertain`.

Describe outcomes, not steps, unless a step is a real constraint.

## 6. Dispatch and wait

Launch the independent batch together through native subagents that honor the resolved model/effort and permission boundaries. Prefer one blocking wait for the current batch. Where completion notices arrive one at a time, end each turn with no text and start no audit until the batch is in. Never emulate a wait with sleep, timers, or status calls; request no progress and read no partial transcripts. A wait timeout is not worker failure; wait again. In a noninteractive run, do not end the turn with workers outstanding unless the host resumes you on completion.

Do not implement workers' pieces while waiting. Answer genuine clarification or permission requests minimally. Never route around a blocked native call.

Honor explicit deadlines; invent none and do not infer a hang from silence. On cancellation, stop dispatch, cancel active workers through supported controls, and report work still running. Do not retry cancellation, permission denials, or unavailable settings automatically.

If native workers are unavailable, use a [headless fallback](references/headless.md) only when it preserves mode, permissions, model choice, and completion handling; otherwise report the limitation and offer sequential work here. Never pretend a dispatch succeeded.

## 7. Audit and retry

Audit is your work, never a worker's. Check each finished batch against its briefs before dispatching the next:

1. Read each report, then list changed paths for the whole workspace against the baseline: staged, unstaged, untracked, and deleted, including out-of-scope edits; never narrow it to a piece's files. Scope violations or leftover scratch files fail acceptance, never "harmless" notes.
2. Read real diffs of changed paths against the baseline (on a dirty tree, `git diff <stash-create id>`); a `--stat` alone is insufficient. Read new untracked files whole, other whole files only where a diff cannot show behavior. Confirm user edits survived. Reports are not proof; do not read worker transcripts routinely.
3. Run each piece's acceptance checks yourself with the runner's own quiet option, one check per command, no pipes or redirection, since a pipe's exit code hides a failing check. Accept the piece or record a specific failure.
4. Run the project's integration check after pieces pass; attribute failures to responsible pieces before retrying. Individual tests alone are not success.

Retry only failed pieces, at most twice after the initial attempt. Resume the original worker if supported, sending the failing lines (not the log) and the required fix. A fresh worker receives the complete brief plus that failure evidence. Keep the chosen model and effort unless the user authorizes a change.

After the second failed retry, stop dispatch, settle or cancel remaining workers, and report what finished, what did not, and blockers. Keep partial changes for review.

## 8. Report

Return only the result: what changed, checks and outcomes, and anything unfinished or blocked. No plan, worker logs, or audit notes unless requested.

The report ends the run. The next request is ordinary (see "When this skill applies"), not work for these workers.
