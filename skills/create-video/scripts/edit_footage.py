#!/usr/bin/env python3
"""Edit real footage: scan it into clips, extract clips, or auto-cut a beat-synced edit.

Zero-dependency (stdlib + ffmpeg/ffprobe). Three subcommands:

  scan     Detect scene cuts in raw footage and write a clips.json inventory
           (one entry per continuous take: start, end, duration, cut score).

             edit_footage.py scan raw.mp4 clips.json [--threshold 0.3] [--min-dur 0.6]

  cut      Extract clips (all, or --ids 0,3,5) to numbered MP4s for the timeline.
           Frame-accurate (re-encodes).

             edit_footage.py cut raw.mp4 clips.json outdir/ [--ids 0,3,5]

  beatcut  Auto-edit: slice the best material onto a beat grid and concat into a
           finished cut (music-video / montage / highlight-reel mode).

             edit_footage.py beatcut raw.mp4 clips.json out.mp4 \
                 --bpm 110 [--beat-every 2] [--target 30] [--order chrono|long|random]

Typical flow: scan -> Claude reads clips.json (and looks at a contact sheet of the
clips) -> either `cut` the chosen takes into timeline.json video shots, or `beatcut`
for a fully automatic rhythm edit.
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys


def run(cmd, label, capture=True):
    r = subprocess.run(cmd, capture_output=capture, text=True)
    if r.returncode != 0:
        err = (r.stderr or "")[-800:] if capture else ""
        print(f"ERROR {label}: {err}", file=sys.stderr)
        sys.exit(1)
    return r


def probe_duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path], "ffprobe")
    return float(r.stdout.strip())


def cmd_scan(args):
    dur = probe_duration(args.input)
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", args.input,
         "-vf", f"select='gt(scene,{args.threshold})',metadata=print",
         "-an", "-f", "null", "-"],
        capture_output=True, text=True)
    # scene cuts appear in stderr/stdout as: pts_time:12.345 ... scene_score=0.42
    text = (r.stderr or "") + (r.stdout or "")
    cuts = []
    pts = None
    for line in text.splitlines():
        m = re.search(r"pts_time:([\d.]+)", line)
        if m:
            pts = float(m.group(1))
        m = re.search(r"scene_score=([\d.]+)", line)
        if m and pts is not None:
            cuts.append((pts, float(m.group(1))))
            pts = None

    bounds = [0.0] + [t for t, _ in cuts] + [dur]
    scores = [s for _, s in cuts] + [0.0]
    clips = []
    for i in range(len(bounds) - 1):
        start, end = bounds[i], bounds[i + 1]
        if end - start < args.min_dur:
            continue
        clips.append({
            "id": len(clips),
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(end - start, 3),
            "cut_score": round(scores[i], 3),
        })
    out = {"source": os.path.abspath(args.input), "source_duration": round(dur, 3),
           "threshold": args.threshold, "clips": clips}
    with open(args.clips, "w") as f:
        json.dump(out, f, indent=2)
    print(f"OK: {len(clips)} clips ({dur:.1f}s of footage) -> {args.clips}")
    return 0


def load_clips(path):
    with open(path) as f:
        data = json.load(f)
    return data["source"], data["clips"]


def extract(src, start, length, outpath, scale=None):
    vf = ["-vf", f"scale={scale}:-2"] if scale else []
    run(["ffmpeg", "-hide_banner", "-loglevel", "error",
         "-ss", f"{start}", "-t", f"{length}", "-i", src,
         *vf, "-c:v", "libx264", "-preset", "medium", "-crf", "19",
         "-c:a", "aac", "-b:a", "160k", "-y", outpath],
        f"extract {outpath}")


def cmd_cut(args):
    src, clips = load_clips(args.clips)
    if not os.path.exists(src):
        src = args.input
    wanted = ({int(x) for x in args.ids.split(",")} if args.ids
              else {c["id"] for c in clips})
    os.makedirs(args.outdir, exist_ok=True)
    n = 0
    for c in clips:
        if c["id"] not in wanted:
            continue
        out = os.path.join(args.outdir, f"clip{c['id']:03d}.mp4")
        extract(src, c["start"], c["duration"], out)
        print(f"clip {c['id']}: {c['start']:.2f}s +{c['duration']:.2f}s -> {out}")
        n += 1
    print(f"OK: {n} clips -> {args.outdir}")
    return 0


def cmd_beatcut(args):
    src, clips = load_clips(args.clips)
    if not os.path.exists(src):
        src = args.input
    beat = 60.0 / args.bpm * args.beat_every
    n_seg = max(1, round(args.target / beat))

    usable = [c for c in clips if c["duration"] >= beat * 1.1]
    if not usable:
        print(f"ERROR: no clip is >= {beat * 1.1:.2f}s; lower --bpm, "
              f"--beat-every, or re-scan with a lower --min-dur", file=sys.stderr)
        return 1
    if args.order == "long":
        usable.sort(key=lambda c: -c["duration"])
    elif args.order == "random":
        random.seed(args.seed)
        random.shuffle(usable)
    # else chrono: keep source order

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        parts = []
        for k in range(n_seg):
            c = usable[k % len(usable)]
            # k-th pass through a clip takes a different slice of its middle
            pass_no = k // len(usable)
            room = c["duration"] - beat
            off = min(room, (pass_no + 0.5) * beat) if room > 0 else 0
            start = c["start"] + off
            part = os.path.join(tmp, f"seg{k:03d}.mp4")
            extract(src, start, beat, part)
            parts.append(part)
        concat = os.path.join(tmp, "concat.txt")
        with open(concat, "w") as f:
            for part in parts:
                f.write(f"file '{part}'\n")
        acmd = []
        if args.music:
            total = n_seg * beat
            acmd = ["-stream_loop", "-1", "-i", args.music]
            run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                 "-f", "concat", "-safe", "0", "-i", concat, *acmd,
                 "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                 "-c:a", "aac", "-b:a", "192k",
                 "-t", f"{total:.3f}", "-y", args.out], "beatcut mux")
        else:
            run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                 "-f", "concat", "-safe", "0", "-i", concat,
                 "-c", "copy", "-y", args.out], "beatcut concat")
    print(f"OK: {n_seg} x {beat:.2f}s beats ({n_seg * beat:.1f}s) -> {args.out}")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="detect scene cuts -> clips.json")
    s.add_argument("input")
    s.add_argument("clips")
    s.add_argument("--threshold", type=float, default=0.3,
                   help="scene-change score 0-1 (lower = more cuts)")
    s.add_argument("--min-dur", type=float, default=0.6,
                   help="drop clips shorter than this (s)")
    s.set_defaults(fn=cmd_scan)

    s = sub.add_parser("cut", help="extract clips to numbered MP4s")
    s.add_argument("input")
    s.add_argument("clips")
    s.add_argument("outdir")
    s.add_argument("--ids", default=None, help="comma-separated clip ids (default all)")
    s.set_defaults(fn=cmd_cut)

    s = sub.add_parser("beatcut", help="auto-edit onto a beat grid")
    s.add_argument("input")
    s.add_argument("clips")
    s.add_argument("out")
    s.add_argument("--bpm", type=float, default=100.0)
    s.add_argument("--beat-every", type=int, default=2,
                   help="cut every N beats (2 = half-bar cuts at 4/4)")
    s.add_argument("--target", type=float, default=30.0, help="target duration (s)")
    s.add_argument("--order", choices=["chrono", "long", "random"], default="chrono")
    s.add_argument("--music", default=None, help="music track to lay under the cut")
    s.add_argument("--seed", type=int, default=7)
    s.set_defaults(fn=cmd_beatcut)

    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
