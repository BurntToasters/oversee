# Codex

- Workers: the native spawn tool with the `worker` or `default` agent. `explorer` is a host helper, never a worker. Tool names vary by version; use the fields actually present.
- Model and effort: request them per spawn, or use a profile (`model`, `model_reasoning_effort`; `name`, `description`, and `developer_instructions` are required) in `.codex/agents/` or `~/.codex/agents/`, created only with the user's agreement and kept out of the audited deliverable. Precedence: explicit spawn value, then `agents.default_subagent_model` and `agents.default_subagent_reasoning_effort`, then the parent's value; a value in the custom-agent file overrides all of these. Check the resolved metadata.
- Fresh context: where the schema has `spawn_agent` with `fork_turns: "none"`, use it. A full-history fork may force the parent's model.
- Workers inherit the parent's sandbox and approval policy. `agents.max_concurrent_threads_per_session` caps open threads.
- `workspace-write` keeps `.git`, `.agents`, and `.codex` read-only, so `git stash create` and commits fail there (use the hash fallback) and writing a `.codex/agents/` profile needs approval.
- Headless `codex exec` workers run read-only by default; implementing needs `--sandbox workspace-write`. Never add `--dangerously-bypass-approvals-and-sandbox` (alias `--yolo`), `--sandbox danger-full-access`, or `--approve-for-me` to keep them running.
- Waiting: use the blocking wait or completion events for the whole batch. Close settled threads where appropriate.
- Write no preamble before tool calls, in Plan or Default mode: in Plan mode the plan is your only message.
- Plan mode is host-controlled. Keep the plan and worker choice, present the native handoff, and dispatch only after execution mode is active. An approval sentence does not change the mode.
- You are invoked as `$oversee` or from `/skills`. The shipped `agents/openai.yaml` turns off implicit invocation.

Checked 2026-11-16; tool names (`spawn_agent`, `fork_turns`) are from the 2026-11-07 schema check, as the docs do not name them. Docs: https://learn.chatgpt.com/docs/agent-configuration/subagents https://learn.chatgpt.com/docs/non-interactive-mode https://learn.chatgpt.com/docs/agent-approvals-security
