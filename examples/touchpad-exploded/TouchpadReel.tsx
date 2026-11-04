import React from "react";
import {
  AbsoluteFill, Audio, Easing, OffthreadVideo, interpolate, staticFile,
  useCurrentFrame, useVideoConfig,
} from "remotion";
import anchors from "../public/touchpad.anchors.json";
import { SelectionBox } from "./Main";
import { PuppetTrack } from "./puppet/PuppetTrack";
import lipsync from "../public/touchpad.lipsync.json";
import words from "../public/touchpad.words.json";
import { KaraokeCaption } from "./captions/KaraokeCaption";

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

      {/* word-timed karaoke captions (align_words.py) */}
      <KaraokeCaption words={words.words} phrases={[
        { from: 0, to: 3, styles: { 3: "box" }, text: { 3: "trackpad?" } },
        { from: 4, to: 5, styles: { 4: "box", 5: "bold" }, text: { 5: "layers." } },
      ]} />

      <div style={{ position: "absolute", bottom: "17.5%", left: "4%", fontFamily: FONT, fontSize: 21, color: "#6E6E74" }}>
        Illustrative · layer gaps exaggerated
      </div>

      {/* vignette (reference look) */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, transparent 50%, rgba(0,0,0,0.55) 100%)" }} />
      {/* presenter puppet: bottom-centre, cropped at the waist */}
      <div style={{ position: "absolute", left: "50%", bottom: -70, transform: "translateX(-50%)",
        width: height * 0.25 * (400 / 520), height: height * 0.25 }}>
        <PuppetTrack cues={[{ t: 0, pose: "explain" }, { t: 2.55, pose: "thumbs_up" }]}
          words={words.words} triggers={{ trackpad: { pose: "point_up", dur: 0.7 }, five: { pose: "wow", dur: 1.0 } }}
          lipsync={lipsync as any} />
      </div>

      <Audio src={staticFile("touchpad_audio.wav")} />
    </AbsoluteFill>
  );
};
