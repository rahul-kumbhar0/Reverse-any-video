import React from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

/* ============================================================
   "Why LEGO bricks never let go" — photoreal-tech-explainer style
   Blender hero shots composited under the caption/mascot system.
   ============================================================ */

export const TOTAL_SECONDS = 42;

const C = {
  bg: "#050507",
  white: "#FFFFFF",
  dim: "#9A9AA0",
  amber: "#E0A33E",
  blue: "#3478F6",
  surface: "#1C1C1E",
  skin: "#F2C6A0",
};
const FONT =
  "-apple-system, 'SF Pro Display', Inter, 'Helvetica Neue', Arial, sans-serif";

/* ---------- captions ---------- */
type Word = { t: string; k?: "dim" | "bold" | "box" };
type Pose =
  | "point-up" | "thumbs-up" | "shrug" | "hips"
  | "facepalm" | "clutch" | "peace" | "fist";
type Beat = { start: number; end: number; words: Word[]; words2?: Word[]; pose: Pose };

const BEATS: Beat[] = [
  { start: 0.0, end: 2.0, pose: "point-up",
    words: [{ t: "Every LEGO brick", k: "dim" }, { t: "ever made", k: "box" }] },
  { start: 2.0, end: 4.0, pose: "thumbs-up",
    words: [{ t: "still", k: "dim" }, { t: "fits", k: "bold" }, { t: "every other one", k: "dim" }] },
  { start: 4.0, end: 6.5, pose: "shrug",
    words: [{ t: "the secret is", k: "dim" }, { t: "0.01mm", k: "box" }] },
  { start: 6.5, end: 10.5, pose: "hips",
    words: [{ t: "the studs are slightly", k: "dim" }, { t: "too big", k: "bold" }],
    words2: [{ t: "for the gap", k: "dim" }] },
  { start: 10.5, end: 13.0, pose: "point-up",
    words: [{ t: "so the plastic", k: "dim" }, { t: "flexes", k: "box" }] },
  { start: 13.0, end: 16.0, pose: "fist",
    words: [{ t: "and", k: "dim" }, { t: "pushes", k: "bold" }, { t: "back. forever.", k: "dim" }] },
  { start: 16.0, end: 19.5, pose: "point-up",
    words: [{ t: "they call it", k: "dim" }, { t: "clutch power", k: "box" }] },
  { start: 19.5, end: 23.0, pose: "hips",
    words: [{ t: "patented in", k: "dim" }, { t: "1958.", k: "box" }] },
  { start: 23.0, end: 27.0, pose: "peace",
    words: [{ t: "a", k: "dim" }, { t: "1958", k: "bold" }, { t: "brick still clicks today", k: "dim" }] },
  { start: 27.0, end: 30.5, pose: "point-up",
    words: [{ t: "molds accurate to", k: "dim" }, { t: "0.004mm", k: "box" }] },
  { start: 30.5, end: 34.0, pose: "clutch",
    words: [{ t: "only", k: "dim" }, { t: "18 in a million", k: "bold" }, { t: "fail", k: "dim" }] },
  { start: 34.0, end: 37.0, pose: "fist",
    words: [{ t: "that click is", k: "dim" }, { t: "engineering.", k: "box" }] },
  { start: 37.0, end: 42.0, pose: "fist",
    words: [{ t: "send this to a", k: "dim" }, { t: "builder", k: "box" }] },
];

const SelectionBox: React.FC<{ children: React.ReactNode; draw: number }> = ({ children, draw }) => (
  <span style={{
    position: "relative", display: "inline-block", padding: "2px 14px", margin: "0 4px",
    borderRadius: 10, border: `3px solid ${C.blue}`, background: "rgba(52,120,246,0.10)",
    color: C.white, fontWeight: 700, opacity: draw,
  }}>
    {children}
    <span style={{ position: "absolute", left: -8, top: -8, width: 14, height: 14, borderRadius: 7, background: C.blue }} />
    <span style={{ position: "absolute", right: -8, bottom: -8, width: 14, height: 14, borderRadius: 7, background: C.blue }} />
  </span>
);

const CaptionLine: React.FC<{ words: Word[]; size: number; boxDraw: number }> = ({ words, size, boxDraw }) => (
  <div style={{ fontFamily: FONT, fontSize: size, textAlign: "center", lineHeight: 1.45 }}>
    {words.map((w, i) =>
      w.k === "box" ? (
        <SelectionBox key={i} draw={boxDraw}>{w.t}</SelectionBox>
      ) : (
        <span key={i} style={{
          color: w.k === "bold" ? C.white : C.dim,
          fontWeight: w.k === "bold" ? 700 : 400, margin: "0 6px",
        }}>{w.t}</span>
      )
    )}
  </div>
);

const Captions: React.FC<{ beat: Beat; tIn: number }> = ({ beat, tIn }) => {
  const { height } = useVideoConfig();
  const size = height * 0.032;
  const opacity = interpolate(tIn, [0, 0.15], [0, 1], { extrapolateRight: "clamp" });
  const rise = interpolate(tIn, [0, 0.15], [8, 0], { extrapolateRight: "clamp" });
  const boxDraw = interpolate(tIn, [0.1, 0.3], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", top: height * 0.07, left: "6%", right: "6%", opacity, transform: `translateY(${rise}px)` }}>
      <CaptionLine words={beat.words} size={size} boxDraw={boxDraw} />
      {beat.words2 ? <div style={{ marginTop: 10 }}><CaptionLine words={beat.words2} size={size} boxDraw={boxDraw} /></div> : null}
    </div>
  );
};

/* ---------- mascot (teal hoodie + orange beanie; crossfaded poses) ---------- */
const MascotSVG: React.FC<{ pose: Pose }> = ({ pose }) => {
  const arms: Record<Pose, React.ReactNode> = {
    "point-up": (<>
      <path d="M78 150 Q60 165 52 185" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      <path d="M122 150 Q150 120 158 78" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      <circle cx="158" cy="70" r="10" fill={C.skin} /></>),
    "thumbs-up": (<>
      <path d="M78 150 Q60 165 52 185" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      <path d="M122 150 Q152 140 160 115" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      <rect x="152" y="94" width="16" height="22" rx="8" fill={C.skin} /></>),
    shrug: (<>
      <path d="M78 150 Q48 135 38 118" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      <path d="M122 150 Q152 135 162 118" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      <circle cx="36" cy="112" r="10" fill={C.skin} /><circle cx="164" cy="112" r="10" fill={C.skin} /></>),
    hips: (<>
      <path d="M78 150 Q52 160 62 182" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      <path d="M122 150 Q148 160 138 182" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" /></>),
    facepalm: (<>
      <path d="M78 150 Q60 165 52 185" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      <path d="M122 150 Q135 110 112 72" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      <circle cx="108" cy="64" r="12" fill={C.skin} /></>),
    clutch: (<>
      <path d="M78 150 Q58 105 76 62" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      <path d="M122 150 Q142 105 124 62" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      <circle cx="78" cy="56" r="10" fill={C.skin} /><circle cx="122" cy="56" r="10" fill={C.skin} /></>),
    peace: (<>
      <path d="M78 150 Q60 165 52 185" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      <path d="M122 150 Q150 125 156 92" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      <path d="M150 88 L146 66 M160 88 L166 66" stroke={C.skin} strokeWidth="9" strokeLinecap="round" /></>),
    fist: (<>
      <path d="M78 150 Q60 165 52 185" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      <path d="M122 150 Q152 118 156 86" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      <circle cx="157" cy="80" r="13" fill={C.skin} /></>),
  };
  const mouths: Record<string, React.ReactNode> = {
    happy: <path d="M86 94 Q100 106 114 94" stroke="#7A4A2B" strokeWidth="5" fill="none" strokeLinecap="round" />,
    flat: <path d="M88 98 L112 98" stroke="#7A4A2B" strokeWidth="5" strokeLinecap="round" />,
    open: <ellipse cx="100" cy="98" rx="10" ry="12" fill="#7A4A2B" />,
  };
  const mouthFor: Record<Pose, React.ReactNode> = {
    "point-up": mouths.open, "thumbs-up": mouths.happy, shrug: mouths.flat,
    hips: mouths.happy, facepalm: mouths.flat, clutch: mouths.open,
    peace: mouths.happy, fist: mouths.open,
  };
  return (
    <svg viewBox="0 0 200 260" style={{ width: "100%", height: "100%" }}>
      <path d="M58 255 L58 165 Q58 138 100 138 Q142 138 142 165 L142 255 Z" fill="#26968E" />
      <path d="M72 140 Q100 158 128 140 L128 162 Q100 176 72 162 Z" fill="#1F7A74" />
      {arms[pose]}
      <circle cx="100" cy="78" r="42" fill={C.skin} />
      <path d="M58 72 Q58 30 100 30 Q142 30 142 72 L142 60 Q142 50 132 50 L68 50 Q58 50 58 60 Z" fill="#E8762C" />
      <rect x="56" y="58" width="88" height="14" rx="7" fill="#D16522" />
      <circle cx="85" cy="82" r="5" fill="#2B2B2E" /><circle cx="115" cy="82" r="5" fill="#2B2B2E" />
      {mouthFor[pose]}
    </svg>
  );
};

const Mascot: React.FC<{ t: number }> = ({ t }) => {
  const { height, fps } = useVideoConfig();
  const idx = BEATS.findIndex((b) => t >= b.start && t < b.end);
  const beat = BEATS[Math.max(0, idx)] ?? BEATS[BEATS.length - 1];
  const prev = BEATS[Math.max(0, idx - 1)];
  const tIn = t - beat.start;
  const fade = Math.min(1, tIn / 0.15); // 150ms crossfade (per motion-strip finding)
  const style: React.CSSProperties = {
    position: "absolute", bottom: 0, left: "50%", transform: "translateX(-50%)",
    width: height * 0.18 * (200 / 260), height: height * 0.18,
  };
  return (
    <>
      {prev && prev.pose !== beat.pose && fade < 1 ? (
        <div style={{ ...style, opacity: 1 - fade }}><MascotSVG pose={prev.pose} /></div>
      ) : null}
      <div style={{ ...style, opacity: fade }}><MascotSVG pose={beat.pose} /></div>
    </>
  );
};

/* ---------- overlays ---------- */
const Annotation: React.FC<{ label: string; x: string; y: string; lineTo: { x: string; y: string }; show: number }> = ({
  label, x, y, lineTo, show,
}) => (
  <div style={{ position: "absolute", inset: 0, opacity: show, pointerEvents: "none" }}>
    <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%", overflow: "visible" }}>
      <line x1={lineTo.x} y1={lineTo.y} x2={x} y2={y} stroke="white" strokeWidth="2" />
      <circle cx={lineTo.x} cy={lineTo.y} r="6" fill="white" />
    </svg>
    <div style={{
      position: "absolute", left: `calc(${x} - 220px)`, top: `calc(${y} - 60px)`, width: 440,
      textAlign: "center", fontFamily: FONT, fontSize: 30, color: C.white, letterSpacing: 2,
    }}>{label}</div>
  </div>
);

const Footnote: React.FC<{ left?: string; right?: string }> = ({ left, right }) => (
  <>
    {left ? <div style={{ position: "absolute", bottom: "21%", left: "4%", fontFamily: FONT, fontSize: 22, color: "#6E6E74" }}>{left}</div> : null}
    {right ? <div style={{ position: "absolute", bottom: "21%", right: "4%", fontFamily: FONT, fontSize: 22, color: "#6E6E74" }}>{right}</div> : null}
  </>
);

/* ---------- DOM scenes ---------- */
const CardScene: React.FC<{ children: React.ReactNode; tIn: number }> = ({ children, tIn }) => {
  const op = interpolate(tIn, [0, 0.35], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: op, transform: `scale(${0.97 + op * 0.03})` }}>
      {children}
    </AbsoluteFill>
  );
};

const PatentCard: React.FC = () => (
  <div style={{ width: 780, borderRadius: 28, background: C.surface, border: "1px solid #2E2E34", padding: "56px 60px", fontFamily: FONT, color: C.white, boxShadow: "0 30px 80px rgba(0,0,0,0.7)" }}>
    <div style={{ fontSize: 30, color: C.dim, marginBottom: 18 }}>U.S. Patent 3,005,282</div>
    <div style={{ fontSize: 46, fontWeight: 700, lineHeight: 1.25 }}>
      "Toy Building Brick" — filed <span style={{ color: C.amber }}>January 28, 1958</span>
    </div>
    <div style={{ fontSize: 28, color: C.dim, marginTop: 22, lineHeight: 1.5 }}>
      The stud-and-tube coupling in that filing is the same one inside every brick today.
    </div>
  </div>
);

const StatCard: React.FC<{ tIn: number }> = ({ tIn }) => {
  const n = Math.round(interpolate(tIn, [0.3, 1.6], [0, 18], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  return (
    <div style={{ width: 780, borderRadius: 28, background: C.surface, border: "1px solid #2E2E34", padding: "64px 60px", fontFamily: FONT, color: C.white, textAlign: "center", boxShadow: "0 30px 80px rgba(0,0,0,0.7)" }}>
      <div style={{ fontSize: 120, fontWeight: 700, color: C.amber }}>{n}</div>
      <div style={{ fontSize: 34, color: C.white, marginTop: 8 }}>bricks per <b>1,000,000</b></div>
      <div style={{ fontSize: 28, color: C.dim, marginTop: 16 }}>fail final inspection</div>
    </div>
  );
};

const ShareSheet: React.FC<{ tIn: number }> = ({ tIn }) => {
  const rise = interpolate(tIn, [0, 0.35], [0, 1], { extrapolateRight: "clamp" });
  const tap = interpolate(tIn, [1.6, 2.0], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const people = [["B", "the builder"], ["D", "dani"], ["M", "mia"], ["L", "leo"]] as const;
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: 860, borderRadius: 40, background: C.surface, border: "1px solid #2E2E34", padding: "50px 50px 70px", fontFamily: FONT, transform: `translateY(${(1 - rise) * 500}px)`, boxShadow: "0 -30px 80px rgba(0,0,0,0.7)" }}>
        <div style={{ width: 90, height: 8, borderRadius: 4, background: "#3A3A40", margin: "0 auto 40px" }} />
        <div style={{ height: 76, borderRadius: 20, background: "#28282E", display: "flex", alignItems: "center", padding: "0 28px", color: C.dim, fontSize: 30, marginBottom: 46 }}>🔍&nbsp; Search</div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          {people.map(([ini, name], i) => (
            <div key={ini} style={{ textAlign: "center" }}>
              <div style={{
                width: 130, height: 130, borderRadius: 65, background: `hsl(${20 + i * 70}, 38%, 36%)`,
                display: "flex", alignItems: "center", justifyContent: "center", fontSize: 52, color: C.white, fontWeight: 700,
                border: i === 0 && tap > 0.5 ? `5px solid ${C.blue}` : "5px solid transparent",
                transform: i === 0 && tap > 0.5 ? "scale(0.95)" : "scale(1)",
              }}>{ini}</div>
              <div style={{ color: i === 0 && tap > 0.5 ? C.blue : C.dim, fontSize: 26, marginTop: 14 }}>
                {i === 0 ? (tap > 0.5 ? "Sent ✓" : name) : name}
              </div>
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- video segment helper ---------- */
const Hero: React.FC<{ src: string; rate: number; zoom?: number }> = ({ src, rate, zoom = 1 }) => (
  <AbsoluteFill style={{ transform: `scale(${zoom})` }}>
    <OffthreadVideo src={staticFile(src)} muted playbackRate={rate}
      style={{ width: "100%", height: "100%", objectFit: "cover" }} />
  </AbsoluteFill>
);

/* ---------- root ---------- */
export const Main: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const beat = BEATS.find((b) => t >= b.start && t < b.end) ?? BEATS[BEATS.length - 1];
  const tIn = t - beat.start;
  const seq = (from: number, to: number) => ({
    from: Math.round(from * fps),
    durationInFrames: Math.round((to - from) * fps),
  });

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {/* hero segments */}
      <Sequence {...seq(0, 6.5)}><Hero src="s1.mp4" rate={0.54} /></Sequence>
      <Sequence {...seq(6.5, 13.5)}><Hero src="s2.mp4" rate={0.5} /></Sequence>
      <Sequence {...seq(13.5, 20.5)}>
        <Hero src="s3.mp4" rate={0.5} />
        <Annotation label="CLUTCH POWER" x="50%" y="24%" lineTo={{ x: "46%", y: "44%" }}
          show={interpolate(t, [16.2, 16.8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
        <Footnote left="Magnified illustration" />
      </Sequence>
      <Sequence {...seq(20.5, 24)}><CardScene tIn={t - 20.5}><PatentCard /></CardScene></Sequence>
      <Sequence {...seq(24, 30.5)}>
        <Hero src="s3.mp4" rate={0.54} zoom={1.25} />
        <Annotation label="± 0.004 MM" x="52%" y="26%" lineTo={{ x: "47%", y: "46%" }}
          show={interpolate(t, [27.3, 27.9], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
        <Footnote right="Tolerances: LEGO Group" />
      </Sequence>
      <Sequence {...seq(30.5, 34)}><CardScene tIn={t - 30.5}><StatCard tIn={t - 30.5} /></CardScene></Sequence>
      <Sequence {...seq(34, 37)}><Hero src="s1.mp4" rate={0.86} zoom={1.15} /></Sequence>
      <Sequence {...seq(37, 42)}><ShareSheet tIn={t - 37} /></Sequence>

      {/* soft vignette so DOM scenes sit in the same world */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, transparent 55%, rgba(0,0,0,0.5) 100%)", pointerEvents: "none" }} />

      <Captions beat={beat} tIn={tIn} />
      <Mascot t={t} />
    </AbsoluteFill>
  );
};
