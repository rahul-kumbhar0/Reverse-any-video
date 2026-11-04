#!/usr/bin/env python3
"""Text -> voiceover WAV with the best local engine available.

  1. Kokoro-82M via kokoro-onnx (Apache-2.0, hexgrad/kokoro). Natural, fast on CPU.
     Models: kokoro-v1.0.onnx + voices-v1.0.bin (scripts/install_tools.sh fetches them),
     located via --models DIR or $RAV_KOKORO_DIR (default ~/.cache/reverse-any-video/kokoro).
  2. Piper (piper-tts) with an .onnx voice via --piper-model or $RAV_PIPER_MODEL.
  For premium cloud voices use the ElevenLabs MCP connector instead and pass its file.

Usage: tts.py "text" out.wav [--voice am_puck] [--speed 1.0] [--lang en-us]
       tts.py --list-voices
"""
import argparse
import os
import subprocess
import sys

DEFAULT_DIR = os.path.expanduser("~/.cache/reverse-any-video/kokoro")


def kokoro(text, out, voice, speed, lang, models):
    import soundfile as sf
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(models, "kokoro-v1.0.onnx"), os.path.join(models, "voices-v1.0.bin"))
    audio, sr = k.create(text, voice=voice, speed=speed, lang=lang)
    sf.write(out, audio, sr)
    return len(audio) / sr


def piper(text, out, model, speed):
    subprocess.run([sys.executable, "-m", "piper", "-m", model, "--length-scale", str(1 / speed), "-f", out],
                   input=text.encode(), check=True, capture_output=True)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("text", nargs="?")
    p.add_argument("out", nargs="?")
    p.add_argument("--voice", default="am_puck")
    p.add_argument("--speed", type=float, default=1.0)
    p.add_argument("--lang", default="en-us")
    p.add_argument("--models", default=os.environ.get("RAV_KOKORO_DIR", DEFAULT_DIR))
    p.add_argument("--piper-model", default=os.environ.get("RAV_PIPER_MODEL"))
    p.add_argument("--list-voices", action="store_true")
    a = p.parse_args()

    if a.list_voices:
        from kokoro_onnx import Kokoro
        k = Kokoro(os.path.join(a.models, "kokoro-v1.0.onnx"), os.path.join(a.models, "voices-v1.0.bin"))
        print(" ".join(k.get_voices()))
        return 0
    if not a.text or not a.out:
        p.error("text and out are required")
    try:
        d = kokoro(a.text, a.out, a.voice, a.speed, a.lang, a.models)
        print(f"OK kokoro:{a.voice} {d:.2f}s -> {a.out}")
        return 0
    except Exception as e:  # noqa: BLE001 - fall through to the next engine
        print(f"kokoro unavailable ({e.__class__.__name__}: {e}); trying piper", file=sys.stderr)
    if a.piper_model:
        piper(a.text, a.out, a.piper_model, a.speed)
        print(f"OK piper -> {a.out}")
        return 0
    print("ERROR: no TTS engine available. Run scripts/install_tools.sh or use the ElevenLabs MCP.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
