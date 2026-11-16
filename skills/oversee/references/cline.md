# Cline

Best-effort host, not live-tested. Inspect the installed schema before relying on parallel completion or per-call model settings.

- Workers: agent teams with coordinator and teammate tools, or headless CLI runs (`--json`).
- Model: `-m/--model`, `-P/--provider`, and `--thinking` levels on the CLI; `--timeout` bounds a headless run.
- Plan: `-p`/`--plan` keeps a run read-only. Enable execution before dispatch; a programmatic approval transition is unverified.
- Never add `--auto-approve` just to keep workers running.

Checked 2026-11-03. Docs: https://docs.cline.bot/cli
