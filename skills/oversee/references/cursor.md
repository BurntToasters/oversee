# Cursor

- Workers: native `Task`. Several calls in one message run together. Explore and Browser are host helpers, never workers.
- `is_background: true` returns at once and the subagent can be resumed later. Leave it off to block on the batch.
- Model: profile frontmatter `model` is `inherit` or a model ID with bracket options, such as `claude-opus-5[effort=high]`; `readonly` and `is_background` are also set there. Profiles live in `.cursor/agents/` or `~/.cursor/agents/`; `.claude/agents/` and `.codex/agents/` are also read, and `.cursor/` wins a name clash.
- The docs say the parent can name a model at launch but do not document the parameter. If the live Task schema has none, create a project profile with the user's agreement. Plan tier or admin rules can force a fallback model; check the actual metadata.
- Plan mode: the user reviews the plan and clicks Build. Keep the handoff; do not implement while Plan mode is active.
- Headless CLI: never add `--force` or `--yolo` to get past an approval. Verify workspace permissions first.

Checked 2026-11-07. Docs: https://cursor.com/docs/subagents
