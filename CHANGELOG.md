# Changelog

Changes to the `oversee` skill, by version. The version comes from `version.txt` (`python bump-ver.py`). Dates are release dates; an unreleased version is marked as such.

## 1.0.1 (unreleased)

### Changed

- The worker model and effort named in `/oversee` now apply only to implementation. Planning, research, exploration, and audit are manager work in every mode. Workers research or audit only when the user explicitly asks, and those workers are read-only.
- In Plan mode, `/oversee <worker>` added to a task or plan means "implement with this worker after approval". The manager researches and plans itself, records in the plan that implementation runs under oversee with that worker, and starts workers only once the host enables execution. The recorded choice survives a host that implements from the plan in fresh context.
- Outside Plan mode, the same invocation plans in the manager and dispatches implementing workers in the same run.
- Helpers the host's own planning workflow launches keep host defaults and never receive the worker choice.
- `references/harnesses.md`: read-only built-ins (Explore, explorer, research) are for host planning or explicitly requested research, never for applying the worker choice to planning.

### Evaluation

- Added planning-scope scenarios 34-39 to `evals/evals.json`: Plan-mode and normal-mode invocations added to a task, host planning helpers, explicitly requested research in and out of Plan mode, and fresh-context plan handoff. These are catalog-only; none has run live.
- Plan-phase expectations for scenarios 5, 18, and 27 now also forbid subagents running with the requested worker setting.
- The OpenCode recorder fails a plan phase in which a subagent ran with the requested worker setting (unknown when manager and worker settings match). Regrading older evidence derives this check from retained plan-phase transcripts.

## 1.0.0 (2026-10-15)

- First release of the `oversee` skill: explicit `/oversee` activation, arbitrary live worker model/effort selection, ready-plan reuse and Plan-mode handoff, workspace baseline and audit, two retries per piece, and result-only reporting.
- Installers and uninstallers for Windows and Bash, plus internet install, writing `SKILL.md` and `references/` to the four documented skill folders.
- Evaluation catalog, OpenCode and Codex recorders and reviewers, and offline regression tests.
