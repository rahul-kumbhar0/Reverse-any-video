# style-spec.json — the machine-readable DNA of a video style

Every generated style skill ships a `style-spec.json` following this shape. All fields
required unless marked optional; use `null` + a `confidence` of `"low"` when the
reference didn't expose a dimension. Add fields freely — renderers must ignore unknowns.

```jsonc
{
  "spec_version": 1,
  "name": "bold-serif-cutaway-reel",          // kebab-case, matches folder name
  "summary": "One-sentence description of the style.",
  "source": {
    "duration_s": 42.5,
    "analyzed_at": "2026-11-03",
    "notes": "Public reel; style only, no content cloned."
  },

  "format": {
    "width": 1080, "height": 1920, "fps": 30,
    "orientation": "vertical",                 // vertical | horizontal | square
    "safe_margins_pct": { "top": 12, "bottom": 18, "sides": 6 }
  },

  "pacing": {
    "median_shot_s": 1.8,
    "shot_s_range": [0.6, 4.2],
    "cuts_per_minute": 33,
    "curve": "fast-hook-then-steady",          // free text, but concrete
    "beat_synced": true,                       // cuts land on audio peaks
    "hook_max_s": 3.0                          // how fast the hook lands
  },

  "palette": {
    "background": "#0E0E10",
    "text_primary": "#F5F1E8",
    "accent": "#E8C547",
    "extra": ["#2E86AB"],
    "mood": "high-contrast dark with warm accent"
  },

  "typography": {
    "family_vibe": "high-contrast serif (Playfair/Canela-like)",
    "fallback_stack": "Playfair Display, Georgia, serif",
    "case": "UPPERCASE",                       // UPPERCASE | Title | Sentence | mixed
    "weight": 700,
    "headline_size_pct_h": 7.5,                // % of frame height
    "effects": ["soft drop shadow", "tight letter-spacing"]
  },

  "captions": {
    "present": true,
    "style": "word-pop",                       // word-pop | karaoke | static-lines | none
    "max_words_per_screen": 4,
    "position": "chest",                       // chest | center | lower-third | top
    "highlight": { "mode": "color", "value": "#E8C547" },
    "container": "none"                        // none | pill | box | glass-panel
  },

  "layout": {
    "system": "speaker-cutout-over-cards",     // full-bleed | split | grid-2x2 | cutout | panel
    "description": "Speaker cut out bottom-center; full-color card fills frame behind on key lines.",
    "recurring_devices": ["chapter title card every ~10s", "progress bar top"]
  },

  "shots": {
    "types_ratio": { "talking_head": 0.55, "broll": 0.25, "motion_graphics": 0.20 },
    "camera": "static close-up with digital punch-ins",
    "transitions": ["hard cut", "scale punch-in on emphasis"]
  },

  "motion": {
    "idle": "slow 3%/s Ken Burns on stills",
    "on_beat": "4% scale pulse, 120ms",
    "text_in": "pop: scale 0.9→1.0 + fade, 150ms ease-out",
    "text_out": "hard cut"
  },

  "audio": {
    "voiceover": true,
    "music": "driving, ~100-120bpm, ducked -12dB under VO",
    "words_per_second": 2.9,
    "sfx": ["whoosh on card transitions"]       // optional
  },

  "script_formula": {
    "hook": "Bold contrarian claim in first 2s, text mirrors VO",
    "structure": ["hook", "promise", "3 points w/ visual per point", "CTA"],
    "sentence_style": "short, punchy, 2nd person",
    "cta": "soft follow-CTA, final 3s"
  },

  "confidence": {                               // per top-level section
    "pacing": "high", "palette": "high", "typography": "medium",
    "captions": "high", "layout": "high", "motion": "medium",
    "audio": "medium", "script_formula": "high"
  },

  "renderer_hints": {                           // optional
    "preferred": "remotion",                    // remotion | ffmpeg | any
    "remotion_notes": "cutout via @remotion/layout-utils + background cards",
    "ffmpeg_notes": "drawtext with fontfile; cards as color sources"
  }
}
```

## Rules

- **Concrete numbers over adjectives.** A renderer must be able to act without judgment calls.
- **Never include** source watermarks, handles, logos, names, faces, or transcript text.
- Hex colors sampled from real frames; sizes as % of frame height so the spec is resolution-independent.
