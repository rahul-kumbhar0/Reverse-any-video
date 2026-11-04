import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * Word-timed karaoke captions (dark-explainer style): one phrase in the top band, each
 * word fading in exactly when it is spoken (from align_words.py), emphasis words bold
 * white, one key word wrapped in an iOS-style selection box that draws when spoken.
 */
export type TimedWord = { word: string; start: number; end: number };
export type Phrase = {
  from: number; // first word index (inclusive)
  to: number;   // last word index (inclusive)
  styles?: Record<number, "bold" | "box">;
  text?: Record<number, string>; // display overrides, e.g. punctuation: {3: "trackpad?"}
};

const DIM = "#9A9AA0", WHITE = "#FFFFFF", BLUE = "#3478F6";
const FONT = "-apple-system, 'SF Pro Display', Inter, 'Helvetica Neue', Arial, sans-serif";

export const KaraokeCaption: React.FC<{ words: TimedWord[]; phrases: Phrase[]; topPct?: number }> = ({
  words, phrases, topPct = 7,
}) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const t = frame / fps;
  let pi = -1;
  phrases.forEach((p, i) => { if (t >= words[p.from].start - 0.05) pi = i; });
  if (pi < 0) return null;
  const ph = phrases[pi];
  const size = height * 0.032;

  return (
    <div style={{ position: "absolute", top: `${topPct}%`, left: "6%", right: "6%", textAlign: "center",
      fontFamily: FONT, fontSize: size, lineHeight: 1.45 }}>
      {Array.from({ length: ph.to - ph.from + 1 }, (_, k) => {
        const i = ph.from + k;
        const w = words[i];
        const style = ph.styles?.[i];
        const label = ph.text?.[i] ?? w.word;
        const op = interpolate(t, [w.start - 0.04, w.start + 0.08], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const rise = (1 - op) * 6;
        if (style === "box") {
          const draw = interpolate(t, [w.start, w.start + 0.2], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <span key={i} style={{ position: "relative", display: "inline-block", padding: "2px 14px", margin: "0 4px",
              borderRadius: 10, border: `3px solid rgba(52,120,246,${draw})`, background: `rgba(52,120,246,${0.1 * draw})`,
              color: WHITE, fontWeight: 700, opacity: op, transform: `translateY(${rise}px)` }}>
              {label}
              <span style={{ position: "absolute", left: -8, top: -8, width: 14, height: 14, borderRadius: 7, background: BLUE, opacity: draw }} />
              <span style={{ position: "absolute", right: -8, bottom: -8, width: 14, height: 14, borderRadius: 7, background: BLUE, opacity: draw }} />
            </span>
          );
        }
        return (
          <span key={i} style={{ display: "inline-block", margin: "0 6px", color: style === "bold" ? WHITE : DIM,
            fontWeight: style === "bold" ? 700 : 400, opacity: op, transform: `translateY(${rise}px)` }}>{label}</span>
        );
      })}
    </div>
  );
};
