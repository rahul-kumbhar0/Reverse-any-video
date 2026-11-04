#!/usr/bin/env python3
"""Voiceover -> per-frame mouth visemes for the presenter puppet.

Engines, best first:
  1. Rhubarb Lip Sync (DanielSWolf/rhubarb-lip-sync, MIT): phonetic recognition -> the
     Hanna-Barbera mouth set A-H + X, mapped to Nova visemes. Pass the script with
     --dialog for much better accuracy. Binary via $RHUBARB_PATH, PATH, or
     ~/.cache/reverse-any-video/rhubarb/rhubarb (scripts/install_tools.sh).
  2. Heuristic (no install): loudness + spectral centroid, debounced to >=2-frame holds.

Usage: lipsync.py voice.wav out.json [--dialog "script"] [--fps 30] [--offset 0.15]
                  [--duration 3.0] [--engine auto|rhubarb|heuristic]
Output: {"fps":30,"engine":"rhubarb","frames":[{"v":"aa","e":0.62}, ...]}
  v = Nova viseme, e = smoothed speech energy (0..1) for nods/bounce.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import wave

import numpy as np

RHUBARB_TO_VISEME = {"A": "mbp", "B": "ee", "C": "eh", "D": "aa", "E": "oh",
                     "F": "uw", "G": "fv", "H": "l", "X": "rest"}


def load(path, sr=16000):
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-ac", "1",
                        "-ar", str(sr), "-y", tmp.name], check=True)
        with wave.open(tmp.name) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    return x, sr


def energy_track(x, sr, fps):
    hop = sr / fps
    n = int(len(x) / hop)
    win = int(sr * 0.04)
    rms = np.array([np.sqrt(np.mean(np.pad(x[int(i * hop):int(i * hop) + win], (0, win))[:win] ** 2))
                    for i in range(n)])
    db = 20 * np.log10(rms + 1e-9)
    speech = db[db > -45]
    ref = np.percentile(speech, 90) if len(speech) else -20
    norm = np.clip((db - (ref - 30)) / 30, 0, 1)
    return norm, np.convolve(norm, np.ones(5) / 5, mode="same")


def find_rhubarb():
    for c in (os.environ.get("RHUBARB_PATH"), shutil.which("rhubarb"),
              os.path.expanduser("~/.cache/reverse-any-video/rhubarb/rhubarb")):
        if c and os.path.exists(c):
            return c
    return None


def via_rhubarb(path, fps, n_frames, dialog):
    exe = find_rhubarb()
    if not exe:
        raise FileNotFoundError("rhubarb not installed")
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "v.wav")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", "44100",
                        "-c:a", "pcm_s16le", "-y", wav], check=True)
        cmd = [exe, "-q", "-f", "json", "--extendedShapes", "GHX", wav, "-o", os.path.join(tmp, "o.json")]
        if dialog:
            dfile = os.path.join(tmp, "d.txt")
            open(dfile, "w").write(dialog)
            cmd[1:1] = ["-d", dfile]
        subprocess.run(cmd, check=True, capture_output=True)
        cues = json.load(open(os.path.join(tmp, "o.json")))["mouthCues"]
    out = []
    for f in range(n_frames):
        t = (f + 0.5) / fps
        v = next((c["value"] for c in cues if c["start"] <= t < c["end"]), "X")
        out.append(RHUBARB_TO_VISEME.get(v, "rest"))
    return out


def via_heuristic(x, sr, fps, norm, hold):
    hop = sr / fps
    win = int(sr * 0.04)
    freqs = np.fft.rfftfreq(win, 1 / sr)
    cen = []
    for i in range(len(norm)):
        seg = np.pad(x[int(i * hop):int(i * hop) + win], (0, win))[:win]
        mag = np.abs(np.fft.rfft(seg * np.hanning(win)))
        cen.append((mag * freqs).sum() / (mag.sum() + 1e-9))
    cen = np.array(cen)
    voiced = norm > 0.2
    c_lo, c_hi = np.percentile(cen[voiced], [30, 75]) if voiced.sum() > 5 else (900, 2500)
    raw = []
    for e, c in zip(norm, cen):
        if e < 0.12:
            raw.append("rest")
        elif e < 0.3:
            raw.append("mbp")
        elif c >= c_hi:
            raw.append("ee")
        elif c <= c_lo:
            raw.append("oh" if e > 0.55 else "uw")
        else:
            raw.append("aa" if e > 0.6 else "eh")
    vis, cur, held = [], "rest", hold
    for v in raw:
        if v != cur and held >= hold:
            cur, held = v, 0
        vis.append(cur)
        held += 1
    return vis


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("audio")
    p.add_argument("out")
    p.add_argument("--dialog", default=None, help="the spoken script (improves Rhubarb accuracy)")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--offset", type=float, default=0.0)
    p.add_argument("--duration", type=float, default=None)
    p.add_argument("--hold", type=int, default=2)
    p.add_argument("--engine", default="auto", choices=["auto", "rhubarb", "heuristic"])
    a = p.parse_args()

    x, sr = load(a.audio)
    norm, energy = energy_track(x, sr, a.fps)
    n = len(norm)
    vis, used = None, None
    if a.engine in ("auto", "rhubarb"):
        try:
            vis, used = via_rhubarb(a.audio, a.fps, n, a.dialog), "rhubarb"
        except Exception as e:  # noqa: BLE001
            if a.engine == "rhubarb":
                raise
            print(f"rhubarb unavailable ({e}); using heuristic", file=sys.stderr)
    if vis is None:
        vis, used = via_heuristic(x, sr, a.fps, norm, a.hold), "heuristic"

    pre = int(round(a.offset * a.fps))
    total = int(round(a.duration * a.fps)) if a.duration else pre + n
    frames = [{"v": "rest", "e": 0.0}] * pre
    frames += [{"v": v, "e": round(float(e), 3)} for v, e in zip(vis, energy)]
    frames = (frames + [{"v": "rest", "e": 0.0}] * max(0, total - len(frames)))[:total]
    json.dump({"fps": a.fps, "engine": used, "frames": frames}, open(a.out, "w"))
    counts = {}
    for fr in frames:
        counts[fr["v"]] = counts.get(fr["v"], 0) + 1
    print(json.dumps({"engine": used, "frames": len(frames), "visemes": counts}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
