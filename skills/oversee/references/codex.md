# Codex

- Workers: the native spawn tool with the `worker` or `default` agent. `explorer` is a host helper, never a worker. Tool names vary by version; use the fields actually present.
- Model and effort: request them per spawn, or use a profile (`model`, `model_reasoning_effort`) in `.codex/agents/` or `~/.codex/agents/`. Precedence: explicit spawn value, then `agents.default_subagent_model` and `agents.default_subagent_reasoning_effort`, then the parent's value; a value in the custom-agent file overrides all of these. Check the resolved metadata.
- Fresh context: where the schema has `spawn_agent` with `fork_turns: "none"`, use it. A full-history fork may force the parent's model.
- Workers inherit the parent's sandbox and approval policy. `agents.max_concurrent_threads_per_session` caps open threads.
- Waiting: use the blocking wait or completion events for the whole batch. Close settled threads where appropriate.
- Plan mode is host-controlled. Keep the plan and worker choice, present the native handoff, and dispatch only after execution mode is active. An approval sentence does not change the mode.
- You are invoked as `$oversee` or from `/skills`.

Checked 2026-11-07. Docs: https://learn.chatgpt.com/docs/agent-configuration/subagents
