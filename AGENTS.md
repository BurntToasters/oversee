# AGENTS.md

Instructions for agents working on this repo. Read this before changing anything.

This file is not installed with the skill. The installed payload is `skills/oversee/` (`SKILL.md` plus `references/`), installed by `npx skills add`. Anything the installed skill needs at runtime must live there.

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
| `npx skills add BurntToasters/oversee -g` | Only installer since 1.2.0 (primary since 1.1.0). skills CLI 1.7.6 smoke-tested on macOS against a throwaway `HOME` with a local-path source: one canonical copy in `~/.agents/skills/oversee`, symlinks for Claude Code and Kiro. GitHub-source install not yet run. CLI 1.8.0 changed the global layout (source-checked 2026-11-16; see Install layout) |
| `SKILL.md` | Explicit activation, implementation-only scope, run ends at its report, arbitrary live model selection, ready-plan handoff, baseline audit, bounded retries; 1.2.0 manager context economy (Decision 15) within a 13.5 KB budget |
| `references/*.md` | One file per host since 1.2.0 (`claude-code`, `codex`, `opencode`, `cursor`, `copilot`, `antigravity`, `cline`, `kiro`, `headless`); a run opens only its host's file. Claude Code and OpenCode v2 rechecked 2026-11-16 (OpenCode against the v2.3.0 docs source); Codex, Cursor, Kiro keep their 2026-11-07 check; Cline and Antigravity 2026-11-03; Copilot 2026-10-15. OpenCode v2.0.29 service-API prompt and Codex CLI 0.162.0-alpha.17.2 have Windows smoke evidence; OpenCode v1, TUI slash parsing, Kiro CLI, Cline, and other hosts are not live-tested |
| `evals/` | Scenario catalog (including invocation-wording scenarios 19-33 and planning-scope scenarios 34-39, implementation-only scenarios 40-44, and context-economy scenarios 45-49, structure-checked by `tests/test_catalog.py`), OpenCode/Codex native evidence and review tools with `usage_by_role` (manager versus children), and offline regression checks; three Codex smoke cases added to existing Go evidence; dependent narration compliance still fails |
| `version.txt`, `bump-ver.py` | Canonical skill version with synchronized metadata/README, validation, dry run, and replacement rollback; development-only |
| `docs/hosts.md` | Maintainer host tables and sources, moved out of this file in 1.2.0; not installed |
| `CHANGELOG.md` | Per-version change log; 1.2.0 in progress |
| `README.md` | Install, migration from the removed scripts, uninstall, host notes, compatibility, usage, and "Keeping runs cheap" (no savings claim) |

## Decisions

Items 1 to 5, 7 to 8, 13, 14, and 15 were agreed with the owner. Change them only with the owner. Decision 13 was reworded 2026-11-16 after the owner ordered the install scripts removed; Decision 12 gained the `git stash create` baseline the same day at the owner's request.

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
9. **Trigger.** Explicit invocation or an explicit request for this workflow only. Quoted commands, skill reviews, and ordinary coding questions must not activate execution. A run ends with its final report; later turns are ordinary requests until the user invokes again. Keep the portable behavioral guard; optional host controls are documented, not installed.
10. **Universal core.** `SKILL.md` must not depend on one harness's tool names or model IDs. Harness details go in `references/`.
11. **Plan mode.** A ready conversation plan counts as existing work. In Plan mode the worker choice names who implements after approval, not who plans: the manager researches and plans itself, prepares briefs, records the worker choice in the plan, and uses native approval/mode transition. Dispatch implementation only after the host enables execution; no second invocation or duplicate workers. Host planning helpers keep host defaults and never receive the worker choice. Outside Plan mode the same invocation plans and dispatches now.
12. **Workspace preservation.** Snapshot staged, unstaged, and untracked state; compare actual changes against that baseline. Never reset, stash, stage, or discard user edits for convenience. Since 2026-11-16 (owner-approved) a dirty-tree baseline may use `git stash create`, which records staged and unstaged edits as a commit id without changing the index, working tree, or stash list.
13. **Host priority.** Agreed with the owner 2026-10-15. Primary: Claude Code, Codex, Cursor, OpenCode. Stable-release host gates apply to these only. Copilot, Cline, Antigravity, and Kiro CLI are best-effort: the skills CLI installs the skill for them (Cline needs a link into `~/.cline/skills`, see README) and their harness notes stay in `references/`, but their live verification is optional and does not block a release.
14. **Implementation-only scope.** Agreed with the owner 2026-10-16; tightened 2026-11-09. Workers only implement. Planning, research, repo mapping, review, and audit are manager work in every mode, even when the user asks for workers to do them. A read-only invocation dispatches nothing. After a run, later requests never go to the earlier workers; only a later oversee run that names no worker may reuse the choice.
15. **Manager context economy.** Agreed with the owner 2026-11-16 for 1.2.0. The manager's context is re-read every turn, so it opens only its host's reference, does not re-explore a ready plan, and keeps a compact baseline (commit id and short status; on a dirty tree a `git stash create` id plus untracked-file hashes; no full diffs; no snapshot files), reopens its rules if compaction drops them. Briefs carry start pointers and piece-scoped checks; workers return `Changed`/`Checks`/`Unfinished`/`Uncertain`. The manager waits for the whole current batch with no text, audits from a whole-workspace path list and real diffs, and runs quiet checks one per command with no pipes. Between the worker-choice line and the report, manager turns are tool calls only, except required handoff, clarification, blocker, and cancellation messages and announcing an authorized worker change. Decisions 4, 5, 8, and 14 are unchanged; Decision 12 gained the `git stash create` baseline.

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
4. Plan, ownership, dependencies, and a compact starting baseline (`git stash create` on a dirty tree).
5. Self-contained worker briefs: scope, start pointers, constraints, piece-scoped checks, fixed report fields.
6. Batch dispatch within concurrency limits, then one wait for the current batch; no text on staggered notices; headless fallback reference.
7. Audit from a whole-workspace path list and real diffs, quiet unpiped checks, integration checks, retries with failing lines, stopping conditions.
8. Result-only report, which ends the run.

## Skill file rules

- Frontmatter uses only Agent Skills spec fields: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Spec: https://agentskills.io/specification
- No Claude-only fields such as `disable-model-invocation`, `argument-hint`, `context`, `model`, `effort`, or `paths`. The claude.ai packaging step rejects unknown keys (Claude Code skills docs).
- OpenCode-specific switches go under `metadata` as quoted strings. The legacy v1 docs describe `opencode/slash: "true"` for TUI slash commands; current v2 docs describe `@skill-id` and native skill loading, and do not document that switch. `opencode/autoinvoke: "false"` keeps the skill out of the model's automatic picks. Other tools ignore these keys.
- `name` is `oversee`, matching the folder name. Use lowercase letters, digits, and single hyphens only.
- `description` is 1 to 1024 characters. Lead with the `/oversee` trigger and the coding-only scope.
- `SKILL.md` stays under 500 lines and 13,500 bytes. Put detail in `references/`, one level deep: each file at most 3,500 bytes, all together at most 16,000.
- The installed payload is `skills/oversee/` only, holding `SKILL.md` and `references/`. Put nothing else in that folder: the skills CLI copies the whole folder, and `tests/test_payload.py` checks the layout, frontmatter, byte budgets, and links.

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

- Run `python -B -m unittest discover -s tests -v` for deterministic payload, catalog, version, and evidence checks. CI (`.github/workflows/tests.yml`) runs them and `bump-ver.py --check` on every push and pull request. Tests use temporary folders and synthetic evidence; no installs or live inference.
- `evals/run.py` records six paired OpenCode sessions with caller-specified manager/worker settings. Outputs belong in a new sibling workspace folder. Usage/cost must come from native records; missing measurements stay unknown.
- `evals/codex_run.py` records unpaired Codex smoke cases with caller-specified settings and native completion events. `evals/codex_review.py` validates retained file hashes and recovers root/child turn contexts without inference. Do not apply OpenCode's transcript schema to Codex events. Current and legacy child-event shapes require coverage; thread configuration alone is not per-turn execution proof.
- Six Go sessions then ran using Muse Spark 1.3 Contributor xhigh and DeepSeek V4.1 Flash max. Both overseen coding cases passed independent behavior checks, with exact workers, concurrency/dependencies, and Plan handoff observed. Two coding follow-ups retested final silence/scratch wording: behavior and handoff passed, but narration compliance still failed. The original verified scratch artifact was removed; external filesystem cleanliness is not proven by the follow-up reports.
- Evidence: `../oversee-workspace/reliability-pilot-go/`; corrected derived review: `../oversee-workspace/reliability-pilot-go-reviewed/`. Small-pilot native costs were higher with oversee ($0.029469 versus $0.006872); dependent baseline was incomplete. No savings claim is justified.
- Codex smoke evidence: `../oversee-workspace/codex-smoke-1/`; recovered/graded evidence: `../oversee-workspace/codex-smoke-1-reviewed/`. Caller chose GPT-6.1 Sol medium with GPT-6 Luna max. Ordinary-question and parallel cases passed observed orchestration checks; dependent implementation passed behavior, exact settings, and native handoff, but failed silence. Original exporter missed current child-event shapes; derived review recovers them from retained native events without more model calls. Cost is unknown.
- `npx skills add` was run once (skills 1.7.6, macOS, local-path source, throwaway `HOME`). CLI 1.8 layout (source-checked only), the GitHub-source path, `skills update` after the layout move, whether Cline reads `~/.agents/skills`, and Windows symlink/junction behavior are untested.
- Only the three pilot scenarios are automated live cases. Retry, dirty workspace, cancellation, and other interaction scenarios require controlled/manual behavioral runs; unit tests of the recorder do not prove model compliance.
- Wording flexibility is intended behavior, not comprehensive live coverage. Eval scenarios 19-33 specify natural `use <model>` wording, reordered model names, missing effort, command-first/command-last placement, ready plans, pasted findings, combined audit-and-fix requests, negative quoted examples, and host parser limits. They are catalog-only; none has run live. Entries 20-22 use the placeholder model name "Example Worker"; substitute a real live model before running them. Do not claim exact wording passed without retained evidence. Scenarios 34-39 specify planning scope (worker choice never used for plan research, host helpers keep defaults, fresh-context plan handoff); also catalog-only. Scenarios 40-44 specify the 1.1.1 fix (post-run requests stay ordinary; read-only invocations dispatch nothing); catalog-only, and live checks need a multi-turn session the recorders do not drive. The OpenCode recorder now fails plan phases where a subagent ran with the requested worker setting.
- Claude Code and Copilot CLI were not found on PATH. Cursor 3.24.18 and Antigravity app 2.23.1.0 are installed, but standalone agent CLIs were not found; GUI workflows remain untested. Remaining live verification, by priority: Claude Code, Cursor, OpenCode v1 and the v2 TUI slash parser; then duplicate global discovery. Copilot, Cline, Antigravity, and Kiro CLI live checks are optional (Decision 13); Kiro CLI and Cline are documentation-checked only, and Kiro per-subagent effort is not documented. On paper, Claude Code fits best (per-call `model` and `effort`); Cursor sets worker model in agent-file frontmatter, so an arbitrary worker may need a `.cursor/agents/` profile. Both Antigravity global destinations are now confirmed in official docs for their respective hosts.
- The 1.2.0 context-economy rules (Decision 15) and scenarios 45-49 are unmeasured and catalog-only. Regrading the retained Go pilot with `evals.review` gives a pre-1.2.0 `usage_by_role.manager` baseline without inference; a new live run is needed to measure the effect. Structural silence is also unproven until rerun live.
- Codex docs hosts were unreachable on 2026-11-16, so `codex.md` keeps its 2026-11-07 check.
- Default effort selection remains a relative difficulty heuristic limited to each model's supported variants. No cross-model strength ranking is claimed.

## Glossary

- **Manager**: the higher-tier model running the skill.
- **Worker**: a cheaper subagent that handles one piece.
- **Piece**: a unit of work with one owner, the files it may touch, and a definition of done.
- **Brief**: the self-contained prompt for one worker.
- **Batch**: the workers launched together.
- **Audit**: the manager's review of a finished batch.
