# Three.js craft — the real-time 3D tier inside Remotion

Use for: fast motion previews of a Blender shot (~1 min vs ~15), stylized 3D that must sync
with captions per-frame, data-viz in 3D. Components: `templates/remotion/src/three-kit.tsx`.

## Setup

```bash
npm i three@0.166 @remotion/three@4 "@react-three/fiber@^8"   # fiber 8 ↔ React 18
npx remotion render <Comp> out.mp4 --gl=swangle                # required headless
```

## Look rules

| Rule | Why |
|---|---|
| **Always install an environment map** (`<StudioEnvironment/>`: PMREM RoomEnvironment) | Without IBL, metal/glass have nothing to reflect and render flat/plastic. Single biggest quality jump. |
| `ACESFilmicToneMapping`, sRGB output | Matches the Cycles AgX feel. |
| `RoundedBoxGeometry` (radius 0.003–0.02) instead of boxes | Same bevel rule as Blender: edges must catch light. |
| `meshPhysicalMaterial` with `transmission` for glass, `clearcoat` for PCBs/paint | Standard material can't do either. |
| Emissives: `toneMapped={false}`, intensity 2–4 | Glow reads without blowing out. |
| **Fog in the background colour** (`<fog args={[bg, 4.5, 8.5]}/>`) | Otherwise the floor's far edge draws a grey horizon line. |
| Studio rig mirrors Blender: cool key, amber rim spot, blue fill spot | Same visual language across tiers. |

## Animation rules

- Drive everything from `useCurrentFrame()`; never `useFrame`/clocks (renders must be deterministic).
- Use Remotion `interpolate` + `Easing.inOut(Easing.cubic)`; reuse Blender timings so the
  preview matches the final.
- Re-aim the camera every frame (`CameraRig`): position + lookAt both animated.
- Coordinates: Blender (x, y, z) → Three (x, z, −y).

## Known limits vs Cycles

No real refraction blur, contact shadows or area-light softness; transmission is
screen-space. Good enough for stylized shots and previews; hero photoreal stays in Blender.
