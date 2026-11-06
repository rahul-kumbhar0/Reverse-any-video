---
name: create-video
description: >
  Create any video: a new video in a previously reverse-engineered style, a video from
  scratch via built-in archetypes (explainer, tutorial, ad, montage, documentary, trailer,
  kinetic typography, …), or an edit of the user's raw footage (scene scan, best takes,
  beat-synced cuts). Use when the user asks to "make a video", "edit my footage", or
  invokes /create-video. Renders with Remotion (preferred) or the bundled FFmpeg assembler
  in any aspect (9:16, 16:9, 1:1, 4:5, 21:9).
---

# Create Video — render any video

## Inputs

1. **Style — three ways to get one, in order of preference:**
   - **Generated style**: a folder `skills/generated/<style-name>/`. Read its `SKILL.md`
     fully and load `style-spec.json`.
   - **Built-in archetype**: no suitable generated style? Pick one from
     `references/video-archetypes.md` (explainer-reel, tutorial-screencast, talking-head,
     product-ad, kinetic-typography, slideshow-montage, documentary-chapter,
     music-beat-edit, trailer-teaser, data-story, ugc-style, whiteboard-sketch) and
     synthesize a `style-spec.json` from its numbers. Never refuse for lack of a
     reference video.
   - **Reference on the spot**: the user supplied a reference video with their request?
     Run `/reverse-video` first, then use the result.
2. **Brief**: topic, target duration, platform, any assets (logo, footage, product shots).
3. **Format**: resolve the aspect/resolution/fps from the brief's platform using the
   preset table in `references/video-archetypes.md`; set `"aspect"` in timeline.json.
   Default 9:16 for social briefs, 16:9 for long-form/tutorial briefs.

## Mode B — editing real footage

When the user hands you raw footage (talking-head takes, event clips, screen recordings,
phone videos), the pipeline starts with `scripts/edit_footage.py`:

```bash
python3 scripts/edit_footage.py scan raw.mp4 clips.json --threshold 0.3 --min-dur 0.6
python3 scripts/edit_footage.py cut raw.mp4 clips.json clips/ --ids 0,3,5
python3 scripts/edit_footage.py beatcut raw.mp4 clips.json out.mp4 --bpm 110 --target 30 --music track.mp3
```

- **scan** → clips.json (one entry per continuous take). Extract a contact sheet of one
  frame per clip (`ffmpeg -ss <mid> -frames:v 1`) and **look** at it to choose takes.
- **cut** → frame-accurate MP4s to drop into the timeline as `video` shots (trim further
  with `trim_start`, tighten with `speed`, keep the spoken audio with `keep_audio: true`).
- **beatcut** → a finished rhythm edit on a beat grid (music-video / highlight mode).

A talking-head edit = A-roll shots with `keep_audio: true` + muted b-roll shots punched
in on top, captions from `align_words.py` against the extracted speech.

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
  "fps": 30, "aspect": "9:16",               // or explicit "width"/"height"
  "shots": [
    {
      "start": 0.0, "duration": 1.8,
      "transition": { "type": "fade", "duration": 0.3 },  // INTO this shot; any ffmpeg
                                              // xfade name: fade, dissolve, slideleft,
                                              // circleopen, zoomin, fadeblack, wipeup…
      "visual": { "type": "card",             // card | image | video | solid | cutout
                  "src": null,                // for image/video
                  "bg": "#0E0E10",
                  "trim_start": 12.5,         // video: seek into source (s)
                  "speed": 1.0,               // video: 0.5–2.0 speed ramp
                  "fit": "cover",             // cover | contain | blur (blurred pad)
                  "keep_audio": false,        // video: carry source audio into the mix
                  "kenburns": { "zoom": 1.06, "pan": "up" } },
      "text": { "content": "THE HOOK LINE", "role": "headline", // headline|caption|chapter
                "highlight_words": [1],
                "box": false },               // true = caption plate behind text
      // or several layers: "texts": [{...}, {...}]
      "sfx": "whoosh"                         // auto-placed from <assets>/sfx/<name>.wav
    }
  ],
  "voiceover": { "script": "…full VO text…", "wps": 2.9, "offset": 0 },
  "music": { "bpm": 110, "duck_db": -12, "loop": true, "fade_out": 1.0 }
}
```

Transitions overlap the previous shot's tail (total = Σ durations − Σ transition
durations) — budget shot durations accordingly. Jump-cut styles (ugc, tutorial) simply
omit `transition`.

Every timeline must pass the style's **fidelity checklist** on paper before rendering.

### 3. Gather assets

- Images/b-roll: use what the user provided; otherwise generate via an available image
  MCP tool, or use solid cards in the style palette. Never scrape copyrighted footage.
- Voiceover: user recording > TTS MCP tool (e.g. ElevenLabs) > render silent with
  captions (word timing from wps) and say so.
- Music: user-provided only; otherwise render without and note where the beat grid is.

### 4. Render — tiered, mix tiers per shot

**Before any 3D work read `references/blender-craft.md` and `references/threejs-craft.md`**
and follow their workflow: study reference motion strips → model → verify with 2 stills →
(optional) Three.js motion preview → full render → frame-verify. **New styles/topics are
tested as a 3-second clip first**; only scale to full length once the 3s test passes.

For Blender, write a scene script against `scripts/blender_kit.py` (bevelled
`rounded_slab`, material presets, `studio_rig`, eased `key_loc`, emission ramps,
`dust_field`, `anchor` + `export_anchors` for 3D-tracked labels, `render`). Worked example:
`examples/touchpad-exploded/scene_touchpad.py`. `blender_shot.py` (JSON specs) remains for
simple primitive shots.

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

**Tier 5 — FFmpeg assembler (zero-dependency floor).** Handles cards, images
(Ken Burns), trimmed/speed-ramped video clips with fit modes, xfade transitions,
multi-layer text, SFX auto-placement, source-audio passthrough, looping/ducked/faded
music — enough to ship montages, slideshows, UGC edits and talking-head cuts without
Node at all.

```bash
python3 scripts/assemble.py timeline.json style-spec.json out/video.mp4 \
    --assets assets/ --vo vo.wav --music bed.mp3        # SFX from assets/sfx/<name>.wav
```

Composite: render Tier 1–3 shots to MP4 first, then place them in the Remotion timeline
as `<OffthreadVideo>` layers with captions/mascot on top.

### 3b. Voice, word timing, lip-sync (run in this order, from the FINAL script)

```bash
python3 scripts/tts.py "<script>" vo.wav --voice am_puck          # Kokoro-82M (Piper fallback;
                                                                   #  or ElevenLabs MCP for premium)
python3 scripts/align_words.py vo.wav "<script>" words.json --offset <vo start s>
                                                                   # WhisperX > PocketSphinx > proportional
python3 scripts/lipsync.py vo.wav lipsync.json --dialog "<script>" --offset <vo start s> --duration <len>
                                                                   # Rhubarb (A-H,X) > heuristic
```
`words.json` drives `<KaraokeCaption>` (words fade in exactly when spoken; key word in the
selection box) and keyword-triggered poses in `<PuppetTrack triggers=...>`.
Install everything with `scripts/install_tools.sh` (repo root).

### 3c. Full-length videos (after a 3 s test passes)

Proven on `examples/pressure-cooker` (45 s, 5 ray-traced shots + 2 graphics scenes):

1. **Script as JSON lines** `{id, text, gap}`; generate TTS **per sentence**, trim silence,
   concatenate with the gaps → exact sentence start/end times (`script_timed.json`).
   Any language/accent: Kokoro `hm_omega`/`hf_beta` give Indian-English narration
   (English text, Hindi voice); ElevenLabs MCP for premium voices.
2. **Align words per sentence** (cut each sentence, `align_words.py --offset start`) —
   robust for accents and long VO. Rhubarb lip-sync on the full VO with the full script.
3. **Shot plan from the sentence times**: one visual idea per 1–3 sentences; use cheap
   motion-graphics scenes (gauges, counters, cards over a blurred frame of the previous
   shot) for numbers/evidence, ray-traced shots for objects and mechanisms.
4. **One scene script, many shots** (`--shot hero|cutaway|...`): shared model, per-shot
   camera + animation. Cutaways = boolean DIFFERENCE + solidified walls.
5. **Verify every shot with a still** (scale 0.3, 16 samples) before the long render;
   steam/smoke = many small low-alpha (≈0.13) emissive puffs, never a few big ones.
6. **Render budget**: 6 fps for slow camera shots, 8 fps for particle/steam shots,
   scale 0.4, 24 samples → ≈7 s/frame on 4 CPU cores, motion-interpolated to 30 fps.
7. **Composite**: push-crossfades (0.3 s, scale 1.05→1) between shots, tracked labels per
   shot (anchor JSON times are shot-local), captions chunked ≤4 words at sentence ends and
   pauses with spoken numbers merged ("one hundred and twenty degrees" → **120°C**), pose
   cue per sentence + keyword triggers, synthesized SFX timed to sentence/word times.

### 4a. Presenter puppet

If the style has a presenter, read `references/character-craft.md`: generate visemes with
`scripts/lipsync.py` from the final VO, cue poses on caption beats, render with
`<PuppetTrack>` (original character only — never the reference creator's mascot).

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
