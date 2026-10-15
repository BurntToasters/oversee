# oversee

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

Harness-specific subagent tools, model names, and effort flags live in [`references/harnesses.md`](references/harnesses.md).

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
./install.sh
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
./uninstall.sh
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

You can invoke oversee while in Plan mode. It reuses the ready plan, prepares worker briefs, and retains the requested model through the host's approval/Build transition. Workers implement only after the host enables execution. Another skill invocation is unnecessary. If the host exposes no transition tool, oversee explains the required user action.

Activation is explicit: ordinary requests, reviews of the skill, and quoted commands do not start the workflow. The portable payload includes a behavioral guard; optional host-enforced invocation controls are documented in the harness reference and are not installed automatically.

## How it works

1. **Plan.** Restate the task, define done with the project's real check commands, and split the work into pieces with clear file ownership.
2. **Brief.** Each worker gets a self-contained brief: goal, scope, constraints, definition of done, and the reporting format. Outcomes, not steps.
3. **Dispatch and wait.** Independent workers go out together within host limits. Blocking waits and completion notices replace status polling. Necessary clarification, approval, and cancellation handling remain allowed.
4. **Audit.** The manager compares staged, unstaged, and untracked changes against the initial snapshot, preserves existing user edits, runs acceptance checks itself, then runs integration checks.
5. **Retry only failed pieces**, capped at two per piece, then escalate to the user.
6. **Report the result only.**

User/harness deadlines and cancellation stop further dispatch and request cancellation of active workers. There is no default time limit. Wait transport timeouts alone do not mean a worker failed. Permission denials and unavailable models are blockers, not reasons to spend implementation retries.

## Development

- Eval scenarios live in [`evals/evals.json`](evals/evals.json). The catalog includes manual/fault-injection scenarios as well as the three automated pilot cases; adding a scenario is not evidence it passed.
- Run offline regression checks with `python -B -m unittest discover -s tests -v`. Installer checks use throwaway profiles; Bash and Windows-specific checks skip when their platform is unavailable. No dependencies beyond Python's standard library are needed for these tests.
- Run the paired pilot with [`evals/run.py`](evals/run.py); procedure and evidence limits are in [`evals/README.md`](evals/README.md).
- Focused reruns can select cases and one arm; they are marked unpaired. Regrading rejects retained projects that differ from their recorded final hashes.
- Repo conventions and remaining verification gaps are in [`AGENTS.md`](AGENTS.md).

The earlier three-case score measured workflow compliance using summary logs; it did not establish coding superiority or cost savings. The new recorder retains native events, independently checks resulting behavior, and reports correctness, orchestration, time, and measured usage separately. Missing measurements remain unknown. Other harnesses remain documentation-checked until live-tested.

The Go pilot and two focused follow-ups passed overseen coding checks, including Plan-to-Build handoff. They still emitted routine narration, so result-only compliance remains unproven. Measured results and retained failures are documented in [`evals/README.md`](evals/README.md).

## License

[MIT](LICENSE)
