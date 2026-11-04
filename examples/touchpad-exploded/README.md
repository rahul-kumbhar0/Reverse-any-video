# Example: exploded laptop trackpad (3-second test clip)

The reference workflow from `skills/create-video/references/blender-craft.md`, end to end:

1. **Study**: motion strips of the touchscreen reference (layer cutaways, edge highlights,
   emissive grid, dust, tracked labels).
2. **Model**: `scene_touchpad.py` builds five real trackpad layers with `blender_kit`
   (etched glass, capacitive electrode grid, controller PCB, force sensors + haptic engine,
   aluminium frame): bevelled rounded slabs, material presets, studio rig.
3. **Verify stills** (assembled + exploded) before animating:
   `python3 scene_touchpad.py --out out/check.mp4 --still 2.8 --samples 32 --scale 0.4`
4. **Preview motion** in Three.js: `TouchpadThree.tsx` (same timings, renders in ~1 min).
5. **Render**: `python3 scene_touchpad.py --out public/touchpad.mp4` (~15 min, 4 cores),
   which also writes `touchpad.anchors.json` (per-frame screen positions of each layer).
   Use `--anchors-only` to regenerate labels without re-rendering.
6. **Composite**: `TouchpadReel.tsx` (Remotion) puts labels that track the 3D layers,
   captions, mascot and the audio track over the render.

`TouchpadReel.tsx` imports `SelectionBox` from the LEGO example`s `Main.tsx`, the `puppet/` folder from the Remotion template (lip-sync: `python3 ../../skills/create-video/scripts/lipsync.py vo.wav public/touchpad.lipsync.json --offset 0.15 --duration 3`)
and `three-kit.tsx` from the Remotion template; copy those into the same `src/`.
