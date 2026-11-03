import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

/* ============================================================
   mascot-tech-explainer style renderer
   30s worked example: "elevator door-close button"
   Style spec: ../style-spec.json
   ============================================================ */

export const TOTAL_SECONDS = 30;

const C = {
  bg: "#0C0C0E",
  grid: "rgba(255,255,255,0.055)",
  white: "#FFFFFF",
  dim: "#9A9AA0",
  amber: "#E0A33E",
  blue: "#3478F6",
  surface: "#1C1C1E",
  metal: "#2A2A2E",
  skin: "#F2C6A0",
};

const FONT =
  "-apple-system, 'SF Pro Display', Inter, 'Helvetica Neue', Arial, sans-serif";

/* ---------- caption system ---------- */
type Word = { t: string; k?: "dim" | "bold" | "box" };
type Beat = {
  start: number;
  end: number;
  words: Word[];
  words2?: Word[]; // optional second line
  pose: Pose;
  scene: number;
};

const BEATS: Beat[] = [
  { start: 0.0, end: 2.0, scene: 0, pose: "point-up",
    words: [{ t: "That", k: "dim" }, { t: "door-close", k: "box" }, { t: "button", k: "dim" }] },
  { start: 2.0, end: 4.0, scene: 0, pose: "thumbs-up",
    words: [{ t: "you always", k: "dim" }, { t: "press", k: "bold" }] },
  { start: 4.0, end: 6.5, scene: 0, pose: "shrug",
    words: [{ t: "probably does", k: "dim" }, { t: "nothing.", k: "box" }] },
  { start: 6.5, end: 10.0, scene: 3, pose: "hips",
    words: [{ t: "what you", k: "dim" }, { t: "see", k: "bold" }],
    words2: [{ t: "vs what's", k: "dim" }, { t: "connected", k: "bold" }] },
  { start: 10.0, end: 13.0, scene: 4, pose: "facepalm",
    words: [{ t: "firefighters", k: "box" }, { t: "get the real one", k: "dim" }] },
  { start: 13.0, end: 16.0, scene: 5, pose: "hips",
    words: [{ t: "since", k: "dim" }, { t: "1990.", k: "box" }] },
  { start: 16.0, end: 20.0, scene: 6, pose: "point-up",
    words: [{ t: "it", k: "dim" }, { t: "used", k: "bold" }, { t: "to work", k: "dim" }] },
  { start: 20.0, end: 23.5, scene: 7, pose: "clutch",
    words: [{ t: "then it became", k: "dim" }, { t: "placebo.", k: "box" }] },
  { start: 23.5, end: 26.5, scene: 8, pose: "peace",
    words: [{ t: "but pressing it", k: "dim" }, { t: "feels", k: "bold" }, { t: "faster", k: "dim" }] },
  { start: 26.5, end: 30.0, scene: 9, pose: "fist",
    words: [{ t: "send this to the", k: "dim" }, { t: "impatient", k: "box" }, { t: "one", k: "dim" }] },
];

const SelectionBox: React.FC<{ children: React.ReactNode; draw: number }> = ({
  children,
  draw,
}) => (
  <span
    style={{
      position: "relative",
      display: "inline-block",
      padding: "2px 14px",
      margin: "0 4px",
      borderRadius: 10,
      border: `3px solid ${C.blue}`,
      background: "rgba(52,120,246,0.10)",
      color: C.white,
      fontWeight: 700,
      opacity: draw,
    }}
  >
    {children}
    <span style={{ position: "absolute", left: -8, top: -8, width: 14, height: 14, borderRadius: 7, background: C.blue }} />
    <span style={{ position: "absolute", right: -8, bottom: -8, width: 14, height: 14, borderRadius: 7, background: C.blue }} />
  </span>
);

const CaptionLine: React.FC<{ words: Word[]; size: number; boxDraw: number }> = ({
  words,
  size,
  boxDraw,
}) => (
  <div style={{ fontFamily: FONT, fontSize: size, textAlign: "center", lineHeight: 1.45 }}>
    {words.map((w, i) =>
      w.k === "box" ? (
        <SelectionBox key={i} draw={boxDraw}>{w.t}</SelectionBox>
      ) : (
        <span
          key={i}
          style={{
            color: w.k === "bold" ? C.white : C.dim,
            fontWeight: w.k === "bold" ? 700 : 400,
            margin: "0 6px",
          }}
        >
          {w.t}
        </span>
      )
    )}
  </div>
);

const Captions: React.FC<{ beat: Beat; tIn: number }> = ({ beat, tIn }) => {
  const { height } = useVideoConfig();
  const size = height * 0.032;
  const opacity = interpolate(tIn, [0, 0.15], [0, 1], { extrapolateRight: "clamp" });
  const rise = interpolate(tIn, [0, 0.15], [8, 0], { extrapolateRight: "clamp" });
  const boxDraw = interpolate(tIn, [0.1, 0.3], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        top: height * 0.07,
        left: "6%",
        right: "6%",
        opacity,
        transform: `translateY(${rise}px)`,
      }}
    >
      <CaptionLine words={beat.words} size={size} boxDraw={boxDraw} />
      {beat.words2 ? (
        <div style={{ marginTop: 10 }}>
          <CaptionLine words={beat.words2} size={size} boxDraw={boxDraw} />
        </div>
      ) : null}
    </div>
  );
};

/* ---------- mascot (NEW character: teal hoodie + orange beanie) ---------- */
type Pose =
  | "point-up" | "thumbs-up" | "shrug" | "hips"
  | "facepalm" | "clutch" | "peace" | "fist";

const Mascot: React.FC<{ pose: Pose }> = ({ pose }) => {
  const arms: Record<Pose, React.ReactNode> = {
    "point-up": (
      <>
        <path d="M78 150 Q60 165 52 185" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
        <path d="M122 150 Q150 120 158 78" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
        <circle cx="158" cy="70" r="10" fill={C.skin} />
      </>
    ),
    "thumbs-up": (
      <>
        <path d="M78 150 Q60 165 52 185" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
        <path d="M122 150 Q152 140 160 115" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
        <rect x="152" y="94" width="16" height="22" rx="8" fill={C.skin} />
      </>
    ),
    shrug: (
      <>
        <path d="M78 150 Q48 135 38 118" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
        <path d="M122 150 Q152 135 162 118" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
        <circle cx="36" cy="112" r="10" fill={C.skin} />
        <circle cx="164" cy="112" r="10" fill={C.skin} />
      </>
    ),
    hips: (
      <>
        <path d="M78 150 Q52 160 62 182" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
        <path d="M122 150 Q148 160 138 182" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
      </>
    ),
    facepalm: (
      <>
        <path d="M78 150 Q60 165 52 185" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
        <path d="M122 150 Q135 110 112 72" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
        <circle cx="108" cy="64" r="12" fill={C.skin} />
      </>
    ),
    clutch: (
      <>
        <path d="M78 150 Q58 105 76 62" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
        <path d="M122 150 Q142 105 124 62" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
        <circle cx="78" cy="56" r="10" fill={C.skin} />
        <circle cx="122" cy="56" r="10" fill={C.skin} />
      </>
    ),
    peace: (
      <>
        <path d="M78 150 Q60 165 52 185" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
        <path d="M122 150 Q150 125 156 92" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
        <path d="M150 88 L146 66 M160 88 L166 66" stroke={C.skin} strokeWidth="9" strokeLinecap="round" />
      </>
    ),
    fist: (
      <>
        <path d="M78 150 Q60 165 52 185" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
        <path d="M122 150 Q152 118 156 86" stroke="#1F7A74" strokeWidth="16" fill="none" strokeLinecap="round" />
        <circle cx="157" cy="80" r="13" fill={C.skin} />
      </>
    ),
  };
  const mouth: Record<string, React.ReactNode> = {
    happy: <path d="M86 94 Q100 106 114 94" stroke="#7A4A2B" strokeWidth="5" fill="none" strokeLinecap="round" />,
    flat: <path d="M88 98 L112 98" stroke="#7A4A2B" strokeWidth="5" strokeLinecap="round" />,
    open: <ellipse cx="100" cy="98" rx="10" ry="12" fill="#7A4A2B" />,
  };
  const mouthFor: Record<Pose, React.ReactNode> = {
    "point-up": mouth.open, "thumbs-up": mouth.happy, shrug: mouth.flat,
    hips: mouth.happy, facepalm: mouth.flat, clutch: mouth.open,
    peace: mouth.happy, fist: mouth.open,
  };
  return (
    <svg viewBox="0 0 200 260" style={{ width: "100%", height: "100%" }}>
      {/* body: teal hoodie */}
      <path d="M58 255 L58 165 Q58 138 100 138 Q142 138 142 165 L142 255 Z" fill="#26968E" />
      <path d="M72 140 Q100 158 128 140 L128 162 Q100 176 72 162 Z" fill="#1F7A74" />
      {arms[pose]}
      {/* head */}
      <circle cx="100" cy="78" r="42" fill={C.skin} />
      {/* orange beanie */}
      <path d="M58 72 Q58 30 100 30 Q142 30 142 72 L142 60 Q142 50 132 50 L68 50 Q58 50 58 60 Z" fill="#E8762C" />
      <rect x="56" y="58" width="88" height="14" rx="7" fill="#D16522" />
      {/* eyes + brows */}
      <circle cx="85" cy="82" r="5" fill="#2B2B2E" />
      <circle cx="115" cy="82" r="5" fill="#2B2B2E" />
      {mouthFor[pose]}
    </svg>
  );
};

/* ---------- stage scenes ---------- */

const Panel: React.FC<{ glow?: number; pressed?: boolean; vintage?: boolean; scale?: number }> = ({
  glow = 0,
  pressed = false,
  vintage = false,
  scale = 1,
}) => {
  const btn = (label: string, hot = false) => (
    <div
      style={{
        width: 150, height: 150, borderRadius: 75,
        background: vintage ? "#C9B690" : "#17171A",
        border: `4px solid ${hot && glow > 0 ? C.amber : vintage ? "#8A7A55" : "#3A3A40"}`,
        boxShadow: hot && glow > 0 ? `0 0 ${60 * glow}px ${18 * glow}px rgba(224,163,62,0.45)` : "0 8px 20px rgba(0,0,0,0.6)",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: FONT, fontSize: 52, fontWeight: 700,
        color: hot && glow > 0 ? C.amber : vintage ? "#5A4A2B" : "#B9B9C0",
        transform: hot && pressed ? "scale(0.93)" : "scale(1)",
      }}
    >
      {label}
    </div>
  );
  return (
    <div
      style={{
        width: 560, padding: "70px 60px", borderRadius: 36,
        background: vintage
          ? "linear-gradient(160deg,#8A7A55,#6B5C3D)"
          : `linear-gradient(160deg,${C.metal},#1A1A1E)`,
        display: "grid", gridTemplateColumns: "1fr 1fr", gap: 50,
        justifyItems: "center", transform: `scale(${scale})`,
        boxShadow: "0 30px 80px rgba(0,0,0,0.7)",
      }}
    >
      {btn("▲")}{btn("▼")}{btn("⟨|⟩")}{btn("⟩|⟨", true)}
    </div>
  );
};

const Finger: React.FC<{ x: number; y: number; press: number }> = ({ x, y, press }) => (
  <div
    style={{
      position: "absolute", left: x, top: y + press * 40,
      width: 210, height: 400, borderRadius: "105px 105px 40px 40px",
      background: `linear-gradient(180deg, ${C.skin}, #D8A478)`,
      boxShadow: "0 -10px 50px rgba(0,0,0,0.5)",
      transform: "rotate(8deg)",
    }}
  >
    <div style={{ position: "absolute", top: 26, left: 48, width: 134, height: 150, borderRadius: 60, background: "rgba(255,255,255,0.28)" }} />
  </div>
);

const Annotation: React.FC<{ x1: number; y1: number; x2: number; y2: number; label: string; show: number }> = ({
  x1, y1, x2, y2, label, show,
}) => (
  <div style={{ position: "absolute", inset: 0, opacity: show, pointerEvents: "none" }}>
    <svg style={{ position: "absolute", inset: 0, overflow: "visible" }} width="560" height="900">
      <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="white" strokeWidth="2" />
      <circle cx={x1} cy={y1} r="6" fill="white" />
    </svg>
    <div style={{ position: "absolute", left: x2 - 200, top: y2 - 56, width: 400, textAlign: "center", fontFamily: FONT, fontSize: 30, color: C.white }}>
      {label}
    </div>
  </div>
);

const Footnote: React.FC<{ left?: string; right?: string }> = ({ left, right }) => (
  <>
    {left ? <div style={{ position: "absolute", bottom: "22%", left: "4%", fontFamily: FONT, fontSize: 22, color: "#6E6E74" }}>{left}</div> : null}
    {right ? <div style={{ position: "absolute", bottom: "22%", right: "4%", fontFamily: FONT, fontSize: 22, color: "#6E6E74", textAlign: "right" }}>{right}</div> : null}
  </>
);

const Wiring: React.FC<{ show: number }> = ({ show }) => (
  <svg width="900" height="700" viewBox="0 0 900 700" style={{ opacity: show }}>
    {[
      { x: 180, ok: true }, { x: 380, ok: true }, { x: 580, ok: true },
    ].map((w, i) => (
      <g key={i}>
        <line x1={w.x} y1={80} x2={w.x} y2={560} stroke={C.amber} strokeWidth="5" />
        <circle cx={w.x} cy={580} r="16" fill={C.amber} />
      </g>
    ))}
    {/* door-close: not connected */}
    <line x1={780} y1={80} x2={780} y2={360} stroke="#55555C" strokeWidth="5" strokeDasharray="14 14" />
    <circle cx={780} cy={390} r="16" fill="none" stroke="#55555C" strokeWidth="5" />
    <text x={180} y={640} fill={C.dim} fontSize="30" fontFamily={FONT} textAnchor="middle">▲</text>
    <text x={380} y={640} fill={C.dim} fontSize="30" fontFamily={FONT} textAnchor="middle">▼</text>
    <text x={580} y={640} fill={C.dim} fontSize="30" fontFamily={FONT} textAnchor="middle">open</text>
    <text x={780} y={640} fill={C.dim} fontSize="30" fontFamily={FONT} textAnchor="middle">close</text>
  </svg>
);

const EvidenceCard: React.FC = () => (
  <div
    style={{
      width: 760, borderRadius: 28, background: C.surface,
      border: "1px solid #2E2E34", padding: "56px 60px",
      fontFamily: FONT, color: C.white,
      boxShadow: "0 30px 80px rgba(0,0,0,0.7)",
    }}
  >
    <div style={{ fontSize: 30, color: C.dim, marginBottom: 18 }}>U.S. federal law</div>
    <div style={{ fontSize: 44, fontWeight: 700, lineHeight: 1.25 }}>
      Americans with Disabilities Act — <span style={{ color: C.amber }}>1990</span>
    </div>
    <div style={{ fontSize: 28, color: C.dim, marginTop: 22, lineHeight: 1.5 }}>
      Doors must stay open long enough for everyone. The close button's timing is out of your hands.
    </div>
  </div>
);

const ShareSheet: React.FC<{ rise: number; tap: number }> = ({ rise, tap }) => {
  const people = ["A", "D", "M", "L"];
  return (
    <div
      style={{
        width: 860, borderRadius: 40, background: C.surface,
        border: "1px solid #2E2E34", padding: "50px 50px 70px",
        fontFamily: FONT, transform: `translateY(${(1 - rise) * 500}px)`,
        boxShadow: "0 -30px 80px rgba(0,0,0,0.7)",
      }}
    >
      <div style={{ width: 90, height: 8, borderRadius: 4, background: "#3A3A40", margin: "0 auto 40px" }} />
      <div style={{ height: 76, borderRadius: 20, background: "#28282E", display: "flex", alignItems: "center", padding: "0 28px", color: C.dim, fontSize: 30, marginBottom: 46 }}>
        🔍&nbsp; Search
      </div>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        {people.map((p, i) => (
          <div key={p} style={{ textAlign: "center" }}>
            <div
              style={{
                width: 130, height: 130, borderRadius: 65,
                background: `hsl(${40 + i * 70}, 35%, 35%)`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 52, color: C.white, fontWeight: 700,
                border: i === 0 && tap > 0.5 ? `5px solid ${C.blue}` : "5px solid transparent",
                transform: i === 0 && tap > 0.5 ? "scale(0.95)" : "scale(1)",
              }}
            >
              {p}
            </div>
            <div style={{ color: i === 0 && tap > 0.5 ? C.blue : C.dim, fontSize: 26, marginTop: 14 }}>
              {i === 0 ? (tap > 0.5 ? "Sent ✓" : "alex") : ["dani", "mia", "leo"][i - 1]}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

/* ---------- scene composer ---------- */
const Stage: React.FC<{ t: number; scene: number; sceneT: number }> = ({ t, scene, sceneT }) => {
  const { width, height } = useVideoConfig();
  // constant slow camera drift (style rule: nothing fully static)
  const drift = 1 + 0.015 * (t / TOTAL_SECONDS);

  const center: React.CSSProperties = {
    position: "absolute", top: height * 0.17, left: 0, right: 0, bottom: height * 0.21,
    display: "flex", alignItems: "center", justifyContent: "center",
  };

  let content: React.ReactNode = null;
  let footL: string | undefined; let footR: string | undefined;

  if (scene === 0) {
    // macro panel + finger: one continuous scene across beats 1-3
    const glow = t > 2 ? 1 : 0.25;
    const press = interpolate(t, [2.3, 3.0, 3.8], [0, 1, 0.15], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    const zoom = 1.12 + t * 0.035;
    content = (
      <div style={{ transform: `scale(${zoom})` }}>
        <Panel glow={glow} pressed={press > 0.5} />
        <Finger x={330} y={430} press={press} />
      </div>
    );
    footL = "Illustration";
  } else if (scene === 3) {
    content = <Wiring show={interpolate(sceneT, [0, 0.4], [0, 1], { extrapolateRight: "clamp" })} />;
    footL = "Simplified wiring";
  } else if (scene === 4) {
    content = (
      <div style={{ transform: "scale(1.02)" }}>
        <Panel glow={0.4} />
        <Annotation x1={390} y1={345} x2={160} y2={-60} label="bypass circuit — fire service only"
          show={interpolate(sceneT, [0.15, 0.45], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
      </div>
    );
    footR = "Varies by installation";
  } else if (scene === 5) {
    content = <EvidenceCard />;
    footR = "In many U.S. installations";
  } else if (scene === 6) {
    content = <div style={{ transform: `scale(${1 + sceneT * 0.04})` }}><Panel vintage glow={1} /></div>;
    footL = "1980s panel — illustrative";
  } else if (scene === 7) {
    content = (
      <div style={{ display: "flex", gap: 40, transform: "scale(0.62)", alignItems: "center" }}>
        <div style={{ textAlign: "center" }}>
          <Panel vintage glow={1} />
          <div style={{ fontFamily: FONT, color: C.amber, fontSize: 44, marginTop: 30 }}>1985 · wired</div>
        </div>
        <div style={{ textAlign: "center" }}>
          <Panel glow={0} />
          <div style={{ fontFamily: FONT, color: C.dim, fontSize: 44, marginTop: 30 }}>today · placebo</div>
        </div>
      </div>
    );
  } else if (scene === 8) {
    content = (
      <div style={{ transform: `scale(${1.1 + sceneT * 0.08})` }}>
        <Panel glow={0.8} />
        <Finger x={330} y={430} press={interpolate(sceneT, [0.3, 0.6, 1], [0, 1, 0.4], { extrapolateRight: "clamp" })} />
      </div>
    );
  } else {
    content = (
      <ShareSheet
        rise={interpolate(sceneT, [0, 0.3], [0, 1], { extrapolateRight: "clamp" })}
        tap={interpolate(sceneT, [0.55, 0.7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}
      />
    );
  }

  // morph in: scale+fade (no hard cuts)
  const morphIn = interpolate(sceneT, [0, 0.35], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", inset: 0, transform: `scale(${drift})` }}>
      <div style={{ ...center, opacity: morphIn, transform: `scale(${0.96 + morphIn * 0.04})` }}>
        {content}
      </div>
      <Footnote left={footL} right={footR} />
    </div>
  );
};

/* ---------- root ---------- */
export const Main: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;

  const beat = BEATS.find((b) => t >= b.start && t < b.end) ?? BEATS[BEATS.length - 1];
  const tIn = t - beat.start;

  // scene timing: sceneT measured from first beat of that scene
  const sceneStart = BEATS.find((b) => b.scene === beat.scene)!.start;
  const sceneEnd = [...BEATS].reverse().find((b) => b.scene === beat.scene)!.end;
  const sceneT = (t - sceneStart) / Math.max(0.001, sceneEnd - sceneStart);

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {/* blueprint grid */}
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${C.grid} 1px, transparent 1px), linear-gradient(90deg, ${C.grid} 1px, transparent 1px)`,
          backgroundSize: "68px 68px",
        }}
      />
      <Stage t={t} scene={beat.scene} sceneT={sceneT} />
      <Captions beat={beat} tIn={tIn} />
      {/* mascot band */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: "50%",
          transform: "translateX(-50%)",
          width: height * 0.18 * (200 / 260),
          height: height * 0.18,
        }}
      >
        <Mascot pose={beat.pose} />
      </div>
    </AbsoluteFill>
  );
};
