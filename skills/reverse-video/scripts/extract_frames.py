#!/usr/bin/env python3
"""Extract per-shot + uniform-grid frames and build contact sheets for Claude's vision.

Usage: extract_frames.py <video> <outdir> [--shots shots.json] [--grid 12]
                         [--max-shots 40] [--tile 3x4] [--width 480]
"""
import argparse
import json
import math
import os
import subprocess
import sys


def grab(video: str, t: float, path: str, width: int) -> bool:
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}",
         "-i", video, "-frames:v", "1", "-vf", f"scale={width}:-2", "-y", path],
        capture_output=True, text=True)
    return r.returncode == 0 and os.path.exists(path)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("outdir")
    p.add_argument("--shots", default=None)
    p.add_argument("--grid", type=int, default=12)
    p.add_argument("--max-shots", type=int, default=40)
    p.add_argument("--tile", default="3x4")
    p.add_argument("--width", type=int, default=480)
    args = p.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    times: list[tuple[str, float]] = []
    duration = None
    if args.shots:
        with open(args.shots) as f:
            sj = json.load(f)
        duration = sj.get("analyzed_seconds")
        shots = sj.get("shots", [])
        if len(shots) > args.max_shots:  # evenly subsample long shot lists
            step = len(shots) / args.max_shots
            shots = [shots[int(i * step)] for i in range(args.max_shots)]
        for s in shots:
            mid = s["start"] + (s["end"] - s["start"]) / 2
            times.append((f"shot{s['index']:03d}", mid))
    if duration is None:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", args.video],
            capture_output=True, text=True).stdout.strip()
        duration = float(out or 0)
    for i in range(args.grid):
        t = duration * (i + 0.5) / args.grid
        times.append((f"grid{i:02d}", t))

    frames = []
    manifest = []
    for name, t in times:
        path = os.path.join(args.outdir, f"{name}_t{t:.2f}.png")
        if grab(args.video, t, path, args.width):
            frames.append(path)
            manifest.append({"name": name, "time_s": round(t, 2), "file": os.path.basename(path)})

    # Contact sheets: tile frames so one Read shows many frames.
    cols, rows = (int(x) for x in args.tile.split("x"))
    per = cols * rows
    sheets = []
    for i in range(math.ceil(len(frames) / per)):
        batch = frames[i * per:(i + 1) * per]
        sheet = os.path.join(args.outdir, f"sheet_{i:02d}.png")
        n = len(batch)
        c = min(cols, n)
        r = math.ceil(n / c)
        inputs = []
        for fpath in batch:
            inputs += ["-i", fpath]
        if n == 1:
            subprocess.run(["cp", batch[0], sheet], check=False)
        else:
            r2 = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", *inputs,
                 "-filter_complex",
                 "".join(f"[{j}:v]" for j in range(n)) +
                 f"concat=n={n}:v=1:a=0,tile={c}x{r}", "-y", sheet],
                capture_output=True, text=True)
            if r2.returncode != 0:
                print(f"sheet {i} failed: {r2.stderr[-300:]}", file=sys.stderr)
                continue
        sheets.append(sheet)

    with open(os.path.join(args.outdir, "frames.json"), "w") as f:
        json.dump({"frames": manifest, "sheets": [os.path.basename(s) for s in sheets]},
                  f, indent=2)
    print(json.dumps({"frames": len(frames), "sheets": sheets}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
