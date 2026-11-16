# Host facts

Development reference for maintainers; not installed. The installed runtime notes are `skills/oversee/references/`. Don't state harness behavior from memory: check the official docs or source, and record the date.

## Harness tables

Checked 2026-10-15; Kiro CLI and additional hosts 2026-11-03; Claude Code, Codex, Cursor, and OpenCode v2 rows 2026-11-16; Copilot built-in agents and Cline CLI flags 2026-11-16. Per-host dates are on the last line of each `references/` file.

### Invoking the skill

| Harness | How the user runs it |
|---|---|
| Claude Code | `/oversee` |
| Cline | `/oversee` in the CLI or IDE skill slash commands |
| OpenCode v2 | Mention `@oversee` or use the native skill tool; TUI slash commands are configured separately |
| OpenCode v1 | `/oversee` when the host honors `opencode/slash: "true"` |
| Codex | `$oversee`, or pick it from `/skills`. Implicit description matching is off through the shipped `agents/openai.yaml` |
| Copilot CLI | `/oversee` in the prompt |
| Cursor | `/oversee` in Agent chat |
| Antigravity app | `/oversee` in the prompt panel |
| Antigravity CLI | Official docs confirm skills become slash commands such as `/oversee`; not live-tested here |
| Kiro CLI 2.x | `/oversee` as a skill slash command from 2.1; earlier 2.x auto-loads skills by description |
| Kiro CLI V3 | `/oversee` as a skill slash command, or automatic description match |

### Subagents

| Harness | Spawn workers with | Parallel and wait | Custom worker file | Model and effort |
|---|---|---|---|---|
| Claude Code | `Agent` tool, `general-purpose` or a custom profile; `Explore`/`Plan` are host helpers | Several calls in one message run in parallel; background. Interactive sessions cannot block on workers while fork mode is on (completion notices arrive in later turns); `claude -p`, the SDK, and sessions with fork mode off expose `run_in_background` on `Agent`, and `false` blocks until the worker returns. A main-agent turn that ends with no visible text gets one host prompt, "Your previous response had no visible output" (2.1.325, interactive and headless), so a session that cannot block ends waiting turns with one fixed line. Parent sees only the final message; `SendMessage` (agent ID or name, no agent teams needed) resumes a finished worker with its history. 20 concurrent, 3 nesting layers. `isolation: worktree` branches from the default branch, not the parent's `HEAD`; with agent teams enabled, a call with `name` launches a teammate. Sandbox: started in a repo subfolder, `.git` can be outside the writable area | `.claude/agents/*.md` or `~/.claude/agents/`; edits load within seconds, but a newly created `agents` folder needs a restart | Per call: `model` alias only and `effort` (v2.1.292+). Full model ID only in profile frontmatter. Model order: call, profile, `CLAUDE_CODE_SUBAGENT_MODEL`, parent; `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` makes the variable win and ignores the call. `CLAUDE_CODE_EFFORT_LEVEL` overrides call and profile effort. `/tasks` shows the model and effort used |
| OpenCode v2 | Native `subagent` with `general`; `explore` is a host helper; no Scout | v2.3.0: always background; returns `sessionID` (continues a child), `<subagent>` notice when idle; depth 1; shared working tree. Earlier v2 had a `background` flag | `.opencode/agents/*.md`; config uses `agents`, `system`, `permissions` | Optional per-call `model`, `provider/model#variant`; call > agent config > parent; unknown variant errors |
| OpenCode v1 | Task delegation; General, Explore, Scout | Inspect active schema/version | Profiles or singular `agent` config | Native selection/profile capabilities differ from v2 |
| Codex | Ask in plain language. Built in: `default`, `worker`, `explorer` | Waits for all results, then consolidates | `~/.codex/agents/*.toml` or `.codex/agents/*.toml`; `name`, `description`, `developer_instructions` required | `model` and `model_reasoning_effort` in the file, or per spawn. Headless `codex exec` is read-only unless `--sandbox workspace-write`. `workspace-write` keeps `.git`, `.agents`, `.codex` read-only (recursive), so `git stash create` and commits fail |
| Copilot | Built-in (`explore`, `task`, `general-purpose`, `code-review`, `research`, `rubber-duck`, `security-review`) or custom agents; inspect actual schema | Version-specific; not live-tested | `.github/agents/NAME.md` | Profile `model` is documented; per-call effort/override needs local verification |
| Cursor | Task tool. Built in: explore, browser | Several calls in one message run in parallel. `is_background` flag. Two nesting levels: the main agent's direct subagents can launch subagents; theirs cannot (Cursor 2.5+) | `.cursor/agents/*.md`. Also reads `.claude/agents` and `.codex/agents` | Per-call Task `model` (CLI 2026.11.13 schema, observed live); profile frontmatter `model`: `inherit` or a model ID. Effort is part of the ID or in brackets, such as `[effort=high]` |
| Antigravity | `invoke_subagent` and `define_subagent`; built in: research, browser, self | Asynchronous background subagents, parallel execution, nesting limit 10 | `.agents/agents/NAME.md` or `~/.gemini/config/agents/NAME.md` | Native subagents: tiers `inherit`, `flash`, `pro`; headless `agy -p --model --effort` for exact settings |
| Cline | Agent teams with coordinator/teammate tools; headless CLI | Multi-agent teams; headless runs with `--json`. A prompt run auto-approves all tools by default (yolo); `--auto-approve false` keeps approvals | Inspect current Cline agent config; not verified here | `-m/--model`, `-P/--provider`, `--thinking` `none`/`low`/`medium`/`high`/`xhigh` |
| Kiro CLI | Native subagent delegation; any custom agent file can run as a sub-agent; no ad-hoc definition in 2.x or V3 | Parallel, DAG dependencies, review loops; main agent waits and aggregates | `.kiro/agents/NAME.json|.md` or `~/.kiro/agents/` | Custom-agent `model`; effort only per session (`--effort`, `/effort`) or per model via `chat.modelDefaults`; no per-subagent effort |

### Model selection and Plan-mode transitions

Model IDs and variants are location/version-specific. Discover them at run time; do not maintain a model snapshot as an availability guarantee. The installed per-host references record syntax, sources, override precedence, and permission limits.

| Harness | Plan-to-execution handoff |
|---|---|
| OpenCode v2 | Native transition if exposed, otherwise user switches Plan to Build; controlled eval uses native session agent switch |
| OpenCode v1 | User Plan/Build control; programmatic handoff unverified |
| Claude Code | Native plan approval/exit; user permission-mode control if tool absent |
| Codex | Native app-server Plan-to-Default transition smoke-tested; retain ready plan and worker choice until host enables execution; UI remains unverified |
| Cursor | Editor: user clicks Build after reviewing plan. CLI: Shift+Tab, `/plan`, or `--plan` |
| Antigravity | `/plan` creates an Implementation Plan artifact; **Proceed** enters execution; `Shift+Tab` cycles modes |
| Cline | `-p`/`--plan` keeps the run read-only; enable execution before dispatch |
| Kiro CLI | Native Plan mode (V3 `Shift+Tab`; V2 `/plan`); approval hands the plan to the Default agent |
| Copilot | Specific programmatic transitions unverified; request host implementation mode |

### Reading AGENTS.md

| Harness | Reads AGENTS.md | Notes |
|---|---|---|
| Claude Code | Yes, from v2.1.277 | Only when no CLAUDE.md or CLAUDE.local.md exists in the working directory or above. Older versions need `@AGENTS.md` inside a CLAUDE.md |
| OpenCode | Yes | Used before CLAUDE.md. First match wins |
| Codex | Yes | Combined instructions capped at 32 KiB by default (`project_doc_max_bytes`) |
| Cursor | Yes | Root and subdirectories |
| Copilot | Yes | Nearest file wins. Also reads a root CLAUDE.md or GEMINI.md |
| Antigravity | Yes | Any subdirectory (docs search snippet, not fetched) |
| Kiro CLI | Yes | Root, subdirectories, and global steering; all AGENTS.md files are always included |

## Sources

Checked 2026-10-15 unless noted; source dates in retained evidence remain historical.

- skills CLI agent paths (`src/agents.ts`, 1.8.1; `globalReadsCanonical` from 1.8.0; unchanged in the 1.9.0 package, which adds `--rename` and records the source commit in the lock file), checked 2026-11-16: https://github.com/vercel-labs/skills/blob/main/src/agents.ts
- Cline skill folders (docs source), checked 2026-11-16: https://github.com/cline/cline/blob/main/docs/customization/skills.mdx
- Codex headless flags (`codex-rs/utils/cli/src/shared_options.rs`), checked 2026-11-16: https://github.com/openai/codex
- Claude Code CLI reference, checked 2026-11-16: https://code.claude.com/docs/en/cli-reference
- Claude Code env vars and sub-agents (model order, fork mode, `-p` wait ceiling, background tools), checked 2026-11-16: https://code.claude.com/docs/en/env-vars
- Codex skills (`agents/openai.yaml`) and non-interactive mode, checked 2026-11-16: https://learn.chatgpt.com/docs/build-skills and https://learn.chatgpt.com/docs/non-interactive-mode
- OpenCode v2.3.0 source (`packages/core/src/tool/plugin/subagent.ts`, `packages/core/src/config/plugin/skill-file.ts`), checked 2026-11-16: https://github.com/anomalyco/opencode/tree/v2.3.0
- Codex sandbox protected paths (`.git`, `.agents`, `.codex`), checked 2026-11-16: https://learn.chatgpt.com/docs/agent-approvals-security
- Claude Code sandboxing (`.git` writability) and sub-agents (`SendMessage`, `isolation`, `name` with agent teams), checked 2026-11-16: https://code.claude.com/docs/en/sandboxing and https://code.claude.com/docs/en/sub-agents
- Cursor subagent nesting (two levels since 2.5), checked 2026-11-16: https://cursor.com/docs/subagents
- Cursor skills (one-message attachment, Custom Mode, `~/.agents/skills` and `~/.claude/skills` discovery) and CLI modes and permissions, checked 2026-11-16: https://cursor.com/docs/skills https://cursor.com/docs/cli/using https://cursor.com/docs/cli/reference/permissions
- Cursor Task per-call `model` (live CLI 2026.11.13 stream-json `taskToolCall.args.model`), observed 2026-11-16
- skills CLI `check` exit status (docs/commands.md, 1.8.1), checked 2026-11-16: https://github.com/vercel-labs/skills/blob/main/docs/commands.md
- Claude Code `Agent` `run_in_background` (live `claude -p` 2.1.325 tool schema: present by default and with `CLAUDE_CODE_FORK_SUBAGENT=0`, absent with `=1`) and the no-visible-output prompt (2.1.325 binary; not in the docs), checked 2026-11-16
- Cline CLI approval default (`cline --help` text in the docs), checked 2026-11-16: https://docs.cline.bot/cli
- Copilot CLI built-in agents, checked 2026-11-16: https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-custom-agents

- Agent Skills spec: https://agentskills.io/specification
- skills CLI (docs/commands.md, docs/agents.md, docs/creating-skills.md): https://github.com/vercel-labs/skills
- Claude Code skills: https://code.claude.com/docs/en/skills
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents
- Claude Code memory and AGENTS.md: https://code.claude.com/docs/en/memory
- OpenCode skills: https://opencode.ai/docs/skills/
- OpenCode agents: https://opencode.ai/docs/agents/
- OpenCode rules: https://opencode.ai/docs/rules/
- OpenCode v2 agents/tools/models/permissions/skills/API: https://opencode.ai/v2/docs/
- OpenCode v2 skills and commands: https://opencode.ai/v2/docs/skills/ and https://opencode.ai/v2/docs/commands/
- OpenCode v1 skills and commands: https://opencode.ai/docs/skills/ and https://opencode.ai/docs/commands/
- Copilot model configuration: https://docs.github.com/en/copilot/reference/custom-agents-configuration
- Cursor Plan mode: https://cursor.com/help/ai-features/plan-mode
- Codex skills: https://learn.chatgpt.com/docs/build-skills
- Codex subagents: https://learn.chatgpt.com/docs/agent-configuration/subagents
- Codex AGENTS.md: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Copilot skills: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- Copilot CLI skills: https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills
- Copilot CLI custom agents: https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-custom-agents
- Copilot repository instructions: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions
- Cursor skills: https://cursor.com/docs/skills
- Cursor subagents: https://cursor.com/docs/subagents
- Cursor rules and AGENTS.md: https://cursor.com/docs/rules
- Antigravity skills: https://antigravity.google/docs/skills/
- Antigravity subagents: https://antigravity.google/docs/subagents/
- Antigravity customization discovery: https://antigravity.google/docs/customization-discovery/
- Antigravity plan: https://antigravity.google/docs/plan/
- Antigravity CLI reference: https://antigravity.google/docs/cli/reference/
- Antigravity rules (AGENTS.md in subdirectories, from a search snippet): https://antigravity.google/docs/rules/
- Antigravity codelab: https://codelabs.developers.google.com/getting-started-with-antigravity-skills
- Cline skills: https://docs.cline.bot/customization/skills
- Cline CLI: https://docs.cline.bot/cli
- Warp skills: https://docs.warp.dev/agents/capabilities/skills
- Warp multi-agent orchestration: https://docs.warp.dev/platform/orchestration
- Factory Droid skills: https://docs.factory.ai/harness/skills
- Factory Droid subagents: https://docs.factory.ai/harness/subagents
- Junie agent skills: https://junie.jetbrains.com/docs/agent-skills.html
- Junie subagents: https://junie.jetbrains.com/docs/junie-cli-subagents.html
- Qwen Code skills: https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/
- Gemini CLI skills: https://geminicli.com/docs/cli/skills/
- Amp skills: https://ampcode.com/docs/customize/skills
- Goose skills: https://goose-docs.ai/docs/guides/context-engineering/using-skills
- Pi skills: https://pi.dev/docs/latest/skills
- OpenHands skills: https://docs.openhands.dev/overview/skills
- Augment skills: https://docs.augmentcode.com/cli/skills
- Crush skills: https://github.com/charmbracelet/crush#agent-skills
- Devin CLI skills: https://docs.devin.ai/cli/extensibility/skills/overview
- Zed skills: https://zed.dev/docs/ai/skills
- Roo Code skills: https://docs.roocode.com/features/skills
- Kilo Code skills: https://kilo.ai/docs/customize/skills
- Windsurf skills: https://docs.windsurf.com/windsurf/cascade/skills
- Kiro skills: https://kiro.dev/docs/skills/
- Kiro configuration scopes: https://kiro.dev/docs/configuration/
- Kiro sub-agents: https://kiro.dev/docs/custom-agents/subagents/
- Kiro agent configuration: https://kiro.dev/docs/custom-agents/configuration-reference/
- Kiro CLI V3: https://kiro.dev/docs/cli/v3/
- Kiro CLI commands: https://kiro.dev/docs/reference/cli-commands/
- Kiro CLI headless: https://kiro.dev/docs/cli/headless/
- Kiro reasoning effort: https://kiro.dev/docs/models/effort/
- Kiro steering and AGENTS.md: https://kiro.dev/docs/steering/
