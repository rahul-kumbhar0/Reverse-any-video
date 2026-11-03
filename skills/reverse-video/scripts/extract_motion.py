#!/usr/bin/env python3
"""Extract MOTION STRIPS: bursts of consecutive frames tiled side by side,
so Claude can see how things move — camera direction, easing (spacing between
positions), particle behavior, morphs. A strip = 8 frames span`window` seconds.

Usage: extract_motion.py <video> <outdir> [--times 2,10,25]  (default: 6 evenly spread)
                         [--window 0.8] [--width 240]
"""
import argparse
import json
import os
import subprocess
import sys


def duration_of(video: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", video], capture_output=True, text=True).stdout
    return float(out.strip() or 0)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("outdir")
    p.add_argument("--times", default=None, help="comma-separated start seconds")
    p.add_argument("--window", type=float, default=0.8)
    p.add_argument("--frames", type=int, default=8)
    p.add_argument("--width", type=int, default=240)
    args = p.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    dur = duration_of(args.video)
    if args.times:
        starts = [float(t) for t in args.times.split(",")]
    else:
        starts = [dur * (i + 0.5) / 6 for i in range(6)]

    made = []
    for s in starts:
        s = max(0, min(s, dur - args.window - 0.05))
        fps = args.frames / args.window
        out = os.path.join(args.outdir, f"strip_t{s:.1f}.png")
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error",
             "-ss", f"{s:.3f}", "-t", f"{args.window:.3f}", "-i", args.video,
             "-vf", f"fps={fps:.4f},scale={args.width}:-2,tile={args.frames}x1",
             "-frames:v", "1", "-y", out],
            capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(out):
            made.append({"start_s": round(s, 2), "window_s": args.window,
                         "file": os.path.basename(out)})
        else:
            print(f"strip at {s:.1f}s failed: {r.stderr[-200:]}", file=sys.stderr)

    with open(os.path.join(args.outdir, "motion.json"), "w") as f:
        json.dump({"strips": made,
                   "how_to_read": "8 frames left-to-right over the window. "
                   "Equal spacing between element positions = linear motion; "
                   "spacing that shrinks = ease-out; grows = ease-in; "
                   "grows then shrinks = ease-in-out. Blur direction = motion blur axis."},
                  f, indent=2)
    print(json.dumps({"strips": len(made), "dir": args.outdir}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
