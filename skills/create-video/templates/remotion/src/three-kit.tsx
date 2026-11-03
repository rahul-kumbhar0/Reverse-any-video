import React, { useMemo } from "react";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import { useVideoConfig } from "remotion";
import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";

/**
 * three-kit — the Three.js tier of the craft rules (references/threejs-craft.md).
 *
 * Why things looked plasticky before: no environment map. PBR metal/glass reflects its
 * surroundings; with nothing to reflect it renders flat. <StudioEnvironment/> installs a
 * PMREM-filtered RoomEnvironment as scene.environment (IBL), then the studio rig adds the
 * dark-explainer key/rim/fill on top. Always render with: --gl=swangle
 */

export const StudioEnvironment: React.FC<{ intensity?: number }> = ({ intensity = 0.35 }) => {
  const { gl, scene } = useThree();
  useMemo(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    const env = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environment = env;
    (scene as any).environmentIntensity = intensity;
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.0;
    gl.outputColorSpace = THREE.SRGBColorSpace;
    pmrem.dispose();
  }, [gl, scene, intensity]);
  return null;
};

export const StudioRig: React.FC<{ target?: [number, number, number]; rim?: string; fill?: string }> = ({
  target = [0, 0.6, 0],
  rim = "#E0A33E",
  fill = "#6FA8FF",
}) => {
  const t = useMemo(() => {
    const o = new THREE.Object3D();
    o.position.set(...target);
    o.updateMatrixWorld();
    return o;
  }, [target]);
  return (
    <>
      <primitive object={t} />
      {/* soft cool-white key, high left */}
      <directionalLight position={[-3, 4.2, 2.6]} intensity={1.6} color="#F1F4FF" target={t} />
      {/* warm rim behind, grazing the silhouettes */}
      <spotLight position={[-2.4, 2.2, -3.8]} intensity={60} angle={0.6} penumbra={0.9} color={rim} target={t} />
      {/* cool fill opposite */}
      <spotLight position={[3.4, 1.0, -2.8]} intensity={25} angle={0.7} penumbra={1} color={fill} target={t} />
      <ambientLight intensity={0.04} />
    </>
  );
};

export const RoundedSlab: React.FC<{
  size: [number, number, number];
  radius?: number;
  position?: [number, number, number];
  children: React.ReactNode; // the material
}> = ({ size, radius = 0.02, position = [0, 0, 0], children }) => {
  const geo = useMemo(() => new RoundedBoxGeometry(size[0], size[1], size[2], 6, radius), [
    size[0], size[1], size[2], radius,
  ]);
  return (
    <mesh geometry={geo} position={position}>
      {children}
    </mesh>
  );
};

/** Material presets mirroring blender_kit (sRGB hex). */
export const Mat = {
  glassFrosted: () => (
    <meshPhysicalMaterial color="#E8ECF2" roughness={0.28} transmission={1} thickness={0.03}
      ior={1.5} clearcoat={0.6} transparent />
  ),
  aluSpaceGray: () => <meshPhysicalMaterial color="#5A5D63" roughness={0.32} metalness={1} />,
  aluSilver: () => <meshPhysicalMaterial color="#C9CCD1" roughness={0.25} metalness={1} />,
  pcb: () => <meshPhysicalMaterial color="#0D2B1F" roughness={0.45} clearcoat={0.8} clearcoatRoughness={0.15} />,
  copper: () => <meshPhysicalMaterial color="#D98A5B" roughness={0.25} metalness={1} />,
  chip: () => <meshPhysicalMaterial color="#121214" roughness={0.55} />,
  emissive: (color = "#E0A33E", intensity = 3) => (
    <meshStandardMaterial color={color} emissive={color} emissiveIntensity={intensity} toneMapped={false} />
  ),
};

/** Canvas with the near-black world, IBL and rig already in place. y is up in Three.js. */
export const ThreeStudio: React.FC<{
  children: React.ReactNode;
  camera: { position: [number, number, number]; lookAt: [number, number, number]; fov?: number };
  background?: string;
}> = ({ children, camera, background = "#050507" }) => {
  const { width, height } = useVideoConfig();
  return (
    <div style={{ width, height, background }}>
      <ThreeCanvas width={width} height={height} camera={{ position: camera.position, fov: camera.fov ?? 35 }}
        onCreated={({ camera: cam }) => cam.lookAt(...camera.lookAt)}>
        <CameraRig position={camera.position} lookAt={camera.lookAt} />
        {/* fog in the background colour hides the floor's far edge (no horizon line) */}
        <fog attach="fog" args={[background, 4.5, 8.5]} />
        <StudioEnvironment />
        <StudioRig />
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.06, 0]}>
          <planeGeometry args={[40, 40]} />
          <meshPhysicalMaterial color="#0B0B0E" roughness={0.35} metalness={0.1} />
        </mesh>
        {children}
      </ThreeCanvas>
    </div>
  );
};

/** Per-frame camera placement (Remotion drives position; we re-aim every frame). */
const CameraRig: React.FC<{ position: [number, number, number]; lookAt: [number, number, number] }> = ({
  position,
  lookAt,
}) => {
  const { camera } = useThree();
  camera.position.set(...position);
  camera.lookAt(...lookAt);
  camera.updateProjectionMatrix();
  return null;
};
