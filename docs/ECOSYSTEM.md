# Ecosystem: open-source projects that can level up Reverse Any Video

Researched 2026-11-04 (stars/licenses from the GitHub API that day). "Use" = integrate as a
dependency/tool; "Study" = read for techniques only (license or scope makes copying code
unsuitable for this MIT repo).

## 1. Presenter puppet & lip-sync (biggest gap vs. the references)

| Project | License | Use / Study | Why |
|---|---|---|---|
| [DanielSWolf/rhubarb-lip-sync](https://github.com/DanielSWolf/rhubarb-lip-sync) ★2.7k | MIT (LICENSE file) | **Use** | Real phonetic lip-sync → the industry-standard 6–9 Hanna-Barbera mouth shapes (A–H, X). Replaces our loudness/spectrum heuristic in `lipsync.py`. |
| [kevinbadi/claude-codes-influencers](https://github.com/kevinbadi/claude-codes-influencers) ★36 | MIT | **Use/Study** | Talking-mascot pipeline for Claude Code: Rhubarb + Whisper word timings + keyword-triggered poses + blinks + bounce. Almost exactly our `PuppetTrack`; borrow its keyword→pose mapping and sprite-pack format. |
| [danielgatis/rembg](https://github.com/danielgatis/rembg) ★25k | MIT | **Use** | Background removal, for turning drawn/generated character art or product photos into cut-out layers. |

## 2. Blender / 3D quality

| Project | License | Use / Study | Why |
|---|---|---|---|
| [EL4CTEO/blender-skills](https://github.com/EL4CTEO/blender-skills) ★703 | MIT | **Use** | 28 Agent Skills for Blender 5.2 (hard-surface bevels/booleans, texturing, lighting, rendering, video). Runs Blender in the background, which fits our headless setup. Pair with `blender_kit.py`. |
| [arjun988/blender-skills](https://github.com/arjun988/blender-skills) ★1.8k | MIT | Use (with MCP) | 94 specialist Blender skills; executes through a Blender MCP server (interactive, user's machine). |
| [ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender) ★33k | MIT | **Use** (local) | MCP server so Claude drives a live Blender: iterate on scenes visually on the user's computer instead of blind headless renders. |
| [Poly Haven](https://polyhaven.com) assets via [Public-API](https://github.com/Poly-Haven/Public-API) | Assets CC0 (API code AGPL) | **Use** (assets) | CC0 HDRIs, PBR textures and models. A studio HDRI alone fixes most "CG-looking" reflections on metal/glass. |
| [ambientCG](https://ambientcg.com) | Assets CC0 | **Use** | More CC0 PBR materials (brushed metal, PCB, rubber, fabric). |
| [Tencent-Hunyuan/Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2) ★15k / TRELLIS ([trellis_blender](https://github.com/FishWoWater/trellis_blender)) | Custom (check) | Study/optional | Image→detailed 3D mesh with PBR textures. Needs a GPU; the route to hero objects (tires, fingers, gadgets) far beyond primitive modelling. |
| [DLR-RM/BlenderProc](https://github.com/DLR-RM/BlenderProc) ★3.8k | GPL-3.0 | Study | Mature headless-bpy pipeline patterns (loaders, lighting, camera sampling). |
| [princeton-vl/infinigen](https://github.com/princeton-vl/infinigen) ★7.4k | BSD-3 | Study | Procedural photoreal materials/geometry node recipes. |

## 3. Explainer-video agents to learn from (closest to the speedy_devv format)

| Project | License | Use / Study | Why |
|---|---|---|---|
| [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) ★76k | AGPL-3.0 | **Study** | Agentic production system with 12 pipelines and a "start from a video you already love" mode, the same idea as ours. AGPL: ideas only, no code copying into this MIT repo. |
| [Vincentwei1021/anything2explainer](https://github.com/Vincentwei1021/anything2explainer) ★3k | Custom | Study | Topic → narrated Remotion explainer: research, VO, frame-accurate timeline, storyboard, **parallel build agents per shot**, word-aligned subtitles. |
| [Vincentwei1021/video-talkcraft](https://github.com/Vincentwei1021/video-talkcraft) ★2k | Custom | Study | Voiceover-driven explainers: word-level timestamp alignment, 108 motion recipe cards, "anti-PowerPoint" shot system, triple QA gate, film-grade SFX locked to the voice. |
| [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) ★17k | Apache-2.0 | **Use/Study** | Remotion product-promo skill with a large shot library; Apache-2.0 so patterns can be adapted with attribution. |
| [vincentsch/explainroo](https://github.com/vincentsch/explainroo) ★828 | MIT | **Use/Study** | Agent-made explainers with local voice, timing and rendering; camera that follows narration (v0.4). |
| [Alisa0808/vox-director](https://github.com/Alisa0808/vox-director) ★2.6k | MIT | Study | Topic → finished Vox-style explainer, automated end to end. |
| [iart-ai/motion-skills](https://github.com/iart-ai/motion-skills) ★1.2k | MIT | **Use** | 56 motion-graphics skills incl. explainer, TikTok/Reels, WebGL/3D and kinetic-type packs. |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) ★79k | Apache-2.0 | Use (alt. renderer) | HTML→video built for agents; alternative to Remotion for caption/UI layers. |

## 4. Voice, captions, timing

| Project | License | Use / Study | Why |
|---|---|---|---|
| [m-bain/whisperX](https://github.com/m-bain/whisperX) ★25k | BSD-2 | **Use** | Word-level timestamps, so karaoke captions land on each word exactly as the references do, and transcripts of reference videos in the reverse stage. |
| [hexgrad/kokoro](https://github.com/hexgrad/kokoro) ★9.9k | Apache-2.0 | **Use** | 82M-param local TTS, far more natural than Piper and CPU-friendly. |
| [resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox) ★28k | MIT | Use | State-of-the-art open TTS with emotion/exaggeration control and voice cloning (your own voice only). |

## 5. Analysis & sound

| Project | License | Use / Study | Why |
|---|---|---|---|
| [Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect) ★5.4k | BSD-3 | **Use** | Content/adaptive/threshold detectors catch fades and morphs that ffmpeg `scdet` misses; upgrade `detect_scenes.py`. |
| [MTG/freesound-python](https://github.com/MTG/freesound-python) | MIT | Use | Search/download CC-licensed real SFX (whooshes, clicks, mechanical) instead of only synthesized ones. |
| [3b1b/manim](https://github.com/3b1b/manim) / [ManimCommunity/manim](https://github.com/ManimCommunity/manim) | MIT | Use (tier) | Math/data-viz scenes (the PCA-style reference). |

## Licensing notes for this repo (MIT)

- **Remotion** has a custom license: free for individuals and small teams, while larger
  companies need a company license. Mention this in the README.
- AGPL/GPL projects (OpenMontage, BlenderProc) and "custom" licenses: study only.
- CC0 assets (Poly Haven, ambientCG) can ship in examples freely.

## Integration status (v0.3)

| Project | Status | Where |
|---|---|---|
| Rhubarb Lip Sync | ✅ integrated (primary lip-sync) | `create-video/scripts/lipsync.py`, Nova visemes |
| claude-codes-influencers patterns | ✅ adapted (keyword triggers, double blink, bounce) | `puppet/PuppetTrack.tsx` |
| WhisperX | ✅ integrated (preferred when its models are available) | `scripts/align_words.py` |
| PocketSphinx (Rhubarb's recognizer) | ✅ integrated (offline forced alignment) | `scripts/align_words.py` |
| Kokoro-82M (kokoro-onnx) | ✅ integrated (default voice) | `scripts/tts.py` |
| Chatterbox | ⚪ documented alternative (GPU recommended) | `scripts/tts.py` docstring |
| PySceneDetect | ✅ integrated (hard cuts + soft transitions) | `reverse-video/scripts/detect_scenes.py` |
| rembg | ✅ integrated | `scripts/cutout.py` |
| Poly Haven / ambientCG | ✅ integrated (fetcher + HDRI world; gradient fallback) | `scripts/fetch_assets.py`, `blender_kit.hdri_world` |
| EL4CTEO/blender-skills | ✅ installed by `install_tools.sh`; rules applied in `blender_kit` (weighted normals, reflection strips, firefly clamp, 70–135 mm lens) | |
| mcp-for-blender | ✅ documented setup | `docs/BLENDER_MCP.md` |
| Freesound | ✅ integrated (API key; synth fallback) | `scripts/fetch_sfx.py` |
| OpenMontage, anything2explainer, video-talkcraft, vox-director | 📖 study only (license) | |
| Hunyuan3D / TRELLIS | ⚪ needs GPU; not bundled | |
| Manim, HyperFrames | ⚪ alternative renderers, not bundled | |

## Recommended integration order

1. Rhubarb in `lipsync.py` (+ map A–H/X onto Nova's visemes).
2. WhisperX word timings → per-word karaoke captions + keyword-triggered poses.
3. Kokoro TTS as the default local voice.
4. Poly Haven studio HDRI + ambientCG materials in `blender_kit`.
5. PySceneDetect in the reverse stage.
6. EL4CTEO/blender-skills alongside our craft docs; mcp-for-blender for local interactive work.
7. Study anything2explainer/video-talkcraft for the multi-shot pipeline (storyboard → parallel shot builds → QA gates) before scaling past 3-second tests.

Network note: in the cloud container used to develop this, HuggingFace, GitHub release
downloads and some media CDNs are blocked by the egress policy. Kokoro/Chatterbox weights,
Rhubarb binaries and Poly Haven assets need those hosts allowed, or a local machine.
