# Antigravity

Best-effort host, not live-tested.

- Workers: native `invoke_subagent` runs asynchronous background children; `define_subagent` creates transient ones. `research` and `browser` are host helpers. Children have isolated context and can share the workspace or branch into a worktree; several run at once; nesting is capped at 10. Approval requests reach the parent UI.
- Model: profile `model` accepts only `inherit`, `flash`, or `pro` (`.agents/agents/<name>.md` or `~/.gemini/config/agents/`). Native subagents have no arbitrary model or per-worker effort. Agree on a tier with the user, or use headless workers.
- Headless: `agy -p` with `--model`, `--effort`, `--agent`, `--output-format stream-json`, `--sandbox` can honor an exact model and effort. Never add `--dangerously-skip-permissions`; set narrower permissions or a sandbox first.
- Plan: `/plan` drafts an Implementation Plan artifact; **Proceed** enters execution. The planning agent is a host helper and keeps its defaults. Keep the plan and worker choice until execution is enabled.

Checked 2026-11-03. Docs: https://antigravity.google/docs/subagents/
