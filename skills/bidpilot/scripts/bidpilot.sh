#!/usr/bin/env bash
# BidPilot skill script. Prints exactly one JSON document to stdout.
#
# Usage:
#   bidpilot.sh list-tenders
#   bidpilot.sh get-tender <NOTICE_NUMBER>
#   bidpilot.sh decide <NOTICE_NUMBER> [--evidence '{"0": true, "1": false}']
#   bidpilot.sh list-runs
#   bidpilot.sh replay <RUN_ID>
#   bidpilot.sh draft-proposal <NOTICE_NUMBER> [--evidence JSON] [--supplier ID]
#                              [--position N] [--historical]
#
# Backend selection:
#   BIDPILOT_API_URL set   -> remote REST (GET /tenders, GET /tenders/{id},
#                             POST /decide, POST /proposal, GET /runs,
#                             GET /runs/{id})
#   otherwise              -> local core: uv run python -m bidpilot.agent_core
#                             from the repo root (BIDPILOT_REPO overrides).
#
# Read-only. Never starts a Cortex run and never writes to Snowflake.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${BIDPILOT_REPO:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"

usage() {
  echo '{"error": "usage: bidpilot.sh <list-tenders|get-tender NOTICE|decide NOTICE [--evidence JSON]|draft-proposal NOTICE [--evidence JSON] [--supplier ID] [--position N] [--historical]|list-runs|replay RUN_ID>"}' >&2
  exit 1
}

command="${1:-}"
[ -n "$command" ] || usage
shift

urlencode() { python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$1"; }

if [ -n "${BIDPILOT_API_URL:-}" ]; then
  base="${BIDPILOT_API_URL%/}"
  case "$command" in
    list-tenders)
      exec curl -sS --fail-with-body "$base/tenders" ;;
    get-tender)
      [ $# -ge 1 ] || usage
      exec curl -sS --fail-with-body "$base/tenders/$(urlencode "$1")" ;;
    decide)
      [ $# -ge 1 ] || usage
      notice="$1"; shift
      evidence='null'
      while [ $# -gt 0 ]; do
        case "$1" in
          --evidence) evidence="$2"; shift 2 ;;
          *) usage ;;
        esac
      done
      body="$(python3 -c 'import json, sys; print(json.dumps({"notice_number": sys.argv[1], "supplier_evidence": json.loads(sys.argv[2])}))' "$notice" "$evidence")"
      exec curl -sS --fail-with-body -H 'Content-Type: application/json' -X POST "$base/decide" --data "$body" ;;
    draft-proposal)
      [ $# -ge 1 ] || usage
      notice="$1"; shift
      evidence='null'; supplier='supplier-northstar'; position='0'; historical='false'
      while [ $# -gt 0 ]; do
        case "$1" in
          --evidence) evidence="$2"; shift 2 ;;
          --supplier) supplier="$2"; shift 2 ;;
          --position) position="$2"; shift 2 ;;
          --historical) historical='true'; shift ;;
          *) usage ;;
        esac
      done
      body="$(python3 -c 'import json, sys; print(json.dumps({"notice_number": sys.argv[1], "supplier_evidence": json.loads(sys.argv[2]), "supplier_id": sys.argv[3], "position_index": int(sys.argv[4]), "historical_exercise": sys.argv[5] == "true"}))' "$notice" "$evidence" "$supplier" "$position" "$historical")"
      exec curl -sS --fail-with-body -H 'Content-Type: application/json' -X POST "$base/proposal" --data "$body" ;;
    list-runs)
      exec curl -sS --fail-with-body "$base/runs" ;;
    replay)
      [ $# -ge 1 ] || usage
      exec curl -sS --fail-with-body "$base/runs/$(urlencode "$1")" ;;
    *) usage ;;
  esac
fi

case "$command" in
  list-tenders|get-tender|decide|draft-proposal|list-runs|replay) ;;
  *) usage ;;
esac

if [ ! -f "$REPO_ROOT/pyproject.toml" ]; then
  echo "{\"error\": \"bidpilot repo not found at $REPO_ROOT; set BIDPILOT_REPO or BIDPILOT_API_URL\"}" >&2
  exit 1
fi

exec uv run -q --project "$REPO_ROOT" python -m bidpilot.agent_core "$command" "$@"
