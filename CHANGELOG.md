# Changelog

Changes to the `oversee` skill, by version. The version comes from `version.txt` (`python bump-ver.py`). Dates are release dates; an unreleased version is marked as such.

## 1.1.0

### Added

- `npx skills add BurntToasters/oversee -g` is now the primary installer. The skill payload moved to `skills/oversee/` so the skills CLI installs only `SKILL.md` and `references/`; with the old root layout it copied the whole repository (evals, tests, installers) into every agent's skill folder.
- A layout regression test checks that the repository root holds no `SKILL.md` and that `skills/oversee/` holds only the payload.

### Changed

- `install.sh`, `install.bat`, and `remote-install.ps1` read the payload from `skills/oversee/`. A script copied next to a payload still works. `install.sh` now skips a destination that is a symlink (for example one created by `npx skills add`) instead of aborting; the canonical `~/.agents/skills/oversee` copy is still updated.
- `uninstall.sh` removes a dangling skill symlink left after the canonical copy is deleted.
- README: switching from the scripts to `npx skills add` starts with the script uninstaller; otherwise the skills CLI replaces script-installed folders with links and leaves untracked copies for other agents.
- `references/harnesses.md`, rechecked 2026-11-07: Claude Code per-call `model` accepts aliases only (full IDs belong in agent profiles), effort/model environment overrides, concurrency and nesting defaults; Codex model/effort precedence, thread cap, and skill directories; OpenCode v2 undocumented per-call model override and duplicate skill discovery; Cursor `is_background`/`readonly` and bracket options; Kiro CLI V3 as the default engine, no ad-hoc sub-agent definition in 2.x or V3, workspace agent files as the worker route, and effort precedence.
- `bump-ver.py` and the eval recorders point at the new payload path.

### Deprecated

- The bundled install scripts (`install.sh`, `install.bat`, `uninstall.sh`, `uninstall.bat`, `remote-install.ps1`) and their `curl | bash` and `irm | iex` one-liners are deprecated and scheduled for removal in 1.2.0. Use `npx skills add BurntToasters/oversee -g` to install and `npx skills remove oversee -g` to uninstall. To switch, run the script uninstaller first.

## 1.0.2

### Changed

- Installers and uninstallers now place the skill for Kiro CLI 2.x and V3 at `~/.kiro/skills/oversee` (Windows: `%USERPROFILE%\.kiro\skills\oversee`). Both versions share the global skills directory; V2 exposes skills as slash commands from 2.1, and V3 supports them natively.
- Installers and uninstallers now place the skill for Cline at `~/.cline/skills/oversee` (Windows: `%USERPROFILE%\.cline\skills\oversee`), its official global skills directory.
- `references/harnesses.md`: expanded Antigravity support with current App/IDE/CLI skill paths, asynchronous subagents and custom-agent fields, `/plan` and Proceed handoff, and headless `agy -p --model --effort` for exact worker settings. Added a Cline section and recorded that many other hosts are already covered by `~/.agents/skills`.

## 1.0.1

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
