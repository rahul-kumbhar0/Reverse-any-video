# Character craft — presenter puppets the way pro explainer channels do it

## What the reference mascots actually are (from frame-by-frame study)

Top explainer reels use a **2D cel-shaded illustrated puppet**, not a 3D character:
- **Lip-sync**: inside one pose, the mouth changes every ~2 frames between viseme shapes
  (closed, open, wide, round, smile) driven by the voiceover — Character-Animator style.
- **Pose swaps, not animation**: arm/hand poses come from a library (point up, wave, shrug,
  hands-on-head, thumbs-up, chin-think, presenting…) and switch on caption beats with a
  **2–3 frame crossfade** (the ghosting is visible frame-by-frame).
- **Life between swaps**: slow head drift/tilt, nods on stressed words, blinks every 2–4 s,
  brow expression per pose.
- **Placement**: bottom-centre, cropped at the waist, ~22–25% of frame height, always in
  front of the 3D stage.

## Our implementation

- `templates/remotion/src/puppet/Nova.tsx` — original character "Nova" (curly hair, round
  amber glasses, navy hoodie, orange stripe). Layers: torso, hood/drawstrings, neck, head
  (hair back/front, ears, face shading, blush, nose), brows ×4, eyes with 3 blink states,
  glasses with glints, 7 visemes, 2 arms × 11 poses with 6 hand shapes. Outlines are a
  dark under-stroke; shading is one shadow tone + one highlight (cel look).
- `templates/remotion/src/puppet/Kai.tsx` — **default presenter**, original, semi-realistic
  illustrated style matching pro explainer channels: gradient-shaded skin, almond eyes with
  irises/catchlights/lids, real nose and lips (per-viseme lip shapes with teeth/tongue),
  textured curly-top with fade, stubble, mustard overshirt with rolled sleeves (bare
  forearms), knuckled hands, and the signature orange headphones around the neck. Same
  pose/viseme API as Nova: `<PuppetTrack character="kai" ...>` (or `"nova"` for flat style).
- `templates/remotion/src/puppet/PuppetTrack.tsx` — pose cues + 3-frame crossfade, lip-sync
  frames, deterministic blinks, drift/nod/breathe.
- `scripts/lipsync.py` — voiceover → per-frame visemes. Primary engine: **Rhubarb Lip Sync**
  (phonetic, Hanna-Barbera A–H + X, mapped to Nova's mbp/ee/eh/aa/oh/uw/fv/l/rest; pass the
  script with `--dialog`). Fallback: loudness + spectral centroid heuristic. Also emits energy.
- `scripts/align_words.py` — word timestamps for captions and **keyword-triggered poses**
  (`<PuppetTrack triggers={{ five: { pose: "wow", dur: 1 } }} words={...}>`), the trigger
  pattern adapted from kevinbadi/claude-codes-influencers (MIT). Blinks include an
  occasional double-blink; the body bounces with speech loudness.

```bash
python3 scripts/lipsync.py vo.wav public/lipsync.json --dialog "<script>" --offset <vo start s> --duration <video s>
```
```tsx
<PuppetTrack cues={[{t:0,pose:"point_up"},{t:1.6,pose:"wow"}]} lipsync={lipsyncJson} />
```

## Rules

1. **Never clone a real creator's mascot or avatar** (their outfit + face + accessories are
   their brand identity). The reverse-video skill captures the *mechanics* (pose library,
   crossfade timing, lip-sync, placement, size); `create-video` always uses an original
   character. To make a new one, copy `Nova.tsx` and change palette/hair/outfit/accessory —
   keep the layer structure so lip-sync and poses keep working.
2. Cue a pose change on caption beats, ≥1 per 2.5 s, never mid-word if avoidable.
3. Pose must match the line: claims → point_up, numbers/evidence → explain/present,
   surprises → wow, payoff → thumbs_up/peace, doubt → shrug, process → think.
4. Lip-sync must be generated from the *final* VO with the same offset it has in the edit.
