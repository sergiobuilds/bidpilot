"""Structure tests for the Cortex Code skill package and agent mounts."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "bidpilot" / "SKILL.md"
SCRIPT = ROOT / "skills" / "bidpilot" / "scripts" / "bidpilot.sh"
INTEGRATION_JSON = [
    ROOT / "integrations" / "claude-code" / ".mcp.json",
    ROOT / "integrations" / "cursor" / "mcp.json",
    ROOT / "integrations" / "cortex-code" / "mcp.json",
    ROOT / "integrations" / "gemini-cli" / "settings.json",
]
HARD_RULES = [
    "only when the decision is `PURSUE`",
    "Never invent evidence",
    "Closed notices are historical",
    "reader-only",
    "Never start a Cortex run for an\n   anonymous user",
]


def _frontmatter(text: str) -> dict[str, str]:
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    block = text.split("---\n", 2)[1]
    fields: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"')
    return fields


def test_skill_frontmatter_has_name_and_description() -> None:
    fields = _frontmatter(SKILL.read_text(encoding="utf-8"))
    assert fields["name"] == "bidpilot"
    assert len(fields["description"]) > 80
    for trigger in ("tender", "bid", "pursue", "공고", "입찰"):
        assert trigger in fields["description"]


def test_skill_states_hard_rules_and_examples() -> None:
    text = SKILL.read_text(encoding="utf-8")
    for rule in HARD_RULES:
        assert rule in text, rule
    assert text.count("### Example") == 3
    for command in ("list-tenders", "get-tender", "decide", "list-runs", "replay"):
        assert f"bidpilot.sh {command}" in text


def test_script_is_executable_and_rejects_unknown_command() -> None:
    assert os.access(SCRIPT, os.X_OK)
    result = subprocess.run([str(SCRIPT), "bogus"], capture_output=True, text=True, env={**os.environ, "BIDPILOT_API_URL": ""})
    assert result.returncode == 1
    assert json.loads(result.stderr.strip())["error"].startswith("usage")


def test_script_builds_remote_decide_body(tmp_path: Path) -> None:
    fake_curl = tmp_path / "curl"
    fake_curl.write_text('#!/usr/bin/env bash\nprintf \'%s\\n\' "$@"\n', encoding="utf-8")
    fake_curl.chmod(0o755)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}", "BIDPILOT_API_URL": "https://api.example/"}
    result = subprocess.run(
        [str(SCRIPT), "decide", "R26BK01680611-000", "--evidence", '{"0": true}'],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    lines = result.stdout.splitlines()
    assert "https://api.example/decide" in lines
    body = json.loads(lines[-1])
    assert body == {"notice_number": "R26BK01680611-000", "supplier_evidence": {"0": True}}


def test_integration_configs_parse_and_name_bidpilot() -> None:
    for path in INTEGRATION_JSON:
        data = json.loads(path.read_text(encoding="utf-8"))
        servers = data["mcpServers"]
        assert "bidpilot" in servers, path
        assert "bidpilot-local" in servers, path
        assert servers["bidpilot-local"]["args"][-1] == "bidpilot.mcp_server"


def test_readme_and_surface_docs_exist() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## 5 Mount BidPilot in your agent" in readme
    assert (ROOT / "integrations" / "chatgpt" / "README.md").exists()
    assert (ROOT / "integrations" / "cortex-code" / "README.md").exists()
