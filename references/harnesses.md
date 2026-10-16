# Harness reference

Checked 2026-10-15 against the linked official docs. Live smoke tests: OpenCode v2.0.29 through the local service API's `session.prompt` operation and Codex CLI 0.162.0-alpha.17.2 on Windows. OpenCode v1 and the OpenCode TUI slash parser were not tested. Other harnesses remain documentation-checked. Smoke coverage is limited; it does not establish full compatibility. Read only the relevant section. Current tool schemas, supported model variants, and host mode take precedence over examples. Tool names overlap; do not identify a harness from one name.

## Common rules

- Resolve arbitrary user model display names, shorthand, or full IDs against the live catalog. Preserve version and variant. Prefer the session's provider only for the same requested model; clarify if distinct models remain ambiguous. No static model allowlist.
- Resolve human effort names such as `MAX` to supported catalog variants. Canonical IDs may be case-sensitive. Unsupported `max` does not mean the highest available level.
- Use native launch parameters when exposed. Inspect resolved metadata for forced inheritance or overrides; do not claim an unverified model/effort was honored.
- Request fresh context where supported. Check worker permissions: a separate profile/session must not exceed authorized boundaries. Do not change global configuration to enable dispatch.
- Plan-mode invocation prepares the handoff. Request a native approval/transition when exposed, otherwise state the user action. Only the host can enable execution.
- Read-only built-ins listed below (Explore, explorer, research) serve the host's own planning or research the user explicitly requested from workers. Never pass the worker model/effort to host planning helpers; oversee implementation uses an implementing agent.

## Invocation and activation

| Harness | Invocation | Host controls / limits |
|---|---|---|
| Claude Code | `/oversee` | Portable guard applies. User can optionally set `skillOverrides.oversee` to `user-invocable-only` in their settings. |
| OpenCode v2 | `@oversee` in the prompt, or the native skill tool when exposed | Current v2 docs describe skill loading by ID; TUI slash commands are a separate feature. The v2 skill docs do not document `opencode/slash`. |
| OpenCode v1 | `/oversee` when the host honors `metadata.opencode/slash: "true"` | This slash switch is documented by the legacy v1 skills page; do not assume it applies to v2. |
| Codex | `$oversee` or `/skills` | Host enforcement uses `policy.allow_implicit_invocation: false` in `agents/openai.yaml`; that optional sidecar is not installed. |
| Copilot CLI | `/oversee` | Retain execution guard even if host loads relevant skills automatically. |
| Cursor | `/oversee` | Retain execution guard; discussing the skill is not invoking it. |
| Antigravity app | `/oversee` | Check the installed app/version's UI. |
| Antigravity CLI | `/oversee` | Current official docs describe automatic conversion of skills to slash commands. Documentation-checked; not live-tested. |

Installation paths are discovery candidates, not proof of full behavior. Duplicate discovery from `.agents` and `.claude` needs a local smoke test. Installers never change host settings.

Sources: [Claude skills](https://code.claude.com/docs/en/skills), [OpenCode v1 skills](https://opencode.ai/docs/skills/), [OpenCode v2 skills](https://opencode.ai/v2/docs/skills/), [OpenCode v1 commands](https://opencode.ai/docs/commands/), [OpenCode v2 commands](https://opencode.ai/v2/docs/commands/), [OpenCode v2 CLI](https://opencode.ai/v2/docs/cli/), [Codex skills](https://learn.chatgpt.com/docs/build-skills), [Copilot skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills), [Cursor skills](https://cursor.com/docs/skills), [Antigravity skills](https://antigravity.google/docs/skills/), [Google codelab](https://codelabs.developers.google.com/getting-started-with-antigravity-skills).

## OpenCode v2

- Native `subagent`, directly or through Code Mode `execute`: agent ID, `description`, complete `prompt`, `background`, and `sessionID` for continuation. Use the current schema's per-call `model` override when offered. Do not assume every build exposes it or require a profile per requested model.
- Built-ins: `general` implements, `explore` reads. V2 has no built-in `scout`. General cannot launch nested subagents by default.
- Select `provider/model#variant`; model IDs can contain extra slashes. Use `opencode models` or exposed live catalog, including project custom models. A disk cache does not establish current access. Variants come from each model's metadata.
- Definitions: `.opencode/agents/*.md` or `~/.config/opencode/agents/*.md`. JSON uses `agents`, `system`, `permissions`, unlike v1.
- Foreground calls block; background calls notify on completion. Batch independent calls and wait for all; resume returned `sessionID`.
- Plan: native `plan` restricts project edits; `build` implements. Use an exposed native transition or ask user to switch to Build. In a controlled evaluation, an explicit later `run --agent build --session <id>` selects implementation; verify host mode changed.
- Current v2 skills docs describe loading by `@skill-id` or the native `skill` tool. They do not document the legacy `opencode/slash` switch; TUI custom commands are configured separately under `.opencode/commands/`.
- The live v2.0.29 smoke sent `/oversee` as ordinary text through the local service API's `session.prompt` operation and explicitly attached the project-local skill by ID. It retained native session evidence but did not exercise the TUI parser or prove that typing `/oversee` is recognized there. Test the installed TUI directly before claiming slash-command support.
- Observed v2.0.29: `run --model <selector> --agent <id> --session <id> --format json`; `api` and `session` commands, no v1 `export`. Collect parent/child evidence after completion, never through status polling.
- Child profiles have their own permissions. Preserve restrictions explicitly for independent headless sessions. `--auto` auto-approves permissions not explicitly denied; do not add it as a fallback convenience.

Sources: [v2 agents](https://opencode.ai/v2/docs/agents/), [v2 tools](https://opencode.ai/v2/docs/tools/), [v2 models](https://opencode.ai/v2/docs/models/), [v2 permissions](https://opencode.ai/v2/docs/permissions/), [v2 skills](https://opencode.ai/v2/docs/skills/), [v2 commands](https://opencode.ai/v2/docs/commands/), [v2 CLI](https://opencode.ai/v2/docs/cli/).

## OpenCode v1

- Legacy docs describe General, Explore, Scout, and Task delegation. Inspect the actual schema; do not apply v2 `subagent` arguments.
- The legacy v1 skills docs describe `metadata.opencode/slash: "true"` for exposing a skill as a TUI `/name` command. This is a version-specific control; current v2 skills docs instead describe `@skill-id` and native tool loading.
- JSON uses `agent`, `prompt`, `permission`; profiles live in `.opencode/agents/` or `~/.config/opencode/agents/`.
- Select model/effort through supported native parameters or existing matching profiles; do not promise v2 overrides on v1.
- Plan/Build selection is documented. A programmatic transition for this skill is unverified; use the visible control or ask user to switch.

Sources: [v1 agents](https://opencode.ai/docs/agents/), [v1 CLI](https://opencode.ai/docs/cli/), [v1 skills](https://opencode.ai/docs/skills/), [v1 commands](https://opencode.ai/docs/commands/).

## Claude Code

- Native `Agent`: `general-purpose` implements, `Explore` reads. Batch independent calls; use background notifications or foreground waits.
- Non-fork workers start fresh. A `fork` inherits conversation/model; it cannot promise a cheaper named worker.
- Use actual `model` and `effort` parameters. Per-call effort requires v2.1.292+. Environment overrides can take precedence. Resolve unsupported settings instead of dropping them.
- Profiles: `.claude/agents/` or `~/.claude/agents/`. Use full IDs when a version is named; aliases can move.
- Plan mode needs native approval/exit before edits. Use the exposed exit-plan tool; otherwise user can cycle permission mode with Shift+Tab. Verify execution before dispatch.

Sources: [subagents](https://code.claude.com/docs/en/sub-agents), [interactive mode](https://code.claude.com/docs/en/interactive-mode), [workflows](https://code.claude.com/docs/en/common-workflows).

## Codex

- Use available native spawn tool. Public docs describe plain-language delegation; internal tool names vary. Invoking this skill requests delegation; discussing it does not.
- Built-ins: `default`, `worker`, `explorer`. Custom TOML: `.codex/agents/`, `~/.codex/agents/`, with `name`, `description`, `developer_instructions`.
- Model/effort can be requested per spawn or in profiles. Explicit custom-agent settings may override spawn requests. Check actual precedence and resolved metadata.
- Some schemas expose `spawn_agent` and `fork_turns: "none"` for fresh context and explicit settings. Full-history forks may force inheritance. Use fields only when present.
- Use blocking waits/completion events, respect thread limits, and close settled threads where appropriate.
- Host controls Plan mode. Retain plan and worker choice, present native handoff, and await execution mode. An approval sentence or skill cannot override active host restrictions. App-server `turn/start` accepts native `collaborationMode` settings; controlled smoke tests verified Plan-to-Default transition in the same thread, with read-only preparation and workspace-write execution. The interactive UI transition remains unverified.
- Live Windows smoke tests verified explicit project-local skill attachment, exact manager/worker model and effort, concurrent independent workers, manager checks, and dependent handoff. Dependent work still emitted extra progress narration. These observations do not cover retries, cancellation, or other platforms.

Sources: [subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [skills](https://learn.chatgpt.com/docs/build-skills), [configuration](https://learn.chatgpt.com/docs/config-file/config-reference), [AGENTS.md](https://developers.openai.com/codex/agent-configuration/agents-md), [app-server](https://learn.chatgpt.com/docs/app-server). Fresh-context fields and mode selection also checked against local schemas and retained smoke evidence.

## GitHub Copilot

- CLI built-ins include `explore`, `task`, `general-purpose`, `code-review`, `research`. Inspect current agent tool. Command-only workers do not replace an implementation agent with edit access.
- Profiles: `.github/agents/NAME.md`. Current docs explicitly support `model`; claiming no model configuration is incorrect. Per-call override, effort, and parallel completion behavior need verification for the active CLI/IDE.
- Use a matching existing profile if per-call selection is unavailable, or resolve limitation with user. Do not silently inherit another model.
- Native Plan-to-Agent transition for this skill is unverified. Retain handoff and ask user to enable implementation; never simulate a switch with a process.

Sources: [CLI agents](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-custom-agents), [profile model field](https://docs.github.com/en/copilot/reference/custom-agents-configuration).

## Cursor

- Native `Task` supports concurrent subagents. Built-ins include Explore and Browser. Profiles: `.cursor/agents/`; compatible Claude/Codex locations also read.
- `model` accepts `inherit` or supported ID. Options use brackets, e.g. `[effort=high]`, according to the selected model. Plan/admin restrictions can force fallback; check actual metadata.
- Plan mode: user reviews plan, then clicks Build. Retain oversee handoff; do not implement while Plan mode remains active.
- The editor launcher and standalone agent CLI are separate test surfaces. Local Cursor 3.24.18 exposes editor help; no standalone `agent`/`cursor-agent` was found on PATH. Do not treat editor presence as a passing CLI test. Headless documentation describes `--force`/`--yolo`; never add these automatically to bypass approval. Verify workspace permissions and actual installed CLI behavior before headless implementation.

Sources: [subagents](https://cursor.com/docs/subagents), [Plan mode](https://cursor.com/help/ai-features/plan-mode), [CLI overview](https://cursor.com/docs/cli/overview), [headless mode](https://cursor.com/docs/cli/headless), [CLI permissions](https://cursor.com/docs/cli/reference/permissions).

## Antigravity

- Native `invoke_subagent` runs concurrent children and returns messages. Built-ins include `research`, `self`; browser has a dedicated invocation flow.
- Profiles: `.agents/agents/`, `~/.gemini/config/agents/`. Documented `model` takes tiers: `inherit`, `flash`, `pro`. Converting arbitrary provider models to tiers needs user agreement.
- Retain ready plan and request exposed native approval/implementation flow. Specific transition tool is unverified; ask user to enable execution if absent.
- Official skill docs now distinguish app/IDE global `~/.gemini/config/skills/` from CLI global `~/.gemini/antigravity-cli/skills/`; both use project `.agents/skills/`. CLI automatically converts skills to slash commands. Both installer destinations remain appropriate. Local Antigravity app 2.23.1.0 is installed, but no `agy`/agent CLI was found on PATH; discovery and execution remain unverified live.

Sources: [subagents](https://antigravity.google/docs/subagents/), [skills](https://antigravity.google/docs/skills/).

## Headless fallback

Use only if native dispatch is unavailable, never after an approval denial. Check installed help and establish equivalent or narrower permissions, correct directory, exact requested model/effort, and reliable completion. Otherwise report blocked and offer sequential work.

Pass briefs through argument arrays, stdin, or an accepted input file. Never interpolate task text into shell code: backticks, `$()`, quotes, and newlines are data. Wait for all processes without consuming partial transcripts. Retain native events for evaluation when requested. Never add an auto-approval flag just to keep workers running.
