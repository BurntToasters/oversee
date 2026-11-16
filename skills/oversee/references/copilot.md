# GitHub Copilot

Best-effort host, not live-tested. Inspect the current agent tool before relying on any of this.

- Workers: `general-purpose` or a custom agent with edit access. `explore`, `research`, and `code-review` are host helpers. A command-only `task` agent is not an implementing worker.
- Model: profile `model` in `.github/agents/NAME.md` is documented. Per-call override, effort, and parallel completion are unverified. Use a matching existing profile, or settle the limitation with the user; do not silently inherit another model.
- Plan: the Plan-to-Agent transition is unverified. Keep the handoff and ask the user to enable implementation; never simulate a switch with a process.

Checked 2026-10-15. Docs: https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-custom-agents
