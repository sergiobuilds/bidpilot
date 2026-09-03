"""Pure-function tests for the Cortex Code interactive-session driver.

The live driver (pty + Cortex Code TUI) is verified manually; these tests cover
ANSI stripping, transcript cleaning, answer extraction from a saved transcript,
and the trust pre-marking that skips the first-run dialog.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "bidpilot" / "scripts" / "cortex-run.py"
FIXTURE = ROOT / "tests" / "fixtures" / "cortex_transcript_decide.txt"

spec = importlib.util.spec_from_file_location("cortex_run", SCRIPT)
cortex_run = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(cortex_run)

PROMPT = (
    "Use the bidpilot skill: list the tenders and decide R26BK01680611-000 "
    "with no evidence. Answer in 4 lines."
)


def test_strip_ansi_removes_csi_osc_and_controls() -> None:
    raw = "\x1b[?25l\x1b[38;5;153mChecking\x1b[39m \x1b]0;title\x07done\x1b[2K\x07"
    assert cortex_run.strip_ansi(raw) == "Checking done"


def test_strip_ansi_keeps_plain_text_and_newlines() -> None:
    assert cortex_run.strip_ansi("a\r\nb\tc") == "a\r\nb\tc"


def test_clean_transcript_collapses_blank_runs_and_trailing_space() -> None:
    lines = ["one   ", "", "", "two", "   ", "", "three", "", ""]
    assert cortex_run.clean_transcript(lines) == "one\n\ntwo\n\nthree"


def test_extract_answer_from_saved_transcript() -> None:
    transcript = FIXTURE.read_text(encoding="utf-8")
    answer = cortex_run.extract_answer(transcript, PROMPT)
    lines = answer.splitlines()
    assert len(lines) == 4
    assert "REVIEW" in answer
    assert "LOCKED" in answer
    assert "4개" in answer
    assert "EVIDENCE REQUIRED" in answer
    # tool-call chrome and the echoed prompt are not part of the answer
    assert "BASH" not in answer
    assert "bidpilot.sh" not in answer
    assert not answer.startswith("* ")


def test_extract_answer_takes_the_last_block_after_the_prompt() -> None:
    transcript = "\n".join(  # noqa: FLY002
        [
            "* earlier chatter from a previous turn",
            "> Reply with exactly the single word OK.",
            "* I'll answer now.",
            "✓  BASH  (noop)",
            "  ├─ true",
            "  └─ ... (1 more line)",
            "* OK",
            "╭── * Session Summary ──╮",
            "│ ◆ Duration 1s        │",
        ]
    )
    assert (
        cortex_run.extract_answer(transcript, "Reply with exactly the single word OK.")
        == "OK"
    )


def test_extract_answer_keeps_paragraph_breaks_inside_a_block() -> None:
    transcript = (
        "> q\n* first line\n  second line\n\n  third after blank\n✓  BASH  (x)\n"
    )
    assert (
        cortex_run.extract_answer(transcript, "q")
        == "first line\nsecond line\n\nthird after blank"
    )


def test_extract_answer_returns_empty_when_no_assistant_text() -> None:
    assert (
        cortex_run.extract_answer("> q\n✓  BASH  (x)\n  └─ ... (1 more line)\n", "q")
        == ""
    )


def test_ensure_trust_marks_directory_and_is_idempotent(tmp_path: Path) -> None:
    home = tmp_path / "cortex"
    cwd = tmp_path / "proj"
    cwd.mkdir()
    cortex_run.ensure_trust(cwd, home)
    data = json.loads((home / "cortex.json").read_text(encoding="utf-8"))
    assert data["projects"][str(cwd)]["hasTrustDialogAccepted"] is True
    # existing keys survive and a second call does not rewrite
    data["securityNoticeAccepted"] = True
    (home / "cortex.json").write_text(json.dumps(data), encoding="utf-8")
    before = (home / "cortex.json").stat().st_mtime_ns
    cortex_run.ensure_trust(cwd, home)
    after = json.loads((home / "cortex.json").read_text(encoding="utf-8"))
    assert after["securityNoticeAccepted"] is True
    assert (home / "cortex.json").stat().st_mtime_ns == before


def test_parse_args_defaults_to_reader_connection(tmp_path: Path) -> None:
    args = cortex_run.parse_args(["hello", "--cwd", str(tmp_path)])
    assert args.connection == "bidpilot-reader"
    assert args.cwd == tmp_path.resolve()
    assert args.timeout == 300
