# oversee

<!-- [![skills.sh](https://skills.sh/b/BurntToasters/oversee)](https://skills.sh/BurntToasters/oversee) -->

Version: `1.2.0`.

Release status: preview. Current smoke evidence is limited to OpenCode v2 service-API prompt runs and Codex app-server runs on Windows. Before removing the preview label, run and retain passing evidence for controlled retries, dirty-workspace preservation, cancellation, denied Plan handoff, result-only reporting, and the live workflow on each primary host (Claude Code, Codex, Cursor, OpenCode). The procedures and current gaps are in [evals/README.md](evals/README.md).

An [Agent Skill](https://agentskills.io) for a manager model to oversee worker subagents without micromanaging them. You choose any model and effort supported by your current harness; names in examples are not defaults or an allowlist.

The manager plans the work, dispatches independent pieces within available concurrency, waits without polling, audits changes against the starting workspace, runs checks itself, and reports the result. Oversee is for implementation only: workers change code, and never audit, review, or map a repository. Fewer manager check-ins is the design goal; lower total tokens or cost is not yet established by a successful live pilot.

## Requirements

- A supported skills host with subagents or a headless fallback that preserves permissions
- Node.js 22.20 or later for `npx skills add`

## Compatibility

The portable payload is [`skills/oversee/`](skills/oversee/): `SKILL.md` plus `references/`. `npx skills add` keeps one copy in `~/.agents/skills/oversee` and links or copies it into the folders of the agents it detects. Model selection, permissions, and mode transitions depend on the host/version. References distinguish documentation checks from live verification.

Where each host reads the skill (global folders; several hosts read more than one, see [Host notes](#host-notes)):

| Agent | Skill folder |
|---|---|
| OpenCode, Codex, GitHub Copilot, Cursor | `~/.agents/skills/oversee` |
| Claude Code | `~/.claude/skills/oversee` |
| Cline | `~/.cline/skills/oversee` |
| Antigravity app, IDE, and CLI | `~/.gemini/config/skills/oversee` |
| Antigravity CLI (additional path) | `~/.gemini/antigravity-cli/skills/oversee` |
| Kiro CLI 2.x and V3 | `~/.kiro/skills/oversee` |

Primary hosts are Claude Code, Codex, Cursor, and OpenCode. GitHub Copilot, Cline, Antigravity, and Kiro CLI are supported on a best-effort basis: the skills CLI places the skill where they read it (except Cline, see [Cline](#cline)), and their harness notes are kept, but they are lower priority, live checks on them are optional, and they do not block releases. Antigravity can only pick worker tiers (`inherit`, `flash`, `pro`) for native subagents; exact model and effort require its headless CLI. Kiro CLI 2.x and V3 share the global skills directory; V2 exposes skills as slash commands from 2.1, and V3 supports them natively.

Many other hosts read the same `~/.agents/skills/oversee` path and are covered by that entry, including Warp, Zed, Amp, Goose, Pi, OpenHands, Augment, Crush, Junie, Qwen Code, Factory Droid, Roo Code, Windsurf, Kilo Code, Gemini CLI, and Devin CLI.

Harness-specific subagent tools, model names, and effort flags live in [`skills/oversee/references/`](skills/oversee/references/), one file per host; a run opens only its host's file.

Invocation syntax depends on the host version. Current OpenCode v2 docs describe loading a skill with `@oversee` or its native skill tool, while TUI slash commands are configured separately. The live smoke sent `/oversee` as prompt text through the local service API and attached the skill explicitly; this does not prove the TUI parser exposes that command. See the versioned notes in [`references/opencode.md`](skills/oversee/references/opencode.md).

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

### Cline

The skills CLI writes Cline's copy to `~/.agents/skills`, but Cline's docs list only `~/.cline/skills` for global skills. After installing, link the skill there so `npx skills update` keeps it current. `npx skills remove` does not remove this link; delete it yourself.

```bash
mkdir -p ~/.cline/skills && ln -s ~/.agents/skills/oversee ~/.cline/skills/oversee
```

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.cline\skills" | Out-Null
New-Item -ItemType Junction -Path "$env:USERPROFILE\.cline\skills\oversee" -Target "$env:USERPROFILE\.agents\skills\oversee"
```

### Migrating from the old install scripts

The bundled install scripts were removed in 1.2.0. The skills CLI's global paths are Claude Code `~/.claude/skills`, Codex and Cline `~/.agents/skills`, Cursor `~/.cursor/skills`, OpenCode `~/.config/opencode/skills`, Copilot `~/.copilot/skills`, Antigravity `~/.gemini/config/skills`, and Kiro CLI `~/.kiro/skills`. `npx skills remove oversee -g` deletes a named skill folder from the agent folders it targets even if another installer put it there, but it does not know about `~/.cline/skills/oversee` or `~/.gemini/antigravity-cli/skills/oversee`. If you installed with the scripts, remove all six of their folders by hand, install with the skills CLI, then add the [Cline](#cline) link if you use Cline.

Bash (macOS, Linux, WSL, Git Bash):

```bash
rm -rf ~/.agents/skills/oversee ~/.claude/skills/oversee ~/.cline/skills/oversee \
  ~/.gemini/config/skills/oversee ~/.gemini/antigravity-cli/skills/oversee ~/.kiro/skills/oversee
npx skills add BurntToasters/oversee -g
```

PowerShell (Windows; untested):

```powershell
'.agents\skills', '.claude\skills', '.cline\skills', '.gemini\config\skills', '.gemini\antigravity-cli\skills', '.kiro\skills' |
  ForEach-Object { Get-Item -Force -ErrorAction SilentlyContinue (Join-Path $env:USERPROFILE "$_\oversee") } |
  ForEach-Object { if ($_.LinkType) { $_.Delete() } else { Remove-Item -Recurse -Force $_.FullName } }
npx skills add BurntToasters/oversee -g
```

These commands delete only folders named `oversee`; other skills are untouched. A symlink or junction is removed as a link, so its target's contents are not touched.

## Uninstall

Run `npx skills remove oversee -g`. If copies from the old scripts remain, remove them with the commands above.

## Host notes

- **Invocation controls.** The payload carries a behavioral guard. Host-enforced controls are optional and not installed: in Claude Code, set `skillOverrides.oversee` to `user-invocable-only` in your settings (the `disable-model-invocation: true` frontmatter key also works there, but the claude.ai packager rejects it, so the payload omits it); in Codex, an `agents/openai.yaml` sidecar with `policy.allow_implicit_invocation: false`. OpenCode v2 honors the shipped `metadata.opencode/autoinvoke: "false"`, which hides the skill from the model's list while `@oversee` still loads it.
- **Duplicate discovery.** OpenCode v2 and Cursor read both `~/.agents/skills` and `~/.claude/skills` (OpenCode also `~/.config/opencode/skills`; Cursor also `~/.cursor/skills` and `~/.codex/skills`), so one skill can be discovered twice. In OpenCode the later-registered copy wins.
- **Codex.** Skills are read from `.agents/skills` in each folder from the working directory up to the repository root, `~/.agents/skills`, and `/etc/codex/skills`; Codex follows symlinked skill folders. The skills listing is capped by `skills.max_context_tokens`.
- **Kiro CLI.** `KIRO_HOME` overrides the global `~/.kiro` folder; if you set it, check that the skill landed in that profile's `skills` folder and copy it there otherwise. The default agent finds skills automatically. A custom agent loads them only when its `resources` include `skill://` URIs (for example `skill://.kiro/skills/**/SKILL.md`), unless default resource inheritance is on. Workspace skills override same-name global skills.

## Usage

Start a new overseen task:

```text
/oversee add a --json flag to the list command, with unit tests
```

Specify the worker model and effort:

```text
/oversee LUNA MAX: add input validation to the parser and tests
/oversee DeepSeek V4.1 Flash MAX: implement the ready plan
```

Oversee work already in progress in this conversation:

```text
/oversee
```

In Codex, use `$oversee` or pick the skill from `/skills`.

Model-only invocations such as `/oversee LUNA MAX` use the ready plan or remaining work in the conversation. The manager resolves names, versions, and variants from the host's live catalog. Ambiguous or unsupported choices need clarification; no model or effort is silently substituted. If no choice was given, it asks once; a noninteractive run selects an available worker by difficulty and announces the choice. This selection never overrides an explicitly named setting.

The same invocation works in or out of Plan mode. In Plan mode, `/oversee Haiku 5.5 high` added to a task or plan means "implement this plan with Haiku 5.5 high workers": the manager researches and plans itself (the host's own planning helpers keep their defaults), prepares worker briefs, and records the worker choice in the plan through the host's approval/Build transition. Workers start only after the host enables execution. Another skill invocation is unnecessary. If the host exposes no transition tool, oversee explains the required user action. Outside Plan mode, the same invocation plans and dispatches workers now.

Workers only implement. They never audit, review, map, or research a repository; the manager does that reading itself. `/oversee Haiku 5.5 high: audit the parser for missing validation, then fix what you find` means the manager audits and the workers fix. An audit-only request dispatches nothing: the main agent does it directly.

A run ends with its report. Later requests in the same conversation, such as another codebase audit, are ordinary requests; they do not restart the workflow or reuse the earlier worker model. Invoke `/oversee` again to hand new work to workers.

Activation is explicit: ordinary requests, reviews of the skill, and quoted commands do not start the workflow. The portable payload includes a behavioral guard; optional host-enforced invocation controls are listed under [Host notes](#host-notes) and are not installed automatically.

## How it works

1. **Plan.** The manager inspects the project itself, restates the task, defines done with the project's real check commands, and splits the work into pieces with clear file ownership. Workers never research for the plan.
2. **Brief.** Each worker gets a self-contained brief: goal, scope, constraints, definition of done, and the reporting format. Outcomes, not steps.
3. **Dispatch and wait.** Independent workers go out together within host limits. Blocking waits and completion notices replace status polling. Necessary clarification, approval, and cancellation handling remain allowed.
4. **Audit.** The manager compares staged, unstaged, and untracked changes against the initial snapshot, preserves existing user edits, runs acceptance checks itself, then runs integration checks.
5. **Retry only failed pieces**, capped at two per piece, then escalate to the user.
6. **Report the result only.** The report ends the run.

User/harness deadlines and cancellation stop further dispatch and request cancellation of active workers. There is no default time limit. Wait transport timeouts alone do not mean a worker failed. Permission denials and unavailable models are blockers, not reasons to spend implementation retries.

## Keeping runs cheap

Oversee has not been shown to save tokens or money. The only measurement so far, the Go pilot in [evals/README.md](evals/README.md), cost more with oversee than a direct run, and the 1.2.0 changes are unmeasured. These points follow from how hosts resend and cache context:

- **The manager's context is the main recurring cost.** It is re-sent on every manager turn. In 1.2.0 the manager opens one host reference file instead of notes for all nine, and reads and prints only what its decisions need.
- **Each worker completion is a manager turn, and caches expire.** Claude Code keeps the main conversation's prompt cache for 1 hour on a subscription and 5 minutes with an API key or usage credits, and a subagent's for 5 minutes (`promptCacheTtl`, `CLAUDE_CODE_PROMPT_CACHE_TTL`). A worker that outlasts the cache means the manager's whole context is written again at the cache-write price.
- **Each model has its own cache.** Switching model mid-session re-reads the whole history uncached. After a large planning session, save the plan to a file and start implementation in a fresh session that invokes oversee on that file (OpenCode: `@PLAN.md`; Claude Code: the `showClearContextOnPlanAccept` setting adds a clear-context option when you approve a plan).
- **One small change is cheaper done directly.** Each piece has fixed overhead: a brief, a worker start, and an audit.

### OpenCode v2 configuration sketch

Checked 2026-11-16 against the v2.3.0 docs source; verify against your installed version.

- The top-level key is `agents` (v1 used `agent`).
- Effort is a variant on the model string, `provider/model#variant`. An unknown variant is an error.
- `agents.general.model` sets the default worker.
- Fable 5.2 is a Zen model (`opencode/claude-fable-5-2`), not an OpenCode Go model. Go usage limits are per model.
- `/compact` sends the full conversation, so it can reuse the cache. Pinning `agents.compaction.model` to a different model gives that up.
- Cache warming exists but is off by default (`"warming": true`), and it never warms subagent sessions.

```jsonc
{ "$schema": "https://opencode.ai/config.json",
  "agents": {
    "build":   { "model": "anthropic/claude-opus-5-5#medium" },
    "general": { "model": "opencode-go/deepseek-v4.1-flash" } } }
```

## Development

- The payload is `skills/oversee/`; keep everything else at the repository root, because the skills CLI copies the whole skill folder.
- `version.txt` is the skill's version source. Run `python bump-ver.py patch`, `minor`, `major`, or an exact version such as `0.2.0-rc.1`. The script synchronizes `version.txt`, skill metadata, and the README version line; it preserves line endings and leaves model/harness versions and historical evidence unchanged. Add new current-version declarations to `TARGETS` in the script.
- Run `python bump-ver.py --check` before a release. Use `python bump-ver.py patch --dry-run` to preview. The script stops on version drift or missing declarations before changing files. Version tooling is development-only and is not installed with the skill.
- Eval scenarios live in [`evals/evals.json`](evals/evals.json). The catalog includes manual/fault-injection scenarios as well as the three automated pilot cases; adding a scenario is not evidence it passed.
- Run offline regression checks with `python -B -m unittest discover -s tests -v`. `tests/test_payload.py` checks the payload layout, frontmatter, byte budgets, and reference links. No dependencies beyond Python's standard library are needed for these tests.
- Run the paired pilot with [`evals/run.py`](evals/run.py); procedure and evidence limits are in [`evals/README.md`](evals/README.md).
- Focused reruns can select cases and one arm; they are marked unpaired. Regrading rejects retained projects that differ from their recorded final hashes.
- Repo conventions and remaining verification gaps are in [`AGENTS.md`](AGENTS.md).

The earlier three-case score measured workflow compliance using summary logs; it did not establish coding superiority or cost savings. Native recorders retain OpenCode and Codex evidence, independently check resulting behavior, and report correctness, orchestration, time, and measured usage separately. Missing measurements remain unknown. Claude Code and Cursor remain documentation-checked until live-tested; Copilot and Antigravity are best-effort and documentation-checked only.

The Go pilot and two focused follow-ups passed overseen coding checks, including Plan-to-Build handoff. They still emitted routine narration, so result-only compliance remains unproven. Measured results and retained failures are documented in [`evals/README.md`](evals/README.md).

## License

[MIT](LICENSE)
