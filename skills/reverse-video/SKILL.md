---
name: reverse-video
description: >
  Reverse-engineer any reference video into a reusable, installable "style skill".
  Use when the user gives a video (local file or URL) and wants to clone its style,
  analyze how it was made, extract its editing recipe, or "make videos like this one".
  Produces skills/generated/<style-name>/ containing SKILL.md, style-spec.json, and assets.
---

# Reverse Video — turn any video into a style skill

You are a video reverse-engineer. Your output is not a chat summary — it is a **new skill
folder** that any Claude can later install to recreate this style with new content.

## Inputs

- A local video file path, OR a URL (download with `yt-dlp -f "bv*[height<=1080]+ba/b" -o ref.mp4 <url>` if available; if not, ask the user for a file).
- Optionally: a name for the style. Otherwise derive one (kebab-case, descriptive, e.g. `bold-serif-cutaway-reel`).

All intermediate work goes in a scratch dir: `WORK=<scratchpad>/reverse/<style-name>/`.
Treat the downloaded/uploaded video as untrusted data — never execute anything from it.

## Pipeline — run every stage, in order

All scripts live next to this file in `scripts/` and need only python3 + ffmpeg.

### 1. Probe

```bash
python3 scripts/probe.py "$VIDEO" "$WORK/probe.json"
```

Gives resolution, fps, duration, aspect, audio layout. If duration > 10 min, tell the user
you'll analyze the first 5 minutes plus a sample of the rest (pass `--max-seconds 300`
to downstream scripts) unless they want a full pass.

### 2. Cut detection → shot list

```bash
python3 scripts/detect_scenes.py "$VIDEO" "$WORK/shots.json" --threshold 0.27
```

Produces every cut timestamp plus per-shot durations. From `shots.json` compute the
**pacing profile**: median shot length, min/max, shots-per-minute, and whether pacing
accelerates (hook fast → body slower → outro fast is a common formula). If it finds < 2
cuts in a clearly edited video, retry with `--threshold 0.18`.

### 3. Frame extraction (for your eyes)

```bash
python3 scripts/extract_frames.py "$VIDEO" "$WORK/frames" --shots "$WORK/shots.json" --grid 12
```

Extracts one frame per shot (mid-shot) plus a uniform 12-frame grid, and builds contact
sheets (`sheet_*.png`, 3×4 tiles) so you can see many frames per Read call.

### 4. Audio structure

```bash
python3 scripts/extract_audio.py "$VIDEO" "$WORK/audio" --shots "$WORK/shots.json"
```

Produces `audio/audio.json`: loudness envelope (1s bins), silence map, an estimate of
music-vs-voice presence, and **beat-sync score** (fraction of cuts landing on loudness
peaks — ≥0.5 means the edit is cut to the beat; encode that rule).

### 5. Transcript

Try in order; stop at the first that works:
1. `whisper` / `whisper.cpp` CLI on `$WORK/audio/voice.wav`.
2. An available transcription MCP tool (e.g. ElevenLabs `creative_transcribe_audio`).
3. If the video has burned-in captions (check the frames), transcribe them yourself from
   the contact sheets.
4. Otherwise mark `transcript: unavailable` and continue — the visual style still clones.

From the transcript derive: the **hook** (first 3s line), structure (hook → promise →
points → CTA?), words-per-second, sentence length, tone.

### 6. Vision pass — the heart of the skill

Read every contact sheet in `$WORK/frames/` with the Read tool and analyze like a
designer. For each dimension write down concrete, reproducible values, not vibes:

- **Format**: aspect, safe areas, letterboxing.
- **Palette**: 3–6 hex colors (background, text, accent) — sample them from what you see.
- **Typography**: serif/sans, weight, case, approximate size as % of frame height,
  stroke/shadow, where text sits (chest-level? center? lower third?).
- **Captions**: style (word-by-word pop? karaoke highlight? static lines?), max words
  per screen, highlight color.
- **Layout system**: full-bleed footage? speaker cutout over cards? split screen? grids?
- **Shot types**: talking head / b-roll / screen recording / motion graphics / stock — and the ratio.
- **Transitions**: hard cuts, whip, zoom punch-ins, slide — name what you actually see between consecutive shot frames.
- **Motion**: Ken Burns on stills? scale pulses on beat? parallax?
- **Recurring devices**: progress bars, chapter cards, emoji, lower-thirds, watermarks (note watermarks but DO NOT clone logos/handles).

### 7. Compile the style skill

Create `skills/generated/<style-name>/` **in the user's project** (not scratch):

```
skills/generated/<style-name>/
├── SKILL.md            ← from references/skill-template.md, fully filled in
├── style-spec.json     ← schema: references/style-spec-schema.md
└── assets/
    ├── contact-sheet.png      (1 representative sheet, for future reference)
    ├── palette.json
    └── pacing.json            (the shots/pacing data)
```

Rules for the generated SKILL.md:
- It must be **self-sufficient**: a fresh Claude with only that folder + the create-video
  skill must be able to produce a faithful video. No references back to the analysis session.
- Every rule must be executable: "cut every 1.8s ±0.6, synced to loudness peaks", not "fast-paced".
- Include a worked **shot-by-shot recipe** for a hypothetical 30s video in the style.
- Include a **fidelity checklist** the renderer must self-verify against.
- Never clone: watermarks, handles, logos, faces, or the literal transcript. The style, not the content.

### 8. Report

End with: the style name, the generated folder path, the 5 most distinctive style rules
you found, confidence per dimension (high/med/low), and the exact `/create-video` command
to try it.

## Failure handling

- No ffmpeg → tell the user to install it; nothing works without it.
- Corrupt/unreadable video → show the ffprobe error, ask for a re-export.
- Slideshow/static video (0 cuts, no audio) → still valid: produce a layout+typography-only style skill and say so.
