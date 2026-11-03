# 3D & Motion Playbook — how premium explainer reels actually get that look

Field guide for the vision pass and for the generated skill's recreation recipe. Derived
from deep-analysis of photoreal explainer reels (tire manufacturing, touchscreen physics,
PCA data-viz class of videos). The professional pipeline behind these is **Blender (3D,
Cycles/Eevee) + After Effects (captions/compositing)**; our programmatic equivalents are
**Blender via `bpy` (photoreal tier)** and **Three.js in Remotion (stylized 3D tier)**.

## 1. The lighting grammar (this is 80% of "premium")

Every premium dark explainer shot uses the same studio recipe:

- **Big soft key**: one large area light, high and off to one side, 30–50° down. Soft
  falloff across the subject, never flat.
- **Warm rim/accent**: amber/gold spot or area from behind-left or behind-right, grazing
  the silhouette. This is the "expensive" edge glow (`#E0A33E`-family).
- **Cool fill**: faint blue accent from the opposite side (`#6FA8FF`-family), 1/8 the key.
- **Near-black world**: background `#0A0A0E`, so objects are drawn by light, not outlines.
- **Volumetric/spot pools**: light visibly pools on the floor; subject sits in the pool.
- Tone mapping: filmic/AgX (Blender) or ACES (Three.js) — never raw sRGB.

What to note in the vision pass: where the key is, rim color, whether light pools, how
dark the darkest visible surface is.

## 2. Materials

- Rubber/plastic: very dark base (#141416), roughness 0.45–0.6, zero metallic.
- Machined steel: mid-gray, roughness 0.2–0.35, metallic 0.9+, visible anisotropic sheen.
- Glass/screens: emissive planes (the UI texture itself lights the scene).
- Skin (giant finger): subsurface-looking warm tone, soft specular highlight band.
- Glowing physics (field lines, heat): emission shaders, bloom in post, additive layering.

## 3. Camera grammar

The moves are few and always eased (ease-in-out, nothing linear):

| Move | Use |
|---|---|
| **Slow push-in** (dolly, 2–5%/s) | default on everything; nothing is static |
| **Low-angle macro** | makes small objects (keys, treads) monumental |
| **Orbit segment** (10–30° over a shot) | hero-object reveals |
| **Rack focus / shallow DOF** (f/1.4–2.8) | directs the eye; backgrounds always melt |
| **Whip/morph transition** | scene changes: the camera push *becomes* the next scene |

Motion blur on fast moves; micro-drift (handheld noise ≈1–2px) on "locked" shots.

## 4. Easing — read it from motion strips

In an 8-frame motion strip: equal spacing = linear (amateur); spacing tightening at the
end = ease-out (UI elements arriving); tight→wide→tight = ease-in-out (cameras, morphs).
Premium reels use spring/ease-out for element entrances (200–400ms) and long
ease-in-out for camera moves (full shot length). Encode easing per element class.

## 5. Particles & simulation devices

- Scatter/instancing: thousands of small instances (rubber hairs, data points, sparks)
  with slight random rotation/scale — instanced meshes (Three.js) or particle hair (Blender).
- Float fields: dust/particles drifting slowly in light beams (big depth cue).
- Physics beats: one simulated event per video (something drops, splashes, snaps) as the
  "wow" moment. In Blender: rigid body or cloth, baked.

## 6. Sound design (the invisible half)

Map from detect_sfx.py events, typical grammar:
- **whoosh** on every camera move/morph (aligned to move start, ~0.3–0.6s)
- **tap/click** on UI touches and text pops
- **impact/thump** on heavy objects landing (with ~60Hz weight)
- **riser** under the last 2–3s before a reveal, cut to silence at the reveal
- Room tone/music bed at -20 to -26dB under VO; VO always dominant; dead silence is never
  allowed except as a deliberate beat (~0.3s before a punchline).

## 7. Recreation tiers (what the create-video skill should pick)

1. **Blender photoreal** (`blender_shot.py`, pip install bpy): hero 3D shots — PBR,
   real DOF, studio lights, eased camera keys. ~15–25s/frame CPU → render at 15fps/half-res,
   motion-interpolate to 30fps. Budget: only the 2–5 hero shots.
2. **Three.js in Remotion** (`@remotion/three`, render with `--gl=swangle`): everything
   3D that moves per-frame with captions — real-time PBR-ish, rect-area + spot lights,
   ACES tone mapping. This is the workhorse tier.
3. **Generative video MCP** (if the session has one, e.g. Gemini/Veo-class `create_video`):
   photoreal b-roll that's impractical to model (factory floors, nature). Composite under
   captions in Remotion. Mark as AI-generated footage.
4. **DOM/CSS Remotion**: flat UI mockups, captions, charts (pixel-perfect app recreations).
5. **FFmpeg assembler**: zero-dependency floor.

A single video mixes tiers: Blender/gen-video shots are rendered to MP4 first, then
composited as `<OffthreadVideo>` layers inside the Remotion timeline with captions/mascot
on top — exactly like the pros composite Blender renders in After Effects.
