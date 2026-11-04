import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { Nova, Pose, Viseme } from "./Nova";

/**
 * Drives Nova like a Character-Animator puppet:
 *  - pose schedule, switching with a 3-frame crossfade (as in the reference)
 *  - mouth from lipsync.py output (per-frame visemes)
 *  - deterministic blinks every ~2.4–3.8 s (half → closed → half)
 *  - head micro-drift + nods on speech energy, breathing
 */
export type PoseCue = { t: number; pose: Pose };
export type LipSync = { fps: number; frames: { v: string; e: number }[] };

const blinkAt = (frame: number, fps: number): 0 | 1 | 2 => {
  // pseudo-random but deterministic blink times
  let t = 0.9 * fps, k = 0;
  while (t < frame + 3) {
    const d = frame - t;
    if (d >= 0 && d < 4) return (d === 1 || d === 2 ? 2 : 1) as 0 | 1 | 2;
    k += 1;
    t += fps * (2.4 + ((k * 7919) % 14) / 10);
  }
  return 0;
};

export const PuppetTrack: React.FC<{ cues: PoseCue[]; lipsync?: LipSync; fadeFrames?: number }> = ({
  cues, lipsync, fadeFrames = 3,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  let i = 0;
  while (i + 1 < cues.length && cues[i + 1].t <= t) i++;
  const cur = cues[i];
  const prev = i > 0 ? cues[i - 1] : null;
  const since = frame - Math.round(cur.t * fps);
  const fade = prev && since < fadeFrames ? (since + 1) / (fadeFrames + 1) : 1;

  const ls = lipsync?.frames[Math.min(frame, (lipsync?.frames.length ?? 1) - 1)];
  const viseme = (ls?.v ?? "rest") as Viseme;
  const e = ls?.e ?? 0;
  const blink = blinkAt(frame, fps);
  const drift = Math.sin(t * 1.3) * 1.2 + Math.sin(t * 0.7 + 1) * 0.8;
  const nod = e * Math.sin(t * 9) * 0.8 + e * 0.6;
  const breathe = Math.sin(t * 2.2);
  const look = Math.sin(t * 0.5) * 1.5;

  const common = { viseme, blink, headTilt: drift, headNod: nod, breathe, look };
  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      {prev && fade < 1 ? (
        <div style={{ position: "absolute", inset: 0, opacity: 1 - fade }}><Nova pose={prev.pose} {...common} /></div>
      ) : null}
      <div style={{ position: "absolute", inset: 0, opacity: fade }}><Nova pose={cur.pose} {...common} /></div>
    </div>
  );
};
