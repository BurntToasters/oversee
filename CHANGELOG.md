# Changelog

Changes to the `oversee` skill, by version. The version comes from `version.txt` (`python bump-ver.py`). Dates are release dates; an unreleased version is marked as such.

## Install

Install for every coding agent detected on this machine, globally:

```bash
npx skills add BurntToasters/oversee -g
```

### Customize the install:

```bash
npx skills add BurntToasters/oversee -g -a claude-code -a codex -y   # pick agents, no prompts
npx skills add BurntToasters/oversee -g --copy                       # copies instead of symlinks
npx skills add BurntToasters/oversee                                 # this project only
npx skills check && npx skills update oversee -g                     # update
npx skills remove oversee -g                                         # uninstall
```

It installs only `skills/oversee/` (`SKILL.md` and `references/`). Kiro CLI custom agents must list skills in their `resources` (`skill://.kiro/skills/**/SKILL.md`); the default agent needs nothing. The CLI sends anonymous install telemetry unless `DISABLE_TELEMETRY=1` is set. Review any skill before use; it runs with your agent's permissions.

Switching from the old scripts: `npx skills remove oversee -g` does not know about `~/.cline/skills/oversee` or `~/.gemini/antigravity-cli/skills/oversee`. Delete the six script folders (`~/.agents/skills/oversee`, `~/.claude/skills/oversee`, `~/.cline/skills/oversee`, `~/.gemini/config/skills/oversee`, `~/.gemini/antigravity-cli/skills/oversee`, `~/.kiro/skills/oversee`) by hand, then run `npx skills add`. The README has bash and PowerShell commands.

Since skills CLI 1.8.0, Codex, Cursor, OpenCode, Copilot, and Cline are installed only to `~/.agents/skills`. CLI 1.7.x also wrote `~/.cursor/skills`, `~/.config/opencode/skills`, and `~/.copilot/skills`; the README migration commands remove those too. Cline's docs list only `~/.cline/skills`: if `/oversee` is missing in Cline, link it there (README).

## 1.2.0 (unreleased)

### Removed

- The legacy install scripts (`install.sh`, `install.bat`, `uninstall.sh`, `uninstall.bat`, `remote-install.ps1`), their `curl | bash` and `irm | iex` one-liners, and their tests (`tests/test_installers.py`, `tests/test_installer_rollback.py`). Install and remove with the skills CLI; the README has a migration note.

### Changed

- The single harness reference is split into one file per host under `references/` (`claude-code.md`, `codex.md`, `opencode.md`, `cursor.md`, `copilot.md`, `antigravity.md`, `cline.md`, `kiro.md`, `headless.md`). A run opens only its host's file instead of notes for every host.
- `SKILL.md` context-economy rules: a ready plan is not re-explored; the baseline is compact (commit id or path list with hashes, no full diffs, no snapshot left behind); briefs give start pointers and piece-scoped checks, and workers return fixed `Changed`/`Checks`/`Unfinished`/`Uncertain` reports; the manager waits for the whole current batch without text, audits from a whole-workspace path list and real diffs, and runs checks quietly with one check per command and no pipes. Silence is stated structurally: between the worker-choice line and the report, turns contain tool calls only. Three rules from the old reference moved into `SKILL.md`: an unsupported `max` is not the highest level, an unverified setting is never claimed as honored, and global configuration is never changed to enable dispatch.
- Corrected host facts: OpenCode v2 has an optional per-call `model` (`provider/model#variant`) and, in v2.3.0, always runs subagents in the background with a completion notice; Claude Code interactive sessions cannot block on workers, and a finished worker can be resumed with its history.
- README: install layout updated for skills CLI 1.8.0, and the migration commands also remove CLI 1.7.x copies in `~/.cursor/skills`, `~/.config/opencode/skills`, and `~/.copilot/skills`. Cline users link the skill into `~/.cline/skills` only if `/oversee` is missing. The PowerShell migration command removes symlinks and junctions as links instead of recursing into their targets. The skills CLI ignores `KIRO_HOME`.
- `SKILL.md` baseline: on a dirty tree the manager records a `git stash create` id, which captures staged and unstaged edits without touching the index, files, or stash list, so the audit can diff exactly what workers changed on top of user edits. New untracked files are read whole. Owner Decision 12 records this exception.
- `SKILL.md`: announcing an authorized worker change is listed among the allowed messages, and the manager reopens the skill and its host reference if compaction drops them. Repeated wording was trimmed to keep headroom under the 13,500-byte budget.
- Host references: auto-approval warnings for headless `claude -p` and `codex exec` workers; the OpenCode headless `run` form, Kiro V3 spawn-list limits, and Cline `--timeout`, which the per-host split had dropped.
- `AGENTS.md`: host tables and sources moved to `docs/hosts.md` (not installed), cutting the file from 30.8 KB to about 22 KB; decisions are listed in order.
- Eval recorders write `usage_by_role` (manager, children, manager turns) beside the unchanged `usage`, so manager cost can be compared before and after. Chained inspection commands such as `git status --short && git diff` now count as reading the diff; a `git diff` inside a quoted string does not.

### Added

- `tests/test_payload.py`: payload layout, frontmatter keys, byte budgets, reference links, no removed file names, and local links and anchors in README, AGENTS.md, and `docs/hosts.md`.
- CI: `.github/workflows/tests.yml` runs the unit tests and `bump-ver.py --check` on Linux and Windows. `.gitattributes` sets LF for all text files.
- Catalog-only eval scenarios 45-49 for the context-economy rules.
- README section "Keeping runs cheap".

The cost effect of these changes is not yet measured.

## 1.1.1

### Fixed

- After a finished run, a later request such as "audit the codebase" could be treated as more oversee work and sent to the earlier run's worker model. A run now ends with its final report: later messages are ordinary requests, the manager role does not persist, and the worker choice is not a standing preference for subagents. A new run needs a new invocation.

### Changed

- Oversee is implementation-only. Workers change code; auditing, reviewing, mapping, research, and explanation are always done by the manager or main agent. The exception that let workers research or audit on explicit request is removed, because it was the route by which audit requests reached workers.
- An audit-only or repo-mapping invocation dispatches no workers: the main agent does the work and mentions that `/oversee` can implement the fixes. An audit-and-fix invocation still works: the manager audits, workers fix.
- No workers start in Plan mode, including read-only ones.
- `SKILL.md` reorganized: a "When this skill applies" section states the three limits (invocation only, implementation only, one run then done) ahead of the run steps, and the description names the implementation-only scope.
- `references/harnesses.md`: read-only built-in agents belong to the host and are never dispatched by oversee.
- Eval catalog: scenarios 29, 37, and 38 now expect manager-only auditing and research; scenarios 40-44 cover post-run requests and read-only invocations. Catalog-only, not run live.

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
