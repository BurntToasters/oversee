# Evaluation

The installed skill has no Python dependency. This development-only tooling uses Python's standard library and a running, authenticated OpenCode v2 service. It reads service discovery credentials in memory; credentials never enter artifacts or command arguments.

Run deterministic checks from the repository root:

```text
python -B -m unittest discover -s tests -v
```

Tests use temporary folders and synthetic evidence. They do not install anything or contact model providers. `tests/test_payload.py` checks the installed payload's layout, frontmatter, byte budgets, and reference links.

## Live pilot

Supply both model choices and supported efforts. No family is baked into the runner. For example, using the caller choices from this development session:

```text
python -B -m evals.run --manager "opencode-go/muse-spark-1.3-contributor" --manager-effort xhigh --worker "opencode-go/deepseek-v4.1-flash" --worker-effort max --output "../oversee-workspace/pilot-new" --preflight
```

Remove `--preflight` to run. Preflight reads the live location-scoped catalog and makes no model calls or session/output directories. Catalog availability does not prove provider authentication; an authentication error at inference stops the run. Display names and unambiguous shorthand are accepted; full IDs preserve case. If multiple providers offer the exact worker, the resolved manager's provider is preferred; specify a full ID to choose another provider. Unknown model/variant choices fail before inference.

An existing OpenCode service is discovered at `~/.local/state/opencode/service.json`, overridable with `--service-file`. The runner reads the service's OpenAPI schema to find supported routes, including experimental routes on v2.0.29. It never changes credentials, provider configuration, subscriptions, or global skill installations. It stages this repository's skill only in each fixture's project-local `.opencode/skills/oversee` directory.

Output must be a new directory outside this repository; existing evidence is never overwritten. Default run: six top-level sessions, one with/without pair for each of parallel implementation, ready-plan dependent implementation, and ordinary-question activation. Both arms use identical manager settings and fixture permission restrictions. Baseline receives the same task without oversee, and implements directly. Plan handoff has a read-only preparation turn and an explicit native switch to Build in the same session; a second skill invocation is not sent.

No default deadline is imposed. An operator can provide `--deadline-seconds N` as an explicit per-session pilot deadline. Transport timeouts reconnect a blocking wait rather than query status. Cancellation or deadline expiry requests interruption of the root and its children. Provider authentication/access errors stop the pilot; reconnect or supply an authorized model and use a new output directory. Never treat an authentication failure as a zero-cost successful run.

For a focused follow-up, add `--case parallel --case plan-handoff --arm with-skill`. Repeated cases are deduplicated. The default remains all six paired sessions. A single-arm rerun is marked unpaired and cannot establish a performance comparison. An expired deadline prevents the Plan-to-Build dispatch as well as further blocking waits. Cancellation interrupts the dispatcher first, then attempts every discoverable descendant; recovery errors are recorded without replacing the original blocker.

## Evidence and limitations

- `preflight.json`: exact resolved models and harness version. `prompt.json`, `session.json`, and `baseline.json` identify the task and initial file hashes. Snapshot version 2 includes project-local skill and permission configuration; only Git internals and Python bytecode caches are excluded.
- `native.json`: complete projected native transcripts for root and descendants, gathered after completion. `plan-phase.json` retains pre-transition evidence. Evidence is local and can contain fixture code and model text; review before sharing.
- `result.json`: independent functional/test outcomes, native orchestration observations, elapsed time, `usage`, and `usage_by_role`. `benchmark.json` retains completed runs and identifies paired or focused execution; `blocked.json` records a run-level blocker. Interrupted runs retain available descendant transcripts and `interruption.json`, including recovery errors. An interruption request alone does not prove all workers stopped.
- Usage sums each native session once; transcript messages and cumulative session totals are never both added. Root totals are treated as that session's usage, with linked child usage added separately. Default zero counters from failed inference are not measurements; unavailable values are `null`.
- `usage_by_role` splits the same counters by session: `manager` is the root session (keyed on the `root` id that `session.json` now records, with fallbacks for older evidence), `workers` and `helpers` split the other sessions by agent type (`explore`, `plan`, `scout` are helpers), `children` is their total (a duplicated root transcript is not a child), and `manager_turns` counts root assistant messages that carry token counts. With no child sessions, `children` is zeros with `sessions: 0`. `usage` is unchanged, so retained evidence regrades the same way, and regrading pre-1.2.0 evidence with `evals.review` yields a manager-only baseline without new model calls.
- Manager diff inspection splits each shell command on `&&`, `;`, and newlines, so `git status --short && git diff` counts as reading the diff. `--stat`, `--name-only`, and `--name-status` still do not.
- A recorded native shell command can establish manager verification. Prose claims cannot. Native Code Mode `metadata.toolCalls` records are inspected alongside direct tools. If a version hides nested execution without native records, audit and no-polling evidence stay unknown rather than passing from code text alone. Silence grading examines every intermediate assistant text block, allowing the model notice and necessary handoff/blocker messages rather than checking a short list of progress phrases.
- OpenCode acceptance also checks the native process exit code for each distinct post-worker test command. Tool completion alone cannot establish passing tests. A successful check for another piece cannot erase a failed check; missing exit evidence stays unknown.
- Scenarios marked `scenario` in `evals.json` require controlled interaction/fault injection or a manual harness run. Offline tests validate recorder behavior, not model compliance with those scenarios. No synthetic event fixture counts as a live behavioral pass.
- One paired run per case cannot establish a general savings guarantee. Unexecuted harnesses and mode transitions remain unverified.

## Manual acceptance and release gates

The `scenario` entries in `evals.json` already cover these behaviors; use their IDs below instead of adding duplicate catalog prompts. A scenario's prompt and expectations are a test specification, not evidence that it passed. Keep each run's native events, resolved settings, before/after fixture state, and independent review together. Offline regression tests prove the recorder, not live agent behavior.

Entries 19-33 are invocation-wording scenarios (natural `use <model>` phrasing, reordered or missing effort, command placement, model-only and ready-plan invocations, pasted or combined audit findings, negative quoted/review/coding prompts, and the host parser limit). They are catalog-only `scenario` specifications, checked for structure by `tests/test_catalog.py`; none has been live-verified.

Entries 34-39 cover planning scope: the worker choice names who implements, not who plans. They specify Plan-mode and normal-mode invocations added to a task, host planning helpers that must keep host defaults, requests for workers to research that the manager must do itself (in and out of Plan mode), and a plan that survives a fresh-context implementation. They are also catalog-only. The OpenCode recorder now fails a plan phase in which any subagent runs with the requested worker setting; when manager and worker settings match, that check is unknown. Regrading older evidence derives this check from retained plan-phase transcripts.

Entries 40-44 cover the implementation-only scope added in 1.1.1: after a finished run, a later audit or coding request is an ordinary request and never reuses the earlier worker; an audit-only or repo-mapping invocation dispatches nothing; a new invocation on reported findings starts a new run. They are catalog-only. A live check needs a multi-turn session that keeps the finished run in context, which the current recorders do not drive.

Entries 45-49 cover the 1.2.0 manager context-economy rules: a ready plan is not re-explored; the baseline is compact (no full diff dumped, no snapshot left behind); briefs give start pointers instead of pasted file contents and workers return the fixed `Changed`/`Checks`/`Unfinished`/`Uncertain` report; checks run quietly with their real exit code (no pipes); and staggered completion notices produce no text and no early audit. They are catalog-only scenarios; the pilot comparison in "1.1.1 versus 1.2.0" below is the only cost measurement so far.

Entries 50-54 cover the 1.2.0 baseline audit: a worker commit is caught by diffing against the baseline commit id (50); a repository with no commits is hashed (51); a new file inside an already-untracked folder is listed through `-uall` (52); a failing `git stash create`, as with Codex's read-only `.git`, falls back to hashes (53); and an explicitly authorized commit is not failed (54). All are catalog-only. Pilot fixtures are now committed before a run, and the OpenCode allowlist adds exactly `git rev-parse`, `git log`, `git stash create`, and `git hash-object` beside the existing `git status`, `git diff`, and `git ls-files` rules; `tests/test_fixtures.py` checks both. Retained evidence predates this and used uncommitted fixtures.

The dependent manager-acceptance grading and Codex distinct-check/cleanup regressions are offline tooling checks against retained or synthetic evidence. They verify evaluator behavior and evidence persistence; they add no live proof that an agent honors dependency gates or cleans up its work.

| Existing case | Controlled procedure | Pass evidence |
|---|---|---|
| `10 dirty-workspace` | Before dispatch, create separate staged, unstaged, and untracked sentinel changes in a disposable repository and record the index, worktree, and file contents independently. Run the scoped task, including an out-of-scope worker edit for the audit to catch. | Every pre-existing change is byte-for-byte preserved in its original state; the manager identifies the out-of-scope edit and does not stage, stash, reset, or discard anything. |
| `12 retry` | Inject a failure in the initial worker attempt and both permitted repair attempts. Capture each full brief and the failure evidence sent to each retry. | No more than three attempts total; each retry retains all scope and constraints; no model/effort escalation; the final result leaves the piece unfinished with the blocker stated. |
| `13 cancel` | Dispatch two independent pieces, then cancel while both workers are active. Record cancellation requests and each descendant's final native state. | No dispatch after cancellation; cancellation is requested for every discoverable active worker; no later worker edits occur. If the host cannot establish that workers settled, mark the outcome unknown rather than passing. |
| `18 handoff-denied` | Start in native Plan mode with a ready plan and selected worker. Deny the host's execution transition or change the plan before approval. | No implementation worker starts and no implementation edits appear; the plan and worker choice are retained or revised for another approval; no headless permission bypass occurs. |
| Existing `parallel` and `plan-handoff` pilots: narration | Capture intermediate manager output separately from worker reports. Retain worker reports as audit evidence, but do not apply the silence check to them. | Allow the initial manager dispatch notice and necessary clarification, approval, blocker, or cancellation messages; fail routine manager progress, setup, audit, or completion narration. Worker reports remain audit inputs and do not count as manager narration. The retained Go and Codex runs emitted extra manager narration, so this gate is currently failing. |

For each primary host/version without live evidence (OpenCode v1, Claude Code, and Cursor), run the existing `explain`, `parallel`, and `plan-handoff` pilots using the host's native interface and caller-selected supported settings. Retain native dispatch/completion records, exact resolved manager and worker settings, fixture snapshots, manager checks, and the host's actual Plan-to-execution transition. The ordinary question must leave the fixture unchanged and spawn no workers; parallel work must show overlapping scoped workers; dependent work must wait for accepted prerequisites. Test the published invocation surface separately. In OpenCode v1 and v2, verify the version-specific TUI behavior directly. The v2 pilot sent `/oversee` as ordinary text through the local service API's `session.prompt` operation and attached the skill by ID; this bypasses the TUI slash parser. Current v2 docs describe `@oversee` or native skill loading. Claim `/oversee` in the TUI only after directly testing it there.

Copilot and Antigravity are best-effort hosts; the same pilots may be run there, but they are not release gates. Before removing the preview label, the offline regression suite and version consistency check must pass, and the live gates above must have retained passing evidence on every primary host (Claude Code, Codex, Cursor, OpenCode). These gates document observed compatibility; they do not establish a general reliability or cost-savings guarantee.

## Observed pilot (2026-10-14)

The first attempt reached OpenCode but failed Console authentication with `Reconnect OpenCode Console to continue.` No workers ran. Raw evidence is in sibling `oversee-workspace/reliability-pilot`; its original default zero counters are not valid performance measurements. The recorder now stops at the first provider failure.

The caller then selected the connected Go provider: `opencode-go/muse-spark-1.3-contributor#xhigh` managing `opencode-go/deepseek-v4.1-flash#max`. Six top-level sessions completed in `oversee-workspace/reliability-pilot-go`. Native evidence verifies exact models/efforts, concurrent independent workers, dependent sequencing, Plan-mode preservation and native Build transition, manager checks, and no observed status polling. Both overseen coding cases passed independent behavior checks. Ordinary questions did not activate oversee or spawn workers. The direct dependent baseline stopped after its store phase, leaving CLI behavior incomplete.

Both overseen coding runs emitted extra routine narration, so strict orchestration grading does not pass. The dependent run also reported an uncleaned temporary test database outside its fixture. Its exact contents and creation time matched this pilot; the development agent removed it after verification. The skill's silence and scratch-file acceptance rules were tightened after these observations. Other harnesses and manual/fault-injection scenarios remain unverified.

Observed native costs across the three overseen cases total $0.029469, versus $0.006872 for direct baselines; the incomplete dependent baseline limits comparison. This pilot does not demonstrate savings. Usage includes parent and child sessions once, with cache and reasoning reported separately.

### Focused follow-up (2026-10-14)

Two with-skill coding sessions retested that final wording with the same Go manager/worker settings. Evidence is in `oversee-workspace/reliability-audit-2`; this follow-up has no new baseline arm. Parallel work passed seven tests and independent probes in 83.66 seconds; dependent Plan-to-Build work passed thirteen tests and independent probes in 227.37 seconds. Native events again verify requested settings, worker concurrency/sequencing, manager verification, and Plan-mode preservation. No status polling was observed.

Both sessions still fail strict silence grading. Parallel work emitted “Auditing results — final report to follow.” The handoff session added setup and worker-completion chatter. Stronger skill wording has not eliminated this model behavior; do not claim result-only compliance. Neither final report identified leftover scratch files, but that is not proof of external filesystem cleanliness. Total recorded cost was $0.033859 across six distinct manager/child sessions. These are observations from two runs, not a reliability rate or performance comparison.

Regrade without inference, using a new destination:

```text
python -B -m evals.review ../oversee-workspace/reliability-pilot-go --output ../oversee-workspace/pilot-review-new
```

Before executing checks, review compares every retained project against its recorded final snapshot. Missing or changed artifacts stop review before output creation. Older snapshots retain their original exclusions, including `.opencode`; their excluded files cannot be verified retrospectively. These local hashes detect drift, not deliberate alteration of both files and records. The derived report corrects the original recorder's recognition of hydrated native skill attachments and separates final answers from intermediate text. Original native evidence remains unchanged. Review output reflects the current grader, not a new behavioral run.

## Codex smoke tests (2026-10-15)

The installed Codex CLI is `0.162.0-alpha.17.2` on Windows. Official [app-server documentation](https://learn.chatgpt.com/docs/app-server) and the installed generated schema were checked before dispatch. Use exact live catalog IDs and supported effort levels; this adapter is development tooling, not a runtime dependency of the skill.

```text
python -B -m evals.codex_run --manager gpt-6.1-sol --manager-effort medium --worker gpt-6-luna --worker-effort max --output ../oversee-workspace/codex-new --preflight
```

These settings were explicitly selected by the caller. Remove `--preflight` for three unpaired smoke cases, or use `--case explain`, `--case parallel`, or `--case plan-handoff` for a focused run. Unsupported inputs stop before inference. Skills are staged in fixture-local `.agents/skills/oversee`; real-profile installations and settings remain unchanged. Each case uses a separate stdio app-server with workspace-write execution, restricted network, and no automatic permission grants. Plan preparation uses native Plan mode and read-only sandboxing; the test host explicitly switches the next turn to Default and enables fixture writes. No second skill invocation is sent. API request transport timeouts are separate from the notification wait, which has no default worker deadline.

`events.json` retains native notifications and their receipt times, including tools omitted from projected thread history. `native.json` retains available thread records and persisted `turn_context` entries. Current `subAgentActivity.agentThreadId`, generic child-thread notifications, and legacy receiver arrays all identify descendants. Configured thread settings alone do not prove a turn's model/effort. Usage uses the latest cumulative native token counters for each unique root/child thread; missing metrics and cost remain unknown. `usage_by_role` splits those counters into the root thread (`manager`), worker and `explorer` helper descendants (`workers`, `helpers`; helper detection reads thread metadata best-effort), and their total (`children`); empty groups report cost as `null`; `manager_turns` is `null` because the events carry cumulative totals only. The runner's exit status covers functional smoke checks; it does not certify orchestration.

Review completed evidence without inference, using a new destination:

```text
python -B -m evals.codex_review ../oversee-workspace/codex-smoke-1 --output ../oversee-workspace/codex-review-new
```

Review checks final file hashes before executing project tests, recovers this run's persisted root/child contexts through app-server, and grades native events independently. This requires the same local Codex history to remain available. It does not overwrite original evidence. Interrupted/incomplete cases retain events, but are not successful smoke runs. Recovery and cancellation requests do not prove all background work stopped.

Observed evidence is in `oversee-workspace/codex-smoke-1`, with derived review in `oversee-workspace/codex-smoke-1-reviewed`. All three functional cases passed. Ordinary-question behavior left files unchanged and dispatched no workers. Parallel implementation passed eight tests and strict observed orchestration checks in 79.77 seconds, with two overlapping exact-model workers and manager verification. Dependent implementation passed fourteen tests and independent probes in 201.63 seconds; native contexts verify Plan-to-Default transition, exact retained model settings, and sequential workers. It still emitted routine progress narration and fails strict silence. Ordinary-question runtime was 18.16 seconds. These three cases comprise seven distinct threads. Cost is unknown, and there is no new Codex baseline arm or savings claim.

The initial smoke exporter missed current child-event shapes; original projected `native.json` files contain incomplete child coverage. The derived review recovers children from retained native events and persisted contexts without additional inference. Original event evidence remains intact. The original Plan-phase snapshot was recorded as a driver-computed equality result; future runs retain the actual phase hashes too. Retry limits, dirty-workspace preservation, cancellation, and denied handoff still require controlled behavioral tests.

## Codex 1.2.0 smoke tests (2026-11-16)

Codex CLI 0.169.0 on macOS. `gpt-6.1-sol` is not in this account's model catalog, so the caller chose `gpt-5.6-terra` medium as manager and `gpt-6-luna` max as worker. Evidence: `oversee-workspace/codex-1.2.0`; derived review: `oversee-workspace/codex-1.2.0-reviewed`.

All three cases passed behavior checks, exact manager and worker settings, and no status polling. The ordinary question left files unchanged, spawned no workers, and did not activate the skill (23 s). The parallel case ran two overlapping workers, took the `-uall` baseline, audited with `git diff <id>`, and had no narration (93 s). The dependent case used the native Plan-to-Default transition, sequenced its workers, and diffed and tested between them (251 s).

The strict review still fails two items. First, the fixture prompts say `python -m unittest` and this Mac has only `python3`. In the parallel case the manager reported that verification could not run instead of trying `python3`. In the dependent case it reran the checks with `python3` and they passed, but the review keys checks by command text, so the failed `python` command still fails `manager_runs_successful_checks` and between-worker acceptance. Second, the dependent Plan phase opened with one sentence of narration before planning. Cost is unknown because Codex reports tokens only: the manager thread used 57% of parallel input tokens and 52% of dependent input tokens.

The pilot prompts now use a `{python}` placeholder (`python3`, or `python` on Windows). The rerun of the parallel case (`codex-1.2.0-r2`, derived review `codex-1.2.0-r2-reviewed`) passed every strict check, including manager checks and silence, in 69 s; the manager thread used 51% of input tokens. The dependent case was rerun twice (`codex-1.2.0-r3`, `codex-1.2.0-r4`, with derived reviews). Both passed behavior, exact settings, sequencing, manager checks with `python3`, diffs between workers, and the native Plan-to-Default transition (217 s and 269 s). Both still opened the Plan phase with one sentence announcing the skill, the second after `SKILL.md` and `codex.md` gained a no-preamble rule; the manager opens `codex.md` only at dispatch, and the cause is not established. That sentence is the only strict failure left in the Codex cases.

## 1.1.1 versus 1.2.0 (2026-11-16, macOS)

Same settings for both versions, one with-skill run per case, no direct baseline arm. The 1.1.1 runs staged the `main` skill folder with the current runner and fixtures, so only the skill differs.

OpenCode 2.3.0, `anthropic/claude-opus-5-5#medium` managing `opencode-go/deepseek-v4.1-flash#max`. Evidence: `oversee-workspace/pilot-1.1.1` and `pilot-1.2.0-r2`. Worker cost reads $0 because the Go provider reports no per-call cost; tokens are recorded.

| Case | 1.1.1 cost / manager turns / manager cache read | 1.2.0 cost / turns / cache read | Silence |
|---|---|---|---|
| parallel | $0.3310 / 11 / 323,525 | $0.2021 / 9 / 180,606 | 1.1.1 fails, 1.2.0 passes |
| plan-handoff | $0.3573 / 13 / 420,559 | $0.2984 / 12 / 294,457 | 1.1.1 fails, 1.2.0 passes |
| explain | $0.1023 / 4 / 48,899 | $0.0954 / 4 / 48,930 | both pass |

All six passed tests and behavior probes; the explain case dispatched no workers. 1.2.0 parallel fails `manager_checks_succeeded` only because the prompt's `python` is missing on this machine (exit 127); the manager reran the same check with `python3`, which passed.

The first 1.2.0 attempt (`pilot-1.2.0`, interrupted after 31 minutes) found a defect: "Issue independent read-only commands together in one turn" led the manager to chain its baseline with `ls`, `cat`, and pipes; the allowlist denied the whole command, the manager concluded the shell was blocked and asked an unanswerable question. The wording now says separate calls, never chained, and `opencode.md` says a denied command blocks only that command. `pilot-1.2.0-r2` ran every command separately.

Claude Code 2.1.325, `claude -p` with `--model claude-opus-5-5 --effort medium`, `/oversee haiku` on the parallel fixture with an unstaged README edit and an untracked file, `acceptEdits`, and an allowlist of `python3 -m unittest` and read-only git commands. Evidence: `oversee-workspace/cc-1.1.1`, `cc-1.2.0`, `cc-1.2.0-r2`, `cc-1.2.0-r3`, `cc-1.2.0-r4`, `cc-1.2.0-r5`, `cc-1.2.0-r6`, `cc-1.2.0-neg` (stream-json events plus final project).

| Run | Total | Opus manager | Haiku workers | Intermediate manager text |
|---|---|---|---|---|
| 1.1.1 | $0.3337 | $0.3280 | $0.0058 | 2 messages; tried to write diff snapshots to `/tmp` (denied) |
| 1.2.0 | $0.3261 | $0.3211 | $0.0050 | none; armed a 30-minute `ScheduleWakeup`, then cancelled it |
| 1.2.0 rerun (fixes above, plus no wake-ups in `claude-code.md`) | $0.3251 | $0.3192 | $0.0058 | 3 messages, 2 of them after the host's "no visible output" prompt |
| 1.2.0 third run (`claude-code.md` tells the manager to set `run_in_background: false`) | $0.2621 | $0.2553 | $0.0068 | none |
| 1.2.0 fourth run (`CLAUDE_CODE_FORK_SUBAGENT=1`, so no `run_in_background`) | $0.3541 | $0.3483 | $0.0058 | `Waiting for 2 workers.`, then `Waiting for 1 worker.` |
| 1.2.0 fifth run (blocking; `SKILL.md` asks for plain check commands) | $0.2727 | $0.2661 | $0.0066 | none |
| 1.2.0 sixth run (blocking; the brief quotes the check rule) | $0.2544 | $0.2502 | $0.0042 | none |

All six were correct, kept the user's edits, and left HEAD unchanged. The 1.2.0 runs used the `git stash create` id and `git diff <id>`. In the first two 1.2.0 runs the workers ran in the background, and each silent turn end made the host ask for visible output ("Your previous response had no visible output"), which forced narration and an extra manager turn; the rerun also spent a no-op `true` command on waiting. The `claude -p` `Agent` schema has `run_in_background`; in the third run the manager set it to `false` on both calls, blocked once, wrote only the worker line and the report, and cost 21% less than 1.1.1. The host prompt is not specific to `-p`: the 2.1.325 binary sends it once per query whenever a main-agent turn ends with no visible text, so interactive sessions with fork mode on (which cannot block) are still affected. `CLAUDE_CODE_FORK_SUBAGENT=1` removes `run_in_background` from the `-p` schema too (checked with a Haiku schema probe; `0` and unset keep it), so the fourth run reproduces that case headless: the manager launched both workers in one message, ended each waiting turn with the one fixed line from `claude-code.md`, got no host prompt, and wrote nothing else before the report. Each completion notice costs a manager turn; across three fork-mode parallel runs the cost was $0.23-0.35 against $0.25-0.27 for four blocking runs (see the recorder section below). An interactive session itself was not run. In runs one to five, workers appended `; echo "exit=$?"` to their checks, which the allowlist denied; the manager ran the checks itself. In the fifth run `SKILL.md` said "each one plain command": the manager wrote plain commands but did not pass the rule on, and one worker still appended `; echo`, then retried without it. `SKILL.md` now puts the rule in the brief as a quoted instruction. In the sixth run both briefs carried it, the workers ran their checks as written, and nothing was denied.

Two negative prompts ran in the same fixture with the skill installed (`cc-1.2.0-neg`): an ordinary question about `right.py` and a question about a quoted `/oversee haiku: ...` command. Neither invoked the skill or spawned a worker, both answered directly, and the files were unchanged ($0.084 and $0.069).

The manager is 97-98% of Claude Code cost here. One run per case on one machine: these are observations, not a savings guarantee.

## Claude Code recorder

```bash
python -B -m evals.claude_run --manager-model claude-opus-5-5 --manager-effort medium --worker haiku --output ../oversee-workspace/claude-new
```

`evals/claude_run.py` runs the three pilot prompts through `claude -p` in a committed fixture that also has an unstaged README edit and an untracked `notes.txt`, with the skill in an ignored `.claude/skills/oversee`. Permissions are `acceptEdits` plus an allowlist of `Agent`, file tools, test-runner commands, and read-only git; it never adds auto-approval flags. `--fork-mode on` sets `CLAUDE_CODE_FORK_SUBAGENT=1`, which removes `run_in_background`, as in an interactive session. It keeps `events.jsonl` (stream-json) and grades it: worker model and batch, worker-choice line, no text between dispatch and report other than `Waiting for N workers.`, no host "no visible output" prompt, no polling tools, the latest run of each manager check passing after the workers, a diff read, and for the dependent case sequenced workers with a passing check between them. The plan-handoff prompt runs outside Plan mode (headless runs cannot approve a plan), so it tests dependent implementation, not the handoff.

Results on 2026-11-16 (Claude Code 2.1.325, Opus 5.5 medium managing Haiku; one run each):

| Run | Case | Mode | Cost | Verified | Notes |
|---|---|---|---|---|---|
| `claude-1.2.0` | explain | default | $0.113 | yes | no workers, no skill |
| `claude-1.2.0` | parallel | default | $0.257 | yes | |
| `claude-1.2.0` | dependent | default | $0.345 | yes | manager `shasum` denied |
| `claude-1.2.0-fork` | parallel | fork on | $0.226 | no | one mid-audit sentence; `shasum` denied |
| `claude-1.2.0-fork` | dependent | fork on | $0.377 | yes | `shasum` denied |
| `claude-1.2.0-fork-r2` | parallel | fork on | $0.275 | yes | after the fixes below |
| `claude-1.2.0-r2` | dependent | default | $0.328 | yes | after the fixes below |

After the first five, `SKILL.md` names `git hash-object` for untracked files and `claude-code.md` says to write nothing but the waiting line before the report; both reruns had no denials and no extra text. All seven kept the user's edit and untracked file, left HEAD and the stash list unchanged, and passed the fixture tests and behavior probe. Blocking parallel runs of the same case cost $0.254-0.273 over four runs; fork-mode runs ranged $0.226-0.354 over three, so a single-run difference of that size is noise.

## Install smoke tests

skills CLI 1.7.6 (local-path source) and 1.9.0 ran on macOS against a throwaway `HOME` with telemetry off. On 2026-11-16 with 1.9.0, a local-path install for all eight hosts wrote one canonical copy to `~/.agents/skills/oversee`, identical to `skills/oversee/` including `agents/openai.yaml`, used it directly for Codex, Cursor, OpenCode, Copilot, and Cline, and symlinked it into `~/.claude/skills`, `~/.gemini/config/skills`, and `~/.kiro/skills`. A GitHub-source install (`main`) recorded the source commit in the lock file; `update` reported it current and `remove` deleted the copy and every link. `update` across the 1.7-to-1.8 layout move and Windows links are untested.

## Other harnesses

As of 2026-10-15, Claude Code and Copilot CLI were not found on PATH (Claude Code 2.1.325 was run on macOS on 2026-11-16; see above). Cursor 3.24.18 and Antigravity app 2.23.1.0 are installed; standalone agent CLIs were not found on PATH or the checked common locations. Their GUI workflows were not exercised. No harness installers, account changes, or global skill installs were performed. Current [Antigravity skill docs](https://antigravity.google/docs/skills/) now confirm separate app and CLI global paths and automatic CLI slash commands; this resolves documentation uncertainty, not live discovery.

For each remaining harness, stage the portable payload only in a throwaway workspace, select supported manager/worker settings, and run the three existing pilot prompts with equivalent acceptance checks. Preserve native events, exact resolved settings, before/after artifacts, and host mode transitions. Verify ordinary and quoted commands do not activate oversee. Run retry/cancellation/dirty-workspace/denied-handoff scenarios under controlled interaction. Record launch, authentication, permission, or schema blockers separately from skill failures. Do not add auto-approval flags to make a harness pass.

## Grading rules (1.2.0)

- A check counts only as a single unpiped command: `python`/`python3`/`python3.X`/`py` (optional path or `.exe`, interpreter flags) followed directly by `-m unittest`. Pipes, redirection, chains, command substitution, and `-c` are rejected. PowerShell `-Command` and POSIX `sh`/`bash`/`zsh -c`/`-lc` wrappers are unwrapped first. The `py -3.X` launcher form is not recognized.
- Diff inspection means `git [global options] diff` showing content; `--stat`, `--numstat`, `--shortstat`, `--name-only`, `--quiet`, `--no-patch`, and similar summaries, piped or redirected diffs, and text inside quotes do not count. Reading a file counts only when it is a changed path.
- Silence: each user turn may end with one text after its last tool call (a plan shown for approval, a question, the final report); any other manager text is narration, keywords no longer exempt it. The run must end with a report after the last tool call and worker completion. One single-line worker notice naming model and effort as whole words is allowed.
- Codex: more than two worker spawns pass when extra spawns are retries; helper threads are ignored for worker settings. Regrading retained Windows Codex evidence can change `manager_runs_successful_checks`, because chained `git diff; …; python -m unittest` commands no longer count as checks.
- The OpenCode recorder repeats wait and child listing until the child set is stable, so late dependent workers are exported. Review skips a case without `after.json` and says so.
