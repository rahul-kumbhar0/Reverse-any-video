import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { Nova, Pose, Viseme } from "./Nova";

/**
 * Drives Nova like a Character-Animator puppet (patterns adapted from
 * kevinbadi/claude-codes-influencers, MIT):
 *  - pose cues + keyword triggers (a spoken word swaps the pose for `dur` seconds)
 *  - 3-frame crossfade between poses (as in the reference reels)
 *  - mouth from lipsync.py (Rhubarb visemes), per frame
 *  - blinks every 2.4–4.6 s with an occasional double blink
 *  - loudness bounce, head drift, nods on speech energy, breathing
 */
export type PoseCue = { t: number; pose: Pose };
export type LipSync = { fps: number; frames: { v: string; e: number }[] };
export type TimedWord = { word: string; start: number; end: number };
export type Triggers = Record<string, { pose: Pose; dur?: number }>;

const rand = (k: number) => {
  const x = Math.sin(k * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

const blinkState = (t: number): 0 | 1 | 2 => {
  let bt = 1.3;
  for (let k = 0; bt < t + 1; k++) {
    for (const b of rand(k) < 0.18 ? [bt, bt + 0.32] : [bt]) {
      const d = t - b;
      if ((d >= 0 && d < 0.05) || (d >= 0.15 && d < 0.2)) return 1;
      if (d >= 0.05 && d < 0.15) return 2;
    }
    bt += 2.4 + rand(k + 100) * 2.2;
  }
  return 0;
};

export const buildCues = (base: PoseCue[], words: TimedWord[] = [], triggers: Triggers = {}): PoseCue[] => {
  const cues = [...base];
  for (const w of words) {
    const key = w.word.toLowerCase().replace(/[^a-z0-9']/g, "");
    const trg = triggers[key];
    if (!trg) continue;
    const start = w.start - 0.05;
    const resume = [...base].reverse().find((c) => c.t <= start + (trg.dur ?? 1));
    cues.push({ t: start, pose: trg.pose });
    if (resume) cues.push({ t: start + (trg.dur ?? 1), pose: resume.pose });
  }
  return cues.sort((a, b) => a.t - b.t);
};

export const PuppetTrack: React.FC<{
  cues: PoseCue[]; lipsync?: LipSync; words?: TimedWord[]; triggers?: Triggers; fadeFrames?: number;
}> = ({ cues, lipsync, words, triggers, fadeFrames = 3 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const all = buildCues(cues, words, triggers);

  let i = 0;
  while (i + 1 < all.length && all[i + 1].t <= t) i++;
  const cur = all[i];
  const prev = i > 0 ? all[i - 1] : null;
  const since = frame - Math.round(cur.t * fps);
  const fade = prev && prev.pose !== cur.pose && since < fadeFrames ? (since + 1) / (fadeFrames + 1) : 1;

  const ls = lipsync?.frames[Math.min(frame, (lipsync?.frames.length ?? 1) - 1)];
  const viseme = (ls?.v ?? "rest") as Viseme;
  const e = ls?.e ?? 0;
  const drift = Math.sin(t * 1.3) * 1.2 + Math.sin(t * 0.7 + 1) * 0.8;
  const nod = e * Math.sin(t * 9) * 0.8 + e * 0.6;
  const bounce = e * 6;   // px: the body bobs with the voice

  const common = { viseme, blink: blinkState(t), headTilt: drift, headNod: nod, breathe: Math.sin(t * 2.2), look: Math.sin(t * 0.5) * 1.5 };
  return (
    <div style={{ position: "relative", width: "100%", height: "100%", transform: `translateY(${-bounce}px)` }}>
      {prev && fade < 1 ? (
        <div style={{ position: "absolute", inset: 0, opacity: 1 - fade }}><Nova pose={prev.pose} {...common} /></div>
      ) : null}
      <div style={{ position: "absolute", inset: 0, opacity: fade }}><Nova pose={cur.pose} {...common} /></div>
    </div>
  );
};
