#!/usr/bin/env python3
"""Extract audio + structure analysis: loudness envelope, silence map,
voice/music heuristic, beat-sync score against the cut list.

Usage: extract_audio.py <video> <outdir> [--shots shots.json] [--max-seconds N]
Outputs: <outdir>/voice.wav (16k mono, for transcription), <outdir>/audio.json
"""
import argparse
import json
import os
import re
import subprocess
import sys


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("outdir")
    p.add_argument("--shots", default=None)
    p.add_argument("--max-seconds", type=float, default=None)
    args = p.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    tlim = ["-t", str(args.max_seconds)] if args.max_seconds else []

    # 16kHz mono wav for whisper-style transcription
    wav = os.path.join(args.outdir, "voice.wav")
    r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", *tlim, "-i", args.video,
             "-vn", "-ac", "1", "-ar", "16000", "-y", wav])
    has_audio = r.returncode == 0 and os.path.exists(wav) and os.path.getsize(wav) > 1000
    if not has_audio:
        with open(os.path.join(args.outdir, "audio.json"), "w") as f:
            json.dump({"has_audio": False}, f, indent=2)
        print(json.dumps({"has_audio": False}))
        return 0

    # Loudness envelope: RMS per ~1s window via astats metadata
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", wav, "-af",
             "astats=metadata=1:reset=16000,"
             "ametadata=print:key=lavfi.astats.Overall.RMS_level",
             "-f", "null", "-"])
    times, levels = [], []
    t = None
    for line in r.stderr.splitlines():
        m = re.search(r"pts_time:([0-9.]+)", line)
        if m:
            t = float(m.group(1))
        m = re.search(r"RMS_level=(-?[0-9.]+|inf|-inf)", line)
        if m and t is not None:
            lv = m.group(1)
            levels.append(-90.0 if "inf" in lv else float(lv))
            times.append(round(t, 2))
            t = None
    envelope = [{"t": tt, "rms_db": round(lv, 1)} for tt, lv in zip(times, levels)]

    # Silence map
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", wav, "-af",
             "silencedetect=noise=-35dB:d=0.4", "-f", "null", "-"])
    silences = []
    start = None
    for line in r.stderr.splitlines():
        m = re.search(r"silence_start:\s*([0-9.]+)", line)
        if m:
            start = float(m.group(1))
        m = re.search(r"silence_end:\s*([0-9.]+)", line)
        if m and start is not None:
            silences.append({"start": round(start, 2), "end": round(float(m.group(1)), 2)})
            start = None

    total = times[-1] if times else 0
    silent = sum(s["end"] - s["start"] for s in silences)
    speech_ratio = round(1 - silent / total, 3) if total else 0

    # Beat-sync score: fraction of cuts within 150ms of a local loudness peak
    beat_sync = None
    if args.shots and envelope:
        with open(args.shots) as f:
            cuts = json.load(f).get("cuts", [])
        peaks = []
        for i in range(1, len(levels) - 1):
            if levels[i] > levels[i - 1] and levels[i] >= levels[i + 1] and levels[i] > -40:
                peaks.append(times[i])
        if cuts and peaks:
            hits = sum(1 for c in cuts if min(abs(c - pk) for pk in peaks) <= 0.6)
            beat_sync = round(hits / len(cuts), 3)

    result = {
        "has_audio": True,
        "duration_s": round(total, 2),
        "speech_or_sound_ratio": speech_ratio,
        "silences": silences,
        "beat_sync_score": beat_sync,
        "envelope_1s": envelope,
        "notes": "beat_sync_score >= 0.5 suggests cuts follow audio peaks; "
                 "speech_or_sound_ratio near 1.0 means continuous VO/music.",
    }
    with open(os.path.join(args.outdir, "audio.json"), "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != "envelope_1s"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
