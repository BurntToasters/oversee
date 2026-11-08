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

Switching from the scripts: run the script uninstaller first (see Uninstall), then `npx skills add`. Otherwise `npx skills add` replaces the script-installed folders of the agents it targets with links, deleting any extra files you kept there, and leaves the other script copies (for example `~/.cline/skills/oversee` and `~/.gemini/config/skills/oversee`) behind, where `npx skills update` and `remove` never touch them.

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
