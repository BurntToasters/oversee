# Kiro CLI

Best-effort host, not live-tested. V3 is the default engine from 3.0.0; `kiro-cli --v2` keeps the old one.

- Workers: native delegation to a custom agent or the built-in general-purpose agent. The context-gathering agent is a host helper. The parent picks an agent by its `description` or the name the user gives; an unknown name fails. Independent sub-agents run in parallel and the parent waits for results.
- A worker must be an agent file in `.kiro/agents/<name>.json|.md` (trusted workspaces) or `~/.kiro/agents/`; neither engine defines one ad hoc. With no suitable agent, propose a workspace agent file with `model` pinned and the needed `tools`, `permissions`, and `resources`. Create it only with the user's agreement, keep it out of the audited deliverable, and confirm it with `kiro-cli agent list` before dispatch.
- V3: the orchestrator needs the `subagent` tool category, and the stricter of the parent's policy and the sub-agent's `permissions` applies. Headless runs deny calls that need approval.
- Model: the agent file's `model` pins it and must match a `/model` ID (`kiro-cli chat --list-models --format json`).
- Effort: there is no per-agent or per-sub-agent effort. It comes from the session (`/effort`, `--effort`), then `chat.modelDefaults` in `.kiro/settings/cli.json`, then the model default. A workspace default for the worker's model is a configuration change that needs the user's agreement. Do not claim a per-worker effort when only a default applied.
- Process workers: `kiro-cli chat --no-interactive --agent <name> --model <id> --effort <level>` pins both. Use `--trust-tools` with exact tool IDs; never add `--trust-all-tools`. An unavailable model only warns in V3 headless, so verify the resolved model.
- Plan: V3 toggles Plan mode with Shift+Tab and approval hands the plan to the Default agent; V2 uses `/plan`. The Plan agent is a host helper. Dispatch only after execution is enabled.

Checked 2026-11-07. Docs: https://kiro.dev/docs/custom-agents/subagents/ https://kiro.dev/docs/models/effort/
