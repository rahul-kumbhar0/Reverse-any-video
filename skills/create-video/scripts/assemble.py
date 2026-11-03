#!/usr/bin/env python3
"""FFmpeg timeline assembler — zero-dependency fallback renderer.

Renders a timeline.json (see create-video SKILL.md) in a given style-spec.json.
Supports: solid/card shots, image shots (with Ken Burns zoom), headline + caption
drawtext with safe margins, optional voiceover + music with ducking.

Usage: assemble.py <timeline.json> <style-spec.json> <out.mp4>
                   [--assets DIR] [--font /path/to/font.ttf]
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


def find_font(explicit: str | None) -> str | None:
    if explicit and os.path.exists(explicit):
        return explicit
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            return f
    return None


def esc(text: str) -> str:
    """Escape text for drawtext."""
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\\\\\'").replace("%", "\\%")


def shot_cmd(shot, spec, w, h, fps, font, assets, outpath):
    dur = shot["duration"]
    vis = shot.get("visual", {})
    vtype = vis.get("type", "card")
    bg = vis.get("bg") or spec.get("palette", {}).get("background", "#101014")
    filters = []

    if vtype in ("image", "video") and vis.get("src"):
        src = vis["src"]
        if assets and not os.path.isabs(src) and not os.path.exists(src):
            src = os.path.join(assets, src)
        if vtype == "image":
            inp = ["-loop", "1", "-t", f"{dur}", "-i", src]
            kb = vis.get("kenburns") or {}
            zoom = float(kb.get("zoom", 1.05))
            frames = max(1, int(dur * fps))
            filters.append(
                f"scale={w * 2}:-2,zoompan=z='min(1+({zoom}-1)*on/{frames},{zoom})'"
                f":d={frames}:s={w}x{h}:fps={fps}")
        else:
            inp = ["-t", f"{dur}", "-i", src]
            filters.append(f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                           f"crop={w}:{h},fps={fps}")
    else:
        inp = ["-f", "lavfi", "-t", f"{dur}",
               "-i", f"color=c={bg}:s={w}x{h}:r={fps}"]
        filters.append("null")

    # Text
    text = shot.get("text") or {}
    content = text.get("content")
    if content and font:
        role = text.get("role", "headline")
        typo = spec.get("typography", {})
        pal = spec.get("palette", {})
        margins = spec.get("format", {}).get("safe_margins_pct",
                                             {"top": 10, "bottom": 15, "sides": 6})
        color = pal.get("text_primary", "#FFFFFF")
        if role == "headline":
            size = int(h * float(typo.get("headline_size_pct_h", 6)) / 100)
            y = f"(h-text_h)/2" if spec.get("captions", {}).get("position") != "top" else f"h*{margins['top']/100}"
        elif role == "chapter":
            size = int(h * 0.045)
            y = f"h*{margins['top']/100}"
        else:  # caption
            size = int(h * 0.035)
            pos = spec.get("captions", {}).get("position", "chest")
            y = {"chest": "h*0.62", "center": "(h-text_h)/2",
                 "lower-third": f"h-(h*{margins['bottom']/100})-text_h",
                 "top": f"h*{margins['top']/100}"}.get(pos, "h*0.62")
        if (typo.get("case") == "UPPERCASE") and role == "headline":
            content = content.upper()
        filters.append(
            "drawtext=fontfile=" + shlex.quote(font).strip("'") +
            f":text='{esc(content)}':fontcolor={color}:fontsize={size}"
            f":x=(w-text_w)/2:y={y}"
            f":shadowcolor=black@0.5:shadowx=2:shadowy=2"
            f":borderw=0")

    vf = ",".join(filters) + f",format=yuv420p"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", *inp,
           "-vf", vf, "-an", "-r", str(fps), "-t", f"{dur}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-y", outpath]
    return cmd


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("timeline")
    p.add_argument("spec")
    p.add_argument("out")
    p.add_argument("--assets", default=None)
    p.add_argument("--font", default=None)
    p.add_argument("--vo", default=None, help="voiceover audio file")
    p.add_argument("--music", default=None, help="music audio file")
    args = p.parse_args()

    with open(args.timeline) as f:
        tl = json.load(f)
    with open(args.spec) as f:
        spec = json.load(f)
    w = tl.get("width") or spec.get("format", {}).get("width", 1080)
    h = tl.get("height") or spec.get("format", {}).get("height", 1920)
    fps = tl.get("fps") or spec.get("format", {}).get("fps", 30)
    font = find_font(args.font)
    if not font:
        print("WARNING: no TTF font found; rendering without text. "
              "Pass --font /path/to/font.ttf", file=sys.stderr)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        parts = []
        for i, shot in enumerate(tl["shots"]):
            part = os.path.join(tmp, f"shot{i:03d}.mp4")
            cmd = shot_cmd(shot, spec, w, h, fps, font, args.assets, part)
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"ERROR shot {i}: {r.stderr[-500:]}", file=sys.stderr)
                return 1
            parts.append(part)

        concat = os.path.join(tmp, "concat.txt")
        with open(concat, "w") as f:
            for part in parts:
                f.write(f"file '{part}'\n")
        silent = os.path.join(tmp, "video.mp4")
        r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                            "-f", "concat", "-safe", "0", "-i", concat,
                            "-c", "copy", "-y", silent],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"ERROR concat: {r.stderr[-500:]}", file=sys.stderr)
            return 1

        # Audio mix
        if args.vo and args.music:
            duck = tl.get("music", {}).get("duck_db", -12)
            acmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", silent,
                    "-i", args.vo, "-i", args.music, "-filter_complex",
                    f"[2:a]volume={duck}dB[m];[1:a][m]amix=inputs=2:duration=first[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-shortest",
                    "-y", args.out]
        elif args.vo or args.music:
            aud = args.vo or args.music
            acmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", silent,
                    "-i", aud, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-shortest", "-y", args.out]
        else:
            acmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", silent,
                    "-c", "copy", "-y", args.out]
        r = subprocess.run(acmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"ERROR audio mux: {r.stderr[-500:]}", file=sys.stderr)
            return 1

    print(f"OK: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
