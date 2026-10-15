# AGENTS.md

Instructions for agents working on this repo. Read this before changing anything.

This file is not installed with the skill. The install scripts copy only `SKILL.md` and `references/`. Anything the installed skill needs at runtime must live in those two places.

## What this repo is

`oversee` is one agent skill. The repo root is the skill folder. Users run it with `/oversee`.

The README premise: a larger model oversees other subagents without micromanaging them.

The intended setup is a higher-tier model as manager (for example Claude Opus 5.5 or GPT-6.1 Sol) and cheaper workers as subagents (for example Claude Haiku 5.5 or GPT-6 Luna). The manager plans and audits. The workers implement. The main goal is fewer tokens, so the manager never polls workers.

The skill must work in Claude Code, OpenCode, Codex, GitHub Copilot, Cursor, and Antigravity.

Owner: BurntToasters. License: MIT.

## Status (2026-10-15)

| Item | State |
|---|---|
| Design | Mostly settled. See Decisions below |
| `install.bat`, `install.sh`, `uninstall.bat`, `uninstall.sh`, `remote-install.ps1` | Current regression suite covers Windows cmd/PowerShell and Git Bash. WSL was tested on the earlier revision; current macOS/WSL checks remain pending. Both installers support local and internet installs |
| `SKILL.md` | Explicit activation, arbitrary live model selection, ready-plan handoff, baseline audit, bounded retries |
| `references/harnesses.md` | Official sources rechecked 2026-10-15; OpenCode v2.0.29 and Codex CLI 0.162.0-alpha.17.2 have live smoke evidence; other hosts not live-tested |
| `evals/` | 18 scenarios, OpenCode/Codex native evidence and review tools, 72 offline tests including version tooling; three Codex smoke cases added to existing Go evidence; dependent narration compliance still fails |
| `version.txt`, `bump-ver.py` | Canonical skill version with synchronized metadata/README, validation, dry run, and replacement rollback; development-only |
| `README.md` | Written with install, uninstall, compatibility, and usage instructions |

## Decisions

Items 1 to 5 and 7 to 8 were agreed with the owner. Change them only with the owner.

1. **Invocation.** `/oversee <task>` starts a run. `/oversee` alone oversees work already in progress in the conversation. If nothing is in progress, ask what to oversee.
2. **Scope.** Coding first. Acceptance means tests, builds, or diffs that can be checked. Non-code work is out of scope for v1.
3. **Roles.** The manager plans, dispatches, audits, and reports. Each worker implements one piece.
4. **Dispatch, then wait.** Launch independent workers within available concurrency, then wait for the batch through blocking waits or completion notices. No status polling or routine check-ins. Necessary clarification, approvals, blockers, and cancellation handling are allowed.
5. **Audit.** When the batch is back, read each report and the actual diff, run the checks yourself, then accept or fail each piece with a specific reason.
6. **Retries.** Two retries per piece after the initial attempt, as agreed in the reliability plan. Retain complete constraints on fresh retries. No automatic model/effort escalation. Permission denials, unavailable settings, and cancellation are not implementation retries. Honor user/harness deadlines; no default time limit.
7. **Worker model and effort.**
   - If the invocation names a worker model and effort (for example `Haiku 5.5 max`), use exactly that.
   - If not, ask once before dispatching. Offer the difficulty-based default as the suggestion.
   - If the user gives no answer, choose by difficulty and say which model you chose, in one line.
   - Model names are open-ended inputs, not an allowlist or fixed default. Resolve current model/version/effort, clarify ambiguity, and never silently substitute. With no named setting in noninteractive use, choose an available tool-capable worker by difficulty and relative supported effort. Examples never establish availability.
8. **Final output.** Result only: changes, checks/outcomes, unfinished work and blockers. No plan, worker logs, or audit notes unless requested. Allow the dispatch notice and necessary handoff, clarification, blocker, and cancellation messages.
9. **Trigger.** Explicit invocation or an explicit request for this workflow only. Quoted commands, skill reviews, and ordinary coding questions must not activate execution. Keep the portable behavioral guard; optional host controls are documented, not installed.
10. **Universal core.** `SKILL.md` must not depend on one harness's tool names or model IDs. Harness details go in `references/`.
11. **Plan mode.** A ready conversation plan counts as existing work. Prepare briefs, retain the worker choice, and use native approval/mode transition. Dispatch implementation only after the host enables execution; no second invocation or duplicate workers.
12. **Workspace preservation.** Snapshot staged, unstaged, and untracked state; compare actual changes against that baseline. Never reset, stash, stage, or discard user edits for convenience.

## Invocation wording

- Interpret an actual invocation using the surrounding message and conversation. Natural wording such as `use <model>`, a model-only invocation, and task text before or after `/oversee` should preserve the user's intent. The host must first recognize and deliver the invocation; the skill cannot change a host's slash-command parser.
- Reuse a ready plan, pasted audit findings, or an explicit coding task as scope. A model-only invocation uses existing work; if none exists, ask what to oversee. If a model is named without effort, choose a supported effort by difficulty, as specified in `SKILL.md`.
- Adding `/oversee` to a ready plan while in Plan mode prepares oversight for implementation after host approval. Retain scope and worker selection; require neither another invocation nor duplicate dispatch after execution is enabled.
- An audit-and-fix request means the manager audits first, turns actionable findings into scoped implementation pieces, then dispatches workers and verifies fixes. Resolve ambiguous findings or acceptance gaps before dispatch.
- User examples illustrate intent, not an exhaustive grammar or model allowlist. Quoted examples and discussions of these forms must not activate the workflow. Keep installed behavior in `SKILL.md`; this file is repository guidance only.

## SKILL.md outline

1. Explicit invocation and reuse of ready plans.
2. Plan-mode handoff before implementing dispatch.
3. Choose workers: named, asked, or chosen by difficulty.
4. Plan, ownership, dependencies, and starting workspace snapshot.
5. Complete worker briefs with scope, constraints, checks, and short reports.
6. Batch dispatch within concurrency limits, then blocking waits/completion events.
7. Audit, integration checks, complete retries, and stopping conditions.
8. Result-only report; link the installed harness reference where needed.

## Skill file rules

- Frontmatter uses only Agent Skills spec fields: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Spec: https://agentskills.io/specification
- No Claude-only fields such as `disable-model-invocation`, `argument-hint`, `context`, `model`, `effort`, or `paths`. The claude.ai packaging step rejects unknown keys (Claude Code skills docs).
- OpenCode-only switches go under `metadata` as quoted strings. `opencode/slash: "true"` exposes `/oversee` in OpenCode. `opencode/autoinvoke: "false"` keeps the skill out of the model's automatic picks. Other tools ignore these keys.
- `name` is `oversee`, matching the folder name. Use lowercase letters, digits, and single hyphens only.
- `description` is 1 to 1024 characters. Lead with the `/oversee` trigger and the coding-only scope.
- `SKILL.md` stays under 500 lines. Put detail in `references/`, one level deep.
- The installed payload is `SKILL.md` and `references/` only.

## Install layout

The scripts write those two items to four folders:

| Folder | Read by | Source |
|---|---|---|
| `~/.agents/skills/oversee` | OpenCode, Codex, Copilot, Cursor. Antigravity app per the Google codelab | Tool docs |
| `~/.claude/skills/oversee` | Claude Code. OpenCode and Cursor also read it, so they may see two copies | Tool docs |
| `~/.gemini/config/skills/oversee` | Antigravity app | Antigravity docs. The codelab names a different path |
| `~/.gemini/antigravity-cli/skills/oversee` | Antigravity CLI | Official skills docs and Google codelab |

Windows uses `%USERPROFILE%` with backslashes. Uninstall removes the `oversee` folder from these four locations and nothing else.

Internet install, added 2026-10-14:

- `install.sh` detects how it was started. From a clone it installs from its own folder. Piped to bash, or run from a file with no `SKILL.md` next to it, it downloads the repo tarball (`OVERSEE_REPO` and `OVERSEE_BRANCH` override the defaults) and installs from that.
- `remote-install.ps1` is the Windows equivalent for `irm ... | iex`. It downloads the tarball, extracts with `tar` (zip fallback), then runs the bundled `install.bat`.
- Allocate Bash download state in the parent shell and install cleanup traps there. Assignments inside command substitutions do not propagate to parent cleanup. Propagate curl and tar failures.
- Installers stage and validate both managed items, replace the entire references subtree, and restore previous managed payload on replacement failure. Updates preserve unrelated files at the destination root and neighboring skills. Each target is a separate transaction; recovery failures must retain and report backup paths.
- README documents that download-and-execute one-liners run remote code; avoid unsupported blanket claims about Windows signing policy.

## Harness reference (checked 2026-10-15)

Doc links are under Sources at the end.

### Invoking the skill

| Harness | How the user runs it |
|---|---|
| Claude Code | `/oversee` |
| OpenCode | `/oversee` with `opencode/slash: "true"`. Otherwise the model loads it by name |
| Codex | `$oversee`, or pick it from `/skills`. Also matched by description |
| Copilot CLI | `/oversee` in the prompt |
| Cursor | `/oversee` in Agent chat |
| Antigravity app | `/oversee` in the prompt panel |
| Antigravity CLI | Official docs confirm skills become slash commands such as `/oversee`; not live-tested here |

### Subagents

| Harness | Spawn workers with | Parallel and wait | Custom worker file | Model and effort |
|---|---|---|---|---|
| Claude Code | `Agent` tool with `subagent_type` | Several calls in one message run in parallel. Background mode exists | `.claude/agents/*.md` or `~/.claude/agents/` | Per call: `model` (alias or full ID) and `effort` |
| OpenCode v2 | Native `subagent`; General and Explore; no Scout | Foreground blocks; background completion notice | `.opencode/agents/*.md`; config uses `agents`, `system`, `permissions` | Per-call model when exposed; `provider/model#variant` from live catalog |
| OpenCode v1 | Task delegation; General, Explore, Scout | Inspect active schema/version | Profiles or singular `agent` config | Native selection/profile capabilities differ from v2 |
| Codex | Ask in plain language. Built in: `default`, `worker`, `explorer` | Waits for all results, then consolidates | `~/.codex/agents/*.toml` or `.codex/agents/*.toml` | `model` and `model_reasoning_effort` in the file, or per spawn |
| Copilot | Built-in or custom agents; inspect actual schema | Version-specific; not live-tested | `.github/agents/NAME.md` | Profile `model` is documented; per-call effort/override needs local verification |
| Cursor | Task tool. Built in: explore, browser | Several calls in one message run in parallel. `is_background` flag | `.cursor/agents/*.md`. Also reads `.claude/agents` and `.codex/agents` | Frontmatter `model`: `inherit` or a model ID. Effort in brackets, such as `[effort=high]` |
| Antigravity | `invoke_subagent` tool. Built in: research, browser, self | Runs concurrently. Results return as messages | `.agents/agents/NAME.md` or `~/.gemini/config/agents/NAME.md` | Tiers only: `inherit`, `flash`, or `pro` |

### Model selection and Plan-mode transitions

Model IDs and variants are location/version-specific. Discover them at run time; do not maintain a model snapshot as an availability guarantee. The installed reference records syntax, sources, override precedence, and permission limits for each harness.

| Harness | Plan-to-execution handoff |
|---|---|
| OpenCode v2 | Native transition if exposed, otherwise user switches Plan to Build; controlled eval uses native session agent switch |
| OpenCode v1 | User Plan/Build control; programmatic handoff unverified |
| Claude Code | Native plan approval/exit; user permission-mode control if tool absent |
| Codex | Native app-server Plan-to-Default transition smoke-tested; retain ready plan and worker choice until host enables execution; UI remains unverified |
| Cursor | User clicks Build after reviewing plan |
| Copilot / Antigravity | Specific programmatic transitions unverified; request host implementation mode |

### Reading AGENTS.md

| Harness | Reads AGENTS.md | Notes |
|---|---|---|
| Claude Code | Yes, from v2.1.277 | Only when no CLAUDE.md or CLAUDE.local.md exists in the working directory or above. Older versions need `@AGENTS.md` inside a CLAUDE.md |
| OpenCode | Yes | Used before CLAUDE.md. First match wins |
| Codex | Yes | Combined instructions capped at 32 KiB by default (`project_doc_max_bytes`) |
| Cursor | Yes | Root and subdirectories |
| Copilot | Yes | Nearest file wins. Also reads a root CLAUDE.md or GEMINI.md |
| Antigravity | Yes | Any subdirectory (docs search snippet, not fetched) |

Consequence for this repo: a CLAUDE.md added at the root would make Claude Code skip this file, unless the CLAUDE.md starts with `@AGENTS.md`. Keep this file well under 32 KiB.

## Working on this repo

- `SKILL.md` is the behavior source of truth. Keep it lean. Move detail into `references/`.
- Harness-specific syntax and model IDs go only in `references/harnesses.md`. Keep it matched to the tables above.
- Don't state harness behavior from memory. Check the official docs, and record the source and date.
- If an install path changes, update all four install and uninstall scripts and the install table here in the same change.
- Line endings: `.bat` files must use CRLF, because cmd can fail on LF-only files, especially with GOTO and labels. `.sh` files must use LF, because bash fails on CR. Check line endings after every edit.
- Test the install scripts against a throwaway folder. Point `USERPROFILE` (cmd) or `HOME` (bash) at a fixture folder first. Don't run the scripts against the real profile unless the owner asks.
- Keep this file under 32 KiB so Codex reads all of it.
- Evals: test prompts go in `evals/evals.json`. That folder is not installed. Run outputs go in a sibling `oversee-workspace` folder, outside this repo.
- Don't commit or push unless the owner asks.
- `version.txt` is the canonical skill version. Use `python bump-ver.py patch|minor|major` or an exact semantic version to sync every current declaration; register new declarations in the script's `TARGETS`. Run `python bump-ver.py --check` before release. Do not change model/harness versions or historical eval evidence when bumping the skill. Version tooling is not installed.
- Keep comments short. The scripts have one-line header comments; keep them that way.

## Verification and remaining gaps

- Run `python -B -m unittest discover -s tests -v` for deterministic installer/evidence checks. Tests use temporary profiles and mock downloads; no real-profile installs or live inference.
- `evals/run.py` records six paired OpenCode sessions with caller-specified manager/worker settings. Outputs belong in a new sibling workspace folder. Usage/cost must come from native records; missing measurements stay unknown.
- `evals/codex_run.py` records unpaired Codex smoke cases with caller-specified settings and native completion events. `evals/codex_review.py` validates retained file hashes and recovers root/child turn contexts without inference. Do not apply OpenCode's transcript schema to Codex events. Current and legacy child-event shapes require coverage; thread configuration alone is not per-turn execution proof.
- The older three-case 100% versus 55% score graded workflow compliance using summary logs. It is not evidence of coding superiority or savings. Do not repeat it as a performance claim.
- First attempt failed Console authentication. At the caller's direction, six Go sessions then ran using Muse Spark 1.3 Contributor xhigh and DeepSeek V4.1 Flash max. Both overseen coding cases passed independent behavior checks, with exact workers, concurrency/dependencies, and Plan handoff observed. Two coding follow-ups retested final silence/scratch wording: behavior and handoff passed, but narration compliance still failed. The original verified scratch artifact was removed; external filesystem cleanliness is not proven by the follow-up reports.
- Evidence: `../oversee-workspace/reliability-pilot-go/`; corrected derived review: `../oversee-workspace/reliability-pilot-go-reviewed/`. Small-pilot native costs were higher with oversee ($0.029469 versus $0.006872); dependent baseline was incomplete. No savings claim is justified.
- Codex smoke evidence: `../oversee-workspace/codex-smoke-1/`; recovered/graded evidence: `../oversee-workspace/codex-smoke-1-reviewed/`. Caller chose GPT-6.1 Sol medium with GPT-6 Luna max. Ordinary-question and parallel cases passed observed orchestration checks; dependent implementation passed behavior, exact settings, and native handoff, but failed silence. Original exporter missed current child-event shapes; derived review recovers them from retained native events without more model calls. Cost is unknown.
- Only the three pilot scenarios are automated live cases. Retry, dirty workspace, cancellation, and other interaction scenarios require controlled/manual behavioral runs; unit tests of the recorder do not prove model compliance.
- Wording flexibility is intended behavior, not comprehensive live coverage. Add eval variations for natural `use <model>` wording, reordered model names, missing effort, command-first/command-last placement, ready plans, pasted findings, and combined audit-and-fix requests. Include negative quoted examples and host parser limits. Do not claim exact wording passed without retained evidence.
- Claude Code and Copilot CLI were not found on PATH. Cursor 3.24.18 and Antigravity app 2.23.1.0 are installed, but standalone agent CLIs were not found; GUI workflows remain untested. Other harnesses, duplicate global discovery, macOS, and WSL in the current revision still need live verification. Both Antigravity global destinations are now confirmed in official docs for their respective hosts. Windows cmd/PowerShell and Git Bash have deterministic installer coverage.
- Default effort selection remains a relative difficulty heuristic limited to each model's supported variants. No cross-model strength ranking is claimed.

## Glossary

- **Manager**: the higher-tier model running the skill.
- **Worker**: a cheaper subagent that handles one piece.
- **Piece**: a unit of work with one owner, the files it may touch, and a definition of done.
- **Brief**: the self-contained prompt for one worker.
- **Batch**: the workers launched together.
- **Audit**: the manager's review of a finished batch.

## Sources

Checked 2026-10-15; source dates in retained evidence remain historical.

- Agent Skills spec: https://agentskills.io/specification
- Claude Code skills: https://code.claude.com/docs/en/skills
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents
- Claude Code memory and AGENTS.md: https://code.claude.com/docs/en/memory
- OpenCode skills: https://opencode.ai/docs/skills/
- OpenCode agents: https://opencode.ai/docs/agents/
- OpenCode rules: https://opencode.ai/docs/rules/
- OpenCode v2 agents/tools/models/permissions/skills/API: https://opencode.ai/v2/docs/
- Copilot model configuration: https://docs.github.com/en/copilot/reference/custom-agents-configuration
- Cursor Plan mode: https://cursor.com/help/ai-features/plan-mode
- Codex skills: https://developers.openai.com/codex/skills
- Codex subagents: https://learn.chatgpt.com/docs/agent-configuration/subagents
- Codex AGENTS.md: https://developers.openai.com/codex/agent-configuration/agents-md
- Copilot skills: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- Copilot CLI skills: https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills
- Copilot CLI custom agents: https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-custom-agents
- Copilot repository instructions: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions
- Cursor skills: https://cursor.com/docs/skills
- Cursor subagents: https://cursor.com/docs/subagents
- Cursor rules and AGENTS.md: https://cursor.com/docs/rules
- Antigravity skills: https://antigravity.google/docs/skills/
- Antigravity subagents: https://antigravity.google/docs/subagents/
- Antigravity rules (AGENTS.md in subdirectories, from a search snippet): https://antigravity.google/docs/rules/
- Antigravity codelab: https://codelabs.developers.google.com/getting-started-with-antigravity-skills
