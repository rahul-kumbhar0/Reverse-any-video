---
name: create-video
description: >
  Generate a new video in a previously reverse-engineered style. Use when the user asks
  to "make a video in <style> about <topic>" or invokes /create-video. Consumes a style
  skill from skills/generated/<style-name>/ (SKILL.md + style-spec.json) and renders
  with Remotion (preferred) or the bundled FFmpeg assembler.
---

# Create Video — render new content in a cloned style

## Inputs

1. **Style**: a folder `skills/generated/<style-name>/`. Read its `SKILL.md` fully and
   load `style-spec.json`. If the user names no style, list the folders under
   `skills/generated/` and ask which one.
2. **Brief**: topic, target duration, platform, any assets (logo, footage, product shots).

## Workflow

### 1. Write the script

Follow the style's `script_formula` exactly: hook formula, structure, sentence style,
words-per-second budget (duration × wps = word budget — respect it), CTA. Show the user
the script **before** rendering anything and incorporate feedback.

### 2. Build the timeline (`timeline.json`)

Expand the script into shots using the style's pacing numbers. Schema:

```jsonc
{
  "style": "<style-name>",
  "fps": 30, "width": 1080, "height": 1920,
  "shots": [
    {
      "start": 0.0, "duration": 1.8,
      "visual": { "type": "card",            // card | image | video | solid | cutout
                  "src": null,                // for image/video
                  "bg": "#0E0E10",
                  "kenburns": { "zoom": 1.06, "pan": "up" } },
      "text": { "content": "THE HOOK LINE", "role": "headline", // headline|caption|chapter
                "highlight_words": [1] },
      "sfx": "whoosh"                         // optional
    }
  ],
  "voiceover": { "script": "…full VO text…", "wps": 2.9 },
  "music": { "bpm": 110, "duck_db": -12 }
}
```

Every timeline must pass the style's **fidelity checklist** on paper before rendering.

### 3. Gather assets

- Images/b-roll: use what the user provided; otherwise generate via an available image
  MCP tool, or use solid cards in the style palette. Never scrape copyrighted footage.
- Voiceover: user recording > TTS MCP tool (e.g. ElevenLabs) > render silent with
  captions (word timing from wps) and say so.
- Music: user-provided only; otherwise render without and note where the beat grid is.

### 4. Render — tiered, mix tiers per shot

Read `../reverse-video/references/3d-motion-playbook.md` §7 first. The pro pipeline is
"Blender renders + After Effects compositing"; ours is Blender/gen-video shots composited
inside Remotion. Pick per shot, by the spec's `scene_3d.renderer_tier`:

**Tier 1 — Blender photoreal** (hero 3D shots: products, machinery, macro objects).
`pip install bpy` (works headless, CPU Cycles). Write a shot-spec JSON and:

```bash
python3 scripts/blender_shot.py shot.json out/shot01.mp4 --fps-render 15 --samples 48 --scale 0.5
```

It builds PBR materials, the studio light rig, eased camera keyframes, DOF, then
motion-interpolates to target fps. ~15–25s/frame CPU — budget 2–5 hero shots per video.
Follow the playbook's lighting grammar exactly (soft key + warm rim + cool fill + AgX).

**Tier 2 — Three.js in Remotion** (the 3D workhorse: anything 3D that must sync with
captions per-frame). `npm i three @remotion/three "@react-three/fiber@^8"` (fiber 8 for
React 18) and render with `--gl=swangle` (required headless). Use rect-area + spot
lights, `THREE.ACESFilmicToneMapping`, instanced meshes for particles.

**Tier 3 — Generative-video MCP** (photoreal b-roll impractical to model): if the
session has a video-generation tool (Gemini/Veo-class), generate the clip and composite.
Tell the user which shots are AI footage.

**Tier 4 — DOM/CSS in Remotion**: flat UI mockups, captions, mascots, charts. Scaffold
from `templates/remotion/`.

**Tier 5 — FFmpeg assembler (zero-dependency floor).**

```bash
python3 scripts/assemble.py timeline.json style-spec.json out/video.mp4 --assets assets/
```

Composite: render Tier 1–3 shots to MP4 first, then place them in the Remotion timeline
as `<OffthreadVideo>` layers with captions/mascot on top.

### 4b. Sound design (never ship silent-by-default)

Follow the spec's `sfx.grammar`. Synthesize the effects locally:

```bash
python3 scripts/synth_sfx.py all sfx/        # whoosh, tap, click, pop, impact, riser, shimmer
```

Place each per the grammar (whoosh at every morph start, tap on UI touches, riser into
the reveal). VO: user recording > TTS MCP tool > silent with a note. Mix in Remotion
(`<Audio>` with `volume`) or with the assembler's `--vo/--music`; keep bed −20 to −26dB
under VO. End with ≥0.5s of tail silence.

### 5. Verify

- Re-run the fidelity checklist against the actual render: extract 6 frames
  (`ffmpeg -i out.mp4 -vf fps=6/DUR ...`) and *look* at them. Check text inside safe
  areas, palette correct, captions ≤ max words.
- `ffprobe` the output: duration within ±5% of target, correct resolution/fps.
- Report what passed/failed; fix and re-render on failure (max 2 retries, then report).

### 6. Deliver

Give the user: the MP4 path, the script, timeline.json (so they can tweak), and the
checklist results. Offer variations (different hook, length, aspect).
