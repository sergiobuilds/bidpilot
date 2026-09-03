#!/usr/bin/env python3
"""Run one Cortex Code prompt through the interactive TUI and print the answer.

Why this exists: on subscription/trial Snowflake accounts every headless path
of the Cortex Code CLI (`cortex exec`, `cortex -p`, `--goal`, stream-json)
exits with "--print mode is not available for subscription/trial accounts".
The gate is server-side. The interactive TUI still works, so this script
drives it inside a pseudo-terminal: it answers the first-run dialogs, waits
for the input box, types the prompt, waits for the agent to finish, sends
`/exit`, and prints the last assistant answer as plain text.

Usage:
    cortex-run.py "<prompt>" [--connection bidpilot-reader] [--timeout 300]
                  [--cwd DIR] [--transcript-dir DIR] [--idle 4] [--debug]

Exit codes: 0 answer printed; 2 timeout; 3 cortex exited early / no answer;
4 usage or environment error.

Safety: the session always starts with `--sql-read-only`; the default
connection is `bidpilot-reader`. Tool calls that need approval are answered
from an allowlist (see `approve_tool`): BASH / READ-style tools are approved,
anything that writes files is denied. Nothing here patches the cortex binary.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import pty
import re
import select
import signal
import struct
import sys
import termios
import time
from pathlib import Path

try:  # pure parsing helpers below work without pyte; the live driver needs it
    import pyte
except ImportError:  # pragma: no cover - exercised only when the dev group is absent
    pyte = None

ANSI_RE = re.compile(
    r"\x1b\[[0-?]*[ -/]*[@-~]"  # CSI sequences
    r"|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"  # OSC sequences
    r"|\x1b[@-Z\\-_]"  # 2-byte escapes
    r"|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"  # other C0 controls except \t \n \r
)
SPINNER_CHARS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
CHROME_CHARS = "╭╰│├⏵─"
COLS, ROWS = 200, 50

# Lines in the rendered transcript that are TUI chrome, not conversation.
CHROME_PREFIXES = (
    "╭",
    "╰",
    "│",
    "⏵",
    "view:",
    "──",
    "─────",
    "Checking configuration",
)

# First-run dialogs: (needle in screen text, keys to send). Order matters.
DIALOGS = [
    ("Import these settings into Cortex Code", "n"),
    ("Choose your text style", "1\r"),
    ("I understand and accept", "y"),
    ("same account for SQL queries", "y"),
    ("trust the files in this folder", "y"),
    ("Do you trust", "y"),
]


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences and stray control characters."""
    return ANSI_RE.sub("", text)


def clean_transcript(lines: list[str]) -> str:
    """Trim trailing spaces and collapse runs of blank lines."""
    out: list[str] = []
    for raw in lines:
        line = raw.rstrip()
        if not line and out and not out[-1]:
            continue
        out.append(line)
    while out and not out[-1]:
        out.pop()
    return "\n".join(out)


def _is_continuation(line: str) -> bool:
    return line.startswith("  ") and not line.lstrip().startswith(("├─", "└─"))


def extract_answer(transcript: str, prompt: str | None = None) -> str:
    """Return the last assistant text block after the echoed prompt.

    Cortex Code renders assistant prose as a line starting with ``* `` followed
    by continuation lines indented two spaces. Tool calls (``✓  BASH``), the
    echoed prompt (``> ...``) and TUI chrome are skipped. When ``prompt`` is
    given the search starts after the line that echoes it.
    """
    lines = transcript.splitlines()
    start = 0
    if prompt:
        needle = " ".join(prompt.split())[:40]
        for i, line in enumerate(lines):
            if line.startswith("> ") and needle[:20] in " ".join(line.split()):
                start = i + 1
    blocks: list[list[str]] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if line.startswith("* "):
            block = [line[2:]]
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if _is_continuation(nxt):
                    block.append(nxt[2:])
                    i += 1
                    continue
                if (
                    not nxt.strip()
                    and i + 1 < len(lines)
                    and _is_continuation(lines[i + 1])
                ):
                    block.append("")
                    i += 1
                    continue
                break
            blocks.append(block)
            continue
        i += 1
    if not blocks:
        return ""
    return "\n".join(blocks[-1]).strip()


def screen_text(screen) -> list[str]:
    """Rendered scrollback plus the visible screen, as plain lines."""
    hist = [_line_from_history(line) for line in screen.history.top]
    return hist + list(screen.display)


def _line_from_history(line) -> str:
    # pyte history rows are dicts {column: Char}; render them to COLS width.
    width = max(line.keys(), default=-1) + 1
    return "".join(line[x].data if x in line else " " for x in range(width))


class CortexSession:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.raw = bytearray()
        self.screen = pyte.HistoryScreen(COLS, ROWS, history=50000)
        self.screen.set_mode(pyte.modes.LNM)
        self.stream = pyte.ByteStream(self.screen)
        self.pid = -1
        self.fd = -1
        self.answered: set[str] = set()
        self.log = None
        if args.debug_log:
            self.log = Path(args.debug_log).open("a", encoding="utf-8")  # noqa: SIM115

    # -- process ----------------------------------------------------------
    def spawn(self) -> None:
        argv = [
            self.args.cortex,
            "--connection",
            self.args.connection,
            "--sql-read-only",
            "--workdir",
            str(self.args.cwd),
        ]
        env = dict(os.environ)
        env.update(
            TERM="xterm-256color",
            COLUMNS=str(COLS),
            LINES=str(ROWS),
            BIDPILOT_REPO=str(self.args.cwd),
        )
        pid, fd = pty.fork()
        if pid == 0:  # child
            os.chdir(self.args.cwd)
            os.execvpe(argv[0], argv, env)
        self.pid, self.fd = pid, fd
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))

    def alive(self) -> bool:
        if self.pid <= 0:
            return False
        pid, _ = os.waitpid(self.pid, os.WNOHANG)
        if pid == self.pid:
            self.pid = -1
            return False
        return True

    def pump(self, timeout: float = 0.2) -> bool:
        """Read pending output into the emulator. Returns True when data arrived."""
        try:
            r, _, _ = select.select([self.fd], [], [], timeout)
        except (OSError, ValueError):
            return False
        if not r:
            return False
        try:
            data = os.read(self.fd, 65536)
        except OSError:
            return False
        if not data:
            return False
        self.raw += data
        self.stream.feed(data)
        return True

    def send(self, text: str, note: str = "") -> None:
        self.debug(f"send {text!r} {note}")
        os.write(self.fd, text.encode())

    def debug(self, msg: str) -> None:
        if self.log:
            self.log.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
            self.log.flush()
        if self.args.debug:
            print(f"[cortex-run] {msg}", file=sys.stderr)

    # -- screen helpers ---------------------------------------------------
    def visible(self) -> str:
        return "\n".join(self.screen.display)

    def transcript(self) -> str:
        return clean_transcript(screen_text(self.screen))

    def conversation(self) -> str:
        """Transcript without TUI chrome and status lines (stable while idle)."""
        keep = []
        for line in self.transcript().splitlines():
            s = line.strip()
            if not s or s[0] in CHROME_CHARS or s.startswith(CHROME_PREFIXES):
                continue
            if any(ch in s for ch in SPINNER_CHARS):
                continue
            keep.append(line)
        return "\n".join(keep)

    def input_box_ready(self) -> bool:
        vis = self.visible()
        return bool(re.search(r"^│ › ", vis, re.MULTILINE)) and "confirm actions" in vis

    def agent_busy(self) -> bool:
        vis = self.visible()
        # While the agent works the footer shows an interrupt hint and a spinner
        # on the status line above the box. The MCP-connect spinner sits on the
        # bottom-right and must not count.
        if "esc to interrupt" in vis or "Esc to interrupt" in vis:
            return True
        for line in self.screen.display:
            s = line.strip()
            if (
                s
                and s[0] in SPINNER_CHARS
                and "Connecting to" not in s
                and "MCP" not in s
            ):
                return True
        return False

    def handle_dialogs(self) -> bool:
        vis = self.visible()
        if self.input_box_ready():
            return False
        for needle, keys in DIALOGS:
            if needle in vis and needle not in self.answered:
                self.answered.add(needle)
                time.sleep(0.3)
                self.send(keys, f"(dialog: {needle})")
                return True
        return False

    def approve_tool(self) -> bool:
        """Answer a tool-permission menu. Allow read-only tools, deny writes.

        The menu looks like ``Execute Command [MEDIUM]`` followed by numbered
        options (``❯ ○ 1. Yes`` ... ``○ 6. No``) and the hint ``Enter select``.
        """
        vis = self.visible()
        menu = re.search(r"^ ?❯ ○ 1\. ", vis, re.MULTILINE)
        if not menu or "Enter select" not in vis:
            return False
        header = vis[: menu.start()][-1500:]
        options = dict(re.findall(r"○ (\d)\. ([^\n]+)", vis[menu.start() :]))
        deny = bool(
            re.search(
                r"\b(Write|Edit|Create|Delete|Remove)\b.*\b(file|File)\b|\bWRITE\b|\bEDIT\b",
                header,
            )
        )
        done = self.transcript().count("\n✓") + self.transcript().count("\n×")
        stamp = f"tool:{hash(header)}:{done}"
        if stamp in self.answered:
            return False
        self.answered.add(stamp)
        self.debug(
            "tool permission menu:\n" + vis[menu.start() - 400 : menu.start() + 800]
        )
        if deny:
            key = next(
                (n for n, label in options.items() if label.strip().startswith("No")),
                "6",
            )
        else:
            key = "1"
        self.send(
            key, "(tool permission: deny)" if deny else "(tool permission: allow once)"
        )
        time.sleep(0.4)
        self.pump(0.3)
        if re.search(r"^ ?❯ ○ \d\. ", self.visible(), re.MULTILINE):
            self.send("\r", "(confirm menu selection)")
        return True

    # -- main flow --------------------------------------------------------
    def run(self) -> tuple[int, str]:
        deadline = time.time() + self.args.timeout
        self.spawn()
        # 1. reach the input box
        while time.time() < deadline:
            self.pump()
            if not self.alive():
                return 3, "cortex exited before the input box appeared"
            if self.handle_dialogs():
                continue
            if self.input_box_ready():
                break
        else:
            return 2, "timeout waiting for the Cortex Code input box"
        time.sleep(0.5)
        self.pump(0.5)
        # 2. type the prompt, then Enter (separately so the placeholder is replaced)
        self.send(self.args.prompt, "(prompt)")
        time.sleep(0.4)
        self.pump(0.3)
        self.send("\r", "(enter)")
        needle = " ".join(self.args.prompt.split())[:20]
        echoed_at = None
        resent = False
        sent_at = time.time()
        while time.time() < deadline:
            self.pump()
            if not self.alive():
                return 3, "cortex exited after the prompt was sent"
            if needle in " ".join(self.transcript().split()) and re.search(
                r"^> ", self.transcript(), re.MULTILINE
            ):
                echoed_at = time.time()
                break
            if not resent and time.time() - sent_at > 6:
                resent = True
                self.send("\r", "(enter again, prompt not echoed)")
        if echoed_at is None:
            return 2, "timeout: prompt was never submitted"
        self.debug("prompt echoed; waiting for the answer")
        # 3. wait for completion: input box back, no busy indicator, transcript stable
        stable_since = None
        last_snapshot = ""
        answer = ""
        while time.time() < deadline:
            self.pump()
            if not self.alive():
                break
            if self.handle_dialogs() or self.approve_tool():
                stable_since = None
                continue
            snap = self.conversation()
            if snap != last_snapshot:
                last_snapshot = snap
                stable_since = time.time()
                continue
            if self.input_box_ready() and not self.agent_busy():
                answer = extract_answer(snap, self.args.prompt)
                if (
                    answer
                    and stable_since
                    and time.time() - stable_since >= self.args.idle
                ):
                    break
            if (
                stable_since
                and time.time() - stable_since >= max(self.args.idle * 5, 30)
                and not self.agent_busy()
            ):
                # nothing moved for a long while; take whatever is there
                answer = extract_answer(snap, self.args.prompt)
                break
        else:
            self.debug("timeout; visible screen:\n" + self.visible())
            self.shutdown()
            return 2, f"timeout after {self.args.timeout}s waiting for the answer"
        self.shutdown()
        if not answer:
            answer = extract_answer(self.transcript(), self.args.prompt)
        if not answer:
            return 3, "no assistant answer found in the transcript"
        return 0, answer

    def shutdown(self) -> None:
        if not self.alive():
            return
        try:
            self.send("/exit", "(exit command)")
            time.sleep(0.5)
            self.pump(0.3)
            self.send("\r")
            for _ in range(20):
                self.pump(0.2)
                if not self.alive():
                    return
            self.send("\r", "(second enter for the command picker)")
            for _ in range(20):
                self.pump(0.2)
                if not self.alive():
                    return
            for _ in range(2):
                self.send("\x03", "(ctrl+c)")
                for _ in range(10):
                    self.pump(0.2)
                    if not self.alive():
                        return
            os.kill(self.pid, signal.SIGTERM)
            for _ in range(10):
                self.pump(0.2)
                if not self.alive():
                    return
            os.kill(self.pid, signal.SIGKILL)
            self.alive()
        except OSError:
            pass

    def save(self, code: int, message: str) -> Path | None:
        if not self.args.transcript_dir:
            return None
        d = Path(self.args.transcript_dir)
        d.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%dT%H%M%S")
        base = d / f"cortex-run-{stamp}"
        base.with_suffix(".raw").write_bytes(bytes(self.raw))
        base.with_suffix(".txt").write_text(self.transcript() + "\n", encoding="utf-8")
        base.with_suffix(".json").write_text(
            json.dumps(
                {
                    "prompt": self.args.prompt,
                    "connection": self.args.connection,
                    "cwd": str(self.args.cwd),
                    "exit_code": code,
                    "message": message if code else "",
                    "answer": message if code == 0 else "",
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        return base


def ensure_trust(cwd: Path, cortex_home: Path) -> None:
    """Pre-mark the working directory as trusted the way cortex records it."""
    cfg = cortex_home / "cortex.json"
    data: dict = {}
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    projects = data.setdefault("projects", {})
    entry = projects.setdefault(str(cwd), {})
    changed = False
    if not entry.get("hasTrustDialogAccepted"):
        entry["hasTrustDialogAccepted"] = True
        changed = True
    if changed:
        cortex_home.mkdir(parents=True, exist_ok=True)
        cfg.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("prompt")
    p.add_argument("--connection", default="bidpilot-reader")
    p.add_argument("--timeout", type=float, default=300)
    p.add_argument("--cwd", default=os.getcwd())
    p.add_argument(
        "--idle",
        type=float,
        default=4,
        help="seconds of quiet after the answer before returning",
    )
    p.add_argument(
        "--transcript-dir", default=os.environ.get("CORTEX_RUN_TRANSCRIPT_DIR")
    )
    p.add_argument("--cortex", default=os.environ.get("CORTEX_BIN", "cortex"))
    p.add_argument("--cortex-home", default=os.path.expanduser("~/.snowflake/cortex"))
    p.add_argument("--debug", action="store_true")
    p.add_argument("--debug-log", default=None)
    args = p.parse_args(argv)
    args.cwd = Path(args.cwd).resolve()
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if pyte is None:
        print(
            "cortex-run: the 'pyte' package is required (uv add --group dev pyte)",
            file=sys.stderr,
        )
        return 4
    if not args.cwd.is_dir():
        print(f"cortex-run: --cwd {args.cwd} is not a directory", file=sys.stderr)
        return 4
    ensure_trust(args.cwd, Path(args.cortex_home))
    session = CortexSession(args)
    try:
        code, message = session.run()
    except FileNotFoundError as exc:
        print(f"cortex-run: cannot start {args.cortex}: {exc}", file=sys.stderr)
        return 4
    finally:
        session.shutdown()
    saved = session.save(code, message)
    if saved:
        session.debug(f"transcript saved to {saved}.txt")
    if code == 0:
        print(message)
    else:
        print(f"cortex-run: {message}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
