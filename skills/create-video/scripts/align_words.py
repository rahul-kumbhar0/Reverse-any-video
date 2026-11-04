#!/usr/bin/env python3
"""Voiceover + script -> word-level timestamps (karaoke captions, keyword-triggered poses).

Engines, best first:
  1. WhisperX (m-bain/whisperX, BSD-2): ASR + wav2vec2 forced alignment. Needs its models
     (HuggingFace / download.pytorch.org). Use --engine whisperx or auto.
  2. PocketSphinx forced alignment of the known script (model ships inside the pip
     package, fully offline). Out-of-dictionary words are split into known parts
     ("trackpad" -> "track pad") or interpolated.
  3. Proportional: script words spread over the voiced audio (always works).

Usage: align_words.py voice.wav "the script text" out.json [--offset 0.15] [--engine auto]
Output: {"words":[{"word":"What's","start":0.15,"end":0.34}, ...], "engine":"pocketsphinx"}
Times include --offset (where the VO starts in the video).
"""
import argparse
import json
import re
import subprocess
import sys


def pcm16k(path):
    return subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", "16000",
                           "-f", "s16le", "-"], capture_output=True, check=True).stdout


def tokens(script):
    return [w for w in re.findall(r"[A-Za-z0-9']+(?:[-'][A-Za-z0-9]+)*|\d+", script)]


def via_whisperx(path, script):
    import whisperx  # noqa: F401  (optional dependency)
    device = "cpu"
    model = whisperx.load_model("small", device, compute_type="int8")
    audio = whisperx.load_audio(path)
    res = model.transcribe(audio)
    amodel, meta = whisperx.load_align_model(language_code=res.get("language", "en"), device=device)
    al = whisperx.align(res["segments"], amodel, meta, audio, device)
    return [{"word": w["word"], "start": w["start"], "end": w["end"]} for w in al["word_segments"] if "start" in w]


def via_pocketsphinx(path, script):
    from pocketsphinx import Decoder
    d = Decoder(samprate=16000, bestpath=False, loglevel="FATAL")
    words = tokens(script)
    plan = []   # (original_index, dict_word)
    for i, w in enumerate(words):
        lw = w.lower()
        if lw.isdigit():
            continue
        if d.lookup_word(lw):
            plan.append((i, lw))
            continue
        split = next(((lw[:k], lw[k:]) for k in range(2, len(lw) - 1)
                      if d.lookup_word(lw[:k]) and d.lookup_word(lw[k:])), None)
        if split:
            plan += [(i, split[0]), (i, split[1])]
    d.set_align_text(" ".join(dw for _, dw in plan))
    d.start_utt()
    d.process_raw(pcm16k(path), full_utt=True)
    d.end_utt()
    segs = [s for s in d.seg() if not s.word.startswith("<") and s.word not in ("[NOISE]",)]
    times = {}
    for (i, _), s in zip(plan, segs):
        st, en = s.start_frame / 100, (s.end_frame + 1) / 100
        if i in times:
            times[i] = (min(times[i][0], st), max(times[i][1], en))
        else:
            times[i] = (st, en)
    out = []
    for i, w in enumerate(words):   # interpolate any word the aligner skipped
        if i not in times:
            prev = max((k for k in times if k < i), default=None)
            nxt = min((k for k in times if k > i), default=None)
            st = times[prev][1] if prev is not None else 0.0
            en = times[nxt][0] if nxt is not None else st + 0.3
            times[i] = (st, max(st + 0.08, en))
        out.append({"word": w, "start": round(times[i][0], 3), "end": round(times[i][1], 3)})
    return out


def via_proportional(path, script):
    raw = pcm16k(path)
    dur = len(raw) / 2 / 16000
    words = tokens(script)
    weights = [max(1, len(w)) for w in words]
    tot, t, out = sum(weights), 0.05, []
    span = dur - 0.1
    for w, k in zip(words, weights):
        d = span * k / tot
        out.append({"word": w, "start": round(t, 3), "end": round(t + d, 3)})
        t += d
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("audio")
    p.add_argument("script")
    p.add_argument("out")
    p.add_argument("--offset", type=float, default=0.0)
    p.add_argument("--engine", default="auto", choices=["auto", "whisperx", "pocketsphinx", "proportional"])
    a = p.parse_args()

    order = ["whisperx", "pocketsphinx", "proportional"] if a.engine == "auto" else [a.engine]
    fns = {"whisperx": via_whisperx, "pocketsphinx": via_pocketsphinx, "proportional": via_proportional}
    words, used = None, None
    for eng in order:
        try:
            words, used = fns[eng](a.audio, a.script), eng
            if words:
                break
        except Exception as e:  # noqa: BLE001 - try the next engine
            print(f"{eng} unavailable: {e.__class__.__name__}: {str(e)[:120]}", file=sys.stderr)
    if not words:
        print("ERROR: alignment failed", file=sys.stderr)
        return 1
    for w in words:
        w["start"] = round(w["start"] + a.offset, 3)
        w["end"] = round(w["end"] + a.offset, 3)
    json.dump({"engine": used, "words": words}, open(a.out, "w"), indent=1)
    print(f"OK {used}: " + " ".join(f"{w['word']}@{w['start']:.2f}" for w in words))
    return 0


if __name__ == "__main__":
    sys.exit(main())
