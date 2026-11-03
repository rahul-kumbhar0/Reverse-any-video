#!/usr/bin/env python3
"""Detect cuts with ffmpeg scene detection -> shot list + pacing stats.

Usage: detect_scenes.py <video> <out.json> [--threshold 0.27] [--max-seconds N]
"""
import argparse
import json
import re
import statistics
import subprocess
import sys


def ffprobe_duration(video: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", video],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out or 0)


def detect_cuts(video: str, threshold: float, max_seconds: float | None) -> list[float]:
    cmd = ["ffmpeg", "-hide_banner", "-nostats"]
    if max_seconds:
        cmd += ["-t", str(max_seconds)]
    cmd += ["-i", video, "-vf",
            f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    cuts = []
    for m in re.finditer(r"pts_time:\s*([0-9.]+)", proc.stderr):
        cuts.append(round(float(m.group(1)), 3))
    return sorted(set(cuts))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("out")
    p.add_argument("--threshold", type=float, default=0.27)
    p.add_argument("--max-seconds", type=float, default=None)
    args = p.parse_args()

    duration = ffprobe_duration(args.video)
    analyzed = min(duration, args.max_seconds) if args.max_seconds else duration
    cuts = detect_cuts(args.video, args.threshold, args.max_seconds)

    bounds = [0.0] + cuts + [round(analyzed, 3)]
    shots = []
    for i in range(len(bounds) - 1):
        start, end = bounds[i], bounds[i + 1]
        if end - start < 0.05:
            continue
        shots.append({"index": len(shots), "start": start, "end": end,
                      "duration": round(end - start, 3)})

    durs = [s["duration"] for s in shots]
    thirds = max(1, len(durs) // 3)
    pacing = {
        "shot_count": len(shots),
        "cuts_per_minute": round(len(cuts) / (analyzed / 60), 2) if analyzed else 0,
        "median_shot_s": round(statistics.median(durs), 3) if durs else None,
        "mean_shot_s": round(statistics.mean(durs), 3) if durs else None,
        "min_shot_s": min(durs) if durs else None,
        "max_shot_s": max(durs) if durs else None,
        "stdev_shot_s": round(statistics.stdev(durs), 3) if len(durs) > 1 else 0,
        "opening_third_median_s": round(statistics.median(durs[:thirds]), 3) if durs else None,
        "closing_third_median_s": round(statistics.median(durs[-thirds:]), 3) if durs else None,
    }

    result = {"threshold": args.threshold, "analyzed_seconds": round(analyzed, 3),
              "full_duration_seconds": round(duration, 3), "cuts": cuts,
              "shots": shots, "pacing": pacing}
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps({"shot_count": len(shots), "pacing": pacing}, indent=2))
    if len(cuts) < 2:
        print("NOTE: <2 cuts detected. If the video is clearly edited, "
              "retry with --threshold 0.18", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
