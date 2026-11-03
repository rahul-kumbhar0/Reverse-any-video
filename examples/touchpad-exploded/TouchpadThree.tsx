import React from "react";
import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Mat, RoundedSlab, ThreeStudio } from "./three-kit";

/* Same exploded trackpad as scene_touchpad.py, in the real-time tier (preview / stylized).
   Blender is z-up; Three.js is y-up: blender (x, y, z) -> three (x, z, -y). */

const W = 1.6, D = 1.0, GAP = 0.44, DUR = 3;
const ease = Easing.inOut(Easing.cubic);

const lift = (t: number, i: number, z0: number, z1: number) => {
  const t0 = 0.35 + i * 0.12;
  return interpolate(t, [t0, t0 + 1.25], [z0, z1], { easing: ease, extrapolateLeft: "clamp", extrapolateRight: "clamp" })
    + interpolate(t, [t0 + 1.25, DUR], [0, 0.03], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
};

const Grid: React.FC<{ glow: number }> = ({ glow }) => (
  <>
    {Array.from({ length: 11 }, (_, i) => (
      <mesh key={`r${i}`} position={[0, 0.006, -(i - 5) * 0.082]}>
        <boxGeometry args={[W - 0.12, 0.003, 0.006]} />
        {Mat.emissive("#E0A33E", glow)}
      </mesh>
    ))}
    {Array.from({ length: 18 }, (_, i) => (
      <mesh key={`c${i}`} position={[(i - 8.5) * 0.082, 0.011, 0]}>
        <boxGeometry args={[0.006, 0.003, D - 0.12]} />
        {Mat.emissive("#E0A33E", glow)}
      </mesh>
    ))}
  </>
);

export const TouchpadThree: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const glow = interpolate(t, [1.3, 2.0], [0.3, 3.2], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const gauge = interpolate(t, [1.6, 2.2], [0, 3], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // camera: blender keys (2.55,-3.7,1.75)->(2.3,-3.95,2.55); aim z 0.12->0.95
  const k = interpolate(t, [0, DUR], [0, 1], { easing: Easing.inOut(Easing.sin) });
  const cam: [number, number, number] = [2.55 - 0.25 * k, 1.75 + 0.8 * k, 3.7 + 0.25 * k];
  const aimY = interpolate(t, [0.35, 2.0], [0.12, 0.95], { easing: ease, extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const zGlass = lift(t, 0, 0.215, 0.215 + 4 * GAP);
  const zSense = lift(t, 1, 0.185, 0.185 + 3 * GAP);
  const zPcb = lift(t, 2, 0.15, 0.15 + 2 * GAP);
  const zHap = lift(t, 3, 0.06, 0.06 + GAP);

  return (
    <ThreeStudio camera={{ position: cam, lookAt: [0, aimY, -0.05], fov: 46 }}>
      {/* frame */}
      <RoundedSlab size={[W + 0.06, 0.035, D + 0.06]} radius={0.012}>{Mat.aluSpaceGray()}</RoundedSlab>
      {/* haptic engine + force sensors */}
      <group position={[0, zHap, 0]}>
        <RoundedSlab size={[0.62, 0.09, 0.17]} radius={0.02} position={[0, 0, 0.05]}>{Mat.aluSilver()}</RoundedSlab>
        <mesh position={[0, 0.05, 0.05]} rotation={[Math.PI / 2, 0, 0]} scale={[1.9, 0.62, 0.6]}>
          <torusGeometry args={[0.11, 0.035, 24, 96]} />
          {Mat.copper()}
        </mesh>
        {[[-0.66, -0.38], [0.66, -0.38], [-0.66, 0.38], [0.66, 0.38]].map(([x, y], i) => (
          <group key={i} position={[x, 0, -y]}>
            <RoundedSlab size={[0.13, 0.03, 0.13]} radius={0.008}>{Mat.aluSilver()}</RoundedSlab>
            <RoundedSlab size={[0.08, 0.01, 0.08]} radius={0.003} position={[0, 0.02, 0]}>{Mat.emissive("#E0A33E", gauge)}</RoundedSlab>
          </group>
        ))}
      </group>
      {/* PCB */}
      <group position={[0, zPcb, 0]}>
        <RoundedSlab size={[W - 0.04, 0.022, D - 0.04]} radius={0.008}>{Mat.pcb()}</RoundedSlab>
        <RoundedSlab size={[0.24, 0.03, 0.24]} radius={0.006} position={[0.42, 0.025, 0.16]}>{Mat.chip()}</RoundedSlab>
        {Array.from({ length: 9 }, (_, i) => (
          <mesh key={i} position={[0, 0.0125, -0.04 - (i - 4) * 0.085]}>
            <boxGeometry args={[W - 0.3, 0.003, 0.006]} />
            {Mat.copper()}
          </mesh>
        ))}
      </group>
      {/* capacitive sensor film + electrode grid */}
      <group position={[0, zSense, 0]}>
        <RoundedSlab size={[W - 0.02, 0.008, D - 0.02]} radius={0.003}>
          <meshPhysicalMaterial color="#9FB4C8" roughness={0.15} transmission={0.85} ior={1.4} thickness={0.01} transparent />
        </RoundedSlab>
        <Grid glow={glow} />
      </group>
      {/* etched glass */}
      <group position={[0, zGlass, 0]}>
        <RoundedSlab size={[W, 0.03, D]} radius={0.012}>{Mat.glassFrosted()}</RoundedSlab>
      </group>
    </ThreeStudio>
  );
};
