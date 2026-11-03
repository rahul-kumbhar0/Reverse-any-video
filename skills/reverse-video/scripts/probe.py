#!/usr/bin/env python3
"""Probe a video with ffprobe -> normalized JSON summary.

Usage: probe.py <video> <out.json>
"""
import json
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    video, out = sys.argv[1], sys.argv[2]
    try:
        raw = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", video],
            capture_output=True, text=True, check=True,
        ).stdout
    except FileNotFoundError:
        print("ERROR: ffprobe not found. Install ffmpeg.", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as e:
        print(f"ERROR: ffprobe failed: {e.stderr.strip()}", file=sys.stderr)
        return 1

    data = json.loads(raw)
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    fmt = data.get("format", {})

    def fps_of(stream):
        r = stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "0/1"
        try:
            num, den = r.split("/")
            return round(float(num) / float(den), 3) if float(den) else 0.0
        except ValueError:
            return 0.0

    w, h = int(v.get("width", 0) or 0), int(v.get("height", 0) or 0)
    rotation = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rotation = int(sd["rotation"])
    if abs(rotation) in (90, 270):
        w, h = h, w

    summary = {
        "duration_s": round(float(fmt.get("duration", 0) or 0), 3),
        "width": w,
        "height": h,
        "aspect": round(w / h, 4) if h else None,
        "orientation": "vertical" if h > w else ("square" if h == w else "horizontal"),
        "fps": fps_of(v),
        "video_codec": v.get("codec_name"),
        "bitrate_kbps": round(int(fmt.get("bit_rate", 0) or 0) / 1000),
        "has_audio": a is not None,
        "audio_codec": a.get("codec_name") if a else None,
        "audio_channels": a.get("channels") if a else 0,
        "audio_sample_rate": int(a.get("sample_rate", 0)) if a else 0,
    }
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
