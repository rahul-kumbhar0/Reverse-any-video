# Example: "Why LEGO bricks never let go" — full photoreal pipeline

A 42s reel produced entirely by the agent in the reverse-engineered
`photoreal-tech-explainer` style. Demonstrates every tier working together:

1. **Hero shots** (`shots/s1-3.json`) rendered ray-traced via
   `skills/create-video/scripts/blender_shot.py` (PBR bricks, studio rig with aim_at,
   eased camera keys, an animated brick-snap via object keyframes, DOF).
2. **Composite** (`src/Main.tsx`, Remotion): hero MP4s as OffthreadVideo layers under the
   caption system (karaoke phrases + selection-box key word), annotation lines, evidence
   cards, animated stat counter, share-sheet CTA, crossfading mascot.
3. **Voiceover**: per-sentence local neural TTS (piper-tts), each line placed at its exact
   caption-beat time for perfect sync.
4. **Sound design**: `synth_sfx.py` whooshes/impact/clicks/riser + room-tone bed, placed
   by the style's SFX grammar.

```bash
# hero shots (~7 min each on 4 CPU cores)
pip install bpy
for s in shots/s*.json; do python3 ../../skills/create-video/scripts/blender_shot.py $s public/$(basename $s .json).mp4 --fps-render 10 --samples 24 --scale 0.45; done
# composite
npm install && npx remotion render Main out/video.mp4
```
