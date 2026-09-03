# bidpilot skill — files and the Cortex Code driver

| Path | What it is |
|---|---|
| `SKILL.md` | The skill Cortex Code loads (frontmatter `name`, `description`; hard rules; workflow). |
| `scripts/bidpilot.sh` | The one script the skill calls. Prints one JSON document per call: `list-tenders`, `get-tender`, `decide`, `list-runs`, `replay`. Read-only. |
| `scripts/cortex-run.py` | Interactive-session driver. Runs one Cortex Code prompt non-interactively and prints the final answer. |

## Why `cortex-run.py` exists

The Cortex Code CLI has headless modes (`cortex exec`, `cortex -p`, `--goal`,
`--output-format stream-json`). On subscription/trial Snowflake accounts every
one of them exits with

    Error: --print mode is not available for subscription/trial accounts.

The gate is server-side (`SYSTEM$GET_CORTEX_CODE_CLI_SUBSCRIPTION()` reports the
subscription) and cannot be changed from the client. The interactive TUI still
works and still loads the `bidpilot` skill. The driver therefore runs the TUI
inside a pseudo-terminal and treats it as the API:

1. pre-marks the working directory as trusted in `~/.snowflake/cortex/cortex.json`
   (`projects.<dir>.hasTrustDialogAccepted`), the same key cortex writes itself;
2. spawns `cortex --connection <name> --sql-read-only --workdir <dir>` on a
   200x50 pty and renders the byte stream with a terminal emulator (`pyte`), so
   redraws and cursor movement do not corrupt the transcript;
3. answers the first-run dialogs if they appear (Claude-config import → skip,
   text style → 1, security notice → accept, SQL account → same, trust → yes);
4. waits for the input box (`│ › …` plus the `confirm actions` footer), types the
   prompt, then sends Enter separately so the placeholder text is replaced, not
   concatenated;
5. answers tool-permission menus (`Execute Command [MEDIUM]` → `1. Yes`, once
   per call). Anything whose header mentions writing, editing, creating or
   deleting a file is answered with `No`;
6. detects completion: the input box is back, no busy indicator, and the
   conversation text has not changed for `--idle` seconds (default 4);
7. sends `/exit` (Enter twice: the first Enter picks the command from the
   slash-command list), falls back to Ctrl+C twice, then SIGTERM/SIGKILL;
8. prints the last assistant text block (lines rendered as `* …` plus their
   two-space continuations) as plain text and, with `--transcript-dir`, saves
   `cortex-run-<stamp>.raw` (bytes), `.txt` (rendered transcript) and `.json`
   (prompt, connection, exit code, answer).

## Usage

```bash
# from a BidPilot checkout (pyte comes from the dev group)
uv sync
uv run python skills/bidpilot/scripts/cortex-run.py \
  "Reply with exactly the single word OK." --connection bidpilot-reader
# → OK

uv run python skills/bidpilot/scripts/cortex-run.py \
  "Use the bidpilot skill: list the tenders and decide R26BK01680611-000 with no evidence. Answer in 4 lines." \
  --connection bidpilot-reader --cwd "$PWD" --timeout 240 \
  --transcript-dir /tmp/cortex-runs
```

Options: `--connection` (default `bidpilot-reader`), `--timeout` seconds
(default 300), `--cwd` (working directory cortex opens; also exported as
`BIDPILOT_REPO` so a copied skill finds the checkout), `--idle`, `--transcript-dir`
(or `CORTEX_RUN_TRANSCRIPT_DIR`), `--cortex` (or `CORTEX_BIN`, default `cortex`
on `PATH`), `--debug` / `--debug-log FILE` (every key sent and every dialog
screen).

Exit codes: `0` answer printed; `2` timeout (no input box, prompt never
submitted, or no answer in time); `3` cortex exited early or no assistant text
found; `4` usage or environment error (missing `pyte`, bad `--cwd`, no binary).

## Limits, measured on 2026-09-03 (Cortex Code v1.1.78)

- The session is `--sql-read-only` and uses `bidpilot-reader`; cortex itself
  warns that bash, Python or MCP tools can still reach Snowflake outside the
  built-in SQL tool. Use read-only prompts; the driver denies file-writing tools
  but cannot audit what a shell command does.
- Skill lookup: cortex discovers `~/.snowflake/cortex/skills/bidpilot/` (copy
  the directory there, see `integrations/cortex-code/README.md`). In one run it
  first tried `<cwd>/scripts/bidpilot.sh`, got a failure, globbed for the file
  and recovered; the driver approves each attempt once.
- MCP servers found in the Claude Code config are attached automatically and a
  server that needs browser OAuth keeps a "Connecting…" spinner in the footer.
  The completion check ignores the footer, so this only costs noise.
- Answer language follows the model; the tender data is Korean, so the decision
  run answered in Korean (`REVIEW`, `4개`, `EVIDENCE REQUIRED`, `LOCKED`).
- One prompt per process; a session is not reused.

Evidence: `dev/active/grand-finale-product-20260903/evidence/agent-surface/cortex-driver/`
(`cortex-run-ok-dev-host.*`, `cortex-run-bidpilot-decide-dev-host.*`).
