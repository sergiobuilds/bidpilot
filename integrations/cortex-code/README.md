# BidPilot in Cortex Code (CoCo CLI)

Verified against Cortex Code v1.1.52 (`cortex --help`, `cortex skill --help`,
`cortex mcp --help`) and the Snowflake documentation page
"Cortex Code CLI extensibility"
(https://docs.snowflake.com/en/user-guide/cortex-code/extensibility).

## 1 Install the skill

Cortex Code discovers skills as `<dir>/<skill-name>/SKILL.md` with YAML
frontmatter `name` and `description` (required; `tools` optional). User-level
skills live in `~/.snowflake/cortex/skills/`; project-level skills in
`.cortex/skills/` inside the workspace.

```bash
# from a BidPilot checkout
mkdir -p ~/.snowflake/cortex/skills
cp -r skills/bidpilot ~/.snowflake/cortex/skills/bidpilot
cortex skill list          # shows "bidpilot" under discovered skills
```

Alternatively register the directory without copying:

```bash
cortex skill add /path/to/bidpilot/skills
```

The skill's script runs BidPilot locally (`uv run python -m bidpilot.agent_core`
from the checkout) or, when `BIDPILOT_API_URL` is exported, against the hosted
REST service. Set `BIDPILOT_REPO=/path/to/bidpilot` if the skill was copied out
of the repository and no API URL is used.

Try it interactively (`cortex` in the checkout, then type the prompt):

```
Use the bidpilot skill, read-only. List tenders, then decide R26BK01680611-000
with no supplier evidence. Report decision, evidence gaps, proposal gate, open or closed.
```

Expected: `SKILL bidpilot` loads, the two scripts run, and the answer is
`REVIEW`, 4 evidence gaps, `proposal_gate: LOCKED`, with the four
`EVIDENCE REQUIRED` checks. `cortex exec` (headless print mode) needs an
account tier that allows it; on subscription/trial accounts it exits with
`--print mode is not available`.

## 2 Mount the MCP server (optional)

Cortex Code reads `~/.snowflake/cortex/mcp.json` with `mcpServers` entries of
type `stdio`, `http`, or `sse`. Either copy `mcp.json` from this directory or
add the servers on the command line:

```bash
# hosted, read-only
cortex mcp add bidpilot https://bidpilot-api-164282963747.us-central1.run.app/mcp --transport http

# local stdio from a checkout
cortex mcp add bidpilot-local uv -- run --project /path/to/bidpilot python -m bidpilot.mcp_server

cortex mcp list
```

Tools exposed: `list_tenders`, `get_tender`, `decide`, `list_runs`, `replay`.
All are read-only; none starts a Cortex run or writes to Snowflake.
