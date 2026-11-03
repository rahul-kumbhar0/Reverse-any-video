import React from "react";
import {
  AbsoluteFill, Audio, Easing, OffthreadVideo, interpolate, staticFile,
  useCurrentFrame, useVideoConfig,
} from "remotion";
import anchors from "../public/touchpad.anchors.json";
import { MascotSVG, SelectionBox } from "./Main";

/* 3s test reel: exploded trackpad (Blender) + 3D-tracked labels + captions + mascot. */

const C = { white: "#FFFFFF", dim: "#9A9AA0", amber: "#E0A33E" };
const FONT = "-apple-system, 'SF Pro Display', Inter, 'Helvetica Neue', Arial, sans-serif";

/** Screen position of a Blender anchor at time t (linear between rendered frames). */
const at = (name: keyof typeof anchors.anchors, t: number) => {
  const track = anchors.anchors[name] as number[][];
  const f = Math.min(Math.max(t * anchors.fps, 0), track.length - 1);
  const i = Math.floor(f), j = Math.min(i + 1, track.length - 1), k = f - i;
  return [track[i][0] + (track[j][0] - track[i][0]) * k, track[i][1] + (track[j][1] - track[i][1]) * k];
};

const LABELS: { id: keyof typeof anchors.anchors; text: string; at: number }[] = [
  { id: "glass", text: "ETCHED GLASS", at: 0.95 },
  { id: "sense", text: "CAPACITIVE GRID", at: 1.15 },
  { id: "pcb", text: "CONTROLLER", at: 1.35 },
  { id: "haptic", text: "HAPTIC ENGINE", at: 1.6 },
  { id: "frame", text: "ALUMINIUM FRAME", at: 1.85 },
];

const TrackedLabel: React.FC<{ id: keyof typeof anchors.anchors; text: string; showAt: number; t: number }> = ({
  id, text, showAt, t,
}) => {
  const { width, height } = useVideoConfig();
  const [nx, ny] = at(id, t);
  const x = nx * width, y = ny * height;
  const lineIn = interpolate(t, [showAt, showAt + 0.2], [0, 1], { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const textIn = interpolate(t, [showAt + 0.1, showAt + 0.28], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const LINE = 54;
  const textW = 340;
  const tx = Math.min(Math.max(x - textW / 2, width * 0.04), width * 0.96 - textW);
  return (
    <>
      <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%", overflow: "visible" }}>
        <circle cx={x} cy={y} r={6 * lineIn} fill="white" />
        <line x1={x} y1={y} x2={x} y2={y - LINE * lineIn} stroke="white" strokeWidth={2} opacity={lineIn} />
      </svg>
      <div style={{
        position: "absolute", left: tx, top: y - LINE - 50, width: textW,
        display: "flex",
        justifyContent: x - textW / 2 < tx || x + textW / 2 > tx + textW ? (tx > x - textW / 2 ? "flex-start" : "flex-end") : "center",
        opacity: textIn, transform: `translateY(${(1 - textIn) * 6}px)`,
      }}>
        <span style={{
          fontFamily: FONT, fontSize: 24, fontWeight: 600, letterSpacing: 3, color: C.white,
          padding: "7px 14px", borderRadius: 10,
          background: "rgba(10,10,12,0.72)", border: "1px solid rgba(255,255,255,0.16)",
          backdropFilter: "blur(6px)",
        }}>{text}</span>
      </div>
    </>
  );
};

type Word = { t: string; k?: "dim" | "bold" | "box" };
const BEATS: { start: number; end: number; words: Word[]; pose: "point-up" | "clutch" }[] = [
  { start: 0, end: 1.6, pose: "point-up", words: [{ t: "What's inside your", k: "dim" }, { t: "trackpad?", k: "box" }] },
  { start: 1.6, end: 3.0, pose: "clutch", words: [{ t: "5 layers", k: "box" }, { t: "of", k: "dim" }, { t: "engineering", k: "bold" }] },
];

export const TouchpadReel: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const t = frame / fps;
  const beat = BEATS.find((b) => t >= b.start && t < b.end) ?? BEATS[BEATS.length - 1];
  const tIn = t - beat.start;
  const capIn = interpolate(tIn, [0, 0.15], [0, 1], { extrapolateRight: "clamp" });
  const boxDraw = interpolate(tIn, [0.1, 0.3], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const prev = BEATS[Math.max(0, BEATS.indexOf(beat) - 1)];
  const poseFade = Math.min(1, tIn / 0.15);
  const mascotBox: React.CSSProperties = {
    position: "absolute", bottom: 0, left: "50%", transform: "translateX(-50%)",
    width: height * 0.16 * (200 / 260), height: height * 0.16,
  };

  return (
    <AbsoluteFill style={{ background: "#050507" }}>
      <OffthreadVideo src={staticFile("touchpad.mp4")} muted style={{ width: "100%", height: "100%" }} />
      {LABELS.map((l) => <TrackedLabel key={l.id} id={l.id} text={l.text} showAt={l.at} t={t} />)}

      {/* caption band */}
      <div style={{ position: "absolute", top: height * 0.07, left: "6%", right: "6%", opacity: capIn,
        transform: `translateY(${(1 - capIn) * 8}px)`, fontFamily: FONT, fontSize: height * 0.032, textAlign: "center" }}>
        {beat.words.map((w, i) => w.k === "box"
          ? <SelectionBox key={i} draw={boxDraw}>{w.t}</SelectionBox>
          : <span key={i} style={{ color: w.k === "bold" ? C.white : C.dim, fontWeight: w.k === "bold" ? 700 : 400, margin: "0 6px" }}>{w.t}</span>)}
      </div>

      <div style={{ position: "absolute", bottom: "17.5%", left: "4%", fontFamily: FONT, fontSize: 21, color: "#6E6E74" }}>
        Illustrative · layer gaps exaggerated
      </div>

      {prev !== beat && poseFade < 1 ? <div style={{ ...mascotBox, opacity: 1 - poseFade }}><MascotSVG pose={prev.pose} /></div> : null}
      <div style={{ ...mascotBox, opacity: poseFade }}><MascotSVG pose={beat.pose} /></div>

      <Audio src={staticFile("touchpad_audio.wav")} />
    </AbsoluteFill>
  );
};
