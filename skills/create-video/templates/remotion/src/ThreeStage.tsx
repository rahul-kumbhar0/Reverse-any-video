import React from "react";
import { ThreeCanvas } from "@remotion/three";
import { useVideoConfig } from "remotion";
import * as THREE from "three";

/**
 * Studio stage for 3D shots — implements the premium-explainer lighting grammar
 * (3d-motion-playbook.md §1): big soft key, warm rim, cool fill, near-black world,
 * ACES tone mapping. Put your animated meshes as children.
 *
 * Render with: npx remotion render <comp> out.mp4 --gl=swangle
 */
export const ThreeStage: React.FC<{
  children: React.ReactNode;
  background?: string;
  rimColor?: string;
  fillColor?: string;
  camera?: { position: [number, number, number]; fov?: number };
}> = ({
  children,
  background = "#0A0A0E",
  rimColor = "#E0A33E",
  fillColor = "#6FA8FF",
  camera = { position: [1.8, 0.7, 3.4], fov: 45 },
}) => {
  const { width, height } = useVideoConfig();
  return (
    <div style={{ width, height, background }}>
      <ThreeCanvas
        width={width}
        height={height}
        gl={{ toneMapping: THREE.ACESFilmicToneMapping }}
        camera={{ position: camera.position, fov: camera.fov ?? 45 }}
      >
        {/* big soft key, high and off to one side */}
        <rectAreaLight position={[4, 5, 3]} rotation={[-0.8, 0.5, 0]} intensity={14} width={6} height={6} />
        {/* warm rim grazing the silhouette from behind */}
        <spotLight position={[-5, 4, -2]} intensity={120} angle={0.5} penumbra={0.9} color={rimColor} />
        {/* faint cool fill from the opposite side */}
        <spotLight position={[3, 2, -5]} intensity={60} angle={0.6} penumbra={1} color={fillColor} />
        <ambientLight intensity={0.12} />
        {/* floor that catches the light pool */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.4, 0]}>
          <planeGeometry args={[40, 40]} />
          <meshStandardMaterial color="#101014" roughness={0.35} metalness={0.1} />
        </mesh>
        {children}
      </ThreeCanvas>
    </div>
  );
};
