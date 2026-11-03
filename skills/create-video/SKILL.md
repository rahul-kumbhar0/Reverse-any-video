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

### 4. Render — pick one path

**A. Remotion (preferred when Node 18+ available).** Scaffold from
`templates/remotion/` next to this skill: it reads `style-spec.json` + `timeline.json`
as props and already implements cards, Ken Burns, word-pop captions, scale pulses, and
safe margins. `npm i && npx remotion render Main out/video.mp4`. For anything beyond the
template, load the project's remotion skills (`remotion:remotion-best-practices`) if present.

**B. FFmpeg assembler (zero-Node fallback).**

```bash
python3 scripts/assemble.py timeline.json style-spec.json out/video.mp4 --assets assets/
```

Handles: solid/card shots, image shots with Ken Burns, drawtext headlines/captions with
safe margins, concat, VO + music mix with ducking. Cruder motion than Remotion; say so.

### 5. Verify

- Re-run the fidelity checklist against the actual render: extract 6 frames
  (`ffmpeg -i out.mp4 -vf fps=6/DUR ...`) and *look* at them. Check text inside safe
  areas, palette correct, captions ≤ max words.
- `ffprobe` the output: duration within ±5% of target, correct resolution/fps.
- Report what passed/failed; fix and re-render on failure (max 2 retries, then report).

### 6. Deliver

Give the user: the MP4 path, the script, timeline.json (so they can tweak), and the
checklist results. Offer variations (different hook, length, aspect).
