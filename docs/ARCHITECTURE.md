# Architecture

## The idea

Most "AI video" tools generate pixels. Reverse Any Video generates **recipes**. A video's
identity lives in reproducible decisions — pacing, typography, palette, caption behavior,
layout, motion, script formula — and those decisions can be extracted once and replayed
forever with new content. The unit of exchange is a **style skill**: a plain folder that
any Claude can read.

```
            ┌──────────────────────── reverse-video skill ───────────────────────┐
            │                                                                     │
 video ──▶  │ ffprobe ─▶ scdet cuts ─▶ frames+sheets ─▶ audio env ─▶ transcript   │
            │                      └────────────┬────────────┘                    │
            │                         Claude vision + synthesis                   │
            └────────────────────────────────── │ ────────────────────────────────┘
                                                ▼
                              skills/generated/<style>/          ◀── the product
                              ├── SKILL.md        (human/Claude recipe)
                              ├── style-spec.json (machine-readable DNA)
                              └── assets/         (palette, pacing, 1 contact sheet)
                                                │
            ┌──────────────────────── create-video skill ─────────┴───────────────┐
            │ script (formula) ─▶ timeline.json (pacing) ─▶ render ─▶ verify loop  │
            │                              Remotion ◀─or─▶ ffmpeg assembler        │
            └──────────────────────────────────────────────────────────────────────┘
```

## Design decisions

**Deterministic extraction, model-based interpretation.** Scripts (stdlib Python + ffmpeg)
do everything measurable: cuts, durations, loudness, beat-sync, frame sampling. Claude does
only what needs eyes and judgment: typography, palette, layout, devices, formula. This
keeps the expensive/vision part small and the measurable part reproducible.

**Contact sheets, not frame floods.** 12 frames per PNG means a 40-shot video is ~4 Read
calls, not 40 — cheaper, and side-by-side tiles make transitions and recurring devices
visible in a way single frames aren't.

**Two renderers.** Remotion gives real motion design (springs, word-pop captions,
per-frame control) and is preferred. The FFmpeg assembler (`assemble.py`) is the
zero-dependency floor: any machine with python3+ffmpeg can render a timeline, just with
cruder motion. Both consume the same `timeline.json` + `style-spec.json`, so a timeline
is renderer-portable.

**Resolution-independent specs.** Sizes are % of frame height, positions are named zones,
margins are %, so one spec renders at 1080×1920 or 4K alike.

**Verification is part of rendering.** The generated skill ships a fidelity checklist;
create-video extracts frames from its own output and visually checks them against it.
Style cloning without a feedback loop drifts.

**Style, not content.** The analyzer is instructed (three times, deliberately) never to
carry watermarks, handles, logos, faces, or transcript text into the generated skill.
What transfers is the grammar, not the sentences.

## Extending

- **New analysis dimension** → add a script in `skills/reverse-video/scripts/`, a section
  in the SKILL.md pipeline, and a field in the spec schema (renderers ignore unknowns).
- **New layout system** → add a component to the Remotion template and a `layout.system`
  enum value.
- **Transcription/TTS/image backends** are deliberately pluggable: the skills try local
  CLIs first, then whatever MCP tools the session has, then degrade gracefully.

## Repo layout

| Path | Purpose |
|---|---|
| `.claude-plugin/` | plugin + marketplace manifests (`claude plugin install`-able) |
| `commands/` | `/reverse-video`, `/create-video` |
| `agents/` | `video-reverse-engineer`, `video-director` subagents |
| `skills/reverse-video/` | analysis skill, pipeline scripts, spec schema, skill template |
| `skills/create-video/` | generation skill, ffmpeg assembler, Remotion template |
| `skills/generated/` | (created at runtime) your reverse-engineered styles |
