# Blender craft — making headless Cycles renders read as "real"

Rules learned the hard way (each one fixed a visible defect in a test render). Build every
scene with `scripts/blender_kit.py`; it applies most of these automatically.

## The workflow (never skip a step)

1. **Study the reference first**: motion strips (`extract_motion.py`) of the shots you are
   matching. Write down: edge treatment, which parts glow, layer spacing, camera move,
   label behaviour.
2. **Model at real proportions** (metres-ish units, 1.0 ≈ the hero object width). Exaggerate
   thickness/gaps only where legibility needs it, and say so in a footnote.
3. **Verify with stills before animating**: render 2 frames (start + end state) at
   `--scale 0.4 --samples 32` (~1 min). Fix framing/lighting there; a full animation
   costs 10–20 min.
4. **Preview the motion in Three.js** (`templates/remotion/src/three-kit.tsx`) when timing
   is uncertain: same animation in ~1 min.
5. **Render the animation** at 10–12 fps, `--scale 0.5`, 40–48 samples, adaptive sampling,
   then motion-interpolate to 30 fps (the kit does this).
6. **Verify the result** by extracting frames and comparing to the reference strip.

## Look rules

| Rule | Why / defect it fixes |
|---|---|
| **Bevel every edge** (`rounded_slab(..., bevel=0.003–0.008)`, harden normals) | Sharp edges never catch light → objects look CG. The thin bright edge line *is* the realism cue. |
| **Rounded plan-view corners** on devices (`corner_r`) | Real products are never rectangular. |
| **Key light cool-white, rim amber, fill blue**; rim ≤ ~3× key | A rim brighter than that floods the whole frame orange (first touchpad test). |
| **AgX + "Medium High Contrast" look** | Filmic highlight roll-off; plain sRGB clips. |
| **Bloom in post, gently** (threshold ~0.74, opacity ~0.4) | Emissives need glow; too much turns grids into white slabs. |
| **Emission 2.5–4 for fine emissive lines**, ramp it up with `key_value` | >8 blows out thin geometry into a solid sheet. |
| **Dust: ~100 specks, radius 1.5–4 mm, emission ≈ 0.45** | More/larger reads as snow or stars. |
| **Floor slightly reflective (rough 0.35, metal 0.1)** | Grounds the subject with a soft reflection + light pool. |
| **DOF f/2.8–4 for multi-layer subjects**, f/1.8 only for single-object macro | Stacks need most layers sharp. |
| **Motion blur on** (shutter 0.5) | Removes the stop-motion feel of interpolated frames. |

## Animation rules

- Exploded views: separate **top-first with a 0.10–0.15 s stagger**, 1.0–1.4 s per move,
  clamped-bezier easing (no overshoot), then a slow 0.03 drift so the end never freezes.
- Animate the **camera target** too (an empty), so framing follows the stack as it grows.
- "Activate" moments (grids lighting, gauges glowing) start *after* the part is separated.

## Labels that track 3D (anchors)

Parent `anchor(name, layer_group, offset)` empties to the parts you will label; call
`export_anchors(path, width, height)` — **width/height must be the final aspect ratio**
(projection depends on it; exporting before the resolution is set projects onto a
landscape frame and every label lands in the wrong place). The compositor reads the JSON
and draws leader lines that move with the parts.

## Headless environment notes

- `pip install bpy` gives a full Blender; import `bpy` **before** `bmesh`.
- Blender 5.x: `Action.fcurves` is gone (layered actions) — use `action_fcurves()`.
- EEVEE runs headless only with Mesa EGL (`apt install libegl1 libegl-mesa0 libgl1-mesa-dri`)
  and is *slower* than Cycles on CPU here — use Cycles.
- `minterpolate` needs ≥5 input frames; the kit falls back to plain fps for stubs.
