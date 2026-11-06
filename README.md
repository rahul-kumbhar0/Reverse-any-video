# 🎬 Reverse Any Video

**Point Claude at any video. Get back a reusable "style skill" that can create unlimited new videos in that exact style.**

Reverse Any Video is an open-source Claude Code plugin that turns Claude into a **video reverse-engineer**. Give it a reference video (a TikTok edit, a YouTube explainer, a motion-graphics ad, a talking-head reel) and it:

1. **Deconstructs** the video — cuts, pacing, typography, color palette, caption style, motion patterns, audio structure, hook formula.
2. **Compiles** everything into a portable **Style Skill** (`SKILL.md` + machine-readable `style-spec.json`) that any Claude session can install.
3. **Recreates** — uses that skill to generate brand-new videos with your content, in the cloned style, rendered with Remotion or FFmpeg.

```
 reference.mp4 ──▶ /reverse-video ──▶ skills/generated/<style-name>/
                                          ├── SKILL.md          (recreation recipe)
                                          ├── style-spec.json   (machine-readable DNA)
                                          └── assets/           (palettes, fonts, frames)

 "make a video about X" ──▶ /create-video <style-name> ──▶ new-video.mp4
```

## Install

### As a Claude Code plugin (recommended)

```bash
claude plugin marketplace add rahul-kumbhar0/Reverse-any-video
```

```bash
claude plugin install reverse-any-video
```

Or from inside Claude Code: `/plugin marketplace add rahul-kumbhar0/Reverse-any-video` then `/plugin install reverse-any-video`.

### As plain skills

Copy `skills/reverse-video` and `skills/create-video` into your project's `.claude/skills/` directory.

## Requirements

- **ffmpeg / ffprobe** (required) — all frame, scene, audio, and motion extraction.
- **Python 3.9+** (required) — analysis scripts, stdlib only (numpy for SFX detection).
- **Node 18+ / Remotion + Three.js** (recommended) — captions/compositing + real-time 3D (`--gl=swangle` headless).
- **Blender via `pip install bpy`** (recommended) — photoreal 3D hero shots, headless CPU Cycles.
- **yt-dlp** (optional) — ingest videos by URL instead of local file.
- **whisper / whisper.cpp** (optional) — local transcription; Claude falls back to an available transcription MCP tool or frame-level caption OCR.

### One-command tool install

```bash
bash scripts/install_tools.sh
```

Installs and wires: Rhubarb Lip Sync, Kokoro-82M TTS, PocketSphinx word alignment (WhisperX
optional), PySceneDetect, rembg, Blender (`bpy`), the EL4CTEO Blender agent skills, and a
Poly Haven studio HDRI. Optional: `FREESOUND_API_KEY` for real CC0 sound effects, and a live
Blender via MCP (`docs/BLENDER_MCP.md`). Credits and licenses: `docs/ECOSYSTEM.md`.

> **Remotion license:** free for individuals and small teams; larger companies need a
> Remotion company license (remotion.dev/license).

## Usage

### 1. Reverse-engineer a video

```
/reverse-video path/to/reference.mp4
/reverse-video https://www.youtube.com/watch?v=...   (needs yt-dlp)
```

Claude runs the full analysis pipeline, *looks at* extracted frames with its vision, and writes a new style skill into `skills/generated/<style-name>/`.

### 2. Create new videos in that style

```
/create-video <style-name> "90-second explainer about our new pricing"
```

Claude loads the generated style skill, writes a script and shot list that obey the style's pacing/typography/palette rules, renders with Remotion (or assembles with FFmpeg), and hands you the MP4.

### No reference video? Create from an archetype

`/create-video` no longer requires a reverse-engineered style. Twelve built-in archetypes
(`skills/create-video/references/video-archetypes.md`) cover the whole map — explainer
reels, screencast tutorials, talking-head edits, product ads, kinetic typography,
photo montages, long-form documentary chapters, beat-synced music edits, trailers,
data stories, UGC-style posts, whiteboard explainers — each with pacing, structure, and
audio grammar, in any aspect (9:16, 16:9, 1:1, 4:5, 21:9):

```
/create-video product-ad "30s promo for our standing desk" 1:1
```

### Edit your own footage

Hand it raw footage and it edits like a cutter: `scripts/edit_footage.py` scene-scans the
material into a clip inventory, extracts the best takes for the timeline, or auto-cuts a
beat-synced montage to your track (`beatcut --bpm 110`). The FFmpeg assembler supports
xfade transitions, trim/speed ramps, fit modes (cover/contain/blurred-pad), source-audio
passthrough, and auto-placed SFX — so talking-head cuts, highlight reels, and slideshows
work with zero Node dependencies.

### 3. Ship the style to your team

A generated style skill is a self-contained folder — commit it, or publish it so anyone can `npx skills add` it. Your whole team gets the style.

## How the analysis works

| Stage | Tool | What it extracts |
|---|---|---|
| Probe | `ffprobe` | resolution, fps, duration, codecs, bitrate, rotation |
| Cut detection | `ffmpeg scdet` | every hard cut → shot list with per-shot duration → pacing curve |
| Frame sampling | `ffmpeg` | keyframe per shot + uniform grid, as contact sheets for Claude's vision |
| Motion strips | `ffmpeg tile` | 8-frame bursts → camera moves, easing curves, morphs vs cuts |
| Audio | `ffmpeg` + loudness filters | music vs. voice segments, loudness envelope, beat-synced cut check |
| SFX map | FFT onset detection | every whoosh/tap/impact/riser, matched to visual events |
| Transcript | whisper / MCP / OCR fallback | spoken script, hook line, CTA, words-per-second |
| Vision pass | **Claude itself** | typography, palette, layout, captions, **3D lighting rig, materials, camera grammar** |

And recreation is tiered like a real studio pipeline (see
[`skills/reverse-video/references/3d-motion-playbook.md`](skills/reverse-video/references/3d-motion-playbook.md)):
**Blender/Cycles** (headless `bpy`) renders photoreal hero shots from declarative scene
specs — PBR materials, studio light rigs with `aim_at`, eased camera keyframes, DOF —
**Three.js in Remotion** handles 3D that syncs with captions per-frame, generative-video
MCP tools cover un-modelable b-roll, DOM/CSS covers UI mockups, and synthesized SFX
(whoosh/tap/impact/riser, no sample packs) are placed by the extracted sound grammar.

The vision pass is the heart of it: Claude reads the extracted frames like a designer, not a signal processor — it names the font *vibe*, the layout grid, the caption placement, the hook formula — and encodes all of it in `style-spec.json` (schema in [`skills/reverse-video/references/style-spec-schema.md`](skills/reverse-video/references/style-spec-schema.md)).

## What's in this repo

```
.claude-plugin/        plugin + marketplace manifests
commands/              /reverse-video and /create-video slash commands
agents/                video-reverse-engineer and video-director subagents
skills/reverse-video/  the analysis skill (+ Python/ffmpeg pipeline scripts)
skills/create-video/   the generation skill (+ Remotion template, ffmpeg assembler)
docs/ARCHITECTURE.md   full pipeline design
```

## Ethics & legal

This tool clones **style** (pacing, typography, structure), not **content**. Don't use it to re-upload someone's actual video, impersonate a creator, or violate a platform's ToS. Styles themselves are generally not copyrightable, but specific footage, music, logos, and likenesses are — bring your own.

## License

MIT — see [LICENSE](LICENSE). Contributions welcome.
