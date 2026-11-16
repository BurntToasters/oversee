# Changelog

Changes to the `oversee` skill, by version. The version comes from `version.txt` (`python bump-ver.py`). Dates are release dates; an unreleased version is marked as such.

## Install

Install for every coding agent detected on this machine, globally:

```bash
npx skills add BurntToasters/oversee -g
```

To update:

```bash
npx skills update -g            # every globally installed skill
npx skills update oversee -g    # only oversee
```

### Customize the install:

```bash
npx skills add BurntToasters/oversee -g -a claude-code -a codex -y   # pick agents, no prompts
npx skills add BurntToasters/oversee -g --copy                       # copies instead of symlinks
npx skills add BurntToasters/oversee                                 # this project only
npx skills check                                                     # list available updates
npx skills remove oversee -g                                         # uninstall
```

It installs only `skills/oversee/` (`SKILL.md`, `references/`, and `agents/openai.yaml`). Kiro CLI custom agents must list skills in their `resources` (`skill://.kiro/skills/**/SKILL.md`); the default agent needs nothing. The CLI sends anonymous install telemetry unless `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` is set. Review any skill before use; it runs with your agent's permissions.

Switching from the old scripts: `npx skills remove oversee -g` does not know about `~/.cline/skills/oversee` or `~/.gemini/antigravity-cli/skills/oversee`. Delete the six script folders (`~/.agents/skills/oversee`, `~/.claude/skills/oversee`, `~/.cline/skills/oversee`, `~/.gemini/config/skills/oversee`, `~/.gemini/antigravity-cli/skills/oversee`, `~/.kiro/skills/oversee`) by hand, then run `npx skills add`. The README has bash and PowerShell commands.

Since skills CLI 1.8.0, Codex, Cursor, OpenCode, Copilot, and Cline are installed only to `~/.agents/skills`. CLI 1.7.x also wrote `~/.cursor/skills`, `~/.config/opencode/skills`, and `~/.copilot/skills`; the README migration commands remove those too. Cline's docs list only `~/.cline/skills`: if `/oversee` is missing in Cline, link it there (README).

## 1.2.0 (unreleased)

### Removed

- The legacy install scripts (`install.sh`, `install.bat`, `uninstall.sh`, `uninstall.bat`, `remote-install.ps1`), their `curl | bash` and `irm | iex` one-liners, and their tests (`tests/test_installers.py`, `tests/test_installer_rollback.py`). Install and remove with the skills CLI; the README has a migration note.

### Changed

- `SKILL.md` audit: the manager diffs with `git diff <baseline id>` (the commit id, or the `git stash create` id on a dirty tree), because plain `git diff` misses staged and committed worker edits. An unauthorized commit (HEAD or branch moved) fails acceptance. The baseline records the branch and `git status --short --branch --ignored=matching -uall`, so ignored scratch files are caught and a new file inside an already-untracked folder is listed instead of hidden behind `?? folder/`. An empty `git stash create` falls back to the commit id; if it fails (read-only `.git`, as in the Codex sandbox, or an unmerged index), the manager hashes the dirty files; a repository with no commits is hashed. Caches or build output from the checks are not scratch files. The post-run prose was shortened to stay within the byte budget.
- Host references rechecked 2026-11-16. Claude Code: corrected model precedence (`CLAUDE_CODE_SUBAGENT_MODEL` ranks below the call and profile unless `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`, which ignores the call; `CLAUDE_CODE_EFFORT_LEVEL` overrides call and profile effort); a newly created `agents` folder needs a restart; the `-p` background wait ceiling; `/tasks` shows the model and effort used; worker permission prompts and session-wide grants; `SendMessage` by agent ID; leave `isolation` and `name` unset, since a worktree branches from the default branch and a named call becomes an agent-teams teammate; a sandboxed session started in a subfolder may not write `.git`. Codex: required profile fields, headless `codex exec` is read-only unless `--sandbox workspace-write`, `workspace-write` keeps `.git`, `.agents`, and `.codex` read-only, and `--sandbox danger-full-access` and `--approve-for-me` join the never-add list. Cursor: two nesting levels (a worker can launch subagents; theirs cannot). OpenCode: checked against v2.3.0 source; a `<subagent>` notice follows each idle, including after a retry. Profiles created for a run stay out of the audited deliverable.
- README: `npx skills check && npx skills update` never updated, because `check` exits 1 when an update exists; the commands are now separate. Added `DO_NOT_TRACK=1`, Claude Code subagent cache TTL settings and the 1-hour TTL tip, the cleared-context plan-accept note, and the claude.ai upload note.
- Eval fixtures are committed before a run, and the OpenCode allowlist adds exactly `git rev-parse`, `git log`, `git stash create`, and `git hash-object`, so the manager can follow the 1.2.0 baseline rules. Staging copies the whole skill folder. Scenario 46 now expects the `git stash create` id.
- The single harness reference is split into one file per host under `references/` (`claude-code.md`, `codex.md`, `opencode.md`, `cursor.md`, `copilot.md`, `antigravity.md`, `cline.md`, `kiro.md`, `headless.md`). A run opens only its host's file instead of notes for every host.
- `SKILL.md` context-economy rules: a ready plan is not re-explored; the baseline is compact (commit id or path list with hashes, no full diffs, no snapshot left behind); briefs give start pointers and piece-scoped checks, and workers return fixed `Changed`/`Checks`/`Unfinished`/`Uncertain` reports; the manager waits for the whole current batch without text, audits from a whole-workspace path list and real diffs, and runs checks quietly with one check per command and no pipes. Silence is stated structurally: between the worker-choice line and the report, turns contain tool calls only. Three rules from the old reference moved into `SKILL.md`: an unsupported `max` is not the highest level, an unverified setting is never claimed as honored, and global configuration is never changed to enable dispatch.
- Corrected host facts: OpenCode v2 has an optional per-call `model` (`provider/model#variant`) and, in v2.3.0, always runs subagents in the background with a completion notice; Claude Code interactive sessions cannot block on workers, and a finished worker can be resumed with its history.
- README: install layout updated for skills CLI 1.8.0, and the migration commands also remove CLI 1.7.x copies in `~/.cursor/skills`, `~/.config/opencode/skills`, and `~/.copilot/skills`. Cline users link the skill into `~/.cline/skills` only if `/oversee` is missing. The PowerShell migration command removes symlinks and junctions as links instead of recursing into their targets. The skills CLI ignores `KIRO_HOME`.
- `SKILL.md` baseline: on a dirty tree the manager records a `git stash create` id, which captures staged and unstaged edits without touching the index, files, or stash list, so the audit can diff exactly what workers changed on top of user edits. New untracked files are read whole. Owner Decision 12 records this exception.
- `SKILL.md`: announcing an authorized worker change is listed among the allowed messages, and the manager reopens the skill and its host reference if compaction drops them. Repeated wording was trimmed to keep headroom under the 13,500-byte budget.
- Host references: auto-approval warnings for headless `claude -p` and `codex exec` workers; the OpenCode headless `run` form, Kiro V3 spawn-list limits, and Cline `--timeout`, which the per-host split had dropped.
- `AGENTS.md`: host tables and sources moved to `docs/hosts.md` (not installed), cutting the file from 30.8 KB to about 22 KB; decisions are listed in order.
- Eval recorders write `usage_by_role` (manager, children, manager turns) beside the unchanged `usage`, so manager cost can be compared before and after. Chained inspection commands such as `git status --short && git diff` now count as reading the diff; a `git diff` inside a quoted string does not.
- Eval graders match the 1.2.0 rules: piped, redirected, or chained checks no longer pass; POSIX shell wrappers are unwrapped for Codex; diff inspection ignores summary flags and accepts git global options; reads count only on changed paths; silence exempts the text ending each user turn (such as a plan shown for approval) instead of keywords, and fails a run with no final report; `usage_by_role` adds `workers` and `helpers`; Codex retries and helper threads no longer fail worker checks; the OpenCode recorder waits until the child set is stable and records the root id. Pilot prompts use quiet checks (`-q`). Regraded Codex Windows evidence may score its check differently.

### Added

- `agents/openai.yaml` in the payload with `policy.allow_implicit_invocation: false`, so Codex loads oversee only through `$oversee` or `/skills` (owner Decision 9).
- Catalog-only eval scenarios 50 (`worker-commit-detected`), 51 (`no-commit-baseline`), 52 (`untracked-directory-edit`), 53 (`stash-create-blocked`), and 54 (`authorized-worker-commit`), and `tests/test_fixtures.py`, which checks that pilot fixtures are committed and allow the baseline commands.
- README section "When another approach fits better": tightly coupled code, Claude Code `opusplan`, and Anthropic's advisor strategy, with sources.
- `tests/test_payload.py`: payload layout, frontmatter keys, byte budgets, reference links, no removed file names, and local links and anchors in README, AGENTS.md, and `docs/hosts.md`.
- CI: `.github/workflows/tests.yml` runs the unit tests and `bump-ver.py --check` on Linux and Windows. `.gitattributes` sets LF for all text files.
- Catalog-only eval scenarios 45-49 for the context-economy rules.
- README section "Keeping runs cheap".

### Fixed

- `SKILL.md`: "Issue independent read-only commands together in one turn" led managers in OpenCode and Claude Code to chain baseline commands into one shell line, which an allowlist denies as a whole; in OpenCode the manager then stalled on a question. Commands now run as separate calls, never chained. `opencode.md`: a denied command blocks only that command. `claude-code.md`: no `ScheduleWakeup`, `Monitor`, no-op command, or loop as a waiting fallback.
- `claude-code.md`: where the `Agent` schema has `run_in_background` (`claude -p`, the Agent SDK, or fork mode off), the manager sets it to `false` on every call of the batch and blocks once. Before, workers ran in the background, each silent turn end drew the host's "no visible output" prompt, and the manager narrated. In an interactive session that cannot block, a waiting turn now ends with the one line `Waiting for N workers.` instead of no text (owner Decision 15 exception). A headless run with `CLAUDE_CODE_FORK_SUBAGENT=1`, which removes `run_in_background`, printed only those lines and drew no host prompt; an interactive session was not run.
- `cline.md`: a headless Cline prompt run auto-approves every tool by default; the note now says to pass `--auto-approve false` instead of only warning against adding the flag. `copilot.md`: `security-review` and `rubber-duck` are host helpers.
- `SKILL.md`: workers appended `; echo "exit=$?"` to their checks, which an allowlist denies. The brief now carries the rule "Run each check exactly as written; never chain or append commands such as `; echo`". With only "plain command" in `SKILL.md`, the manager wrote plain commands but did not pass the rule on, and a worker still appended `; echo`. With the quoted rule, both briefs carried it and the workers had no denials.
- Eval pilots: the parallel and plan-handoff prompts used `python -m unittest`, which fails where only `python3` exists (macOS). They now use a `{python}` placeholder that the OpenCode and Codex runners fill with `python` on Windows and `python3` elsewhere. The fixture READMEs say `python3` and note `python` for Windows.

### Measured

One with-skill run per case, 2026-11-16, same settings for both versions (details in `evals/README.md`). OpenCode 2.3.0 with Opus 5.5 medium managing DeepSeek V4.1 Flash max: parallel $0.331 → $0.202, plan handoff $0.357 → $0.298, ordinary question $0.102 → $0.095; 1.2.0 passed the silence check in both coding cases, 1.1.1 failed both. Claude Code 2.1.325 (`claude -p`, Opus 5.5 medium managing Haiku): $0.334 → $0.325 with background workers, where the host prompted for visible output after each silent turn end and silence failed; $0.262 once the manager blocked on its batch with `run_in_background: false`, with no intermediate text; $0.354 with fork mode on, which cannot block, using the one-line waiting message; $0.254 blocking, after the worker check rule above. The manager is 97-98% of cost. Codex 0.169.0 (1.2.0 only, `gpt-5.6-terra` medium managing `gpt-6-luna` max): all three smoke cases passed behavior and exact settings, and the parallel case passed silence; after the `python3` prompt fix, the parallel case passed every strict check. Cost is unknown. Not a savings guarantee.

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
