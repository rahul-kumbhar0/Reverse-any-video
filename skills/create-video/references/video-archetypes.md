# Video archetypes — create any video without a reference

When the user asks for a video and **no generated style exists** (nothing suitable under
`skills/generated/`), don't refuse and don't demand a reference video. Pick the closest
archetype below, synthesize a `style-spec.json` from its numbers (same schema as
reverse-engineered specs — see `../../reverse-video/references/style-spec-schema.md`),
confirm the one-line plan with the user, and run the normal create-video workflow.

Every archetype lists: format, pacing, structure, typography/palette direction, render
tiers, and audio grammar. Treat the numbers as defaults, not laws — the brief wins.

## Platform presets

| Platform | Aspect | Resolution | fps | Length sweet spot |
|---|---|---|---|---|
| TikTok / Reels / Shorts | 9:16 | 1080×1920 | 30 | 15–60 s |
| YouTube long-form | 16:9 | 1920×1080 | 30 (24 for cinematic) | 3–15 min |
| Square feed / ads | 1:1 | 1080×1080 | 30 | 15–30 s |
| Portrait feed (IG/LinkedIn) | 4:5 | 1080×1350 | 30 | 15–60 s |
| Cinematic / trailer | 21:9 or 16:9 letterboxed | 2520×1080 | 24 | 30–90 s |

Set `"aspect"` in timeline.json (`"9:16" | "16:9" | "1:1" | "4:5" | "21:9"`); the
assembler maps it to the resolution above.

## The archetypes

### 1. `explainer-reel` — short vertical explainer
The repo's native genre. Hook ≤2 s → 3–5 chapters → CTA. Cut every 1.5–3 s, karaoke
captions, headline cards, whoosh/tap SFX grammar. Tiers 1/2/4. Energetic VO at 2.7–3.0 wps.

### 2. `tutorial-screencast` — software / how-to walkthrough
16:9, long-form friendly. Structure: what-you'll-build → numbered steps → recap. Screen
recordings are `video` shots (`fit: "cover"`, `keep_audio` off, VO over); zoom into UI
regions by pre-cropping with ffmpeg or Ken Burns on screenshots. Cut on step boundaries
(5–15 s shots — slow pacing is correct here). Lower-third step captions, chapter cards
between steps. Tier 4 + real footage. Calm VO ~2.3 wps, no music or −26 dB ambient bed.

### 3. `talking-head` — presenter-led piece
User footage of a person talking (or the puppet presenter for faceless). Flow: `scan`
the footage, pick the best takes, cut dead air (clips < min-dur vanish on scan), chest
captions ≤4 words. B-roll `video`/`image` shots punch in every 8–15 s over the continuous
VO (`keep_audio: true` on the A-roll, muted b-roll on top as separate shots). 9:16 or 16:9.

### 4. `product-ad` — 15–30 s promo
Hook on product beauty shot (Tier 1 Blender or user footage), 3 benefit beats, price/CTA
card. Cut every 1–2 s, `zoomin`/`circleopen` transitions, riser into the reveal, impact on
logo. Bold uppercase headlines, brand palette from the user's assets. 9:16 + 1:1 deliverables.

### 5. `kinetic-typography` — text IS the video
No footage needed at all: solid/card shots, one phrase per shot timed to the VO words
(`align_words.py` gives exact times), alternating scale/position, high-contrast two-color
palette, tap SFX per word cluster, beat-locked cuts. Remotion (Tier 4) for real motion;
assembler cards as the floor. Great for quotes, lyrics, manifestos.

### 6. `slideshow-montage` — photos/clips + music
User images/clips → `image` shots with alternating Ken Burns pans (`zoom` 1.04–1.08,
alternate `pan`), 2.5–4 s each, `fade`/`dissolve` transitions (0.5–0.8 s), music-led
(no VO or minimal), text only on first and last shot. Weddings, travel, year-in-review,
real-estate. Any aspect.

### 7. `documentary-chapter` — long-form 16:9 narrative
Chapters of 60–120 s, each: chapter card → interview/VO bed → b-roll sequence →
breather shot. Slow cuts (4–8 s), `fadeblack` between chapters, lower-third captions
only for names/places, music beds swapped per chapter, −24 dB under VO. Combine
`edit_footage.py` (real footage) + Tier 1/3 for reconstructions. Script first as a
chaptered outline; render chapter-by-chapter and concat — never one giant timeline.

### 8. `music-beat-edit` — montage cut to music
`edit_footage.py beatcut` is the engine: scan footage, cut on the beat grid
(`--bpm`, `--beat-every`), lay the track under it. Add text hooks on downbeat shots
afterward by using the beatcut output as a single `video` shot under card overlays, or
rebuild as a timeline with each beat slice as a `video` shot (gives transitions/captions
per slice). Sports highlights, gym edits, event recaps, car edits.

### 9. `trailer-teaser` — tension and reveal
24 fps, letterboxed or 21:9. Three acts: whispers (slow, 4–6 s shots, fadeblack) →
escalation (accelerating cuts 2 s → 0.5 s, riser) → title card + button SFX ending on
silence. Massive serif/display type, desaturated palette + one accent. Works for products,
events, course launches. Tiers 1/3 + typography cards.

### 10. `data-story` — numbers made visceral
One claim per shot; counters, gauges, bar reveals (Tier 4 Remotion; `blender_kit`
emission ramps for 3D gauges). Every number spoken is shown as a merged numeral card
("one hundred twenty" → **120**). Palette: dark bg, one data color, one alarm color.
Pair every stat with a physical comparison shot. 30–90 s.

### 11. `ugc-style` — faux-casual vertical
Looks handheld and native: user footage with `fit: "blur"` padding when sources are
mixed-aspect, jump cuts (no transitions), chest captions with `box: true`, emoji allowed,
speed ramps (`speed: 1.15–1.3`) to tighten takes. Hook is a spoken question in the first
second. Keep imperfections — this archetype fails when it looks produced.

### 12. `whiteboard-sketch` — explainer with drawn feel
Light bg, dark strokes. Assets: generate line-art images (image MCP tool, "white
background marker sketch" prompts), reveal with Ken Burns or Remotion wipe-on masks,
handwriting-style font if available. 2–4 s per drawing, tap/pop SFX on each reveal,
friendly VO ~2.5 wps. Education, onboarding, process docs.

## Choosing

| The brief says… | Archetype |
|---|---|
| "explain X" (short, social) | explainer-reel |
| "show how to use / install / build X" | tutorial-screencast |
| "here's my raw clip of me talking" | talking-head |
| "promote / sell X" | product-ad |
| "this quote/lyrics/announcement as a video" | kinetic-typography |
| "make something from these photos" | slideshow-montage |
| "the full story of X" (minutes) | documentary-chapter |
| "edit my footage to this song / make it hype" | music-beat-edit |
| "tease X / build hype" | trailer-teaser |
| "make these numbers land" | data-story |
| "make it feel native / not like an ad" | ugc-style |
| "explain X simply / for onboarding" | whiteboard-sketch |

If two fit, say which you picked and why in one line. If none fit, blend the two nearest
and note the blend in the spec's `meta.notes`. After a successful render, offer to save
the synthesized spec under `skills/generated/<name>/` so the style becomes reusable —
that folder is the same artifact `/reverse-video` would have produced.
