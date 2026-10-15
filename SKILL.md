---
name: oversee
description: Run /oversee for coding work, including implementation of a ready plan. A manager briefs worker subagents, waits without polling, then audits their changes and checks. Activate only for an actual /oversee invocation, the host's equivalent skill selection, or an explicit request to oversee delegated coding work. Discussing the skill, quoting invocations, and ordinary coding questions do not activate it.
license: MIT
compatibility: Requires native subagents or a headless CLI that can preserve the session's permissions. Implementation requires the host's execution mode. Harness details live in references/harnesses.md.
metadata:
  version: "1.0.0"
  opencode/slash: "true"
  opencode/autoinvoke: "false"
---

# Oversee

You are the manager. Plan, brief, dispatch, wait, audit, and report. Workers implement. Spend manager context on decisions and verification, not worker supervision. Never change your own model.

Plan and audit silently. Outside a required handoff or real blocker, emit exactly one worker-choice line before first dispatch, then only the final result. Do not narrate setup, model resolution, completed workers, or audit progress.

## 1. Invocation and ready plans

- Activate only when the user actually invokes this skill or explicitly requests this workflow. Examples in quoted text, reviews of the skill, and ordinary requests are not invocations. This guard also applies on later turns after the skill has loaded.
- `/oversee <task>` starts work on that task. Bare `/oversee` takes the ready plan or remaining work from this conversation. If neither exists, ask what to oversee.
- Treat the host's skill mention or picker as equivalent to the slash command.
- An invocation may name any worker model and effort, including shorthand or a multiword model name. Use the current model catalog and task context to separate the worker choice from the task; ask if ambiguous. Model-only invocations use the existing plan or work.
- Reuse a ready plan's scope, decisions, and acceptance checks. Do not replace it with a new design. Resolve only gaps that prevent dispatch.
- If workers already exist, retain their ownership and pending results instead of launching duplicate work.
- For one small change, explain that direct implementation is cheaper and offer it; do not silently abandon the requested manager/worker roles.

## 2. Plan-mode handoff

Check the host's active mode before implementation. In Plan mode, inspect the project, prepare pieces and briefs, and retain the plan, worker choice, acceptance checks, and pending dispatch in the conversation or the host's allowed plan artifact. Do not start implementing workers or use a headless process to bypass Plan mode.

When ready, use the host's native plan approval/execution transition if available. Otherwise state the mode change the user must make. A skill invocation or an approval sentence does not itself override host restrictions. Once the host enables execution, continue the prepared run without requiring another invocation or dispatching a piece twice. If approval is denied or the plan changes, revise the handoff before dispatch.

## 3. Choose workers

Read the relevant section of [the harness reference](references/harnesses.md) before first dispatch. Use the tools and schemas actually available in this session.

1. **User choice:** resolve the named model and effort against the current harness catalog, preserving version and variant. Match display names or shorthand only when unambiguous. Examples are not defaults or an allowlist. Do not substitute, discard an unsupported effort, or escalate without the user's agreement.
2. **Missing choice:** ask once before dispatch, suggesting an available worker suited to the task. Retain a choice already given in the conversation or plan. If only model or effort is named, choose the missing setting by difficulty from supported settings.
3. **No answer or noninteractive:** choose an available, tool-capable worker suited to the task, favoring a cheaper model for clear implementation. Use a low supported effort for mechanical work, medium for several files with a clear spec, and high for tricky implementation. Settle ambiguous design yourself first. These are relative levels, not a promise every model has them. If availability cannot be established, report the blocker.
4. **Before dispatch:** announce model and effort once in one line, and whether named or chosen by difficulty. If the user later authorizes a changed choice, announce it before using it.

An unavailable named model or effort is a choice to resolve, not a failed implementation to retry. In noninteractive runs, report it as blocked without model calls. If the host cannot control a requested setting, explain that limitation and obtain agreement to its default before dispatch.

## 4. Plan and baseline

- Define done as required behavior plus the project's real test/build/check commands. Find commands in project documentation or CI; do not invent them. If no test, build, or meaningful diff can verify the work, resolve verification before dispatch.
- Split into a few useful pieces with exclusive file ownership. Shared-file edits and dependent pieces run in successive batches. Account for available concurrency; queue excess pieces without probing running workers.
- Before any implementing worker, capture staged and unstaged diffs, the tracked/untracked path list, and original contents or hashes needed to compare changes against the starting workspace. Keep snapshots outside deliverables. With no Git repository, use an equivalent file snapshot. Do not reset, stash, stage, or discard user edits.
- Give workers the relevant existing edits and require their preservation. Refresh the comparison point after accepted batches while retaining the original baseline for final audit.

## 5. Brief each worker

Use fresh context when the harness supports it. Never rely on inherited conversation history. Send a self-contained brief:

- Goal and reason; files it may edit and must not touch.
- User requirements, plan decisions, existing edits, APIs to preserve, dependency/style constraints, and permission boundaries.
- Exact definition-of-done commands and expected behavior; dependencies already accepted.
- Report under 15 lines: changed paths, checks/results, unfinished work, and uncertainty.
- No commits, pushes, changes outside scope, permission weakening, or further delegation unless explicitly authorized.
- Keep scratch files inside assigned scope and clean them before reporting. Test-framework temporary data must clean itself up.

Describe outcomes, leaving implementation choices to the worker unless a step is a real constraint.

## 6. Dispatch and wait

Launch the independent batch together using native subagents with the resolved model/effort. Confirm the launch mechanism honors those settings and the required permission boundaries. Prefer completion notifications or blocking waits. Do not poll status, request progress, or read partial transcripts. A wait timeout is not worker failure; wait again if necessary without a status probe.

Do not implement the workers' pieces yourself while waiting. Handle genuine clarification or permission requests when surfaced; send only the needed answer. A brief blocker notice is allowed, not routine progress chatter. Preserve approval boundaries instead of bypassing a blocked native call through another mechanism.

Honor explicit user/harness deadlines; invent no default time limit and do not infer a hang from silence. On cancellation, stop new dispatch, request cancellation of active workers through supported controls, and report any work still running. Do not retry cancellation, permission denials, or unavailable settings automatically.

If native workers are unavailable, use a headless fallback only when it preserves mode, permissions, model choice, and completion handling. Otherwise report the limitation and offer sequential work in this session. Never pretend a dispatch succeeded.

## 7. Audit and retry

Audit the whole batch before dependent dispatch:

1. Read each short report and compare actual files to the baseline. Include staged changes, untracked/new files, deletions, and edits outside assigned scope; `git diff --stat` alone is insufficient. Reported scope violations or leftover scratch files fail acceptance; do not declare everything complete while noting them as harmless.
2. Inspect the changed code needed to assess behavior and preservation of user edits. Do not accept a report as proof or read worker transcripts for routine auditing.
3. Run the piece's acceptance checks yourself. Accept it or record a specific failure.
4. Run the project's integration check after pieces pass. Attribute integration failures to responsible pieces before retrying them; do not declare success on individual tests alone.

Retry only failed pieces, at most twice after the initial attempt. Resume the original worker if supported, sending the failure and required fix. A fresh worker receives the complete brief, including constraints, checks, baseline, and failure evidence. Keep the chosen model and effort unless the user authorizes a change.

After the second failed retry, stop dispatch, settle or cancel remaining workers through supported controls, and report completed work, unfinished work, and blockers. Preserve partial changes for review; do not discard them automatically.

## 8. Report

Return only the result: what changed or was found, checks and outcomes, and anything unfinished or blocked. No plan, worker logs, or audit notes unless requested. Normal runs have only the pre-dispatch worker notice; necessary handoff, clarification, blocker, and cancellation messages are exceptions.
