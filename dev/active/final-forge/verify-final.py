#!/usr/bin/env python3
"""Reproduce the final BidPilot submission evidence in one bounded audit."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from bidpilot.snowflake_store import SnowflakeBidRoomStore

ROOT = Path(__file__).resolve().parents[3]
FORGE = ROOT / "dev" / "active" / "final-forge"
LEAGUE = FORGE / "artifact-league-20260802"
RUN = LEAGUE / "run-v2"
PRODUCT_REVISION = "84dc9c38f2311c78c8cf25032df215b23fa00ed2"
APP_URL = "https://bidpilot-demo-tbauoylpra-uc.a.run.app"
VIDEO_URL = "https://storage.googleapis.com/bidpilot-demo-164282963747/BidPilot-Final-Demo.mp4"


def command(args: list[str], env: dict[str, str] | None = None) -> str:
    return subprocess.run(args, cwd=ROOT, env=env, check=True, text=True, capture_output=True).stdout.strip()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    checks: dict[str, object] = {}

    head = command(["git", "rev-parse", "HEAD"])
    origin = command(["git", "rev-parse", "origin/main"])
    checks["git"] = {"head": head, "origin_main": origin, "match": head == origin}

    tests = command(["uv", "run", "pytest", "-q"])
    checks["tests"] = {"passed_48": "48 passed" in tests, "tail": tests.splitlines()[-1]}

    node_env = dict(os.environ)
    node_env["NODE_PATH"] = "~/projects/personal/products/youtube-digest/lilys-clone/node_modules"
    live = json.loads(command(["node", str(FORGE / "verify-live.cjs"), APP_URL], env=node_env))
    checks["public_app"] = live

    pdf = FORGE / "submission-deck" / "BidPilot-Submission-Deck.pdf"
    pdf_info = command(["pdfinfo", str(pdf)])
    pdf_page = command(["pdftotext", "-f", "5", "-l", "5", str(pdf), "-"])
    checks["pdf"] = {
        "pages_8": "Pages:           8" in pdf_info,
        "under_5mb": pdf.stat().st_size <= 5_000_000,
        "task_total_12": "12" in pdf_page,
        "task_split_5_4_3": all(value in pdf_page for value in ("5 owned", "4 red-team", "3 provenance")),
        "bytes": pdf.stat().st_size,
    }

    video = FORGE / "BidPilot-Final-Demo.mp4"
    probe = load_json_command([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-show_entries", "stream=codec_name,width,height,sample_rate,channels", "-of", "json", str(video),
    ])
    headers = command(["curl", "-sSIL", "--range", "0-0", VIDEO_URL])
    volume = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(video), "-af", "volumedetect", "-f", "null", "-"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    ).stderr
    duration = float(probe["format"]["duration"])
    streams = {item["codec_name"]: item for item in probe["streams"]}
    checks["video"] = {
        "duration_3_to_5_minutes": 180 <= duration <= 300,
        "h264_1440x900": streams.get("h264", {}).get("width") == 1440 and streams.get("h264", {}).get("height") == 900,
        "aac_audio": "aac" in streams,
        "audible": "mean_volume:" in volume and "max_volume:" in volume,
        "public_range_206": "206" in headers.splitlines()[0],
        "local_bytes": video.stat().st_size,
    }

    pitch = FORGE / "BidPilot-90s-Pitch.mp4"
    pitch_probe = load_json_command([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-show_entries", "stream=codec_name,width,height,sample_rate,channels", "-of", "json", str(pitch),
    ])
    pitch_streams = {item["codec_name"]: item for item in pitch_probe["streams"]}
    pitch_duration = float(pitch_probe["format"]["duration"])
    checks["pitch_90s"] = {
        "duration_exact_90": pitch_duration == 90.0,
        "h264_1440x900": pitch_streams.get("h264", {}).get("width") == 1440 and pitch_streams.get("h264", {}).get("height") == 900,
        "aac_audio": "aac" in pitch_streams,
        "english_narration_source": (FORGE / "demo-90s-narration.txt").is_file(),
        "burned_subtitle_source": (FORGE / "demo-90s-subtitles.srt").is_file(),
        "qa_frames": len(list((FORGE / "demo-90s-qa").glob("*.png"))),
    }

    run = SnowflakeBidRoomStore("bidpilot-reader").load_run("cortex-final-20260802-a")
    trace = run["run"]["trace"]
    checks["snowflake"] = {
        "state_completed": run["run"]["state"] == "COMPLETED",
        "cli_version": trace["execution_provenance"]["cortex_cli_version"],
        "cli_version_matches": trace["execution_provenance"]["cortex_cli_version"] == "snow-v3.23.0",
        "counts": {
            "decisions": 1 if run["decision"] else 0,
            **{key: len(run[key]) for key in ("strategies", "blueprint", "sections", "tasks")},
        },
        "query_ids": len(trace["execution_provenance"]["cortex_write_query_ids"]),
    }

    candidates = load(LEAGUE / "candidates.json")
    mapping = load(RUN / "private" / "identity-mapping.json")
    bidpilot_candidate = next(item for item in candidates if item["identity"]["name"] == "BidPilot")
    bidpilot_mapping = next(item for item in mapping.values() if item["name"] == "BidPilot")
    lanes = load(RUN / "judge" / "lane-packets.json")
    lane_ids = [[item["blind_id"] for item in lane["candidates"]] for lane in lanes]
    sealed_path = RUN / "sealed-aggregate.json"
    revealed = load(RUN / "revealed-ranking.json")
    sealed_hash = hashlib.sha256(sealed_path.read_bytes()).hexdigest()
    pair_files = sorted((RUN / "judge").glob("pair-*.json"))
    orientations = []
    bidpilot_wins = 0
    for path in pair_files:
        item = load(path)
        orientation = item["orientation"]
        left = orientation.get("LEFT") or orientation.get("left")
        right = orientation.get("RIGHT") or orientation.get("right")
        verdict = item.get("choice") or item.get("verdict")
        winner = left if verdict == "LEFT" else right if verdict == "RIGHT" else None
        orientations.append("AB" if left == "BLIND-4D4B3DACD573" else "BA")
        bidpilot_wins += winner == "BLIND-4D4B3DACD573"
    checks["blind_league"] = {
        "candidate_revision_matches": bidpilot_candidate["identity"]["revision"] == PRODUCT_REVISION,
        "mapping_revision_matches": bidpilot_mapping["revision"] == PRODUCT_REVISION,
        "each_lane_has_six_unique": all(len(ids) == 6 and len(set(ids)) == 6 for ids in lane_ids),
        "every_candidate_three_judges": all(sum(blind_id in ids for ids in lane_ids) == 3 for blind_id in lane_ids[0]),
        "seal_hash_matches_reveal": revealed["sealed_aggregate_sha256"] == sealed_hash,
        "pairwise_orientations": {value: orientations.count(value) for value in ("AB", "BA")},
        "bidpilot_pairwise_wins": bidpilot_wins,
    }

    checks["committed_visual_evidence"] = {
        "public_proposal_capture": (FORGE / "public-app-verified" / "04-proposal.png").is_file(),
        "video_sample_frames": len(list((FORGE / "demo-video-qa").glob("*.png"))),
    }

    failures = flatten_failures(checks)
    report = {"status": "PASS" if not failures else "FAIL", "failures": failures, "checks": checks}
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    raise SystemExit(1 if failures else 0)


def load_json_command(args: list[str]):
    return json.loads(command(args))


def flatten_failures(checks: dict[str, object]) -> list[str]:
    required = {
        "git.match": checks["git"]["match"],
        "tests.passed_48": checks["tests"]["passed_48"],
        "public_app.run_loaded": checks["public_app"]["run_loaded"],
        "public_app.completed": checks["public_app"]["completed"],
        "public_app.review_ready": checks["public_app"]["review_ready"],
        "public_app.no_not_ready_warning": not checks["public_app"]["not_ready_warning"],
        "public_app.four_criteria": len(checks["public_app"]["criterion_headings"]) == 4,
        "public_app.download_enabled": checks["public_app"]["download_enabled"],
        "pdf.pages_8": checks["pdf"]["pages_8"],
        "pdf.under_5mb": checks["pdf"]["under_5mb"],
        "pdf.task_total_12": checks["pdf"]["task_total_12"],
        "pdf.task_split_5_4_3": checks["pdf"]["task_split_5_4_3"],
        "video.duration": checks["video"]["duration_3_to_5_minutes"],
        "video.h264": checks["video"]["h264_1440x900"],
        "video.aac": checks["video"]["aac_audio"],
        "video.audible": checks["video"]["audible"],
        "video.public": checks["video"]["public_range_206"],
        "pitch.duration_exact_90": checks["pitch_90s"]["duration_exact_90"],
        "pitch.h264": checks["pitch_90s"]["h264_1440x900"],
        "pitch.aac": checks["pitch_90s"]["aac_audio"],
        "pitch.narration": checks["pitch_90s"]["english_narration_source"],
        "pitch.subtitles": checks["pitch_90s"]["burned_subtitle_source"],
        "pitch.qa_frames": checks["pitch_90s"]["qa_frames"] == 6,
        "snowflake.completed": checks["snowflake"]["state_completed"],
        "snowflake.cli_version": checks["snowflake"]["cli_version_matches"],
        "snowflake.counts": checks["snowflake"]["counts"] == {"decisions": 1, "strategies": 3, "blueprint": 4, "sections": 8, "tasks": 12},
        "snowflake.query_ids": checks["snowflake"]["query_ids"] == 6,
        "league.candidate_revision": checks["blind_league"]["candidate_revision_matches"],
        "league.mapping_revision": checks["blind_league"]["mapping_revision_matches"],
        "league.balanced_lanes": checks["blind_league"]["each_lane_has_six_unique"],
        "league.three_judges": checks["blind_league"]["every_candidate_three_judges"],
        "league.seal_chain": checks["blind_league"]["seal_hash_matches_reveal"],
        "league.orientation": checks["blind_league"]["pairwise_orientations"] == {"AB": 2, "BA": 2},
        "league.pairwise_wins": checks["blind_league"]["bidpilot_pairwise_wins"] == 4,
        "visual.public_capture": checks["committed_visual_evidence"]["public_proposal_capture"],
    }
    return [name for name, passed in required.items() if not passed]


if __name__ == "__main__":
    main()
