# Claude Code

- Workers: native `Agent` with `general-purpose` or a custom profile. `Explore` and `Plan` are host helpers, never workers. Use a non-fork agent: a fork inherits the conversation and model, so it cannot be a cheaper named worker.
- Model: the per-call `model` takes an alias only (`sonnet`, `opus`, `haiku`, `fable`). A full model ID or `inherit` works only in profile frontmatter. When the user names an exact version no alias guarantees, use or create a project profile in `.claude/agents/` with the full ID, with the user's agreement.
- Effort: per-call `effort` (`low`, `medium`, `high`, `xhigh`, `max`, model-dependent) needs v2.1.292+. `CLAUDE_CODE_EFFORT_LEVEL`, `CLAUDE_CODE_SUBAGENT_MODEL`, and `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` can override the call. Resolve an unsupported setting; do not drop it.
- Launch the batch as several `Agent` calls in one message. Limits: 20 concurrent, three nesting layers.
- Waiting: workers start in the background. In interactive sessions the main agent cannot block on them while fork mode is on (the default); each completion arrives as a notification in a later turn. `claude -p` and the Agent SDK can wait. On an early notice, end the turn without text.
- You receive only a worker's final message. To retry, resume the finished worker with `SendMessage` to its agent ID or name; it keeps its history.
- Plan mode: use the exit-plan tool for approval; otherwise the user cycles permission mode with Shift+Tab. Plan files live in `~/.claude/plans` unless `plansDirectory` is set, which may be outside what a worker can read. Verify execution is enabled before dispatch.

Checked 2026-11-16. Docs: https://code.claude.com/docs/en/sub-agents
