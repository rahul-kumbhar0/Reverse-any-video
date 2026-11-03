#!/usr/bin/env python3
"""Detect sound-design events (SFX) in a video's audio: onsets where energy jumps,
classified roughly by spectral band (low thump / mid tap / high tick+whoosh).

Usage: detect_sfx.py <video-or-wav> <out.json> [--sensitivity 8]
Needs numpy (analysis only; the skill works without this stage if missing).
"""
import argparse
import json
import subprocess
import sys
import tempfile
import wave

try:
    import numpy as np
except ImportError:
    print("ERROR: numpy required for SFX detection; skip this stage.", file=sys.stderr)
    sys.exit(3)


def to_wav(src: str, dst: str) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", src,
                    "-vn", "-ac", "1", "-ar", "22050", "-y", dst], check=True)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("out")
    p.add_argument("--sensitivity", type=float, default=8.0,
                   help="dB jump over local median to count as an onset")
    args = p.parse_args()

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        to_wav(args.input, tmp.name)
        with wave.open(tmp.name) as w:
            sr = w.getframerate()
            x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)
    if len(x) < sr:
        json.dump({"events": []}, open(args.out, "w"))
        print("{}")
        return 0
    x /= 32768.0

    hop, win = sr // 50, sr // 25  # 20ms hop, 40ms window
    n = (len(x) - win) // hop
    freqs = np.fft.rfftfreq(win, 1 / sr)
    bands = {"low": (20, 200), "mid": (200, 2000), "high": (2000, 10000)}
    E = {k: np.zeros(n) for k in bands}
    total = np.zeros(n)
    for i in range(n):
        seg = x[i * hop:i * hop + win] * np.hanning(win)
        mag = np.abs(np.fft.rfft(seg)) ** 2
        total[i] = mag.sum() + 1e-12
        for k, (lo, hi) in bands.items():
            E[k][i] = mag[(freqs >= lo) & (freqs < hi)].sum() + 1e-12

    db = 10 * np.log10(total)
    med = np.array([np.median(db[max(0, i - 25):i + 1]) for i in range(n)])
    jump = db - med
    events = []
    i = 0
    while i < n:
        if jump[i] >= args.sensitivity:
            j = i
            while j < n - 1 and jump[j + 1] > args.sensitivity * 0.4:
                j += 1
            t0, t1 = i * hop / sr, (j * hop + win) / sr
            seg = slice(i, j + 1)
            ratios = {k: float(E[k][seg].sum() / total[seg].sum()) for k in bands}
            dur = t1 - t0
            if ratios["low"] > 0.5:
                kind = "impact/thump"
            elif ratios["high"] > 0.45:
                kind = "whoosh/riser" if dur > 0.25 else "tick/click"
            else:
                kind = "tap/pop" if dur < 0.2 else "swell"
            events.append({"t": round(t0, 2), "dur": round(dur, 2), "kind": kind,
                           "strength_db": round(float(jump[seg].max()), 1),
                           "bands": {k: round(v, 2) for k, v in ratios.items()}})
            i = j + 1
        else:
            i += 1

    result = {"events": events, "events_per_minute": round(len(events) / (n * hop / sr / 60), 1),
              "notes": "Match event times to cut/morph times from shots.json: events within "
                       "0.15s of a visual change are its sound design."}
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps({"events": len(events), "per_minute": result["events_per_minute"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
