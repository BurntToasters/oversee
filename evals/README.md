# Evaluation

The installed skill has no Python dependency. This development-only tooling uses Python's standard library and a running, authenticated OpenCode v2 service. It reads service discovery credentials in memory; credentials never enter artifacts or command arguments.

Run deterministic checks from the repository root:

```text
python -B -m unittest discover -s tests -v
```

The Bash installer tests need Bash; batch and remote PowerShell tests need Windows. Test profiles, mock downloads, archives, and fault-injection wrappers are temporary. Tests do not install to the real profile or contact model providers. In a restricted Windows sandbox, Git Bash may need a test-only escalation to traverse temporary-directory ancestors.

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
- `result.json`: independent functional/test outcomes, native orchestration observations, elapsed time, and usage. `benchmark.json` retains completed runs and identifies paired or focused execution; `blocked.json` records a run-level blocker. Interrupted runs retain available descendant transcripts and `interruption.json`, including recovery errors. An interruption request alone does not prove all workers stopped.
- Usage sums each native session once; transcript messages and cumulative session totals are never both added. Root totals are treated as that session's usage, with linked child usage added separately. Default zero counters from failed inference are not measurements; unavailable values are `null`.
- A recorded native shell command can establish manager verification. Prose claims cannot. Native Code Mode `metadata.toolCalls` records are inspected alongside direct tools. If a version hides nested execution without native records, audit and no-polling evidence stay unknown rather than passing from code text alone. Silence grading examines every intermediate assistant text block, allowing the model notice and necessary handoff/blocker messages rather than checking a short list of progress phrases.
- OpenCode acceptance also checks the native process exit code for each distinct post-worker test command. Tool completion alone cannot establish passing tests. A successful check for another piece cannot erase a failed check; missing exit evidence stays unknown.
- Scenarios marked `scenario` in `evals.json` require controlled interaction/fault injection or a manual harness run. Offline tests validate recorder behavior, not model compliance with those scenarios. No synthetic event fixture counts as a live behavioral pass.
- One paired run per case cannot establish a general savings guarantee. Unexecuted harnesses and mode transitions remain unverified.

## Manual acceptance and release gates

The `scenario` entries in `evals.json` already cover these behaviors; use their IDs below instead of adding duplicate catalog prompts. A scenario's prompt and expectations are a test specification, not evidence that it passed. Keep each run's native events, resolved settings, before/after fixture state, and independent review together. Offline regression tests prove the recorder and installer test harness, not live agent behavior.

Entries 19-33 are invocation-wording scenarios (natural `use <model>` phrasing, reordered or missing effort, command placement, model-only and ready-plan invocations, pasted or combined audit findings, negative quoted/review/coding prompts, and the host parser limit). They are catalog-only `scenario` specifications, checked for structure by `tests/test_catalog.py`; none has been live-verified.

The dependent manager-acceptance grading and Codex distinct-check/cleanup regressions are offline tooling checks against retained or synthetic evidence. They verify evaluator behavior and evidence persistence; they add no live proof that an agent honors dependency gates or cleans up its work.

| Existing case | Controlled procedure | Pass evidence |
|---|---|---|
| `10 dirty-workspace` | Before dispatch, create separate staged, unstaged, and untracked sentinel changes in a disposable repository and record the index, worktree, and file contents independently. Run the scoped task, including an out-of-scope worker edit for the audit to catch. | Every pre-existing change is byte-for-byte preserved in its original state; the manager identifies the out-of-scope edit and does not stage, stash, reset, or discard anything. |
| `12 retry` | Inject a failure in the initial worker attempt and both permitted repair attempts. Capture each full brief and the failure evidence sent to each retry. | No more than three attempts total; each retry retains all scope and constraints; no model/effort escalation; the final result leaves the piece unfinished with the blocker stated. |
| `13 cancel` | Dispatch two independent pieces, then cancel while both workers are active. Record cancellation requests and each descendant's final native state. | No dispatch after cancellation; cancellation is requested for every discoverable active worker; no later worker edits occur. If the host cannot establish that workers settled, mark the outcome unknown rather than passing. |
| `18 handoff-denied` | Start in native Plan mode with a ready plan and selected worker. Deny the host's execution transition or change the plan before approval. | No implementation worker starts and no implementation edits appear; the plan and worker choice are retained or revised for another approval; no headless permission bypass occurs. |
| Existing `parallel` and `plan-handoff` pilots: narration | Capture intermediate manager output separately from worker reports. Retain worker reports as audit evidence, but do not apply the silence check to them. | Allow the initial manager dispatch notice and necessary clarification, approval, blocker, or cancellation messages; fail routine manager progress, setup, audit, or completion narration. Worker reports remain audit inputs and do not count as manager narration. The retained Go and Codex runs emitted extra manager narration, so this gate is currently failing. |

For each primary host/version without live evidence (OpenCode v1, Claude Code, and Cursor), run the existing `explain`, `parallel`, and `plan-handoff` pilots using the host's native interface and caller-selected supported settings. Retain native dispatch/completion records, exact resolved manager and worker settings, fixture snapshots, manager checks, and the host's actual Plan-to-execution transition. The ordinary question must leave the fixture unchanged and spawn no workers; parallel work must show overlapping scoped workers; dependent work must wait for accepted prerequisites. Test the published invocation surface separately. In OpenCode v1 and v2, verify the version-specific TUI behavior directly. The v2 pilot sent `/oversee` as ordinary text through the local service API's `session.prompt` operation and attached the skill by ID; this bypasses the TUI slash parser. Current v2 docs describe `@oversee` or native skill loading. Claim `/oversee` in the TUI only after directly testing it there.

For macOS and current-revision WSL, run local install, update, and uninstall from a clone with `HOME` directed to a disposable profile; verify the complete `SKILL.md` and `references/` payload, replacement of old references, and preservation of unrelated skills. Exercise internet installation against the same disposable profile if claiming that path on the platform. Do not test against the real user profile.

Copilot and Antigravity are best-effort hosts; the same pilots may be run there, but they are not release gates. Before removing the preview label, the offline regression suite and version consistency check must pass, and the live gates above must have retained passing evidence on every primary host (Claude Code, Codex, Cursor, OpenCode) and claimed platform. These gates document observed compatibility; they do not establish a general reliability or cost-savings guarantee.

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

`events.json` retains native notifications and their receipt times, including tools omitted from projected thread history. `native.json` retains available thread records and persisted `turn_context` entries. Current `subAgentActivity.agentThreadId`, generic child-thread notifications, and legacy receiver arrays all identify descendants. Configured thread settings alone do not prove a turn's model/effort. Usage uses the latest cumulative native token counters for each unique root/child thread; missing metrics and cost remain unknown. The runner's exit status covers functional smoke checks; it does not certify orchestration.

Review completed evidence without inference, using a new destination:

```text
python -B -m evals.codex_review ../oversee-workspace/codex-smoke-1 --output ../oversee-workspace/codex-review-new
```

Review checks final file hashes before executing project tests, recovers this run's persisted root/child contexts through app-server, and grades native events independently. This requires the same local Codex history to remain available. It does not overwrite original evidence. Interrupted/incomplete cases retain events, but are not successful smoke runs. Recovery and cancellation requests do not prove all background work stopped.

Observed evidence is in `oversee-workspace/codex-smoke-1`, with derived review in `oversee-workspace/codex-smoke-1-reviewed`. All three functional cases passed. Ordinary-question behavior left files unchanged and dispatched no workers. Parallel implementation passed eight tests and strict observed orchestration checks in 79.77 seconds, with two overlapping exact-model workers and manager verification. Dependent implementation passed fourteen tests and independent probes in 201.63 seconds; native contexts verify Plan-to-Default transition, exact retained model settings, and sequential workers. It still emitted routine progress narration and fails strict silence. Ordinary-question runtime was 18.16 seconds. These three cases comprise seven distinct threads. Cost is unknown, and there is no new Codex baseline arm or savings claim.

The initial smoke exporter missed current child-event shapes; original projected `native.json` files contain incomplete child coverage. The derived review recovers children from retained native events and persisted contexts without additional inference. Original event evidence remains intact. The original Plan-phase snapshot was recorded as a driver-computed equality result; future runs retain the actual phase hashes too. Retry limits, dirty-workspace preservation, cancellation, and denied handoff still require controlled behavioral tests.

## Other harnesses

As of 2026-10-15, Claude Code and Copilot CLI were not found on PATH. Cursor 3.24.18 and Antigravity app 2.23.1.0 are installed; standalone agent CLIs were not found on PATH or the checked common locations. Their GUI workflows were not exercised. No harness installers, account changes, or global skill installs were performed. Current [Antigravity skill docs](https://antigravity.google/docs/skills/) now confirm separate app and CLI global paths and automatic CLI slash commands; this resolves documentation uncertainty, not live discovery.

For each remaining harness, stage the portable payload only in a throwaway workspace, select supported manager/worker settings, and run the three existing pilot prompts with equivalent acceptance checks. Preserve native events, exact resolved settings, before/after artifacts, and host mode transitions. Verify ordinary and quoted commands do not activate oversee. Run retry/cancellation/dirty-workspace/denied-handoff scenarios under controlled interaction. Record launch, authentication, permission, or schema blockers separately from skill failures. Do not add auto-approval flags to make a harness pass.
