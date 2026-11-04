#!/usr/bin/env bash
# Install the open-source tools Reverse Any Video integrates (see docs/ECOSYSTEM.md).
# Everything lands in ~/.cache/reverse-any-video unless noted. Safe to re-run.
set -euo pipefail
C="${RAV_CACHE:-$HOME/.cache/reverse-any-video}"
mkdir -p "$C"/{rhubarb,kokoro,assets}
step() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

step "Python packages (Kokoro TTS, PocketSphinx aligner, PySceneDetect, rembg, Blender as a module)"
python3 -m pip install --upgrade kokoro-onnx soundfile pocketsphinx "scenedetect[opencv-headless]" "rembg[cpu]" bpy piper-tts numpy
python3 -m pip install whisperx || echo "  (whisperX optional: word timing falls back to PocketSphinx)"

step "Rhubarb Lip Sync 1.14.0"
case "$(uname -s)" in
  Linux)  RZ=Rhubarb-Lip-Sync-1.14.0-Linux.zip ;;
  Darwin) RZ=Rhubarb-Lip-Sync-1.14.0-macOS.zip ;;
  *)      RZ=Rhubarb-Lip-Sync-1.14.0-Windows.zip ;;
esac
if [ ! -x "$C/rhubarb/rhubarb" ]; then
  tmp=$(mktemp -d)
  curl -fsSL -o "$tmp/r.zip" "https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/$RZ"
  python3 -I -m zipfile -e "$tmp/r.zip" "$tmp/x"
  cp -r "$tmp"/x/*/* "$C/rhubarb/" && chmod +x "$C/rhubarb/rhubarb"
  rm -rf "$tmp"
fi
"$C/rhubarb/rhubarb" --version

step "Kokoro-82M ONNX models"
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  [ -s "$C/kokoro/$f" ] || curl -fsSL -o "$C/kokoro/$f" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f"
done
ls -la "$C/kokoro"

step "Blender agent skills (EL4CTEO/blender-skills, MIT) -> ~/.claude/skills"
if [ ! -d "$C/blender-skills" ]; then git clone --depth 1 https://github.com/EL4CTEO/blender-skills.git "$C/blender-skills"; fi
mkdir -p "$HOME/.claude/skills"
for d in "$C"/blender-skills/skills/*/; do ln -sfn "$d" "$HOME/.claude/skills/$(basename "$d")"; done
echo "  linked $(ls "$C/blender-skills/skills" | wc -l) skills"

step "Studio HDRI from Poly Haven (CC0), optional"
python3 "$(dirname "$0")/../skills/create-video/scripts/fetch_assets.py" hdri studio_small_09 --dir "$C/assets" \
  || echo "  (skipped: network blocked; blender_kit uses its gradient studio world)"

cat <<MSG

Done. Add to your shell profile:
  export RHUBARB_PATH="$C/rhubarb/rhubarb"
  export RAV_KOKORO_DIR="$C/kokoro"
  export RAV_HDRI="$C/assets/studio_small_09_2k.hdr"   # if the HDRI downloaded
Optional:
  export FREESOUND_API_KEY=...        # real CC0 sound effects (fetch_sfx.py)
  Blender MCP (live Blender on your machine): see docs/BLENDER_MCP.md
MSG
