# OpenCode

Check the running version's tool schema first; v2 behavior changed between releases.

## v2

- Workers: native `subagent` with agent `general`, a short `description`, and a complete `prompt`. `explore` is a host helper, never a worker. There is no `scout`. Children start with fresh context, share the working tree, and cannot nest by default.
- Model: pass the worker as the call's `model`, written `provider/model#variant` (v2.3.0 schema; model IDs can contain extra slashes). The user's worker choice for this run is the explicit request that parameter requires. Precedence: the call's `model`, then the agent's configured model, then the parent's. Look IDs and variants up with the models tool or `opencode models`; an unknown variant is an error, not a fallback.
- If the user names no worker and `agents.general.model` is configured, offer that as the suggestion. If a schema has no `model` parameter, the route is a profile in `.opencode/agents/<name>.md` (`mode: subagent`, `model: provider/model#variant`), created with the user's agreement. Do not create or edit agent profiles mid-run otherwise: the subagent tool's description is rebuilt from the agent catalog.
- Waiting: in v2.3.0 subagents always run in the background. The call returns a `sessionID` at once and a `<subagent>` message arrives when the child goes idle. Launch the batch in one turn, then end the turn without text; do not sleep or poll. Earlier v2 releases had a `background` flag; there, a foreground call blocks.
- Retry: pass the returned `sessionID` to continue that child with its context.
- Plan: `plan` restricts edits, `build` implements. Use a native transition if exposed, otherwise ask the user to switch agents (Shift+Tab). Verify the mode changed before dispatch.
- Child profiles have their own permissions; keep restrictions explicit. Headless `run --auto` approves everything not denied; never add it as a convenience.
- You are invoked as `@oversee` or through the `skill` tool.

## v1

- Legacy Task delegation with General, Explore, Scout. Inspect the actual schema; do not apply v2 `subagent` arguments or promise v2 overrides.
- Config uses `agent`, `prompt`, `permission`; profiles live in `.opencode/agents/`. Select model and effort through native parameters or an existing matching profile.
- Plan/Build is a user control; ask the user to switch.

Checked 2026-11-16 against the v2.3.0 docs source. Docs: https://opencode.ai/v2/docs/agents/ https://opencode.ai/v2/docs/tools/
