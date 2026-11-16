# Cline

Best-effort host, not live-tested. Inspect the installed schema before relying on parallel completion or per-call model settings.

- Workers: agent teams with coordinator and teammate tools, or headless CLI runs (`--json`).
- Model: `-m/--model`, `-P/--provider`, and `--thinking` (`none` to `xhigh`) on the CLI; `--timeout` bounds a headless run.
- Plan: `-p`/`--plan` keeps a run read-only. Enable execution before dispatch; a programmatic approval transition is unverified.
- A headless prompt run auto-approves every tool by default (yolo). Pass `--auto-approve false` so a worker keeps approvals; never rely on the default to keep workers running.

Checked 2026-11-16. Docs: https://docs.cline.bot/cli
