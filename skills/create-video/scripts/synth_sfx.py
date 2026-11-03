#!/usr/bin/env python3
"""Synthesize common motion-design SFX as WAV files — no samples, no downloads.

Kinds: whoosh, tap, click, pop, impact, riser, shimmer
Usage: synth_sfx.py <kind> <out.wav> [--dur 0.4] [--pitch 1.0] [--gain 0.8]
       synth_sfx.py all <outdir>          # one of each, defaults
"""
import argparse
import math
import os
import random
import struct
import sys
import wave

SR = 44100


def env_ar(n, a_frac, curve=2.0):
    """attack-release envelope"""
    a = max(1, int(n * a_frac))
    out = []
    for i in range(n):
        if i < a:
            out.append((i / a) ** 0.5)
        else:
            out.append((1 - (i - a) / (n - a)) ** curve)
    return out


def noise(n):
    rnd = random.Random(7)
    return [rnd.uniform(-1, 1) for _ in range(n)]


def lowpass(x, alpha):
    y, prev = [], 0.0
    for v in x:
        prev = prev + alpha * (v - prev)
        y.append(prev)
    return y


def bandsweep(x, start_a, end_a):
    """crude swept lowpass for whoosh character"""
    y, prev = [], 0.0
    n = len(x)
    for i, v in enumerate(x):
        a = start_a + (end_a - start_a) * (i / n)
        prev = prev + a * (v - prev)
        y.append(prev)
    return y


def sine_sweep(n, f0, f1, curve=1.0):
    out, ph = [], 0.0
    for i in range(n):
        p = (i / n) ** curve
        f = f0 + (f1 - f0) * p
        ph += 2 * math.pi * f / SR
        out.append(math.sin(ph))
    return out


def make(kind, dur, pitch):
    n = int(SR * dur)
    if kind == "whoosh":
        x = bandsweep(noise(n), 0.02 * pitch, 0.35 * pitch)
        e = env_ar(n, 0.45, curve=1.6)
        return [v * g for v, g in zip(x, e)]
    if kind == "tap":
        n = int(SR * min(dur, 0.12))
        x = sine_sweep(n, 420 * pitch, 180 * pitch, 0.6)
        e = env_ar(n, 0.02, curve=3)
        return [v * g for v, g in zip(x, e)]
    if kind == "click":
        n = int(SR * min(dur, 0.05))
        x = lowpass(noise(n), 0.9)
        e = env_ar(n, 0.02, curve=4)
        return [v * g for v, g in zip(x, e)]
    if kind == "pop":
        n = int(SR * min(dur, 0.15))
        x = sine_sweep(n, 900 * pitch, 240 * pitch, 0.4)
        e = env_ar(n, 0.03, curve=3)
        return [v * g for v, g in zip(x, e)]
    if kind == "impact":
        x1 = sine_sweep(n, 160 * pitch, 42 * pitch, 0.5)
        x2 = lowpass(noise(n), 0.12)
        e = env_ar(n, 0.01, curve=2.5)
        return [(a * 0.8 + b * 0.4) * g for a, b, g in zip(x1, x2, e)]
    if kind == "riser":
        x1 = sine_sweep(n, 120 * pitch, 880 * pitch, 1.4)
        x2 = bandsweep(noise(n), 0.03, 0.5)
        e = [((i / n) ** 1.8) for i in range(n)]
        tail = int(n * 0.04)
        for i in range(tail):
            e[-tail + i] *= 1 - i / tail
        return [(a * 0.5 + b * 0.5) * g for a, b, g in zip(x1, x2, e)]
    if kind == "shimmer":
        tones = [1200, 1800, 2700, 3600]
        out = [0.0] * n
        for k, f in enumerate(tones):
            ph = 0.0
            for i in range(n):
                ph += 2 * math.pi * f * pitch / SR
                out[i] += math.sin(ph + k) * 0.25
        e = env_ar(n, 0.1, curve=1.5)
        return [v * g for v, g in zip(out, e)]
    raise SystemExit(f"unknown kind: {kind}")


def write_wav(path, x, gain):
    peak = max(1e-9, max(abs(v) for v in x))
    scale = gain / peak * 32767
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-32767, min(32767, v * scale)))) for v in x))


KINDS = ["whoosh", "tap", "click", "pop", "impact", "riser", "shimmer"]
DEFAULT_DUR = {"whoosh": 0.5, "tap": 0.1, "click": 0.04, "pop": 0.12,
               "impact": 0.6, "riser": 1.2, "shimmer": 0.8}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("kind")
    p.add_argument("out")
    p.add_argument("--dur", type=float, default=None)
    p.add_argument("--pitch", type=float, default=1.0)
    p.add_argument("--gain", type=float, default=0.8)
    args = p.parse_args()

    if args.kind == "all":
        os.makedirs(args.out, exist_ok=True)
        for k in KINDS:
            write_wav(os.path.join(args.out, f"{k}.wav"),
                      make(k, DEFAULT_DUR[k], args.pitch), args.gain)
        print(f"OK: {len(KINDS)} sfx in {args.out}")
        return 0
    write_wav(args.out, make(args.kind, args.dur or DEFAULT_DUR[args.kind], args.pitch), args.gain)
    print(f"OK: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
