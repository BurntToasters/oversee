# Cursor

- Workers: native `Task`. Several calls in one message run together. Explore and Browser are host helpers, never workers. Nesting is two levels; the brief's no-delegation rule keeps workers from using it.
- `is_background: true` returns at once and the subagent can be resumed later. Leave it off to block on the batch.
- Model: profile frontmatter `model` is `inherit` or a model ID with bracket options, such as `claude-opus-5[effort=high]`; `readonly` and `is_background` are also set there. Profiles live in `.cursor/agents/` or `~/.cursor/agents/`; `.claude/agents/` and `.codex/agents/` are also read (`.cursor/` wins a clash).
- Task takes a per-call `model` (CLI 2026.11.13), a model ID from `agent models`; effort is part of the ID (`-low`, `-high`) or a bracket option, and Task has no separate effort. If the live schema has no `model`, create a project profile with the user's agreement, outside the audited deliverable, and name it. Plan tier, usage limits, or admin rules can force a fallback model; check the actual metadata.
- Plan mode: in the editor the user reviews the plan and clicks Build; in the CLI the user leaves Plan mode with Shift+Tab or starts without `--plan`. Keep the handoff; do not implement while Plan mode is active.
- A skill picked from the `/` menu attaches to one message. On a later turn of the same run (Build after a plan, or the answer to your question), reopen `SKILL.md` and this file before dispatch if their rules are no longer in context.
- Headless CLI: never add `--force` or `--yolo` to get past an approval. Verify workspace permissions first.

Checked 2026-11-16 (CLI 2026.11.13). Docs: https://cursor.com/docs/subagents https://cursor.com/docs/skills
