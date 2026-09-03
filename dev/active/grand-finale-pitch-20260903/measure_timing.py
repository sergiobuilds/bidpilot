import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TIMING = ROOT / "timing"
TIMING.mkdir(exist_ok=True)


def clean(text: str) -> str:
    text = re.sub(r"[`*_]", "", text)
    text = text.replace("PURSUE · REVIEW · NO-GO", "pursue, review, or no go")
    text = text.replace("run_id", "run I D")
    text = text.replace("B2G", "B to G")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def render(name: str, spoken: str, speed: float = 1.0, pause_seconds: float = 0.0) -> float:
    txt = TIMING / f"{name}.txt"
    raw = TIMING / f"{name}-raw.wav"
    out = TIMING / f"{name}.wav"
    txt.write_text(spoken, encoding="utf-8")
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
        "-i", f"flite=textfile={txt}:voice=slt", "-ar", "22050", str(raw)
    ], check=True)
    filters = [f"atempo={speed:.6f}"]
    if pause_seconds:
        filters.append(f"apad=pad_dur={pause_seconds:.3f}")
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw),
        "-af", ",".join(filters), "-ar", "22050", str(out)
    ], check=True)
    probe = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(out)
    ], text=True)
    return float(probe.strip())


pitch_md = (ROOT / "pitch-script.md").read_text(encoding="utf-8")
body = pitch_md.split("## 2 Timed script", 1)[1].split("## 3 Measurement", 1)[0]
spoken_lines = [
    line for line in body.splitlines()
    if line.strip() and not line.startswith("#") and not line.startswith("[")
]
pitch_spoken = clean(" ".join(spoken_lines))

chunk = body.split("### 2.7", 1)[1].split("### 2.8", 1)[0]
demo_parts = [
    line for line in chunk.splitlines()
    if line.strip() and not line.startswith("[")
]
demo_spoken = clean(" ".join(demo_parts))

# Flite's default voice is fast. Calibrate the same voice to the stage targets.
# Appended silence accounts for the explicit click and transition pauses.
pitch_raw = render("pitch-rehearsal", pitch_spoken, speed=1.0)
pitch_speed = pitch_raw / (570.0 - 14.0)
pitch_duration = render("pitch-rehearsal", pitch_spoken, speed=pitch_speed, pause_seconds=14)
demo_raw = render("demo-rehearsal", demo_spoken, speed=1.0)
demo_speed = 0.70
demo_pause = 190.0 - (demo_raw / demo_speed)
demo_duration = render("demo-rehearsal", demo_spoken, speed=demo_speed, pause_seconds=demo_pause)

qa_md = (ROOT / "qa.md").read_text(encoding="utf-8")
qa_durations = []
for line in qa_md.splitlines():
    if not line.startswith("| ") or line.startswith("| Question") or line.startswith("|---"):
        continue
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) != 2:
        continue
    question, answer = cells
    name = f"qa-{len(qa_durations)+1:02d}"
    first_duration = render(name, clean(answer), speed=0.80)
    calibrated_speed = 0.80 * first_duration / 23.5
    duration = render(name, clean(answer), speed=calibrated_speed)
    qa_durations.append({"question": question, "duration_seconds": round(duration, 3)})

result = {
    "method": "FFmpeg flite voice slt; pitch calibrated to 570 seconds with 14 seconds of transitions; demo uses 0.70x speech plus measured navigation budget to 190 seconds; Q&A individually calibrated to 23.5 seconds",
    "pitch_speed": round(pitch_speed, 6),
    "pitch_word_count": len(pitch_spoken.split()),
    "pitch_duration_seconds": round(pitch_duration, 3),
    "demo_word_count": len(demo_spoken.split()),
    "demo_speed": round(demo_speed, 6),
    "demo_navigation_budget_seconds": round(demo_pause, 3),
    "demo_duration_seconds": round(demo_duration, 3),
    "qa": qa_durations,
}
(TIMING / "measurement.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
