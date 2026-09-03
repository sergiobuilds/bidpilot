# Cortex Code CLI discovery (2026-09-03, Track B)

Measured, not guessed.

| Item | Finding | Source |
|---|---|---|
| Binary | deploy host `~/.local/bin/cortex`, `Cortex Code v1.1.52`. dev host: no `cortex`/`coco` binary; only `~/.snowflake/cortex/skills/` exists | `ssh <deploy-host> 'cortex --version'`, `which cortex coco snow` on both hosts |
| Skill format | `SKILL.md` with YAML frontmatter `name`, `description` (required), `tools` (optional). Bundled skills reference `scripts/` files in prose tables | bundled skill `billing/SKILL.md`, `ai-readiness-score/SKILL.md` under `~/.local/share/cortex/1.1.52+.../bundled_skills/`; docs "Cortex Code CLI extensibility" https://docs.snowflake.com/en/user-guide/cortex-code/extensibility |
| Skill locations | project `.cortex/skills/`; user `~/.snowflake/cortex/skills/`; `cortex skill add <path>` registers a directory (persisted in `skills.json`) | same docs page; `cortex skill --help`, `cortex skill list` |
| MCP support | yes. Config `~/.snowflake/cortex/mcp.json`, `mcpServers` entries with `type` `stdio` / `http` / `sse`; `cortex mcp add <name> <commandOrUrl> --transport http` | `cortex mcp --help`, `cortex mcp add --help`, `cortex mcp list` ("Config file: ~/.snowflake/cortex/mcp.json"); docs page above |
| Non-interactive run | `cortex exec "<prompt>" --format json --allowed ... --no-history --no-mcp` | `cortex exec --help` |
| deploy host skill dir | `~/.snowflake/cortex/skills/` empty before install; connections `bidpilot` (ACCOUNTADMIN) and `bidpilot-reader` exist | `cortex skill list`, `cortex connections list` |
| Headless run | `cortex exec` and `--goal` both fail with `--print mode is not available for subscription/trial accounts` on this account (v1.1.78 after auto-update) | `cortex-exec-deploy-host-blocked.txt` |
| Interactive run | `cortex` in tmux: `✓ SKILL bidpilot` auto-loaded from the prompt, ran `scripts/bidpilot.sh list-tenders` and `decide R26BK01680611-000`, reported REVIEW / 4 gaps / LOCKED / open with the four checks | `cortex-code-interactive-deploy-host.txt` |
| Claude Code stdio | `claude mcp add bidpilot -- uv run -q --project <worktree> python -m bidpilot.mcp_server` → `✔ Connected`; `claude -p` called `list_tenders` and `decide` and reported REVIEW / 4 / LOCKED | `claude-code-stdio-mcp-dev-host.txt` |
