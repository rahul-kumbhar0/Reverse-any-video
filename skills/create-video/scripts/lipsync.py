#!/usr/bin/env python3
"""Audio -> per-frame mouth visemes for a puppet (Character-Animator-style lip-sync).

Reads a voiceover, and for each video frame decides a viseme from loudness and spectral
balance:
  silence                -> rest   (or mbp for the first frame after speech: lips closing)
  quiet / onset          -> mbp
  bright (high centroid) -> ee     (s, t, ee, ih sounds)
  dark (low centroid)    -> oh / uw (o, u, w sounds; uw when quieter)
  loud + mid             -> aa     (open vowels)
Each viseme is held >= --hold frames (the reference holds ~2 frames; faster reads as
jitter). Also emits a smoothed energy track for head nods.

Usage: lipsync.py <voice.wav|mp3> <out.json> [--fps 30] [--offset 0.15] [--hold 2]
Output: {"fps":30,"frames":[{"v":"aa","e":0.62}, ...]}
"""
import argparse
import json
import subprocess
import sys
import tempfile
import wave

import numpy as np


def load(path, sr=16000):
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-ac", "1",
                        "-ar", str(sr), "-y", tmp.name], check=True)
        with wave.open(tmp.name) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    return x, sr


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("audio")
    p.add_argument("out")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--offset", type=float, default=0.0, help="seconds of silence before audio starts in the video")
    p.add_argument("--hold", type=int, default=2)
    p.add_argument("--duration", type=float, default=None, help="pad/trim to this many seconds")
    args = p.parse_args()

    x, sr = load(args.audio)
    hop = sr / args.fps
    win = int(sr * 0.04)
    n_audio = int(len(x) / hop)
    pre = int(round(args.offset * args.fps))
    total = int(round(args.duration * args.fps)) if args.duration else pre + n_audio

    rms, cen = np.zeros(n_audio), np.zeros(n_audio)
    freqs = np.fft.rfftfreq(win, 1 / sr)
    for i in range(n_audio):
        a = int(i * hop)
        seg = x[a:a + win]
        if len(seg) < win:
            seg = np.pad(seg, (0, win - len(seg)))
        rms[i] = np.sqrt(np.mean(seg ** 2))
        mag = np.abs(np.fft.rfft(seg * np.hanning(win)))
        cen[i] = (mag * freqs).sum() / (mag.sum() + 1e-9)

    db = 20 * np.log10(rms + 1e-9)
    speech = db[db > -45]
    ref = np.percentile(speech, 90) if len(speech) else -20
    norm = np.clip((db - (ref - 30)) / 30, 0, 1)            # 0 = silence, 1 = loud speech
    c_lo, c_hi = (np.percentile(cen[norm > 0.2], [30, 75]) if (norm > 0.2).sum() > 5 else (900, 2500))

    raw = []
    for i in range(n_audio):
        e = norm[i]
        if e < 0.12:
            raw.append("rest")
        elif e < 0.3:
            raw.append("mbp")
        elif cen[i] >= c_hi:
            raw.append("ee")
        elif cen[i] <= c_lo:
            raw.append("oh" if e > 0.55 else "uw")
        else:
            raw.append("aa" if e > 0.6 else "ee")

    # hold each viseme >= hold frames (debounce)
    vis, cur, held = [], "rest", args.hold
    for v in raw:
        if v != cur and held >= args.hold:
            cur, held = v, 0
        vis.append(cur)
        held += 1

    energy = np.convolve(norm, np.ones(5) / 5, mode="same")
    frames = [{"v": "rest", "e": 0.0}] * pre
    frames += [{"v": v, "e": round(float(e), 3)} for v, e in zip(vis, energy)]
    frames = (frames + [{"v": "rest", "e": 0.0}] * max(0, total - len(frames)))[:total]

    with open(args.out, "w") as f:
        json.dump({"fps": args.fps, "frames": frames}, f)
    counts = {k: sum(1 for fr in frames if fr["v"] == k) for k in ("rest", "mbp", "ee", "aa", "oh", "uw")}
    print(json.dumps({"frames": len(frames), "visemes": counts}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
