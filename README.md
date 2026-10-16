# oversee

Version: `1.0.1` (preview).

Release status: preview. Current smoke evidence is limited to OpenCode v2 service-API prompt runs and Codex app-server runs on Windows. Before removing the preview label, run and retain passing evidence for controlled retries, dirty-workspace preservation, cancellation, denied Plan handoff, result-only reporting, the live workflow on each primary host (Claude Code, Codex, Cursor, OpenCode), and local/internet installation on macOS and WSL. The procedures and current gaps are in [evals/README.md](evals/README.md).

An [Agent Skill](https://agentskills.io) for a manager model to oversee worker subagents without micromanaging them. You choose any model and effort supported by your current harness; names in examples are not defaults or an allowlist.

The manager plans the work, dispatches independent pieces within available concurrency, waits without polling, audits changes against the starting workspace, runs checks itself, and reports the result. Fewer manager check-ins is the design goal; lower total tokens or cost is not yet established by a successful live pilot.

## Requirements

- A supported skills host with subagents or a headless fallback that preserves permissions
- Bash, `curl`, and `tar` for internet installation with `install.sh`; Bash for local installation
- PowerShell for Windows internet installation; `tar` when available, with a zip fallback

## Compatibility

The portable payload is `SKILL.md` plus `references/`. The following are intended discovery locations; model selection, permissions, and mode transitions depend on the host/version. References distinguish documentation checks from live verification.

| Agent | Skill folder |
|---|---|
| OpenCode, Codex, GitHub Copilot, Cursor | `~/.agents/skills/oversee` |
| Claude Code | `~/.claude/skills/oversee` |
| Antigravity app | `~/.gemini/config/skills/oversee` |
| Antigravity CLI | `~/.gemini/antigravity-cli/skills/oversee` |

Primary hosts are Claude Code, Codex, Cursor, and OpenCode. GitHub Copilot and Antigravity are supported on a best-effort basis: the installers still place the skill where they read it, but they are lower priority, live checks on them are optional, and they do not block releases. Antigravity can only pick worker tiers (`inherit`, `flash`, `pro`), not arbitrary models.

Harness-specific subagent tools, model names, and effort flags live in [`references/harnesses.md`](references/harnesses.md).

Invocation syntax depends on the host version. Current OpenCode v2 docs describe loading a skill with `@oversee` or its native skill tool, while TUI slash commands are configured separately. The live smoke sent `/oversee` as prompt text through the local service API and attached the skill explicitly; this does not prove the TUI parser exposes that command. See the versioned notes in the harness reference.

## Install

### Unix (macOS, Linux, WSL, Git Bash)

One-liner, straight from GitHub:

```bash
curl -fsSL https://raw.githubusercontent.com/BurntToasters/oversee/main/install.sh | bash
```

Or from a clone of this repo:

```bash
git clone https://github.com/BurntToasters/oversee.git
cd oversee
bash ./install.sh
```

Re-run to update. Installers stage the complete payload, replace `SKILL.md` and the entire `references/` subtree, and restore the previous managed payload if replacement fails. Deleted upstream references disappear. Other files at the skill root and neighboring skills are preserved during updates. Recovery failures report the retained backup path. Each destination is a separate transaction; an earlier destination can succeed before a later one fails.

### Windows

From a clone, in cmd:

```bat
install.bat
```

Or straight from GitHub, in PowerShell:

```powershell
irm https://raw.githubusercontent.com/BurntToasters/oversee/main/remote-install.ps1 | iex
```

These one-liners execute downloaded code. Inspect the script before running it if you need to review what executes. The remote installers download and validate the payload in a temporary folder before updating installed copies; download/extraction failures stop installation and clean that folder.

## Uninstall

### Unix

```bash
bash ./uninstall.sh
```

Or, without a clone:

```bash
curl -fsSL https://raw.githubusercontent.com/BurntToasters/oversee/main/uninstall.sh | bash
```

### Windows

```bat
uninstall.bat
```

Uninstall deletes only the `oversee` folder from the four locations above. Your other skills are untouched.

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

Workers implement. They research or audit only when you ask for that explicitly, for example `/oversee Haiku 5.5 high: have workers map where list output is built, then add --json`; such workers are read-only.

Activation is explicit: ordinary requests, reviews of the skill, and quoted commands do not start the workflow. The portable payload includes a behavioral guard; optional host-enforced invocation controls are documented in the harness reference and are not installed automatically.

## How it works

1. **Plan.** The manager inspects the project itself, restates the task, defines done with the project's real check commands, and splits the work into pieces with clear file ownership. Workers do not research for the plan unless you ask.
2. **Brief.** Each worker gets a self-contained brief: goal, scope, constraints, definition of done, and the reporting format. Outcomes, not steps.
3. **Dispatch and wait.** Independent workers go out together within host limits. Blocking waits and completion notices replace status polling. Necessary clarification, approval, and cancellation handling remain allowed.
4. **Audit.** The manager compares staged, unstaged, and untracked changes against the initial snapshot, preserves existing user edits, runs acceptance checks itself, then runs integration checks.
5. **Retry only failed pieces**, capped at two per piece, then escalate to the user.
6. **Report the result only.**

User/harness deadlines and cancellation stop further dispatch and request cancellation of active workers. There is no default time limit. Wait transport timeouts alone do not mean a worker failed. Permission denials and unavailable models are blockers, not reasons to spend implementation retries.

## Development

- `version.txt` is the skill's version source. Run `python bump-ver.py patch`, `minor`, `major`, or an exact version such as `0.2.0-rc.1`. The script synchronizes `version.txt`, skill metadata, and the README version line; it preserves line endings and leaves model/harness versions and historical evidence unchanged. Add new current-version declarations to `TARGETS` in the script.
- Run `python bump-ver.py --check` before a release. Use `python bump-ver.py patch --dry-run` to preview. The script stops on version drift or missing declarations before changing files. Version tooling is development-only and is not installed with the skill.
- Eval scenarios live in [`evals/evals.json`](evals/evals.json). The catalog includes manual/fault-injection scenarios as well as the three automated pilot cases; adding a scenario is not evidence it passed.
- Run offline regression checks with `python -B -m unittest discover -s tests -v`. Installer checks use throwaway profiles; Bash and Windows-specific checks skip when their platform is unavailable. No dependencies beyond Python's standard library are needed for these tests.
- Run the paired pilot with [`evals/run.py`](evals/run.py); procedure and evidence limits are in [`evals/README.md`](evals/README.md).
- Focused reruns can select cases and one arm; they are marked unpaired. Regrading rejects retained projects that differ from their recorded final hashes.
- Repo conventions and remaining verification gaps are in [`AGENTS.md`](AGENTS.md).

The earlier three-case score measured workflow compliance using summary logs; it did not establish coding superiority or cost savings. Native recorders retain OpenCode and Codex evidence, independently check resulting behavior, and report correctness, orchestration, time, and measured usage separately. Missing measurements remain unknown. Claude Code and Cursor remain documentation-checked until live-tested; Copilot and Antigravity are best-effort and documentation-checked only.

The Go pilot and two focused follow-ups passed overseen coding checks, including Plan-to-Build handoff. They still emitted routine narration, so result-only compliance remains unproven. Measured results and retained failures are documented in [`evals/README.md`](evals/README.md).

## License

[MIT](LICENSE)
