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
- Scenarios marked `scenario` in `evals.json` require controlled interaction/fault injection or a manual harness run. Offline tests validate recorder behavior, not model compliance with those scenarios. No synthetic event fixture counts as a live behavioral pass.
- One paired run per case cannot establish a general savings guarantee. Unexecuted harnesses and mode transitions remain unverified.

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
