#!/usr/bin/env python3
"""FFmpeg timeline assembler v2 — zero-dependency fallback renderer.

Renders a timeline.json (see create-video SKILL.md) in a given style-spec.json.

v2 features on top of the original card/image/kenburns/drawtext/VO+music core:
  - aspect presets ("9:16", "16:9", "1:1", "4:5", "21:9") via timeline "aspect"
  - per-shot transitions INTO a shot: {"transition": {"type": "fade", "duration": 0.3}}
    (any ffmpeg xfade transition name: fade, slideleft, circleopen, dissolve, zoomin, ...)
  - video shots: "trim_start" (seek into source), "speed" (0.5-2.0), "keep_audio"
  - fit modes for image/video: "cover" (default), "contain", "blur" (blurred pad)
  - multiple text layers per shot via "texts": [{...}, {...}]
  - per-shot "sfx": "<name>" auto-placed from <assets>/sfx/<name>.wav at the shot start
  - music: {"loop": true, "fade_out": 1.0, "duck_db": -12}

Usage: assemble.py <timeline.json> <style-spec.json> <out.mp4>
                   [--assets DIR] [--font /path/to/font.ttf] [--vo VO] [--music MUSIC]
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

ASPECTS = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
    "21:9": (2520, 1080),
}


def run(cmd, label):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ERROR {label}: {r.stderr[-800:]}", file=sys.stderr)
        sys.exit(1)
    return r


def find_font(explicit):
    if explicit and os.path.exists(explicit):
        return explicit
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            return f
    return None


def esc(text):
    """Escape text for drawtext."""
    return (text.replace("\\", "\\\\").replace(":", "\\:")
            .replace("'", "\\\\\\'").replace("%", "\\%"))


def resolve_src(src, assets):
    if assets and not os.path.isabs(src) and not os.path.exists(src):
        cand = os.path.join(assets, src)
        if os.path.exists(cand):
            return cand
    return src


def atempo_chain(speed):
    """atempo only accepts 0.5-2.0 per filter; chain for anything outside."""
    parts = []
    s = speed
    while s > 2.0:
        parts.append("atempo=2.0")
        s /= 2.0
    while s < 0.5:
        parts.append("atempo=0.5")
        s /= 0.5
    parts.append(f"atempo={s:.6f}")
    return ",".join(parts)


def text_filters(shot, spec, w, h, font):
    """drawtext filter strings for one shot (supports text or texts[])."""
    layers = shot.get("texts")
    if layers is None:
        t = shot.get("text")
        layers = [t] if t else []
    out = []
    typo = spec.get("typography", {})
    pal = spec.get("palette", {})
    margins = spec.get("format", {}).get(
        "safe_margins_pct", {"top": 10, "bottom": 15, "sides": 6})
    for text in layers:
        content = text.get("content")
        if not content or not font:
            continue
        role = text.get("role", "headline")
        color = text.get("color") or pal.get("text_primary", "#FFFFFF")
        if text.get("size_pct"):
            size = int(h * float(text["size_pct"]) / 100)
        elif role == "headline":
            size = int(h * float(typo.get("headline_size_pct_h", 6)) / 100)
        elif role == "chapter":
            size = int(h * 0.045)
        else:
            size = int(h * 0.035)
        if text.get("y"):
            y = str(text["y"])
        elif role == "headline":
            y = ("(h-text_h)/2" if spec.get("captions", {}).get("position") != "top"
                 else f"h*{margins['top'] / 100}")
        elif role == "chapter":
            y = f"h*{margins['top'] / 100}"
        else:
            pos = spec.get("captions", {}).get("position", "chest")
            y = {"chest": "h*0.62", "center": "(h-text_h)/2",
                 "lower-third": f"h-(h*{margins['bottom'] / 100})-text_h",
                 "top": f"h*{margins['top'] / 100}"}.get(pos, "h*0.62")
        if (typo.get("case") == "UPPERCASE") and role == "headline":
            content = content.upper()
        box = ""
        if text.get("box"):
            box = f":box=1:boxcolor={text.get('box_color', 'black@0.55')}:boxborderw={int(size * 0.35)}"
        out.append(
            "drawtext=fontfile=" + shlex.quote(font).strip("'") +
            f":text='{esc(content)}':fontcolor={color}:fontsize={size}"
            f":x={text.get('x', '(w-text_w)/2')}:y={y}"
            f":shadowcolor=black@0.5:shadowx=2:shadowy=2" + box)
    return out


def fit_filter(fit, w, h, fps, bg):
    """Scale an arbitrary source into the frame."""
    if fit == "contain":
        return (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={bg},fps={fps}")
    if fit == "blur":
        return (f"split[fg][bgin];"
                f"[bgin]scale={w}:{h}:force_original_aspect_ratio=increase,"
                f"crop={w}:{h},boxblur=24:2[bgout];"
                f"[fg]scale={w}:{h}:force_original_aspect_ratio=decrease[fgout];"
                f"[bgout][fgout]overlay=(W-w)/2:(H-h)/2,fps={fps}")
    # cover (default)
    return (f"scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},fps={fps}")


def shot_cmd(shot, spec, w, h, fps, font, assets, outpath):
    """Build the ffmpeg command for one shot's video; return (cmd, audio_extract).

    audio_extract is None or a dict describing the source audio to lift out of a
    keep_audio video shot: {"src", "trim_start", "duration", "speed", "volume"}.
    """
    dur = float(shot["duration"])
    vis = shot.get("visual", {})
    vtype = vis.get("type", "card")
    bg = vis.get("bg") or spec.get("palette", {}).get("background", "#101014")
    fit = vis.get("fit", "cover")
    filters = []
    audio_extract = None

    if vtype in ("image", "video") and vis.get("src"):
        src = resolve_src(vis["src"], assets)
        if vtype == "image":
            inp = ["-loop", "1", "-t", f"{dur}", "-i", src]
            kb = vis.get("kenburns") or {}
            zoom = float(kb.get("zoom", 1.05))
            frames = max(1, int(dur * fps))
            filters.append(
                f"scale={w * 2}:-2,zoompan=z='min(1+({zoom}-1)*on/{frames},{zoom})'"
                f":d={frames}:s={w}x{h}:fps={fps}")
        else:
            speed = float(vis.get("speed", 1.0))
            trim = float(vis.get("trim_start", 0))
            src_dur = dur * speed  # source seconds consumed
            inp = ["-ss", f"{trim}", "-t", f"{src_dur}", "-i", src]
            if abs(speed - 1.0) > 1e-6:
                filters.append(f"setpts=PTS/{speed}")
            filters.append(fit_filter(fit, w, h, fps, bg))
            if vis.get("keep_audio"):
                audio_extract = {"src": src, "trim_start": trim,
                                 "src_dur": src_dur, "speed": speed,
                                 "volume": float(vis.get("audio_volume", 1.0))}
    else:
        inp = ["-f", "lavfi", "-t", f"{dur}",
               "-i", f"color=c={bg}:s={w}x{h}:r={fps}"]
        filters.append("null")

    filters.extend(text_filters(shot, spec, w, h, font))
    vf = ",".join(filters) + ",format=yuv420p"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", *inp,
           "-vf", vf, "-an", "-r", str(fps), "-t", f"{dur}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-y", outpath]
    return cmd, audio_extract


def concat_copy(parts, outpath, tmp, label):
    concat = os.path.join(tmp, f"{label}.txt")
    with open(concat, "w") as f:
        for part in parts:
            f.write(f"file '{part}'\n")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error",
         "-f", "concat", "-safe", "0", "-i", concat,
         "-c", "copy", "-y", outpath], f"concat {label}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("timeline")
    p.add_argument("spec")
    p.add_argument("out")
    p.add_argument("--assets", default=None)
    p.add_argument("--font", default=None)
    p.add_argument("--vo", default=None, help="voiceover audio file")
    p.add_argument("--music", default=None, help="music audio file")
    p.add_argument("--sfx-dir", default=None,
                   help="directory of <name>.wav SFX (default: <assets>/sfx)")
    args = p.parse_args()

    with open(args.timeline) as f:
        tl = json.load(f)
    with open(args.spec) as f:
        spec = json.load(f)

    aspect = tl.get("aspect")
    if aspect and aspect in ASPECTS:
        w, h = ASPECTS[aspect]
    else:
        w = tl.get("width") or spec.get("format", {}).get("width", 1080)
        h = tl.get("height") or spec.get("format", {}).get("height", 1920)
    fps = tl.get("fps") or spec.get("format", {}).get("fps", 30)
    font = find_font(args.font)
    if not font:
        print("WARNING: no TTF font found; rendering without text. "
              "Pass --font /path/to/font.ttf", file=sys.stderr)
    sfx_dir = args.sfx_dir or (os.path.join(args.assets, "sfx") if args.assets else None)

    shots = tl["shots"]
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        # ---- 1. Render each shot, compute final-timeline start times -------
        parts = []          # (path, duration, transition_into or None)
        audio_events = []   # (kind, payload, start_time_s, volume)
        t_cursor = 0.0
        for i, shot in enumerate(shots):
            part = os.path.join(tmp, f"shot{i:03d}.mp4")
            cmd, aext = shot_cmd(shot, spec, w, h, fps, font, args.assets, part)
            run(cmd, f"shot {i}")
            trans = shot.get("transition") if i > 0 else None
            tdur = float(trans.get("duration", 0.3)) if trans else 0.0
            t_cursor -= tdur  # transition overlaps the previous shot's tail
            start = max(0.0, t_cursor)
            if aext:
                audio_events.append(("srcaudio", aext, start, aext["volume"]))
            sfx = shot.get("sfx")
            if sfx and sfx_dir:
                for ext in (".wav", ".mp3", ".ogg"):
                    cand = os.path.join(sfx_dir, sfx + ext)
                    if os.path.exists(cand):
                        audio_events.append(
                            ("file", cand, start, float(shot.get("sfx_volume", 0.8))))
                        break
                else:
                    print(f"WARNING: sfx '{sfx}' not found in {sfx_dir}", file=sys.stderr)
            parts.append((part, float(shot["duration"]), trans))
            t_cursor += float(shot["duration"])
        total = t_cursor

        # ---- 2. Join: merge no-transition runs, then xfade across runs -----
        segments = []  # (path, duration)
        run_files, run_dur = [], 0.0
        for j, (part, dur, trans) in enumerate(parts):
            if j > 0 and trans:
                seg = run_files[0]
                if len(run_files) > 1:
                    seg = os.path.join(tmp, f"seg{len(segments):03d}.mp4")
                    concat_copy(run_files, seg, tmp, f"seg{len(segments):03d}")
                segments.append((seg, run_dur, None))
                run_files, run_dur = [], 0.0
                segments.append(("__trans__", trans, None))
            run_files.append(part)
            run_dur += dur
        if run_files:
            seg = run_files[0]
            if len(run_files) > 1:
                seg = os.path.join(tmp, f"seg{len(segments):03d}.mp4")
                concat_copy(run_files, seg, tmp, f"seg{len(segments):03d}")
            segments.append((seg, run_dur, None))

        silent = os.path.join(tmp, "video.mp4")
        vid_segments = [s for s in segments if s[0] != "__trans__"]
        transitions = [s[1] for s in segments if s[0] == "__trans__"]
        if not transitions:
            concat_copy([s[0] for s in vid_segments], silent, tmp, "all")
        else:
            inputs = []
            for segpath, _, _ in vid_segments:
                inputs += ["-i", segpath]
            fc, prev, chain_dur = [], "0:v", vid_segments[0][1]
            for k in range(1, len(vid_segments)):
                trans = transitions[k - 1]
                ttype = trans.get("type", "fade")
                tdur = float(trans.get("duration", 0.3))
                offset = max(0.0, chain_dur - tdur)
                label = f"v{k}"
                fc.append(f"[{prev}][{k}:v]xfade=transition={ttype}"
                          f":duration={tdur}:offset={offset:.4f}[{label}]")
                prev = label
                chain_dur = chain_dur + vid_segments[k][1] - tdur
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", *inputs,
                 "-filter_complex", ";".join(fc), "-map", f"[{prev}]",
                 "-r", str(fps), "-c:v", "libx264", "-preset", "medium",
                 "-crf", "19", "-y", silent], "xfade")

        # ---- 3. Audio mix: VO + music + shot source audio + SFX ------------
        mix_inputs, mix_filters, mix_labels = [], [], []
        idx = 1  # 0 is the video

        def add_input(pre_args, filt):
            nonlocal idx
            mix_inputs.extend(pre_args)
            label = f"a{idx}"
            mix_filters.append(f"[{idx}:a]{filt}[{label}]")
            mix_labels.append(label)
            idx += 1

        if args.vo:
            vo_off = float(tl.get("voiceover", {}).get("offset", 0))
            add_input(["-i", args.vo],
                      f"adelay={int(vo_off * 1000)}:all=1,apad")
        if args.music:
            m = tl.get("music", {})
            duck = float(m.get("duck_db", -12))
            fade = float(m.get("fade_out", 1.0))
            pre = (["-stream_loop", "-1"] if m.get("loop") else []) + ["-i", args.music]
            add_input(pre,
                      f"atrim=0:{total:.3f},volume={duck}dB,"
                      f"afade=t=out:st={max(0, total - fade):.3f}:d={fade}")
        for kind, payload, start, vol in audio_events:
            delay = int(start * 1000)
            if kind == "file":
                add_input(["-i", payload],
                          f"volume={vol},adelay={delay}:all=1")
            else:  # srcaudio lifted from a keep_audio video shot
                filt = f"{atempo_chain(payload['speed'])}," if abs(payload["speed"] - 1.0) > 1e-6 else ""
                add_input(["-ss", f"{payload['trim_start']}",
                           "-t", f"{payload['src_dur']}", "-i", payload["src"]],
                          f"{filt}volume={vol},adelay={delay}:all=1")

        if mix_labels:
            fc = ";".join(mix_filters)
            if len(mix_labels) > 1:
                fc += (";" + "".join(f"[{l}]" for l in mix_labels) +
                       f"amix=inputs={len(mix_labels)}:duration=longest:normalize=0[aout]")
            else:
                fc += f";[{mix_labels[0]}]anull[aout]"
            run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                 "-i", silent, *mix_inputs, "-filter_complex", fc,
                 "-map", "0:v", "-map", "[aout]", "-c:v", "copy",
                 "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}",
                 "-y", args.out], "audio mux")
        else:
            run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                 "-i", silent, "-c", "copy", "-y", args.out], "copy out")

    print(f"OK: {args.out} ({total:.2f}s, {w}x{h}@{fps})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
