# AGENTS.md

Instructions for agents working on this repo. Read this before changing anything.

This file is not installed with the skill. The installed payload is `skills/oversee/` (`SKILL.md`, `references/`, and the Codex sidecar `agents/openai.yaml`), installed by `npx skills add`. Anything the installed skill needs at runtime must live there.

## What this repo is

`oversee` is one agent skill. The skill folder is `skills/oversee/`; the repo root holds docs, evals, tests, and version tooling. Users run it with `/oversee`.

The README premise: a larger model oversees other subagents without micromanaging them.

The intended setup is a higher-tier model as manager (for example Claude Opus 5.5 or GPT-6.1 Sol) and cheaper workers as subagents (for example Claude Haiku 5.5 or GPT-6 Luna). The manager plans and audits. The workers implement. The main goal is fewer tokens, so the manager never polls workers.

Primary hosts: Claude Code, Codex, Cursor, and OpenCode. The skill must work in these. GitHub Copilot, Cline, Antigravity, and Kiro CLI are best-effort: the skills CLI installs the skill for them (Cline needs a link into `~/.cline/skills`, see README) and their harness notes stay, but do not block releases on them (see Decision 13).

Owner: BurntToasters. License: MIT.

## Status (2026-11-16)

| Item | State |
|---|---|
| Design | Mostly settled. See Decisions below |
| `npx skills add BurntToasters/oversee -g` | Only installer since 1.2.0. skills CLI 1.9.0 smoke-tested on macOS 2026-11-16 with a throwaway `HOME`: local-path install for all eight hosts (layout below, `agents/openai.yaml` copied), GitHub-source install, `update`, and `remove` |
| `SKILL.md` | Explicit activation, implementation-only scope, run ends at its report, arbitrary live model selection, ready-plan handoff, baseline audit, bounded retries; 1.2.0 manager context economy (Decision 15) within a 14.5 KB budget |
| `references/*.md` | One file per host since 1.2.0 (`claude-code`, `codex`, `opencode`, `cursor`, `copilot`, `antigravity`, `cline`, `kiro`, `headless`); a run opens only its host's file. Claude Code, Codex, Cursor, and OpenCode v2 rechecked 2026-11-16 (OpenCode against the v2.3.0 docs and source; Codex tool names and Cursor CLI flags keep 2026-11-07); Kiro keeps its 2026-11-07 check and Antigravity 2026-11-03 (their subagent pages were reread 2026-11-16 with no change); Cline CLI flags and Copilot built-in agents rechecked 2026-11-16. OpenCode v2.0.29 service-API prompt and Codex CLI 0.162.0-alpha.17.2 have Windows smoke evidence; OpenCode v1, TUI slash parsing, Kiro CLI, Cline, and other hosts are not live-tested |
| `evals/` | Scenario catalog (`evals.json`, structure-checked by `tests/test_catalog.py`), committed pilot fixtures, and live recorders and graders for OpenCode, Codex, and Claude Code; results in `evals/README.md` |
| `version.txt`, `bump-ver.py` | Canonical skill version with synchronized metadata/README, validation, dry run, and replacement rollback; development-only |
| `docs/hosts.md` | Maintainer host tables and sources, moved out of this file in 1.2.0; not installed |
| `CHANGELOG.md` | Per-version change log; 1.2.0 in progress |
| `README.md` | Install, migration from the removed scripts, uninstall, host notes, compatibility, usage, and "Keeping runs cheap" (no savings claim) |

## Decisions

Items 1 to 5, 7 to 8, 13, 14, and 15 were agreed with the owner. Change them only with the owner. Decision 13 was reworded 2026-11-16 after the owner ordered the install scripts removed; Decision 12 gained the `git stash create` baseline the same day at the owner's request; Decision 9 gained the shipped Codex sidecar the same day at the owner's request.

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
9. **Trigger.** Explicit invocation or an explicit request for this workflow only. Quoted commands, skill reviews, and ordinary coding questions must not activate execution. A run ends with its final report; later turns are ordinary requests until the user invokes again. Keep the portable behavioral guard. Host switches that fit the payload ship with it: OpenCode `metadata.opencode/autoinvoke: "false"` and, since 2026-11-16 (owner-approved), the Codex sidecar `agents/openai.yaml` with `policy.allow_implicit_invocation: false`. Other host controls (Claude Code `skillOverrides`) are documented, not installed.
10. **Universal core.** `SKILL.md` must not depend on one harness's tool names or model IDs. Harness details go in `references/`.
11. **Plan mode.** A ready conversation plan counts as existing work. In Plan mode the worker choice names who implements after approval, not who plans: the manager researches and plans itself, prepares briefs, records the worker choice in the plan, and uses native approval/mode transition. Dispatch implementation only after the host enables execution; no second invocation or duplicate workers. Host planning helpers keep host defaults and never receive the worker choice. Outside Plan mode the same invocation plans and dispatches now.
12. **Workspace preservation.** Snapshot staged, unstaged, and untracked state; compare actual changes against that baseline. Never reset, stash, stage, or discard user edits for convenience. Since 2026-11-16 (owner-approved) a dirty-tree baseline may use `git stash create`, which records staged and unstaged edits as a commit id without changing the index, working tree, or stash list.
13. **Host priority.** Agreed with the owner 2026-10-15. Primary: Claude Code, Codex, Cursor, OpenCode. Stable-release host gates apply to these only. Copilot, Cline, Antigravity, and Kiro CLI are best-effort: the skills CLI installs the skill for them (Cline needs a link into `~/.cline/skills`, see README) and their harness notes stay in `references/`, but their live verification is optional and does not block a release.
14. **Implementation-only scope.** Agreed with the owner 2026-10-16; tightened 2026-11-09. Workers only implement. Planning, research, repo mapping, review, and audit are manager work in every mode, even when the user asks for workers to do them. A read-only invocation dispatches nothing. After a run, later requests never go to the earlier workers; only a later oversee run that names no worker may reuse the choice.
15. **Manager context economy.** Agreed with the owner 2026-11-16 for 1.2.0. The manager's context is re-read every turn, so it opens only its host's reference, does not re-explore a ready plan, and keeps a compact baseline (commit id and short status; on a dirty tree a `git stash create` id plus untracked-file hashes; no full diffs; no snapshot files), reopens its rules if compaction drops them. Briefs carry start pointers and piece-scoped checks; workers return `Changed`/`Checks`/`Unfinished`/`Uncertain`. The manager waits for the whole current batch with no text, audits from a whole-workspace path list and real diffs, and runs quiet checks one per command with no pipes. Between the worker-choice line and the report, manager turns are tool calls only, except required handoff, clarification, blocker, and cancellation messages and announcing an authorized worker change. Decisions 4, 5, 8, and 14 are unchanged; Decision 12 gained the `git stash create` baseline. Exception agreed 2026-11-16: in a Claude Code session that cannot block on workers (no `run_in_background` on `Agent`), a waiting turn ends with the one line `Waiting for N workers.`, because the host asks for visible output after a silent turn; `claude-code.md` carries it, `SKILL.md` and other hosts are unchanged.

## Invocation wording

- Interpret an actual invocation using the surrounding message and conversation. Natural wording such as `use <model>`, a model-only invocation, and task text before or after `/oversee` should preserve the user's intent. The host must first recognize and deliver the invocation; the skill cannot change a host's slash-command parser.
- Reuse a ready plan, pasted audit findings, or an explicit coding task as scope. A model-only invocation uses existing work; if none exists, ask what to oversee. If a model is named without effort, choose a supported effort by difficulty, as specified in `SKILL.md`.
- Adding `/oversee` to a ready plan or a task to plan while in Plan mode prepares oversight for implementation after host approval. The named worker is for implementation only; it never does plan research. Retain scope and worker selection; require neither another invocation nor duplicate dispatch after execution is enabled.
- Outside Plan mode, `/oversee <worker>` with a task plans in the manager and dispatches implementing workers in the same run.
- An audit-and-fix request means the manager audits first, turns actionable findings into scoped implementation pieces, then dispatches workers and verifies fixes. Resolve ambiguous findings or acceptance gaps before dispatch. An audit-only request dispatches nothing; the main agent audits and reports.
- User examples illustrate intent, not an exhaustive grammar or model allowlist. Quoted examples and discussions of these forms must not activate the workflow. Keep installed behavior in `SKILL.md`; this file is repository guidance only.

## SKILL.md outline

0. When the skill applies: invocation only, implementation only, one run then done. Before it: the context cost model and structural silence.
1. Reading the invocation and reuse of ready plans without re-exploring them.
2. Plan-mode handoff before implementing dispatch; worker choice reserved for implementation, manager-only planning.
3. Open only the host's reference file; choose workers: named, asked, or chosen by difficulty.
4. Plan, ownership, dependencies, and a compact starting baseline (commit id; `git status --short --branch --ignored=matching -uall`, which lists files inside untracked folders; `git stash create` on a dirty tree, hashes if it fails; hashes with no commit).
5. Self-contained worker briefs: scope, start pointers, constraints, piece-scoped checks with the quoted rule to run each exactly as written (allowlists deny `; echo` and chains), fixed report fields.
6. Batch dispatch within concurrency limits, then one wait for the current batch; no text on staggered notices; headless fallback reference.
7. Audit from a whole-workspace path list (ignored paths included; unauthorized commits and leftover scratch files fail, caches from checks do not) and `git diff <baseline id>`, quiet unpiped checks, integration checks, retries with failing lines, stopping conditions.
8. Result-only report, which ends the run.

## Skill file rules

- Frontmatter uses only Agent Skills spec fields: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Spec: https://agentskills.io/specification
- No Claude-only fields such as `disable-model-invocation`, `argument-hint`, `context`, `model`, `effort`, or `paths`. The claude.ai packaging step rejects unknown keys (Claude Code skills docs).
- OpenCode-specific switches go under `metadata` as quoted strings. The legacy v1 docs describe `opencode/slash: "true"` for TUI slash commands; current v2 docs describe `@skill-id` and native skill loading, and do not document that switch. `opencode/autoinvoke: "false"` keeps the skill out of the model's automatic picks. Other tools ignore these keys.
- `name` is `oversee`, matching the folder name. Use lowercase letters, digits, and single hyphens only.
- `description` is 1 to 1024 characters. Lead with the `/oversee` trigger and the coding-only scope.
- `SKILL.md` stays under 500 lines and 14,500 bytes (raised from 13,500 on 2026-11-16 when it reached 13,487; about 3,600 tokens, under the spec's 5,000-token advice, because the manager re-reads it every turn). Put detail in `references/`, one level deep: each file at most 3,500 bytes, all together at most 16,000.
- The installed payload is `skills/oversee/` only, holding `SKILL.md`, `references/`, and `agents/openai.yaml` (Codex reads it; other hosts ignore it). Put nothing else in that folder: the skills CLI copies the whole folder, and `tests/test_payload.py` checks the layout, frontmatter, byte budgets, and links.

## Install layout

Primary: `npx skills add BurntToasters/oversee -g` (skills CLI by Vercel Labs, Node 22.20+). It discovers `skills/oversee/SKILL.md`, writes one canonical copy to `~/.agents/skills/oversee`, and symlinks or copies into the folders of detected agents (`-a <agent>` selects, `--copy` avoids symlinks, `-y` skips prompts). `npx skills update`, `check`, and `remove` manage it; `DISABLE_TELEMETRY=1` opts out of its telemetry. Since CLI 1.8.0 (`readsCanonicalGlobally` in `src/agents.ts`), global installs for Codex, Cursor, OpenCode, Copilot, and Cline go only to `~/.agents/skills`; Claude Code gets `~/.claude/skills` (honoring `CLAUDE_CONFIG_DIR`), Antigravity `~/.gemini/config/skills`, Kiro CLI `~/.kiro/skills` (ignoring `KIRO_HOME`). 1.7.x also wrote `~/.cursor/skills`, `~/.config/opencode/skills`, and `~/.copilot/skills`; the README migration removes those. The CLI's `docs/agents.md` still lists the 1.7.x paths; its code wins. Cline conflict: Cline's docs list only `~/.cline/skills`, so the README tells Cline users to link it only if `/oversee` is missing (checked 2026-11-16 against CLI 1.8.1 source and Cline `docs/customization/skills.mdx`).

Many other hosts read `~/.agents/skills/oversee` and need no separate target; the list, the per-host folder table, and the migration note for people who used the removed scripts or CLI 1.7.x are in the README.

## Host facts

Per-host invocation, subagent, model, Plan-mode, and AGENTS.md tables, with their sources and check dates, are in [`docs/hosts.md`](docs/hosts.md) (not installed). The installed per-host references must stay consistent with it.

Consequence for this repo: a CLAUDE.md added at the root would make Claude Code skip this file, unless the CLAUDE.md starts with `@AGENTS.md`. Keep this file well under 32 KiB.

## Working on this repo

- `SKILL.md` is the behavior source of truth. Keep it lean. Move detail into `references/`.
- Harness-specific syntax and model IDs go only in `references/`: one file per host under `references/`; a run opens only its host's file. Keep them matched to `docs/hosts.md` and within the byte budgets.
- Don't state harness behavior from memory. Check the official docs, and record the source and date.
- If a host's skill folder changes, update the README folder table and migration note.
- Use LF line endings.
- Keep this file under 32 KiB so Codex reads all of it.
- Evals: test prompts go in `evals/evals.json`. That folder is not installed. Run outputs go in a sibling `oversee-workspace` folder, outside this repo.
- Don't commit or push unless the owner asks.
- `version.txt` is the canonical skill version. Use `python bump-ver.py patch|minor|major` or an exact semantic version to sync every current declaration; register new declarations in the script's `TARGETS`. Run `python bump-ver.py --check` before release. Do not change model/harness versions or historical eval evidence when bumping the skill. Version tooling is not installed.
- Record every user-visible change under the current version in `CHANGELOG.md` (development-only, not installed). Mark the version unreleased until it ships.
- Keep comments short.

## Verification and remaining gaps

Keep this section to how to verify and what is still open. Run history, costs, and evidence paths go in `evals/README.md`; per-version changes go in `CHANGELOG.md`.

- `python -B -m unittest discover -s tests -v` runs the deterministic payload, catalog, fixture, version, and grader checks (temporary folders and synthetic evidence; no installs or inference). CI (`.github/workflows/tests.yml`) runs them and `bump-ver.py --check` on Linux and Windows for every push and pull request.
- Live recorders, all writing to a new sibling `oversee-workspace` folder with caller-chosen settings: `evals/run.py` (paired OpenCode sessions through the service API), `evals/codex_run.py` plus `evals/codex_review.py` (Codex app-server; native events and persisted turn contexts), and `evals/claude_run.py` (headless `claude -p`; stream-json events, `--fork-mode on` reproduces an interactive session that cannot block). Cost and usage come only from native records; missing values stay unknown. Never add auto-approval flags to make a run pass.
- Every live result so far is one run per case on one machine: observations, not guarantees. No savings claim against working directly is justified (the Go pilot cost more with oversee).

Open gaps, by priority:

- Cursor: no live run (no standalone agent CLI found; Cursor 3.24.18 GUI untested). An arbitrary worker may need a `.cursor/agents/` profile.
- Claude Code: interactive sessions, the Plan-mode handoff, and `CLAUDE_CODE_FORK_SUBAGENT=0` interactively are untested; the one-line waiting exception ran only headless with fork mode on.
- OpenCode v1 and the v2 TUI slash parser are untested (the v2 pilot sent `/oversee` through the service API).
- Codex: the Plan phase opens with one sentence announcing the skill (3 of 3 runs, also after the no-preamble rule; cause not established); `git stash create` failing under `workspace-write` is inferred from the docs and a local read-only `.git` test.
- Catalog-only scenarios: 19-33 (invocation wording; 20-22 use the placeholder "Example Worker"), 34-39 (planning scope), 40-44 (post-run and read-only requests; need a multi-turn driver), 45-49 (context economy), 50-54 (baseline audit). Retry, cancellation, and denied-handoff behavior needs controlled runs; recorder unit tests do not prove model compliance.
- Install: `skills update` across the 1.7-to-1.8 layout move, whether Cline reads `~/.agents/skills`, duplicate global discovery, and Windows symlinks or junctions are untested.
- Best-effort hosts (Copilot, Cline, Antigravity, Kiro CLI) are documentation-checked only; Kiro has no per-subagent effort (Decision 13).
- Default effort selection is a relative difficulty heuristic within each model's supported levels; no cross-model ranking is claimed.

## Glossary

- **Manager**: the higher-tier model running the skill.
- **Worker**: a cheaper subagent that handles one piece.
- **Piece**: a unit of work with one owner, the files it may touch, and a definition of done.
- **Brief**: the self-contained prompt for one worker.
- **Batch**: the workers launched together.
- **Audit**: the manager's review of a finished batch.
